# Production QA Framework: Unify → ADLS → Databricks → Power BI

## Enterprise Architecture for Data Reconciliation & Observability

This document extends the Control Tower simulation to a **production-ready QA Framework** for monitoring the complete Circana data pipeline.

---

## 1. Pipeline Layers & Reconciliation Points

### Layer 1: Unify (Circana) Source
- **What**: Syndicated POS data extracts
- **Format**: CSV files (60-150 files per product per week)
- **Reconciliation Point**: File manifest from Circana API
- **Key Metrics**:
  - Expected file count per product
  - Expected row count per file (based on historical baseline)
  - File delivery timestamp

### Layer 2: ADLS Landing Zone (Blob Storage)
- **What**: Raw files as received from Circana
- **Path Pattern**: `/raw/{product}/{yyyy}/{MM}/{dd}/`
- **Reconciliation Point**: ADLS file metadata
- **Key Metrics**:
  - Files received vs. expected
  - File size comparison (detect truncation)
  - File arrival latency (delivery timestamp vs. processing time)

### Layer 3: Databricks Medallion Architecture
- **Bronze**: Raw ingestion from ADLS
- **Silver**: Quality-checked data (Clean + Quarantine)
- **Gold**: Aggregated analytics
- **Reconciliation Points**:
  - Bronze row count = ADLS file row count
  - Silver (Clean + Quarantine) = Bronze
  - Gold aggregates reconcile to Silver Clean

### Layer 4: Power BI Semantic Model
- **What**: Imported or DirectQuery dataset
- **Reconciliation Point**: Semantic model refresh metadata
- **Key Metrics**:
  - Last refresh timestamp
  - Row count in model vs. Gold layer
  - Refresh duration and status

### Layer 5: User Reports
- **What**: Published reports consuming the semantic model
- **Reconciliation Point**: Visual-level row counts
- **Key Metrics**:
  - Report usage (who viewed, when)
  - Data staleness indicator

---

## 2. Reconciliation Framework Architecture

### End-to-End Reconciliation Table

Create a unified reconciliation table that tracks data across all layers:

**Schema: `reconciliation_control_tower`**

| Column | Type | Description |
|--------|------|-------------|
| recon_id | String | Unique ID: `{product}_{week_end}_{layer}` |
| product_name | String | Product identifier (e.g., "Nielsen_Retail") |
| week_end_date | Date | Reporting week Saturday |
| layer_name | String | Source, ADLS, Bronze, Silver, Gold, PBI |
| file_count_expected | Int | Expected number of files |
| file_count_actual | Int | Actual files received/processed |
| row_count_expected | Int | Expected rows (baseline or previous layer) |
| row_count_actual | Int | Actual rows processed |
| variance_pct | Float | ((actual - expected) / expected) * 100 |
| status | String | OK, WARNING, ERROR |
| error_details | String | Description of issue |
| check_timestamp | Timestamp | When reconciliation ran |
| data_timestamp | Timestamp | When data was created |
| latency_hours | Float | check_timestamp - data_timestamp |

### Reconciliation Logic (Databricks Notebook)

```python
# Databricks Notebook: reconciliation_framework.py

from pyspark.sql.functions import *
from datetime import datetime, timedelta
import requests

class ReconciliationEngine:
    """
    Enterprise reconciliation engine for multi-layer data lineage tracking.
    """
    
    def __init__(self, spark, product_name, week_end_date):
        self.spark = spark
        self.product_name = product_name
        self.week_end_date = week_end_date
        self.recon_results = []
    
    def check_adls_landing(self, expected_file_manifest):
        """
        Layer 1→2 Reconciliation: Verify files landed in ADLS.
        
        Args:
            expected_file_manifest (list): List of expected file names from Circana
        """
        from azure.storage.blob import BlobServiceClient
        
        # Connect to ADLS
        adls_path = f"/mnt/raw/{self.product_name}/{self.week_end_date.strftime('%Y/%m/%d')}/"
        
        # List actual files
        actual_files = dbutils.fs.ls(adls_path)
        actual_file_names = [f.name for f in actual_files]
        
        # Reconcile
        expected_count = len(expected_file_manifest)
        actual_count = len(actual_file_names)
        
        missing_files = set(expected_file_manifest) - set(actual_file_names)
        unexpected_files = set(actual_file_names) - set(expected_file_manifest)
        
        status = "OK"
        error_details = None
        
        if missing_files:
            status = "ERROR"
            error_details = f"Missing files: {', '.join(list(missing_files)[:5])}"
        elif unexpected_files:
            status = "WARNING"
            error_details = f"Unexpected files: {', '.join(list(unexpected_files)[:5])}"
        
        self.recon_results.append({
            "recon_id": f"{self.product_name}_{self.week_end_date}_ADLS",
            "product_name": self.product_name,
            "week_end_date": self.week_end_date,
            "layer_name": "ADLS_Landing",
            "file_count_expected": expected_count,
            "file_count_actual": actual_count,
            "variance_pct": ((actual_count - expected_count) / expected_count * 100) if expected_count > 0 else 0,
            "status": status,
            "error_details": error_details,
            "check_timestamp": datetime.now()
        })
        
        return actual_file_names
    
    def check_bronze_ingestion(self, adls_file_list):
        """
        Layer 2→3 Reconciliation: Verify ADLS files ingested to Bronze.
        """
        # Get row counts from ADLS files
        adls_row_count = 0
        for file_name in adls_file_list:
            file_path = f"/mnt/raw/{self.product_name}/{self.week_end_date.strftime('%Y/%m/%d')}/{file_name}"
            df_temp = spark.read.csv(file_path, header=True)
            adls_row_count += df_temp.count()
        
        # Get Bronze table row count
        bronze_df = spark.sql(f"""
            SELECT COUNT(*) as row_count 
            FROM bronze_{self.product_name.lower().replace('-', '_')}
            WHERE week_end_date = '{self.week_end_date}'
        """)
        bronze_row_count = bronze_df.first()['row_count']
        
        variance = ((bronze_row_count - adls_row_count) / adls_row_count * 100) if adls_row_count > 0 else 0
        
        status = "OK" if abs(variance) < 0.1 else "ERROR"
        error_details = f"Row count mismatch: ADLS={adls_row_count}, Bronze={bronze_row_count}" if status == "ERROR" else None
        
        self.recon_results.append({
            "recon_id": f"{self.product_name}_{self.week_end_date}_Bronze",
            "product_name": self.product_name,
            "week_end_date": self.week_end_date,
            "layer_name": "Bronze",
            "file_count_expected": len(adls_file_list),
            "file_count_actual": len(adls_file_list),
            "row_count_expected": adls_row_count,
            "row_count_actual": bronze_row_count,
            "variance_pct": variance,
            "status": status,
            "error_details": error_details,
            "check_timestamp": datetime.now()
        })
    
    def check_silver_quality(self):
        """
        Layer 3 (Bronze→Silver) Reconciliation: Verify Clean + Quarantine = Bronze.
        """
        # Get counts
        bronze_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM bronze_{self.product_name.lower().replace('-', '_')}
            WHERE week_end_date = '{self.week_end_date}'
        """).first()['cnt']
        
        clean_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM silver_{self.product_name.lower().replace('-', '_')}_clean
            WHERE week_end_date = '{self.week_end_date}'
        """).first()['cnt']
        
        quarantine_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM silver_{self.product_name.lower().replace('-', '_')}_quarantine
            WHERE week_end_date = '{self.week_end_date}'
        """).first()['cnt']
        
        silver_total = clean_count + quarantine_count
        variance = ((silver_total - bronze_count) / bronze_count * 100) if bronze_count > 0 else 0
        
        trust_score = (clean_count / bronze_count * 100) if bronze_count > 0 else 0
        
        status = "OK" if abs(variance) < 0.1 and trust_score >= 95 else "WARNING" if trust_score >= 90 else "ERROR"
        error_details = None
        
        if abs(variance) >= 0.1:
            error_details = f"Row count mismatch: Bronze={bronze_count}, Silver={silver_total}"
        elif trust_score < 95:
            error_details = f"Low trust score: {trust_score:.2f}%, Quarantine={quarantine_count}"
        
        self.recon_results.append({
            "recon_id": f"{self.product_name}_{self.week_end_date}_Silver",
            "product_name": self.product_name,
            "week_end_date": self.week_end_date,
            "layer_name": "Silver",
            "row_count_expected": bronze_count,
            "row_count_actual": silver_total,
            "variance_pct": variance,
            "status": status,
            "error_details": error_details,
            "trust_score_pct": trust_score,
            "check_timestamp": datetime.now()
        })
    
    def check_gold_aggregation(self):
        """
        Layer 4 (Silver→Gold) Reconciliation: Verify aggregation consistency.
        """
        # Sum of Silver Clean
        silver_sum = spark.sql(f"""
            SELECT SUM(sales_dollars) as total_sales
            FROM silver_{self.product_name.lower().replace('-', '_')}_clean
            WHERE week_end_date = '{self.week_end_date}'
        """).first()['total_sales'] or 0
        
        # Sum of Gold
        gold_sum = spark.sql(f"""
            SELECT SUM(total_revenue) as total_sales
            FROM gold_{self.product_name.lower().replace('-', '_')}_analytics
            WHERE week_end_date = '{self.week_end_date}'
        """).first()['total_sales'] or 0
        
        variance = ((gold_sum - silver_sum) / silver_sum * 100) if silver_sum > 0 else 0
        
        status = "OK" if abs(variance) < 0.01 else "ERROR"
        error_details = f"Aggregation mismatch: Silver=${silver_sum:,.2f}, Gold=${gold_sum:,.2f}" if status == "ERROR" else None
        
        self.recon_results.append({
            "recon_id": f"{self.product_name}_{self.week_end_date}_Gold",
            "product_name": self.product_name,
            "week_end_date": self.week_end_date,
            "layer_name": "Gold",
            "row_count_expected": int(silver_sum),
            "row_count_actual": int(gold_sum),
            "variance_pct": variance,
            "status": status,
            "error_details": error_details,
            "check_timestamp": datetime.now()
        })
    
    def check_pbi_semantic_model(self, dataset_id):
        """
        Layer 5 (Gold→Power BI) Reconciliation: Verify semantic model refresh.
        """
        from pyspark.sql.functions import current_timestamp
        
        # This would use Power BI REST API in production
        # For now, we'll create a placeholder
        
        # In production, you would:
        # 1. Call Power BI REST API to get dataset refresh status
        # 2. Compare row counts via DAX query
        # 3. Check last refresh timestamp
        
        self.recon_results.append({
            "recon_id": f"{self.product_name}_{self.week_end_date}_PBI",
            "product_name": self.product_name,
            "week_end_date": self.week_end_date,
            "layer_name": "PowerBI_SemanticModel",
            "status": "PENDING",  # Would be populated via API
            "error_details": "Requires Power BI REST API integration",
            "check_timestamp": datetime.now()
        })
    
    def save_results(self):
        """Save reconciliation results to Delta table."""
        df_results = spark.createDataFrame(self.recon_results)
        df_results.write.format("delta").mode("append").saveAsTable("reconciliation_control_tower")
        
        print(f"✅ Reconciliation complete for {self.product_name} - {self.week_end_date}")
        return df_results


# Usage Example
if __name__ == "__main__":
    # Run for each product
    products = ["Nielsen_Retail", "Circana_Grocery", "Unify_Convenience"]
    week_end = datetime(2026, 1, 18)
    
    for product in products:
        engine = ReconciliationEngine(spark, product, week_end)
        
        # Step 1: Check ADLS landing
        expected_files = get_expected_files_from_manifest(product, week_end)  # From Circana API
        actual_files = engine.check_adls_landing(expected_files)
        
        # Step 2: Check Bronze ingestion
        engine.check_bronze_ingestion(actual_files)
        
        # Step 3: Check Silver quality
        engine.check_silver_quality()
        
        # Step 4: Check Gold aggregation
        engine.check_gold_aggregation()
        
        # Step 5: Check Power BI
        engine.check_pbi_semantic_model(dataset_id="abc-123")
        
        # Save results
        engine.save_results()
```

---

## 3. Power BI App Structure

### App Components

1. **Home Page**: Executive summary with overall health status
2. **File Monitoring**: Track file delivery and missing files
3. **Reconciliation Dashboard**: Layer-by-layer data lineage
4. **Trust Score Tracker**: Quality trends over time
5. **Drill-Through Details**: Transaction-level quarantine analysis
6. **Alerting Center**: Active issues requiring attention

### Power BI App Configuration

**Workspace**: Create a dedicated workspace `Data_Quality_Control_Tower_Prod`

**Datasets**:
1. `Reconciliation_Control_Tower` (from reconciliation table)
2. `Audit_Log` (from audit log table)
3. `Quarantine_Details` (from quarantine table)
4. `File_Manifest` (from ADLS metadata)

**Reports** (in the app):
1. `QC_Dashboard_Executive`
2. `QC_Dashboard_File_Monitoring`
3. `QC_Dashboard_Reconciliation`
4. `QC_Dashboard_Quarantine_Analysis`

**App Settings**:
- **Auto-refresh**: Scheduled daily at 6 AM (after data pipeline completion)
- **Audience**: Data Engineering team, Business Analysts, Product Owners
- **Permissions**: Read-only for BAs, Edit for Data Engineers

---

## 4. Automation: Replace Manual Monday Checks

### Databricks Workflow

**Name**: `Weekly_Data_QC_Automation`

**Schedule**: Every Monday at 8 AM

**Tasks**:
1. **Task 1**: Run reconciliation for all products
2. **Task 2**: Generate alert report
3. **Task 3**: Send summary email to BA team
4. **Task 4**: Refresh Power BI semantic model

**Alerting Logic**:
```python
# Task 2: Generate Alerts

critical_issues = spark.sql("""
    SELECT 
        product_name,
        layer_name,
        status,
        error_details,
        variance_pct
    FROM reconciliation_control_tower
    WHERE status IN ('ERROR', 'WARNING')
      AND week_end_date = (SELECT MAX(week_end_date) FROM reconciliation_control_tower)
    ORDER BY 
        CASE WHEN status = 'ERROR' THEN 1 ELSE 2 END,
        product_name
""")

if critical_issues.count() > 0:
    # Send alert email
    send_email(
        to="ba-team@company.com",
        subject=f"⚠️ Data Quality Issues Detected - Week of {week_end}",
        body=critical_issues.toPandas().to_html()
    )
```

---

## 5. Next Steps for Implementation

I'll now create the Power BI specific assets for this production scenario...

