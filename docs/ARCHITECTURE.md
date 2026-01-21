# Architecture Document: Data Quality Control Tower
## Solution Design & Technical Blueprint

---

## Executive Architecture Overview

### Visual Representation (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   DATA QUALITY CONTROL TOWER                             │
│                  (Observability & Governance Layer)                      │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Trust Score  │  │ Revenue@Risk │  │ Audit Trail  │                  │
│  │   Metrics    │  │   Analysis   │  │  & Lineage   │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Observability Metrics
                                 │
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE LAYERS                              │
└─────────────────────────────────────────────────────────────────────────┘

Layer 5: POWER BI SEMANTIC MODEL
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 Power BI Premium / Fabric                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │  Product 1  │  │  Product 2  │  │  Product 3  │                     │
│  │   Report    │  │   Report    │  │   Report    │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                                                          │
│  Validation: Refresh Status │ Row Count Match │ Measure Accuracy        │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Semantic Model Refresh
                                 │
Layer 4: GOLD (Business-Ready Data)
┌─────────────────────────────────────────────────────────────────────────┐
│  🥇 Databricks Gold Layer - Delta Tables                                │
│  ┌──────────────────────────────────────────────────────┐              │
│  │  Star Schema: Fact_Sales, Dim_Product, Dim_Region    │              │
│  │  Aggregations: Brand x Region x Week                 │              │
│  │  Optimized: Z-Order, Partitioning                    │              │
│  └──────────────────────────────────────────────────────┘              │
│                                                                          │
│  Validation: Sum Reconciliation │ Business Rule Checks                  │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Aggregation Logic
                                 │
Layer 3: SILVER (Clean, Validated Data)
┌─────────────────────────────────────────────────────────────────────────┐
│  🥈 Databricks Silver Layer - Delta Tables                              │
│                                                                          │
│  ┌────────────────────────┐        ┌────────────────────────┐          │
│  │  Silver_Valid_Data     │        │  Silver_Quarantine     │          │
│  │  (95-98% of records)   │        │  (2-5% of records)     │          │
│  │                        │        │                        │          │
│  │  ✅ Passed validation  │        │  ⚠️ Failed validation  │          │
│  │  ✅ Ready for Gold     │        │  ⚠️ Needs review       │          │
│  │  ✅ Business-ready     │        │  ⚠️ Tagged with errors │          │
│  └────────────────────────┘        └────────────────────────┘          │
│                                                                          │
│            ▲                                  ▲                          │
│            │                                  │                          │
│            └──────────┬───────────────────────┘                          │
│                       │                                                  │
│              ┌────────▼────────┐                                        │
│              │ QUALITY GUARD    │ ← Shadow DLT Pattern                  │
│              │ (Shadow DLT)     │                                        │
│              ├──────────────────┤                                        │
│              │ Validation Rules:│                                        │
│              │ • UPC exists?    │                                        │
│              │ • Store valid?   │                                        │
│              │ • Sales >= 0?    │                                        │
│              │ • Price reasonable?                                       │
│              └──────────────────┘                                        │
│                                                                          │
│  Validation: Master Data Checks │ Null Checks │ Business Rules          │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Raw Data with Metadata
                                 │
Layer 2: BRONZE (Raw Ingestion)
┌─────────────────────────────────────────────────────────────────────────┐
│  🥉 Databricks Bronze Layer - Delta Tables                              │
│  ┌──────────────────────────────────────────────────────┐              │
│  │  Immutable Raw Data with Audit Metadata               │              │
│  │  • Ingestion_Timestamp                                │              │
│  │  • Source_File_Name                                   │              │
│  │  • Batch_ID                                           │              │
│  │  • Row_Count                                          │              │
│  └──────────────────────────────────────────────────────┘              │
│                                                                          │
│  Validation: Row Count Match │ File-to-Table Reconciliation             │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Databricks Auto Loader
                                 │
Layer 1: ADLS BRONZE (File Landing Zone)
┌─────────────────────────────────────────────────────────────────────────┐
│  💾 Azure Data Lake Storage Gen2 (Blob)                                 │
│                                                                          │
│  📁 Container: bronze/                                                  │
│     ├── circana/                                                        │
│     │   ├── product_snacks/weekly/    (75 files)                       │
│     │   │   ├── snacks_sales_summary.csv                               │
│     │   │   ├── snacks_regional_*.csv                                  │
│     │   │   └── ...                                                     │
│     │   ├── product_beverages/weekly/ (150 files)                      │
│     │   │   ├── bev_sales_summary.csv                                  │
│     │   │   ├── bev_carbonated_*.csv                                   │
│     │   │   └── ...                                                     │
│     │   └── product_frozen/weekly/    (60 files)                       │
│     │       └── ...                                                     │
│                                                                          │
│  Validation: File Exists │ File Fresh │ File Size │ Schema Match        │
└─────────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Weekly Data Drop (Monday 3 AM)
                                 │
Layer 0: SOURCE (External System)
┌─────────────────────────────────────────────────────────────────────────┐
│  🌐 Circana (Unify Platform)                                            │
│                                                                          │
│  Weekly POS Data Extracts:                                              │
│  • Product 1: Snacks     → 75 CSV files                                │
│  • Product 2: Beverages  → 150 CSV files                               │
│  • Product 3: Frozen     → 60 CSV files                                │
│                                                                          │
│  Delivery: SFTP → ADLS (Automated)                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Layer Specifications

### Layer 0: Circana Source System

**Purpose**: External data provider (POS syndicated data)

**Characteristics**:
- **Frequency**: Weekly delivery (Monday 3 AM ET)
- **Format**: CSV files (flat, delimited)
- **Volume per Product**: 
  - Snacks: 75 files (~200MB total)
  - Beverages: 150 files (~400MB total)
  - Frozen: 60 files (~150MB total)
- **Delivery Method**: SFTP → Azure Data Factory → ADLS

**Data Structure** (typical):
```
UPC,Store_ID,Week_End,Sales_Dollars,Units_Sold,Promo_Flag
8000000001,ST00001,2026-01-19,125.50,25,N
8000000002,ST00001,2026-01-19,89.99,15,Y
...
```

**Common Issues** (what we're detecting):
- New UPCs not in master data (product launches)
- Store closures/openings (store IDs mismatch)
- Negative values (return processing errors)
- Missing files (transmission failures)
- Schema changes (column additions/removals)

---

### Layer 1: ADLS Bronze (File System)

**Purpose**: Immutable raw file storage

**Technology**: Azure Data Lake Storage Gen2

**Structure**:
```
bronze/
  circana/
    {product_name}/
      weekly/
        {yyyy}/{mm}/
          {file_name}_{yyyy-mm-dd}.csv
```

**Validation Checks** (automated):
1. **File Existence Check**
   - Expected: All 75/150/60 files per product
   - Alert if: ANY file missing
   - Severity: CRITICAL

2. **File Freshness Check**
   - Expected: Modified within last 26 hours
   - Alert if: Older than threshold
   - Severity: CRITICAL

3. **File Size Check**
   - Expected: > 500KB (configurable per file)
   - Alert if: < 50% of historical average
   - Severity: WARNING

4. **Schema Validation** (header check)
   - Expected: Matches predefined column list
   - Alert if: Columns missing or extra
   - Severity: CRITICAL

**Monitoring Metrics**:
- Files landed: 285/285 (100%)
- Average file size: 1.2MB
- Oldest file age: 2.5 hours
- Schema mismatches: 0

---

### Layer 2: Databricks Bronze (Delta Table)

**Purpose**: Ingested raw data with audit metadata

**Technology**: Delta Lake (ACID transactions, time travel)

**Schema**:
```sql
CREATE TABLE bronze_sales (
  -- Original columns from CSV
  UPC STRING,
  Store_ID STRING,
  Week_End DATE,
  Sales_Dollars DECIMAL(10,2),
  Units_Sold INT,
  
  -- Audit metadata (added during ingestion)
  Ingestion_Timestamp TIMESTAMP,
  Source_File_Name STRING,
  Source_File_Size BIGINT,
  Batch_ID STRING,
  Source_System STRING
)
USING DELTA
PARTITIONED BY (Week_End)
LOCATION '/mnt/bronze/sales';
```

**Ingestion Method**: 
- **Databricks Auto Loader** (incremental, cloud-native)
- **Trigger**: File arrival detection
- **Idempotency**: Duplicate file detection via checkpointing

**Validation Checks**:
1. **Row Count Reconciliation**
   - Compare: File row count vs. Table row count
   - Alert if: Mismatch
   - Action: Block downstream processing

2. **Duplicate Detection**
   - Check: Batch_ID uniqueness
   - Alert if: Same file loaded twice
   - Action: Quarantine duplicates

**Monitoring Metrics**:
- Bronze row count: 10,500,000
- Files ingested: 285
- Reconciliation status: ✅ PASS
- Duplicates detected: 0

---

### Layer 3: Databricks Silver (Validated Data + Quarantine)

**Purpose**: Data quality enforcement with quarantine pattern

**Technology**: Delta Lake + Shadow DLT (custom quality engine)

**Schema** (Silver Valid):
```sql
CREATE TABLE silver_sales (
  -- Validated and enriched
  UPC STRING NOT NULL,
  Store_ID STRING NOT NULL,
  Week_End DATE NOT NULL,
  Sales_Dollars DECIMAL(10,2) CHECK (Sales_Dollars >= 0),
  Units_Sold INT CHECK (Units_Sold >= 0),
  
  -- Enrichments
  Product_Brand STRING,
  Product_Category STRING,
  Store_Region STRING,
  
  -- Audit
  Silver_Batch_ID STRING,
  Validation_Timestamp TIMESTAMP
)
USING DELTA
PARTITIONED BY (Week_End, Store_Region);
```

**Schema** (Silver Quarantine):
```sql
CREATE TABLE silver_quarantine (
  -- Original fields (preserved)
  UPC STRING,
  Store_ID STRING,
  Week_End DATE,
  Sales_Dollars DECIMAL(10,2),
  Units_Sold INT,
  
  -- Error tracking
  Error_Details STRING,  -- "upc_in_master|CRITICAL|UPC not in Product Master"
  Error_Count INT,
  Severity STRING,
  Quarantine_Timestamp TIMESTAMP,
  Batch_ID STRING,
  Layer_Name STRING
)
USING DELTA
PARTITIONED BY (Week_End);
```

**Quality Guard (Shadow DLT) Rules**:

```python
VALIDATION_RULES = {
    'upc_not_null': {
        'condition': col('UPC').isNotNull(),
        'severity': 'CRITICAL',
        'description': 'UPC must not be null'
    },
    'upc_in_master': {
        'condition': col('UPC').isin(valid_upcs),
        'severity': 'CRITICAL',
        'description': 'UPC must exist in Product Master'
    },
    'store_in_master': {
        'condition': col('Store_ID').isin(valid_stores),
        'severity': 'CRITICAL',
        'description': 'Store must exist in Store Master'
    },
    'non_negative_sales': {
        'condition': col('Sales_Dollars') >= 0,
        'severity': 'HIGH',
        'description': 'Sales must be non-negative'
    },
    'reasonable_price': {
        'condition': (col('Sales_Dollars') / col('Units_Sold')) <= 100,
        'severity': 'MEDIUM',
        'description': 'Unit price must be <= $100'
    }
}
```

**Processing Logic**:
1. Read from Bronze
2. Load reference data (Product Master, Store Master)
3. Apply validation rules
4. Split stream:
   - Valid → Silver_Valid (95-98%)
   - Invalid → Silver_Quarantine (2-5%)
5. Log to Audit table

**Monitoring Metrics**:
- Input rows: 10,500,000
- Valid rows: 10,100,000 (96.2%)
- Quarantined rows: 400,000 (3.8%)
- **Trust Score: 96.2%**

---

### Layer 4: Databricks Gold (Business Aggregations)

**Purpose**: Analytics-ready data (star schema)

**Schema**:
```sql
CREATE TABLE gold_sales_summary (
  -- Dimensions
  Brand STRING,
  Category STRING,
  Region STRING,
  Week_End DATE,
  
  -- Measures
  Total_Sales DECIMAL(15,2),
  Total_Units BIGINT,
  Transaction_Count BIGINT,
  Avg_Unit_Price DECIMAL(10,2),
  Avg_Basket_Size DECIMAL(10,2),
  
  -- Metadata
  Created_Timestamp TIMESTAMP,
  Batch_ID STRING
)
USING DELTA
PARTITIONED BY (Week_End, Region)
ZORDER BY (Brand, Category);
```

**Aggregation Logic**:
- Source: Silver_Valid only
- Grain: Brand x Category x Region x Week
- Optimizations: Z-Ordering for query performance

**Validation Checks**:
1. **Sum Reconciliation**
   - Silver Total Sales = Gold Total Sales
   - Alert if: > 0.01% variance
   
2. **Count Reconciliation**
   - Silver row count >= Gold row count (due to aggregation)
   - Alert if: Silver < Gold (impossible)

**Monitoring Metrics**:
- Gold row count: 2,500
- Silver-to-Gold sum match: ✅ PASS
- Aggregation ratio: 4,040:1

---

### Layer 5: Power BI Semantic Model

**Purpose**: Business intelligence layer for end users

**Technology**: Power BI Premium / Fabric

**Data Model**:
- Import Mode (for performance)
- Incremental Refresh (last 4 weeks)
- Aggregations enabled

**Measures** (DAX):
```dax
Trust Score % = 
DIVIDE(
    SUM(Audit[valid_rows]),
    SUM(Audit[input_rows]),
    0
) * 100

Revenue at Risk = 
SUM(Quarantine[Sales_Dollars])

Data Freshness Hours = 
DATEDIFF(
    MAX(Audit[timestamp]),
    NOW(),
    HOUR
)
```

**Validation Checks**:
1. **Refresh Status**
   - Expected: Success
   - Alert if: Failed
   - Severity: CRITICAL

2. **Row Count Match**
   - PBI row count = Gold row count
   - Alert if: Mismatch > 1%
   
3. **Measure Validation**
   - Spot-check: Total Sales in PBI = Sum in Gold
   - Alert if: Variance

**Monitoring Metrics**:
- Last refresh: Success (2026-01-21 06:15 AM)
- Row count: 2,500 (matches Gold)
- Refresh duration: 45 seconds

---

## Cross-Layer Data Lineage

```
Circana File (10,000 rows)
         │
         ▼
ADLS File Validation ✅
         │
         ▼
Bronze Ingestion (10,000 rows) ✅
         │
         ▼
Quality Guard Split:
   ├─→ Silver Valid (9,600 rows) ✅
   └─→ Silver Quarantine (400 rows) ⚠️
         │
         ▼
Gold Aggregation (250 rows) ✅
         │
         ▼
Power BI Refresh (250 rows) ✅
```

**Reconciliation Formula**:
```
Bronze_Count = Silver_Valid_Count + Silver_Quarantine_Count
```

If this doesn't hold → **DATA LOSS DETECTED** → CRITICAL ALERT

---

## Control Tower Observability Layer

### Audit Log Schema

```sql
CREATE TABLE audit_log (
  batch_id STRING,
  layer_name STRING,
  timestamp TIMESTAMP,
  input_rows BIGINT,
  valid_rows BIGINT,
  quarantine_rows BIGINT,
  trust_score DECIMAL(5,2),
  
  -- Reconciliation
  bronze_total BIGINT,
  silver_valid BIGINT,
  silver_quarantine BIGINT,
  gold_aggregated BIGINT,
  revenue_at_risk DECIMAL(15,2),
  
  -- Metadata
  reconciliation_passed BOOLEAN,
  critical_errors INT,
  execution_duration_sec INT
);
```

### Key Metrics

**Trust Score**:
```
Trust Score = (Valid Rows / Total Input Rows) × 100
```
- Target: ≥ 98%
- Acceptable: 95-98%
- Critical: < 95%

**Revenue at Risk**:
```
Revenue at Risk = SUM(Quarantine.Sales_Dollars)
```
- Warning threshold: > $10,000
- Critical threshold: > $50,000

**Data Freshness**:
```
Freshness = NOW() - MAX(Batch.Timestamp)
```
- Fresh: < 24 hours
- Acceptable: 24-48 hours
- Stale: 48-168 hours
- Critical: > 168 hours (1 week)

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Source** | Circana Unify | POS data provider |
| **Transport** | Azure Data Factory | File movement automation |
| **Storage** | ADLS Gen2 | Raw file landing zone |
| **Processing** | Databricks (PySpark) | Data transformation engine |
| **Format** | Delta Lake | ACID table format |
| **Orchestration** | Delta Live Tables | Pipeline automation |
| **Governance** | Unity Catalog | Data cataloging & lineage |
| **Monitoring** | Databricks Jobs | Scheduled execution |
| **Visualization** | Power BI Premium | Business dashboards |
| **Alerting** | Microsoft Teams | Notifications |

---

## Security & Compliance

**Data Access**:
- Unity Catalog: Role-based access control
- Row-Level Security: In Power BI by product/region
- Column Masking: PII fields (if applicable)

**Audit Trail**:
- Every transformation logged
- Full data lineage from source to report
- Immutable Bronze layer (compliance)

**Encryption**:
- At-rest: Azure Storage Service Encryption
- In-transit: TLS 1.2+
- Workspace: Private Link (optional)

---

## Scalability Considerations

**Current Scale**:
- Products: 3
- Files per week: 285
- Rows per week: 10M
- Processing time: 15 minutes

**Target Scale** (3-year):
- Products: 20
- Files per week: 2,000
- Rows per week: 100M+
- Processing time: < 60 minutes (with autoscaling)

**Scaling Strategy**:
- Databricks Autoscaling (2-16 workers)
- Delta Lake optimizations (Z-Order, bloom filters)
- Incremental processing (process only new data)
- Partitioning by Week_End and Region

---

This architecture is production-ready, scalable, and follows Microsoft/Databricks best practices for lakehouse analytics.
