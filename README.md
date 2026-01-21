# Enterprise Data Quality Control Tower

## Comprehensive Architectural Blueprint, Simulation Strategy, and Executive Pitch for CPG Analytics

### 🎯 Project Overview

This repository implements a **Data Quality Control Tower** simulation designed for Consumer Packaged Goods (CPG) analytics teams working with syndicated Point-of-Sale (POS) data from providers like Circana (formerly IRI and NPD).

The solution demonstrates:
- **Data Observability** patterns using the Medallion Architecture
- **Shadow DLT** (Delta Live Tables) implementation for quality enforcement
- **KPI Trust Score** calculation and visualization
- **Quarantine Pattern** for managing invalid data
- Synthetic CPG data generation with realistic quality issues
- Power BI dashboard templates for executive reporting

### 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Project Structure](#project-structure)
5. [Implementation Guide](#implementation-guide)
6. [Dashboard Guide](#dashboard-guide)
7. [Troubleshooting](#troubleshooting)
8. [References](#references)

---

## 🎓 Executive Summary

### The Problem: Silent Failures in Data Pipelines

Organizations make million-dollar decisions based on syndicated POS data, but traditional ETL monitoring only tells you **if the pipeline ran**, not **if the data is correct**. This creates "Silent Failures" where:

- New product UPCs aren't in master data → sales go unreported
- Store closures aren't synchronized → regional trends are skewed  
- Data transmission errors → negative values corrupt aggregations

### The Solution: Data Observability with a Trust Score

The **Data Quality Control Tower** introduces:

1. **Quarantine Pattern**: Instead of dropping bad data or crashing, capture it for analysis
2. **KPI Trust Score**: A single metric (e.g., 94%) showing data reliability
3. **Revenue at Risk**: Financial translation of data quality issues (e.g., $50K in unattributed sales)
4. **Root Cause Analysis**: AI-powered drill-down to specific error sources

### Business Value

- **Visibility**: Know when data is untrustworthy before making decisions
- **Efficiency**: 40% reduction in time debugging "missing numbers"
- **Risk Mitigation**: Quantify financial impact of data quality issues
- **Trust**: Measurable confidence in analytics outputs

---

## 🏗️ Architecture

### The Medallion Architecture + Quality Zones

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA QUALITY CONTROL TOWER                │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌─────▼─────┐        ┌─────▼─────┐
   │ BRONZE  │          │  SILVER   │        │   GOLD    │
   │  (Raw)  │──────────│ (Quality  │────────│(Analytics)│
   └─────────┘          │   Gate)   │        └───────────┘
                        └─────┬─────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
              ┌─────▼─────┐      ┌──────▼──────┐
              │  SILVER   │      │   SILVER    │
              │   CLEAN   │      │ QUARANTINE  │
              └───────────┘      └─────────────┘
                                        │
                                        ▼
                                  [Audit Log]
                                  Trust Score
```

### Key Components

1. **Bronze Layer**: Immutable raw data ingestion
   - Observability: File freshness, volume anomalies
   
2. **Silver Layer**: Quality enforcement with quarantine
   - **Valid Data** → Silver_Clean (proceeds to Gold)
   - **Invalid Data** → Silver_Quarantine (tagged with error metadata)
   - Observability: Trust Score = Valid / (Valid + Quarantine)

3. **Gold Layer**: Aggregated business metrics
   - Observability: Reconciliation checks (Bronze = Silver_Clean + Silver_Quarantine)

4. **Audit Log**: Metadata tracking for every transformation
   - Batch ID, Input Rows, Valid Rows, Quarantine Rows, Trust Score

---

## 🚀 Quick Start

### Prerequisites

- **Databricks Community Edition** account (free)
- **Power BI Desktop** (free)
- Python 3.8+ (for local data generation)

### 6-Hour Simulation Timeline

| Time | Activity | Deliverable |
|------|----------|-------------|
| 0:00-0:45 | Setup infrastructure | Cluster running, libraries installed |
| 0:45-2:00 | Generate synthetic data | 100 products, 50 stores, 10K transactions with errors |
| 2:00-3:00 | Implement Shadow DLT | DataQualityGuard class, quarantine logic |
| 3:00-3:30 | Validate & export | Verify quarantine table has data, export CSVs |
| 3:30-4:45 | Build dashboard | Power BI with Trust Score, Sankey, Decomposition Tree |
| 4:45-5:30 | Polish narrative | Add scenario descriptions, color coding |
| 5:30-6:00 | Dry run | Test drill-down to specific errors |

### Installation Steps

#### 1. Local Environment (Data Generation)

```bash
# Clone the repository
git clone https://github.com/JoelR25/QC-Dashboard.git
cd QC-Dashboard

# Install Python dependencies
pip install -r requirements.txt

# Generate synthetic data
python scripts/01_generate_synthetic_data.py
```

#### 2. Databricks Community Edition

```python
# In Databricks Notebook
%pip install faker

# Import the main pipeline notebook
# Upload: notebooks/02_control_tower_pipeline.py

# Run the pipeline
dbutils.notebook.run("02_control_tower_pipeline", timeout_seconds=3600)
```

#### 3. Power BI Desktop

1. Open Power BI Desktop
2. Use "Get Data" → Choose JDBC or import exported CSVs
3. Import the template: `powerbi/ControlTower_Template.pbit`
4. Refresh the data model

---

## 📁 Project Structure

```
QC-Dashboard/
│
├── README.md                          # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Exclusions
│
├── notebooks/                         # Databricks notebooks
│   ├── 00_data_generator.py           # Synthetic data creation
│   ├── 01_shadow_dlt.py               # DataQualityGuard class
│   ├── 02_control_tower_pipeline.py   # Main ETL orchestration
│   └── 03_export_to_powerbi.py        # Data export utility
│
├── scripts/                           # Standalone Python scripts
│   ├── 01_generate_synthetic_data.py  # Local data generation
│   ├── 02_validate_data_quality.py    # Testing quality rules
│   └── utils/                         # Helper functions
│       ├── cpg_data_generator.py      # CPG-specific data logic
│       └── quality_guard.py           # Validation framework
│
├── data/                              # Data storage (gitignored)
│   ├── master/                        # Reference data (Product, Store)
│   ├── bronze/                        # Raw transaction data
│   ├── silver/                        # Clean data
│   ├── quarantine/                    # Invalid data
│   ├── gold/                          # Aggregated analytics
│   └── .gitkeep                       # Preserve structure
│
├── powerbi/                           # Power BI assets
│   ├── ControlTower_Template.pbit     # Dashboard template
│   ├── DAX_Measures.txt               # Trust Score formulas
│   └── DataModel_Guide.md             # Relationship setup
│
└── docs/                              # Documentation
    ├── architecture_diagram.png       # Visual architecture
    ├── executive_pitch_outline.md     # 15-minute pitch script
    ├── data_dictionary.md             # Schema reference
    └── troubleshooting.md             # Common issues

```

---

## 🛠️ Implementation Guide

### Step 1: Generate Synthetic Data

The simulation requires realistic CPG data with **deliberate quality issues**:

```python
# Run locally or in Databricks
from utils.cpg_data_generator import CPGDataGenerator

generator = CPGDataGenerator(seed=42)  # Fixed seed for reproducibility

# Generate reference data (the "truth")
product_master = generator.generate_product_master(num_products=100)
store_master = generator.generate_store_master(num_stores=50)

# Generate transaction data with entropy injections
sales_data = generator.generate_sales_transactions(
    num_transactions=10000,
    error_rate_orphan_upc=0.05,      # 5% missing UPCs
    error_rate_negative_sales=0.01,   # 1% negative values
    error_rate_missing_store=0.02     # 2% unknown stores
)
```

**Key Entropy Injections:**

1. **Orphan UPCs**: 5% of transactions use random UPCs not in Product Master
2. **Negative Sales**: 1% of Sales_Dollars are multiplied by -1
3. **Missing Stores**: 2% use "Store_999" not in Store Master
4. **Specific Pattern**: 500 transactions for consistent "Unknown_UPC_999999001" for pattern detection

### Step 2: Implement Shadow DLT

Since Community Edition lacks Delta Live Tables, implement a "Shadow" pattern:

```python
class DataQualityGuard:
    """
    Simulates DLT Expectations for data quality enforcement.
    Implements the Quarantine Pattern.
    """
    
    def __init__(self, df, expectations, audit_table):
        self.df = df
        self.expectations = expectations  # Dict of rule_name: SQL_condition
        self.audit_table = audit_table
        
    def validate(self):
        """Apply all expectations and tag invalid rows."""
        for rule_name, condition in self.expectations.items():
            self.df = self.df.withColumn(
                f"valid_{rule_name}", 
                expr(condition)
            )
        
        # Combine all checks
        self.df = self.df.withColumn(
            "is_valid", 
            reduce(lambda a, b: a & b, [col(f"valid_{r}") for r in self.expectations])
        )
        
        return self
    
    def split(self):
        """Route to Clean or Quarantine."""
        clean_df = self.df.filter(col("is_valid") == True)
        quarantine_df = self.df.filter(col("is_valid") == False)
        
        return clean_df, quarantine_df
    
    def log_metrics(self, batch_id):
        """Write counts to Audit Log."""
        total = self.df.count()
        clean, quarantine = self.split()
        
        audit_entry = {
            "batch_id": batch_id,
            "input_rows": total,
            "valid_rows": clean.count(),
            "quarantine_rows": quarantine.count(),
            "trust_score": clean.count() / total if total > 0 else 0,
            "timestamp": datetime.now()
        }
        
        # Append to Delta table
        spark.createDataFrame([audit_entry]).write.mode("append").saveAsTable(self.audit_table)
```

### Step 3: Run the Pipeline

The main pipeline orchestrates the Medallion flow:

```python
# Bronze: Ingest raw data
bronze_df = (spark.read.csv("dbfs:/FileStore/raw_sales.csv", header=True)
             .withColumn("ingestion_timestamp", current_timestamp()))
bronze_df.write.format("delta").mode("overwrite").saveAsTable("bronze_sales")

# Silver: Apply quality checks
silver_guard = DataQualityGuard(
    df=bronze_df,
    expectations={
        "upc_exists": "UPC IS NOT NULL AND UPC IN (SELECT UPC FROM product_master)",
        "store_exists": "Store_ID IN (SELECT Store_ID FROM store_master)",
        "sales_positive": "Sales_Dollars >= 0"
    },
    audit_table="audit_log"
)

silver_guard.validate()
clean_df, quarantine_df = silver_guard.split()

clean_df.write.format("delta").mode("overwrite").saveAsTable("silver_sales_clean")
quarantine_df.write.format("delta").mode("overwrite").saveAsTable("silver_quarantine")

silver_guard.log_metrics(batch_id=1)

# Gold: Aggregate
gold_df = (clean_df.groupBy("Brand", "Region")
           .agg(
               sum("Sales_Dollars").alias("Total_Revenue"),
               sum("Units_Sold").alias("Total_Units")
           ))
gold_df.write.format("delta").mode("overwrite").saveAsTable("gold_brand_analytics")
```

---

## 📊 Dashboard Guide

### Power BI Data Model

**Fact Tables:**
1. `Fact_Sales` (from Gold) - Brand/Region aggregates
2. `Fact_Quarantine` (from Silver Quarantine) - Transaction-level errors
3. `Fact_Audit_Log` (from Audit) - Batch-level metrics

**Dimension Tables:**
1. `Dim_Time` - Date hierarchy
2. `Dim_Region` - Geographic lookup
3. `Dim_Error_Reason` - Error code descriptions

### Key DAX Measures

```dax
// KPI Trust Score
Trust Score % = 
DIVIDE(
    SUM(Fact_Audit_Log[Valid_Rows]),
    SUM(Fact_Audit_Log[Input_Rows]),
    0
) * 100

// Revenue at Risk
Revenue at Risk = 
SUMX(
    Fact_Quarantine,
    Fact_Quarantine[Sales_Dollars]
)

// Conditional Formatting for Trust Score
Trust Score Color = 
SWITCH(
    TRUE(),
    [Trust Score %] >= 98, "Green",
    [Trust Score %] >= 95, "Yellow",
    "Red"
)
```

### Dashboard Layout (Z-Pattern)

```
┌─────────────────────────────────────────────────────┐
│  [Trust Score: 94%]     [Revenue at Risk: $50K]     │  ← Zone A & B
├─────────────────────────────────────────────────────┤
│                                                     │
│          [Sankey Diagram: Data Flow]                │  ← Zone C
│       Bronze → Silver Clean → Gold                  │
│              ↘ Silver Quarantine                    │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Decomposition Tree: Root Cause Analysis]          │  ← Zone D
│  Error Type → Region → Brand → Store                │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Databricks Community Edition Connection Timeout**

**Problem**: Power BI can't connect via JDBC to Community Edition.

**Solution**: Use the CSV export fallback:
```python
# In Databricks
df_gold.toPandas().to_csv("/dbfs/FileStore/gold_sales.csv")
df_quarantine.toPandas().to_csv("/dbfs/FileStore/quarantine.csv")

# Download via browser
# https://community.cloud.databricks.com/files/gold_sales.csv
```

#### 2. **Trust Score is 100% (No Errors)**

**Problem**: The synthetic data didn't inject errors.

**Solution**: Check the random seed:
```python
# Ensure deterministic error generation
generator = CPGDataGenerator(seed=42)
```

#### 3. **Cluster Terminates During Demo**

**Problem**: Community Edition clusters auto-terminate after 2 hours.

**Solution**: Save all data to DBFS Delta tables, not ephemeral memory.

#### 4. **Power BI DirectQuery is Slow**

**Problem**: Real-time queries to Community Edition lag.

**Solution**: Use Import Mode instead of DirectQuery for the demo.

---

## 📚 References

### Documentation
- [Databricks Medallion Architecture](https://docs.databricks.com/aws/en/lakehouse/medallion)
- [Delta Live Tables Expectations](https://docs.databricks.com/aws/en/ldp/expectations)
- [Power BI Decomposition Tree](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-tutorial-decomp-tree)

### Concepts
- **Data Observability**: Monitoring data quality, not just pipeline success
- **Silent Failure**: Pipelines succeed but output semantically incorrect data
- **Quarantine Pattern**: Routing invalid data for analysis rather than dropping
- **Trust Score**: Percentage of data passing quality checks

### Industry Context
- Circana (formerly IRI) provides syndicated POS data for CPG companies
- CPG teams use this data for demand planning, pricing, and supply chain decisions
- Data quality issues can lead to million-dollar strategic errors

---

## 🎤 Executive Pitch Script (15 Minutes)

### Slide 1: The Billion Dollar Blindspot (0-3 min)

> "We make inventory decisions worth millions based on Circana data. But we have a blindspot. Our current monitoring tells us if the pipeline ran, not if the data is right. Last month, we missed a $200K sales trend because data for a new product launch was silently dropped."

**Visual**: Blurred sales chart

### Slide 2: Introducing the Control Tower (3-6 min)

> "We're proposing a shift from 'Pipeline Monitoring' to 'Data Observability'. The Data Control Tower introduces a Quarantine Pattern. Instead of dropping bad data, we catch it, measure it, and introduce a Trust Score for every dashboard."

**Visual**: Architecture diagram (Bronze → Silver/Quarantine → Gold)

### Slide 3: Live Demo (6-12 min)

1. **Point to Trust Score**: "See this? 94%. It's red. This tells you not to make a decision yet."
2. **Point to Revenue at Risk**: "$50K in unattributed sales."
3. **Use Decomposition Tree**: "Click 'Missing UPC' → 'Northeast' → 'Summer Seltzer'. We know exactly who to call."

### Slide 4: The Ask (12-15 min)

> "I built this simulation to prove the concept. To scale this, I need approval to implement Delta Live Tables and Unity Catalog in our Azure environment. The ROI is trusted data and a 40% reduction in debugging time."

**Visual**: Current State vs. Target State comparison

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

This is a reference implementation for educational and proof-of-concept purposes. Contributions welcome via pull requests.

---

## ✨ Acknowledgments

Based on industry best practices for Data Observability in CPG analytics, utilizing the Databricks Medallion Architecture pattern.

---

**Built with:**
- Databricks Community Edition
- Python (Faker, Pandas, PySpark)
- Power BI Desktop
- Delta Lake

**Last Updated**: January 2026
