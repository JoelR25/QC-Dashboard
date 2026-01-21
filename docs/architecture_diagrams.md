# Architecture Diagrams - Data Quality Control Tower

## 1. High-Level Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ENTERPRISE DATA QUALITY CONTROL TOWER                │
│                   "Shift from Monitoring to Observability"               │
└─────────────────────────────────────────────────────────────────────────┘

                                                                              
┌───────────────┐         ┌──────────────┐         ┌────────────────────┐   
│               │         │              │         │                    │   
│    UNIFY      │────────▶│  ADLS BLOB   │────────▶│   DATABRICKS       │   
│  (Circana)    │  Weekly │   STORAGE    │  Batch  │   MEDALLION        │   
│               │  Drops  │   (Landing)  │  Ingest │   ARCHITECTURE     │   
│               │         │              │         │                    │   
└───────────────┘         └──────────────┘         └────────────────────┘   
                                  │                          │               
                                  │                          │               
                          ┌───────▼────────┐         ┌───────▼──────────┐  
                          │ File Monitoring │         │  Quality Checks  │  
                          │ • Count         │         │  • Schema        │  
                          │ • Size          │         │  • Business Rules│  
                          │ • Latency       │         │  • Completeness  │  
                          └────────────────┘         └──────────────────┘  
                                                              │               
                                                              │               
                          ┌───────────────────────────────────┘               
                          │                                                   
                          ▼                                                   
               ┌──────────────────────┐                                      
               │  QUARANTINE PATTERN  │                                      
               └──────────────────────┘                                      
                      │          │                                           
          ┌───────────┘          └────────────┐                             
          │                                   │                              
          ▼                                   ▼                              
┌────────────────┐                  ┌──────────────────┐                    
│  SILVER CLEAN  │────┐             │     SILVER       │                    
│  (Valid Data)  │    │             │   QUARANTINE     │                    
│                │    │             │  (Invalid Data)  │                    
└────────────────┘    │             └──────────────────┘                    
                      │                      │                               
                      │              ┌───────▼────────┐                     
                      │              │  Error Tagging │                     
                      │              │  • Error Code  │                     
                      │              │  • Severity    │                     
                      │              │  • Metadata    │                     
                      │              └────────────────┘                     
                      │                      │                               
                      ▼                      │                               
              ┌──────────────┐               │                               
              │     GOLD     │               │                               
              │  (Analytics) │               │                               
              └──────────────┘               │                               
                      │                      │                               
                      └──────────┬───────────┘                               
                                 │                                           
                                 ▼                                           
                    ┌─────────────────────────┐                             
                    │     POWER BI APP        │                             
                    │  • Trust Score KPI      │                             
                    │  • Reconciliation View  │                             
                    │  • Quarantine Analysis  │                             
                    │  • Alert Dashboard      │                             
                    └─────────────────────────┘                             
                                 │                                           
                                 ▼                                           
                    ┌─────────────────────────┐                             
                    │    STAKEHOLDERS         │                             
                    │  • Business Analysts    │                             
                    │  • Data Engineers       │                             
                    │  • Leadership           │                             
                    └─────────────────────────┘                             
```

---

## 2. Medallion Architecture - Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                         BRONZE LAYER (RAW)                         │
│  "Ingest Everything, Reject Nothing" - Immutable Landing Zone      │
└────────────────────────────────────────────────────────────────────┘
│
│  Observability Metrics:
│  • File Freshness: Time since arrival
│  • Volume Anomalies: Row count vs. historical baseline
│  • Schema Drift: Column changes detected
│
│  Table: bronze_sales
│  Format: Delta Lake
│  Partitioning: week_end_date
│  Retention: 90 days
│
▼
┌────────────────────────────────────────────────────────────────────┐
│                        SILVER LAYER (VALIDATED)                     │
│  "Trust But Verify" - Quality Gate with Quarantine Pattern         │
└────────────────────────────────────────────────────────────────────┘
│
│  Quality Checks (Expectations):
│  ┌──────────────────────────────────────────────────────┐
│  │  IF (UPC in Product_Master) THEN                     │
│  │     Route to → silver_sales_clean                    │
│  │  ELSE                                                │
│  │     Route to → silver_quarantine                     │
│  │     Tag with → Error_Code: MISSING_UPC               │
│  └──────────────────────────────────────────────────────┘
│
│  Observability Metrics:
│  • Trust Score = Clean / (Clean + Quarantine) * 100
│  • Quarantine Rate by Error Type
│  • Revenue at Risk = SUM(Quarantine.Sales_Dollars)
│
│  Tables:
│    1. silver_sales_clean (Valid records)
│    2. silver_quarantine (Invalid records with error metadata)
│    3. audit_log (Batch-level quality metrics)
│
▼
┌────────────────────────────────────────────────────────────────────┐
│                         GOLD LAYER (ANALYTICS)                      │
│  "Performance and Context" - Business-Ready Aggregates             │
└────────────────────────────────────────────────────────────────────┘
│
│  Aggregation Example:
│  ┌──────────────────────────────────────────────────────┐
│  │  SELECT Brand, Region,                               │
│  │         SUM(Sales_Dollars) as Total_Revenue,         │
│  │         SUM(Units_Sold) as Total_Units               │
│  │  FROM silver_sales_clean                             │
│  │  GROUP BY Brand, Region                              │
│  └──────────────────────────────────────────────────────┘
│
│  Observability Metrics:
│  • Reconciliation: SUM(Silver_Clean) = SUM(Gold_Aggregates)
│  • Completeness: All Brands/Regions represented
│
│  Tables:
│    1. gold_brand_analytics
│    2. gold_regional_summary
│    3. gold_weekly_trends
│
▼
[Power BI Semantic Model] → [User Reports]
```

---

## 3. Shadow DLT Pattern (Community Edition Workaround)

```
ENTERPRISE (Delta Live Tables)          SIMULATION (Shadow DLT)
─────────────────────────────────       ────────────────────────────────

@dlt.table                              def create_silver_table():
def silver_sales():                         df = spark.table("bronze_sales")
  return (                                  
    spark.table("bronze_sales")             # Apply expectations manually
    .withColumn(...)                        expectations = {
  )                                             "upc_valid": "UPC IS NOT NULL",
                                                "store_valid": "Store_ID IN (...)"
@dlt.expect_or_drop(                        }
  "valid_upc",                              
  "UPC IS NOT NULL"                         guard = DataQualityGuard(
)                                               df=df,
                                                expectations=expectations
@dlt.expect_or_drop(                        )
  "valid_store",                            
  "Store_ID IN master"                      guard.validate()
)                                           clean_df, quarantine_df = guard.split()
                                            
                                            # Write to tables
# Automatic quarantine                      clean_df.write.saveAsTable("silver_clean")
# Automatic metrics                         quarantine_df.write.saveAsTable("silver_quarantine")
                                            guard.log_metrics()

KEY DIFFERENCE:
✅ Enterprise: Declarative (DLT handles routing)
⚠️  Simulation: Imperative (You handle routing manually)
```

---

## 4. Trust Score Calculation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    TRUST SCORE CALCULATION                   │
└─────────────────────────────────────────────────────────────┘

Input: 10,000 rows from Bronze
         │
         ▼
    ┌────────────────────────┐
    │   Apply Expectations   │
    │  • UPC in Master?      │
    │  • Store in Master?    │
    │  • Sales >= 0?         │
    └────────────────────────┘
         │
         ▼
    ┌────────────────────────┐
    │   Tag Each Row         │
    │  is_valid = TRUE/FALSE │
    └────────────────────────┘
         │
         ├──────────────────┬─────────────────┐
         │                  │                 │
         ▼                  ▼                 ▼
    ┌─────────┐      ┌──────────┐     ┌──────────┐
    │  9,200  │      │    500   │     │   300    │
    │  Valid  │      │ Missing  │     │ Negative │
    │  Rows   │      │   UPC    │     │  Sales   │
    └─────────┘      └──────────┘     └──────────┘
         │                  │                 │
         │                  └────────┬────────┘
         │                           │
         ▼                           ▼
    [CLEAN TABLE]            [QUARANTINE TABLE]
     9,200 rows                   800 rows
         │                           │
         │                           │
         └───────────┬───────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  CALCULATE TRUST SCORE │
         │                        │
         │  9,200 / 10,000 = 92%  │
         └────────────────────────┘
                     │
                     ▼
         ┌────────────────────────┐
         │  APPLY THRESHOLD       │
         │                        │
         │  92% < 95% → RED 🔴    │
         │  (Action Required)     │
         └────────────────────────┘
                     │
                     ▼
         [Display in Power BI Gauge]
```

---

## 5. Reconciliation Across Layers

```
┌──────────────────────────────────────────────────────────────────┐
│              END-TO-END RECONCILIATION FRAMEWORK                  │
└──────────────────────────────────────────────────────────────────┘

Layer 1: SOURCE → ADLS
┌─────────────────────────────────────────────────────────────────┐
│ Check: File Count                                               │
│ Expected: 150 files (from Circana manifest)                     │
│ Actual:   148 files (from ADLS listing)                         │
│ Status:   ERROR - 2 files missing                               │
│ Action:   Alert Circana delivery team                           │
└─────────────────────────────────────────────────────────────────┘

Layer 2: ADLS → BRONZE
┌─────────────────────────────────────────────────────────────────┐
│ Check: Row Count                                                │
│ Expected: 10,000 rows (from ADLS CSV row count)                 │
│ Actual:   10,000 rows (from Bronze table SELECT COUNT(*))       │
│ Variance: 0.0%                                                  │
│ Status:   OK ✅                                                 │
└─────────────────────────────────────────────────────────────────┘

Layer 3: BRONZE → SILVER (Quality Gate)
┌─────────────────────────────────────────────────────────────────┐
│ Check: Reconciliation & Trust Score                             │
│ Bronze:      10,000 rows                                        │
│ Silver Clean: 9,200 rows                                        │
│ Quarantine:     800 rows                                        │
│ Total:       10,000 rows ✅ (Bronze = Silver Clean + Quarantine)│
│ Trust Score:   92.0% ⚠️  (Below 95% threshold)                  │
│ Status:   WARNING - Review quarantine records                   │
└─────────────────────────────────────────────────────────────────┘

Layer 4: SILVER → GOLD (Aggregation)
┌─────────────────────────────────────────────────────────────────┐
│ Check: Revenue Reconciliation                                   │
│ Silver Sum:  $450,000.00 (SUM of sales_dollars in clean table)  │
│ Gold Sum:    $450,000.00 (SUM of total_revenue in gold table)   │
│ Variance:    0.00%                                              │
│ Status:      OK ✅                                              │
└─────────────────────────────────────────────────────────────────┘

Layer 5: GOLD → POWER BI
┌─────────────────────────────────────────────────────────────────┐
│ Check: Semantic Model Freshness                                 │
│ Last Refresh: 2026-01-21 06:00:00                               │
│ Data Timestamp: 2026-01-21 05:30:00                             │
│ Latency:      30 minutes                                        │
│ Status:       OK ✅ (Within 2-hour SLA)                         │
└─────────────────────────────────────────────────────────────────┘

OVERALL STATUS: 2 WARNINGS, 0 CRITICAL ERRORS
Action Required: Investigate missing files and quarantine records
```

---

## 6. Error Flow & Quarantine Routing

```
┌────────────────────────────────────────────────────────────────┐
│                 SINGLE ROW ERROR FLOW EXAMPLE                   │
└────────────────────────────────────────────────────────────────┘

Input Row from Bronze:
┌────────────────────────────────────────────────────────────────┐
│ Transaction_ID: TXN_00000042                                   │
│ UPC: 999999001 ← NOT IN PRODUCT MASTER                         │
│ Store_ID: STORE_0015                                           │
│ Sales_Dollars: 45.00                                           │
│ Units_Sold: 9                                                  │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Expectation 1: UPC in Product Master?  │
│  SELECT COUNT(*) FROM product_master    │
│  WHERE UPC = '999999001'                │
│  → Result: 0 (NOT FOUND)                │
│  → valid_upc = FALSE ❌                 │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Expectation 2: Store in Store Master?  │
│  SELECT COUNT(*) FROM store_master      │
│  WHERE Store_ID = 'STORE_0015'          │
│  → Result: 1 (FOUND)                    │
│  → valid_store = TRUE ✅                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Expectation 3: Sales >= 0?             │
│  45.00 >= 0                             │
│  → valid_sales = TRUE ✅                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Combine Validation Results             │
│  is_valid = valid_upc AND valid_store   │
│             AND valid_sales             │
│  is_valid = FALSE AND TRUE AND TRUE     │
│  is_valid = FALSE ❌                    │
└─────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Route to: silver_quarantine                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Transaction_ID: TXN_00000042                             │ │
│  │ UPC: 999999001                                           │ │
│  │ Store_ID: STORE_0015                                     │ │
│  │ Sales_Dollars: 45.00                                     │ │
│  │ Units_Sold: 9                                            │ │
│  │ is_valid: FALSE                                          │ │
│  │ Error_Reason: "upc_exists" ← ADDED METADATA              │ │
│  │ Severity: HIGH                                           │ │
│  │ Batch_ID: 123                                            │ │
│  │ Quarantine_Timestamp: 2026-01-21 10:30:00                │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
  [Available for Analysis in Power BI]
```

---

## 7. Power BI App Navigation

```
┌──────────────────────────────────────────────────────────────────┐
│  DATA QUALITY CONTROL TOWER - Power BI App                       │
└──────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   HOME (Landing) │
                    │  • Trust Score   │
                    │  • Overall Health│
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│ FILE          │   │ RECONCILIATION │   │ QUARANTINE   │
│ MONITORING    │   │ LINEAGE        │   │ ANALYSIS     │
│               │   │                │   │              │
│• Missing Files│   │• Sankey Flow   │   │• Error Types │
│• Late Arrivals│   │• Layer Status  │   │• Root Cause  │
│• Size Anomaly │   │• Drill-Through │   │• Drill-Down  │
└───────────────┘   └────────────────┘   └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ ALERTS & ACTIONS │
                    │ • Active Issues  │
                    │ • Recommendations│
                    └──────────────────┘
```

---

## 8. Weekly Automation Workflow

```
Monday Morning Automation (Databricks Workflow)
┌──────────────────────────────────────────────────────────────────┐
│                      SCHEDULED JOB: 8:00 AM                       │
└──────────────────────────────────────────────────────────────────┘

Task 1: Run Reconciliation (20 min)
  ├─ Check ADLS landing for all products
  ├─ Verify Bronze ingestion
  ├─ Validate Silver quality
  ├─ Check Gold aggregation
  └─ Log results to reconciliation_control_tower table

Task 2: Identify Issues (5 min)
  ├─ Query for status IN ('ERROR', 'WARNING')
  ├─ Group by Product, Layer
  └─ Calculate priority score

Task 3: Send Alert Email (2 min)
  ├─ IF critical issues > 0 THEN
  │   └─ Send email to ba-team@company.com
  │       Subject: "⚠️ Data Quality Issues Detected"
  │       Body: HTML table of issues + dashboard link
  └─ ELSE
      └─ Send success summary

Task 4: Refresh Power BI Dataset (10 min)
  ├─ Call Power BI REST API
  ├─ POST /datasets/{id}/refreshes
  └─ Wait for completion

Task 5: Notify Completion (1 min)
  └─ Post to Slack/Teams: "✅ Weekly QC complete. View dashboard →"

Total Runtime: ~40 minutes
```

---

## 9. Technology Stack Mapping

```
┌────────────────────────────────────────────────────────────────┐
│              ENTERPRISE VS SIMULATION COMPARISON               │
└────────────────────────────────────────────────────────────────┘

Component          Enterprise                 Simulation (Personal)
────────────────────────────────────────────────────────────────
Storage            Azure ADLS Gen2            Local CSV files
                   $$/month                   FREE

Compute            Azure Databricks           Databricks Community
                   $$$$/month                 FREE (2-hour clusters)

Orchestration      Databricks Workflows       Manual notebook execution
                   Auto-retry, dependencies   No scheduling

Quality Framework  Delta Live Tables          Shadow DLT (custom Python)
                   Declarative expectations   Imperative validation

Catalog            Unity Catalog              Manual Delta tables
                   Auto-lineage tracking      Custom audit_log

Visualization      Power BI Premium           Power BI Desktop
                   Auto-refresh, apps         Manual refresh, local files

Alerting           Databricks Jobs email      Print statements / manual
                   Power Automate             email

Cost               ~$5K-10K/month             $0 (personal time only)

Setup Time         2-4 weeks                  6 hours

Production-Ready   YES ✅                     NO (Demo only)
```

---

## 10. Implementation Roadmap (Post-Approval)

```
┌──────────────────────────────────────────────────────────────────┐
│                    4-WEEK IMPLEMENTATION PLAN                     │
└──────────────────────────────────────────────────────────────────┘

WEEK 1: Foundation
├─ Day 1-2: Azure setup (ADLS, Databricks workspace, Unity Catalog)
├─ Day 3: Mount ADLS to Databricks
├─ Day 4: Create Bronze pipeline for 1 product (Nielsen Retail)
└─ Day 5: Test & validate

WEEK 2: Quality Layer
├─ Day 1-2: Implement Delta Live Tables with expectations
├─ Day 3: Create Silver Clean + Quarantine tables
├─ Day 4: Build audit_log framework
└─ Day 5: Test Trust Score calculation

WEEK 3: Analytics & Visualization
├─ Day 1: Create Gold aggregation tables
├─ Day 2: Build reconciliation framework
├─ Day 3: Develop Power BI semantic model
├─ Day 4: Build dashboard (all pages)
└─ Day 5: Publish Power BI App

WEEK 4: Scale & Train
├─ Day 1-2: Expand to all products (Circana Grocery, Unify Convenience)
├─ Day 3: Setup automated workflow (Monday job)
├─ Day 4: BA team training session
└─ Day 5: Handoff & documentation

GO-LIVE: Monday of Week 5
```

---

**Architecture Review**: Complete ✅  
**Visual Diagrams**: ASCII format for documentation ✅  
**Next**: See troubleshooting.md for issue resolution
