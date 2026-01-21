# Data Dictionary

## Overview

This document defines the schema for all data tables in the Data Quality Control Tower simulation.

---

## Master Data (Reference Tables)

### Product Master

**Purpose**: The canonical source of truth for product information.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| UPC | String (13 digits) | Universal Product Code (EAN-13 format) | "123456789012" |
| Brand | String | Brand name for aggregation | "PowerCrunch" |
| Category | String | Product category | "Protein Bars" |
| Sub_Category | String | Product sub-category | "Whey" |
| List_Price | Float | Manufacturer's suggested retail price | 4.99 |

**Row Count**: ~100 products

---

### Store Master

**Purpose**: Reference data for store locations and attributes.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| Store_ID | String | Unique store identifier | "STORE_0001" |
| Retailer_Name | String | Retailer chain name | "Walmart" |
| Region | String | Geographic region | "Northeast" |
| City | String | Store city | "Boston" |
| State | String | Two-letter state code | "MA" |

**Row Count**: ~50 stores across 8 regions

---

## Transaction Data (Bronze Layer)

### Sales Transactions (Bronze)

**Purpose**: Raw point-of-sale transaction data as received from the syndicated data provider (Circana).

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| Transaction_ID | String | Unique transaction identifier | "TXN_00000001" |
| UPC | String | Product UPC (may not exist in master) | "123456789012" |
| Store_ID | String | Store identifier (may not exist in master) | "STORE_0001" |
| Week_End | Date | Saturday of the reporting week | 2026-01-18 |
| Units_Sold | Integer | Number of units sold | 10 |
| Sales_Dollars | Float | Total sales revenue (may be negative) | 49.90 |
| List_Price | Float | Reference price at time of transaction | 4.99 |

**Row Count**: ~10,000 transactions

**Data Quality Issues** (Deliberately Injected):
- **Orphan UPCs**: ~5% of records have UPCs not in Product Master
- **Missing Stores**: ~2% of records have Store_ID not in Store Master  
- **Negative Sales**: ~1% of records have negative Sales_Dollars (returns/errors)
- **Price Spikes**: ~0.5% of records have abnormally high prices (decimal errors)

---

## Quality-Enforced Data (Silver Layer)

### Sales Transactions - Clean (Silver)

**Purpose**: Validated transaction data that passed all quality checks.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| Transaction_ID | String | Unique transaction identifier | "TXN_00000001" |
| UPC | String | Validated product UPC | "123456789012" |
| Store_ID | String | Validated store identifier | "STORE_0001" |
| Week_End | Date | Saturday of the reporting week | 2026-01-18 |
| Units_Sold | Integer | Number of units sold | 10 |
| Sales_Dollars | Float | Total sales revenue (positive) | 49.90 |
| List_Price | Float | Reference price | 4.99 |
| is_valid | Boolean | Validation flag (always True) | True |

**Expected Row Count**: ~9,200 transactions (~92% pass rate)

---

### Sales Transactions - Quarantine (Silver)

**Purpose**: Transaction data that failed one or more quality checks. Tagged with error metadata for analysis.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| Transaction_ID | String | Unique transaction identifier | "TXN_00000002" |
| UPC | String | Product UPC (possibly invalid) | "999999001" |
| Store_ID | String | Store identifier (possibly invalid) | "STORE_999" |
| Week_End | Date | Saturday of the reporting week | 2026-01-18 |
| Units_Sold | Integer | Number of units sold | 5 |
| Sales_Dollars | Float | Total sales revenue (possibly negative) | -25.00 |
| List_Price | Float | Reference price | 5.00 |
| is_valid | Boolean | Validation flag (always False) | False |
| **Error_Reason** | String | Comma-separated list of failed rules | "upc_exists, sales_positive" |
| **Batch_ID** | Integer | Processing batch identifier | 1 |
| **Quarantine_Timestamp** | Timestamp | When record was quarantined | 2026-01-21 10:30:00 |

**Expected Row Count**: ~800 transactions (~8% failure rate)

**Common Error Reasons**:
- `upc_exists`: UPC not found in Product Master
- `store_exists`: Store_ID not found in Store Master
- `sales_positive`: Sales_Dollars is negative
- `units_positive`: Units_Sold is zero or negative

---

## Analytics Data (Gold Layer)

### Brand Analytics (Gold)

**Purpose**: Aggregated sales metrics by Brand and Region for executive dashboards.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| Brand | String | Product brand | "PowerCrunch" |
| Region | String | Geographic region | "Northeast" |
| Total_Revenue | Float | Sum of Sales_Dollars | 125,450.00 |
| Total_Units | Integer | Sum of Units_Sold | 25,090 |
| Avg_Price | Float | Average selling price | 5.00 |
| Transaction_Count | Integer | Number of transactions | 2,500 |

**Row Count**: Variable (Brand x Region combinations, ~100-200 rows)

**Source**: Aggregated from Silver_Clean table only (excludes quarantine records)

---

## Audit & Observability

### Audit Log

**Purpose**: Batch-level metrics tracking data quality over time. Powers the "Trust Score" KPI.

| Column | Data Type | Description | Example |
|--------|-----------|-------------|---------|
| batch_id | Integer | Unique batch identifier | 1 |
| input_rows | Integer | Total rows in bronze | 10,000 |
| valid_rows | Integer | Rows passing all checks | 9,200 |
| quarantine_rows | Integer | Rows failing checks | 800 |
| trust_score_pct | Float | (valid_rows / input_rows) * 100 | 92.00 |
| timestamp | Timestamp | Processing timestamp | 2026-01-21 10:30:00 |

**Key Metric**: 
```
Trust Score = (valid_rows / input_rows) * 100
```

**Thresholds**:
- **Green**: ≥ 98% (High trust)
- **Yellow**: 95-98% (Medium trust)
- **Red**: < 95% (Low trust - action required)

---

## Validation Rules (Expectations)

The following rules are applied during the Bronze → Silver transformation:

| Rule Name | SQL Expression | Severity | Action |
|-----------|----------------|----------|--------|
| upc_exists | `UPC IS NOT NULL AND UPC IN (SELECT UPC FROM product_master)` | High | Quarantine |
| store_exists | `Store_ID IN (SELECT Store_ID FROM store_master)` | High | Quarantine |
| sales_positive | `Sales_Dollars >= 0` | Medium | Quarantine |
| units_positive | `Units_Sold > 0` | Medium | Quarantine |
| price_reasonable | `Sales_Dollars / Units_Sold BETWEEN 0.50 AND 50.00` | Low | Log (optional) |

---

## Entropy Injection Strategy (Simulation Only)

For demonstration purposes, the synthetic data generator deliberately introduces errors:

| Error Type | Rate | Description | Pattern |
|------------|------|-------------|---------|
| Orphan UPC | 5% | UPCs not in Product Master | Includes 500 transactions with consistent UPC "999999001" |
| Missing Store | 2% | Store "STORE_999" (not in master) | Clustered for pattern detection |
| Negative Sales | 1% | Sales_Dollars < 0 | Random distribution |
| Price Spike | 0.5% | Price * 100 (decimal error) | Random distribution |

**Total Expected Failure Rate**: ~8%  
**Expected Trust Score**: ~92%

---

## Power BI Data Model

### Relationships

```
Dim_Time (1) ─────── (*) Fact_Sales
Dim_Region (1) ──────(*) Fact_Sales
Dim_Region (1) ──────(*) Fact_Quarantine
Dim_Error_Reason (1) ─(*) Fact_Quarantine
Dim_Batch (1) ───────(*) Fact_Audit_Log
```

### Recommended Star Schema

**Fact Tables**:
1. `Fact_Sales` = Gold Brand Analytics
2. `Fact_Quarantine` = Silver Quarantine
3. `Fact_Audit_Log` = Audit Log

**Dimension Tables** (create manually in Power BI):
1. `Dim_Time`: Date hierarchy (Year, Quarter, Month, Week)
2. `Dim_Region`: Geographic lookup
3. `Dim_Error_Reason`: Error code descriptions

---

## File Locations

```
data/
├── master/
│   ├── product_master.csv       # Product reference data
│   └── store_master.csv         # Store reference data
├── bronze/
│   └── sales_transactions.csv   # Raw transaction data
├── silver/
│   └── sales_clean.csv          # Validated clean data
├── quarantine/
│   └── sales_quarantine.csv     # Invalid data with error tags
├── gold/
│   └── brand_analytics.csv      # Aggregated metrics
└── audit_log.csv                # Quality metrics log
```

---

## Version History

- **v1.0** (January 2026): Initial schema definition for Control Tower simulation
