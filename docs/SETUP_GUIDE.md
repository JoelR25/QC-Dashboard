# Data Quality Control Tower - Setup Guide

## Overview
This guide walks you through setting up the complete Data Quality Control Tower for CPG analytics, from Databricks backend to Power BI frontend dashboard.

## Table of Contents
1. [Quick Start (6-Hour Timeline)](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Databricks Configuration](#databricks-configuration)
4. [Running the Pipeline](#running-the-pipeline)
5. [Power BI Dashboard Setup](#power-bi-dashboard-setup)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start (6-Hour Timeline)

This timeline assumes starting from zero and reaching a functional demo:

| Time | Activity | Deliverable |
|------|----------|-------------|
| 0:00-0:45 | Infrastructure Setup | Databricks account, cluster running, Power BI installed |
| 0:45-2:00 | Data Engineering | Synthetic data generated with quality issues |
| 2:00-3:00 | Pipeline Implementation | Bronze/Silver/Gold layers created, quarantine populated |
| 3:00-3:30 | Validation & Export | Data verified, CSVs exported |
| 3:30-4:45 | Dashboard Construction | Power BI model built, visuals configured |
| 4:45-5:30 | Narrative Polish | Scenarios documented, colors applied |
| 5:30-6:00 | Dry Run | Full demo walkthrough |

---

## Environment Setup

### 1. Databricks Community Edition

1. **Create Account**
   - Go to: https://community.cloud.databricks.com/signup.html
   - Sign up with email (free tier)
   - Verify email and log in

2. **Create Cluster**
   ```
   - Click "Compute" in sidebar
   - Click "Create Cluster"
   - Name: "ControlTower"
   - Runtime: DBR 13.3 LTS or higher
   - Mode: Single Node
   - Node type: Default (15GB memory)
   - Click "Create Cluster"
   - Wait ~5 minutes for cluster to start
   ```

3. **Install Libraries**
   ```
   - Go to cluster page
   - Click "Libraries" tab
   - Click "Install New"
   - Select "PyPI"
   - Package: faker
   - Click "Install"
   - Repeat for: pyyaml
   ```

### 2. Power BI Desktop

1. **Download and Install**
   - Download from: https://aka.ms/pbidesktop
   - Run installer (Windows only; use Power BI Service for Mac)
   - Launch Power BI Desktop

2. **Verify Installation**
   - Open Power BI Desktop
   - Check version: Help → About
   - Ensure version is 2023 or later for best features

### 3. Python Environment (Optional - for local testing)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Databricks Configuration

### 1. Import Notebook

**Option A: Upload Notebook File**
1. In Databricks, click "Workspace"
2. Navigate to your user folder
3. Click dropdown arrow → "Import"
4. Upload: `databricks/Control_Tower_Pipeline.py`
5. Click "Import"

**Option B: Create Manually**
1. Click "Workspace" → "Create" → "Notebook"
2. Name: "Control Tower Pipeline"
3. Language: Python
4. Cluster: Select your cluster
5. Copy/paste content from `databricks/Control_Tower_Pipeline.py`

### 2. Generate Personal Access Token (PAT)

For Power BI connectivity:
1. Click profile icon (top right)
2. Go to "User Settings"
3. Click "Developer" → "Access Tokens"
4. Click "Generate New Token"
5. Comment: "Power BI Connection"
6. Lifetime: 90 days
7. Click "Generate"
8. **IMPORTANT**: Copy token immediately (you won't see it again)

---

## Running the Pipeline

### 1. Execute Notebook

1. Open the "Control Tower Pipeline" notebook
2. Attach to your running cluster
3. Execute cells in order:
   - Click "Run All" or
   - Press Shift+Enter on each cell

4. Monitor execution:
   - Watch for green checkmarks
   - Look for Trust Score output
   - Verify quarantine count > 0

### 2. Verify Output

Run verification queries at the bottom of the notebook:

```python
# Should show Trust Score ~94-96%
spark.read.format("delta").load(AUDIT_PATH).show()

# Should show ~500-700 quarantined records
spark.read.format("delta").load(SILVER_QUARANTINE_PATH).count()

# Should show error types
spark.read.format("delta").load(SILVER_QUARANTINE_PATH) \
  .groupBy("Error_Details").count().show()
```

### 3. Export Data

The notebook automatically exports CSVs to FileStore.

**Download Files:**
1. Go to: `https://community.cloud.databricks.com/files/`
2. Download these files:
   - `control_tower_gold.csv`
   - `control_tower_quarantine.csv`
   - `control_tower_audit.csv`
   - `control_tower_products.csv`
   - `control_tower_stores.csv`

3. Save to a local folder (e.g., `C:\Data\ControlTower\`)

---

## Power BI Dashboard Setup

### 1. Import Data

1. Open Power BI Desktop
2. Click "Get Data" → "Text/CSV"
3. Import each CSV file:

   **Gold Sales** (`control_tower_gold.csv`)
   - Click "Transform Data"
   - Rename table to: `Fact_Sales`
   - Change types:
     - Week_End → Date
     - Total_Sales → Decimal
     - Total_Units → Whole Number

   **Quarantine** (`control_tower_quarantine.csv`)
   - Rename table to: `Fact_Quarantine`
   - Split `Error_Details` column by delimiter ";"
   - Extract first error as `Primary_Error_Type`

   **Audit Log** (`control_tower_audit.csv`)
   - Rename table to: `Fact_Audit_Log`
   - Verify `trust_score` is Decimal type

   **Product Master** (`control_tower_products.csv`)
   - Rename to: `Dim_Product`

   **Store Master** (`control_tower_stores.csv`)
   - Rename to: `Dim_Store`

4. Click "Close & Apply"

### 2. Create Relationships

1. Go to "Model" view (left sidebar)
2. Create relationships by dragging:
   - `Fact_Sales[Brand]` → `Dim_Product[Brand]`
   - `Fact_Sales[Region]` → `Dim_Store[Region]`
   - `Fact_Quarantine[Store_ID]` → `Dim_Store[Store_ID]`

### 3. Add DAX Measures

1. Click on `Fact_Audit_Log` table
2. Go to "Modeling" tab → "New Measure"
3. Copy/paste measures from `powerbi/dax/control_tower_measures.dax`

Key measures to add:
```dax
Trust Score % = 
DIVIDE(
    SUM(Fact_Audit_Log[valid_rows]),
    SUM(Fact_Audit_Log[input_rows]),
    0
) * 100

Revenue at Risk = 
SUM(Fact_Quarantine[Sales_Dollars])

Quarantined Records = 
SUM(Fact_Audit_Log[quarantine_rows])
```

### 4. Build Dashboard

**Page 1: Control Tower Overview**

1. **Trust Score Gauge** (Top Left)
   - Visual: Gauge
   - Value: `[Trust Score %]`
   - Min: 0, Max: 100
   - Target: 98
   - Conditional Formatting:
     - Red: < 90
     - Yellow: 90-98
     - Green: > 98

2. **Revenue at Risk Card** (Top Right)
   - Visual: Card
   - Field: `[Revenue at Risk]`
   - Format as Currency

3. **Sankey Diagram** (Center)
   - Install from AppSource: "Sankey Diagram"
   - Source: "Bronze Ingest"
   - Destination: Split into "Silver Clean" and "Quarantine"
   - Value: Row counts from `Fact_Audit_Log`

4. **Decomposition Tree** (Bottom)
   - Visual: Decomposition Tree (AI Visual)
   - Analyze: `[Quarantined Records]`
   - Explain By: 
     - Primary_Error_Type
     - Region
     - Brand
     - Store_ID

**Page 2: Detailed Error Analysis**

1. **Error Type Breakdown** (Bar Chart)
   - X-axis: Primary_Error_Type
   - Y-axis: Count of records

2. **Trend Analysis** (Line Chart)
   - X-axis: Week_End
   - Y-axis: Trust Score %

3. **Top Impacted Brands** (Table)
   - Columns: Brand, Quarantined Records, Revenue at Risk

---

## Troubleshooting

### Common Issues

**Issue: Trust Score is 100%**
- **Cause**: Data generator didn't inject errors
- **Fix**: Re-run notebook. Verify `Faker.seed(42)` is set. Check quarantine table has rows.

**Issue: Cannot connect Power BI to Databricks**
- **Cause**: Community Edition JDBC limitations
- **Fix**: Use CSV export method (already implemented in notebook)

**Issue: Cluster terminates during execution**
- **Cause**: 2-hour inactivity timeout
- **Fix**: Keep browser tab active. Re-run from last checkpoint.

**Issue: "Data Loss Count" shows non-zero**
- **Cause**: Reconciliation failure
- **Fix**: Re-run Bronze and Silver steps. Check for errors in cell output.

**Issue: Decomposition Tree doesn't drill down**
- **Cause**: Relationships not configured
- **Fix**: Verify relationships in Model view. Ensure cross-filter direction is set.

### Getting Help

- **Databricks**: https://community.databricks.com/
- **Power BI**: https://community.powerbi.com/
- **Project Issues**: Create issue on GitHub repository

---

## Next Steps

Once your dashboard is running:

1. **Customize for your data**: Replace synthetic data with actual Circana feeds
2. **Add more layers**: Extend to additional data sources (not just Circana)
3. **Automate**: Schedule Databricks Jobs for weekly runs
4. **Alert**: Set up Power BI alerts on Trust Score thresholds
5. **Present**: Use the dashboard in stakeholder meetings

## Security Notes

- **Do not commit** your Databricks PAT token to version control
- Use Azure Key Vault for production credentials
- Implement row-level security in Power BI for sensitive data
- Enable audit logs in Databricks for compliance

---

## Resources

- [Databricks Documentation](https://docs.databricks.com/)
- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [Medallion Architecture Guide](https://www.databricks.com/glossary/medallion-architecture)
- [Data Observability Best Practices](https://www.siffletdata.com/blog/data-observability)
