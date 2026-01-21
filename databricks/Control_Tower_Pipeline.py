# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Control Tower - Medallion Pipeline
# MAGIC ## Enterprise Data Observability for CPG Analytics (Circana/IRI POS Data)
# MAGIC 
# MAGIC This notebook implements the complete Control Tower pipeline:
# MAGIC - **Bronze Layer**: Raw data ingestion from Circana
# MAGIC - **Silver Layer**: Quality enforcement with Quarantine Pattern
# MAGIC - **Gold Layer**: Business-ready aggregations
# MAGIC - **Audit Trail**: Complete observability and reconciliation
# MAGIC 
# MAGIC **Author**: Data Quality Control Tower Team
# MAGIC **Target**: Databricks Community Edition / Enterprise Azure Databricks
# MAGIC **Runtime**: DBR 13.3 LTS or higher

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Install Dependencies and Configure Environment

# COMMAND ----------

# Install required libraries
%pip install faker pyyaml

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# Import libraries
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import json

# Set up Spark configuration for optimal Delta performance
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("Environment configured successfully")
print(f"Spark Version: {spark.version}")
print(f"Execution Time: {datetime.now()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration: Define Paths and Parameters

# COMMAND ----------

# Configuration
BATCH_ID = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
BASE_PATH = "/tmp/control_tower"
DATA_PATH = f"{BASE_PATH}/data"
BRONZE_PATH = f"{BASE_PATH}/bronze"
SILVER_PATH = f"{BASE_PATH}/silver"
SILVER_QUARANTINE_PATH = f"{BASE_PATH}/silver_quarantine"
GOLD_PATH = f"{BASE_PATH}/gold"
AUDIT_PATH = f"{BASE_PATH}/audit"

# Clean up previous runs (optional - comment out to preserve data)
dbutils.fs.rm(BASE_PATH, recurse=True)

print(f"Batch ID: {BATCH_ID}")
print(f"Base Path: {BASE_PATH}")
print("Configuration complete")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Generate Synthetic Circana POS Data
# MAGIC 
# MAGIC Generate realistic CPG Point-of-Sale data with intentional quality issues:
# MAGIC - Orphan UPCs (not in Product Master)
# MAGIC - Missing Store IDs
# MAGIC - Negative sales values
# MAGIC - Extreme pricing errors
# MAGIC - Null values in critical fields
# MAGIC - New product launch scenario (consistent pattern for detection)

# COMMAND ----------

# Data Generator Code (embedded for Community Edition compatibility)
from faker import Faker
import random
import pandas as pd

Faker.seed(42)
random.seed(42)
fake = Faker()

def generate_product_master(num_products=100):
    """Generate Product Master reference data"""
    brands = ["PowerCrunch", "Nature Valley", "Clif Bar", "Kind", "Quest",
              "RxBar", "Larabar", "Gatorade", "Powerade", "Summer Seltzer", "LaCroix"]
    categories = ["Energy Bars", "Beverages", "Sports Drinks", "Water", "Soda"]
    
    products = []
    for i in range(num_products):
        upc = f"{8000000000 + i:013d}"
        brand = random.choice(brands)
        category = random.choice(categories)
        
        product = {
            'UPC': upc,
            'Brand': brand,
            'Category': category,
            'Product_Name': f"{brand} {fake.word().title()}",
            'List_Price': round(random.uniform(2.99, 15.99), 2),
            'Active_Flag': 'Y'
        }
        products.append(product)
    
    return spark.createDataFrame(products)

def generate_store_master(num_stores=50):
    """Generate Store Master reference data"""
    retailers = ["Walmart", "Target", "Kroger", "Safeway", "Whole Foods"]
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    
    stores = []
    for i in range(1, num_stores + 1):
        store = {
            'Store_ID': f"ST{i:05d}",
            'Retailer_Name': random.choice(retailers),
            'Region': random.choice(regions),
            'City': fake.city(),
            'State': fake.state_abbr(),
            'Active_Flag': 'Y'
        }
        stores.append(store)
    
    return spark.createDataFrame(stores)

def generate_sales_transactions(product_master_pd, store_master_pd, num_transactions=10000):
    """Generate sales transactions with quality issues"""
    valid_upcs = product_master_pd.select('UPC').rdd.flatMap(lambda x: x).collect()
    valid_stores = store_master_pd.select('Store_ID').rdd.flatMap(lambda x: x).collect()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=4)
    
    transactions = []
    
    for i in range(num_transactions):
        # Base transaction
        week_end = fake.date_between(start_date=start_date, end_date=end_date)
        upc = random.choice(valid_upcs)
        store_id = random.choice(valid_stores)
        units = random.randint(1, 50)
        sales = round(units * random.uniform(3.0, 12.0), 2)
        
        # Inject errors
        if random.random() < 0.05:  # 5% orphan UPCs
            upc = f"{9990000000 + random.randint(0, 999):013d}"
        if random.random() < 0.02:  # 2% missing stores
            store_id = "ST99999"
        if random.random() < 0.01:  # 1% negative sales
            sales *= -1
            units *= -1
        if random.random() < 0.005:  # 0.5% extreme prices
            sales *= 100
        
        transaction = {
            'Transaction_ID': f"TXN{i:010d}",
            'Week_End': week_end,
            'Store_ID': store_id,
            'UPC': upc if random.random() > 0.03 else None,  # 3% null UPCs
            'Units_Sold': units if random.random() > 0.02 else None,  # 2% null units
            'Sales_Dollars': sales if random.random() > 0.02 else None,  # 2% null sales
            'Batch_ID': BATCH_ID,
            'Source_System': 'Circana_Unify'
        }
        transactions.append(transaction)
    
    # Add new product launch block (consistent pattern)
    for i in range(500):
        transaction = {
            'Transaction_ID': f"TXN_NEW{i:06d}",
            'Week_End': end_date - timedelta(days=random.randint(0, 7)),
            'Store_ID': valid_stores[0] if random.random() < 0.8 else random.choice(valid_stores),
            'UPC': "9999990000001",  # Unknown UPC
            'Units_Sold': random.randint(5, 20),
            'Sales_Dollars': round(random.randint(5, 20) * 12.99, 2),
            'Batch_ID': BATCH_ID,
            'Source_System': 'Circana_Unify'
        }
        transactions.append(transaction)
    
    return spark.createDataFrame(transactions)

# Generate data
print("Generating Product Master...")
product_master_df = generate_product_master(100)
product_master_df.cache()

print("Generating Store Master...")
store_master_df = generate_store_master(50)
store_master_df.cache()

print("Generating Sales Transactions...")
sales_df = generate_sales_transactions(product_master_df, store_master_df, 10000)

print(f"\n{'='*70}")
print("DATA GENERATION COMPLETE")
print(f"{'='*70}")
print(f"Products: {product_master_df.count():,}")
print(f"Stores: {store_master_df.count():,}")
print(f"Transactions: {sales_df.count():,}")
print(f"{'='*70}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Bronze Layer - Raw Data Ingestion
# MAGIC 
# MAGIC Ingest raw data with minimal transformation. Add metadata for audit trail.

# COMMAND ----------

# Bronze Layer: Ingest raw data
print("BRONZE LAYER: Ingesting raw data...")

# Add ingestion metadata
bronze_df = sales_df.withColumn("Ingestion_Timestamp", current_timestamp()) \
                     .withColumn("Bronze_Batch_ID", lit(BATCH_ID))

# Write to Delta
bronze_df.write.format("delta").mode("overwrite").save(BRONZE_PATH)

# Also save reference data
product_master_df.write.format("delta").mode("overwrite").save(f"{BASE_PATH}/product_master")
store_master_df.write.format("delta").mode("overwrite").save(f"{BASE_PATH}/store_master")

bronze_count = bronze_df.count()
print(f"✓ Bronze layer created: {bronze_count:,} records")
print(f"✓ Reference data saved")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Shadow DLT - Quality Guard Implementation
# MAGIC 
# MAGIC Implement validation logic that mimics Delta Live Tables expectations.
# MAGIC Split data into Valid (Silver) and Quarantine streams.

# COMMAND ----------

# Shadow DLT Implementation
class DataQualityGuard:
    """Shadow DLT for Community Edition"""
    
    def __init__(self, batch_id):
        self.batch_id = batch_id
        self.audit_records = []
    
    def validate_with_expectations(self, df, expectations, layer_name):
        """Apply expectations and split valid/quarantine"""
        input_count = df.count()
        
        print(f"\n{'='*70}")
        print(f"Data Quality Guard - {layer_name}")
        print(f"{'='*70}")
        print(f"Input Records: {input_count:,}")
        
        # Apply all expectations
        validated_df = df
        validation_cols = []
        error_cols = []
        
        for rule_name, rule_config in expectations.items():
            condition = rule_config['condition']
            severity = rule_config['severity']
            description = rule_config['description']
            
            val_col = f"_valid_{rule_name}"
            err_col = f"_error_{rule_name}"
            
            validated_df = validated_df.withColumn(val_col, when(condition, lit(True)).otherwise(lit(False)))
            validated_df = validated_df.withColumn(
                err_col,
                when(~col(val_col), lit(f"{rule_name}|{severity}|{description}")).otherwise(lit(None))
            )
            
            validation_cols.append(val_col)
            error_cols.append(err_col)
            
            failed = validated_df.filter(~col(val_col)).count()
            if failed > 0:
                print(f"  ✗ {rule_name}: {failed:,} failures ({severity})")
            else:
                print(f"  ✓ {rule_name}: All records valid")
        
        # Create master validation flag
        is_valid_expr = col(validation_cols[0])
        for val_col in validation_cols[1:]:
            is_valid_expr = is_valid_expr & col(val_col)
        
        validated_df = validated_df.withColumn("_is_valid", is_valid_expr)
        validated_df = validated_df.withColumn("_error_details", concat_ws("; ", *error_cols))
        
        # Split streams
        valid_df = validated_df.filter(col("_is_valid")).drop(*validation_cols, *error_cols, "_is_valid", "_error_details")
        quarantine_df = validated_df.filter(~col("_is_valid")) \
            .withColumn("Quarantine_Timestamp", current_timestamp()) \
            .withColumn("Batch_ID", lit(self.batch_id)) \
            .withColumn("Layer_Name", lit(layer_name)) \
            .withColumn("Error_Details", col("_error_details")) \
            .drop(*validation_cols, *error_cols, "_is_valid", "_error_details")
        
        valid_count = valid_df.count()
        quarantine_count = quarantine_df.count()
        trust_score = (valid_count / input_count * 100) if input_count > 0 else 0
        
        print(f"\nRESULTS:")
        print(f"  Valid: {valid_count:,} ({trust_score:.2f}%)")
        print(f"  Quarantined: {quarantine_count:,} ({100-trust_score:.2f}%)")
        print(f"  TRUST SCORE: {trust_score:.2f}%")
        print(f"{'='*70}\n")
        
        # Audit log
        self.audit_records.append({
            'batch_id': self.batch_id,
            'layer_name': layer_name,
            'timestamp': datetime.now().isoformat(),
            'input_rows': input_count,
            'valid_rows': valid_count,
            'quarantine_rows': quarantine_count,
            'trust_score': trust_score
        })
        
        return valid_df, quarantine_df
    
    def get_audit_records(self):
        return self.audit_records

# Initialize Quality Guard
quality_guard = DataQualityGuard(BATCH_ID)

print("✓ Data Quality Guard initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Silver Layer - Quality Enforcement with Quarantine
# MAGIC 
# MAGIC Apply validation rules and route invalid records to quarantine.

# COMMAND ----------

# Load Bronze data
bronze_read_df = spark.read.format("delta").load(BRONZE_PATH)
product_master_read = spark.read.format("delta").load(f"{BASE_PATH}/product_master")
store_master_read = spark.read.format("delta").load(f"{BASE_PATH}/store_master")

# Define expectations
valid_upcs = [row['UPC'] for row in product_master_read.select('UPC').collect()]
valid_stores = [row['Store_ID'] for row in store_master_read.select('Store_ID').collect()]

expectations = {
    'upc_not_null': {
        'condition': col('UPC').isNotNull(),
        'severity': 'CRITICAL',
        'description': 'UPC must not be null'
    },
    'sales_not_null': {
        'condition': col('Sales_Dollars').isNotNull(),
        'severity': 'CRITICAL',
        'description': 'Sales must not be null'
    },
    'units_not_null': {
        'condition': col('Units_Sold').isNotNull(),
        'severity': 'HIGH',
        'description': 'Units must not be null'
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
        'condition': (col('Sales_Dollars') / col('Units_Sold') <= 100) & (col('Units_Sold') > 0),
        'severity': 'MEDIUM',
        'description': 'Unit price must be reasonable'
    }
}

# Apply Quality Guard
silver_df, quarantine_df = quality_guard.validate_with_expectations(
    bronze_read_df,
    expectations,
    "Bronze_to_Silver"
)

# Write Silver and Quarantine
silver_df.write.format("delta").mode("overwrite").save(SILVER_PATH)
quarantine_df.write.format("delta").mode("overwrite").save(SILVER_QUARANTINE_PATH)

print("✓ Silver layer created")
print("✓ Quarantine table populated")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Gold Layer - Business Aggregations
# MAGIC 
# MAGIC Create business-ready aggregated data for reporting.

# COMMAND ----------

# Load Silver data and join with master data
silver_read_df = spark.read.format("delta").load(SILVER_PATH)

# Join with Product Master to get Brand and Category
gold_df = silver_read_df.join(broadcast(product_master_read), "UPC", "inner") \
    .join(broadcast(store_master_read), "Store_ID", "inner")

# Aggregate by Brand and Region
gold_aggregated = gold_df.groupBy("Brand", "Category", "Region", "Week_End") \
    .agg(
        sum("Sales_Dollars").alias("Total_Sales"),
        sum("Units_Sold").alias("Total_Units"),
        count("*").alias("Transaction_Count"),
        avg(col("Sales_Dollars") / col("Units_Sold")).alias("Avg_Unit_Price")
    ) \
    .withColumn("Batch_ID", lit(BATCH_ID)) \
    .withColumn("Created_Timestamp", current_timestamp())

# Write Gold layer
gold_aggregated.write.format("delta").mode("overwrite").save(GOLD_PATH)

gold_count = gold_aggregated.count()
print(f"✓ Gold layer created: {gold_count:,} aggregated records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Audit Trail and Reconciliation
# MAGIC 
# MAGIC Create comprehensive audit log and perform reconciliation checks.

# COMMAND ----------

# Create audit log
audit_records = quality_guard.get_audit_records()
audit_df = spark.createDataFrame(audit_records)

# Add reconciliation metrics
bronze_final_count = spark.read.format("delta").load(BRONZE_PATH).count()
silver_final_count = spark.read.format("delta").load(SILVER_PATH).count()
quarantine_final_count = spark.read.format("delta").load(SILVER_QUARANTINE_PATH).count()
gold_final_count = spark.read.format("delta").load(GOLD_PATH).count()

# Calculate Revenue at Risk
revenue_at_risk = quarantine_df.select(sum("Sales_Dollars")).collect()[0][0] or 0

# Enhanced audit with reconciliation
audit_summary = audit_df.withColumn("Bronze_Total", lit(bronze_final_count)) \
    .withColumn("Silver_Valid", lit(silver_final_count)) \
    .withColumn("Silver_Quarantine", lit(quarantine_final_count)) \
    .withColumn("Gold_Aggregated", lit(gold_final_count)) \
    .withColumn("Revenue_At_Risk", lit(float(revenue_at_risk))) \
    .withColumn("Reconciliation_Check", lit(silver_final_count + quarantine_final_count == bronze_final_count))

# Write audit log
audit_summary.write.format("delta").mode("overwrite").save(AUDIT_PATH)

print(f"\n{'='*70}")
print("AUDIT SUMMARY")
print(f"{'='*70}")
print(f"Bronze Total: {bronze_final_count:,}")
print(f"Silver Valid: {silver_final_count:,}")
print(f"Silver Quarantine: {quarantine_final_count:,}")
print(f"Gold Aggregated: {gold_final_count:,}")
print(f"Revenue at Risk: ${revenue_at_risk:,.2f}")
print(f"Reconciliation: {'✓ PASS' if (silver_final_count + quarantine_final_count == bronze_final_count) else '✗ FAIL'}")
print(f"{'='*70}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: Export for Power BI (Community Edition Workaround)
# MAGIC 
# MAGIC Export key tables to CSV for Power BI Desktop import.

# COMMAND ----------

# Export for Power BI
print("Exporting data for Power BI...")

# Gold layer for main reporting
gold_export = spark.read.format("delta").load(GOLD_PATH).toPandas()
gold_export.to_csv("/dbfs/FileStore/control_tower_gold.csv", index=False)

# Quarantine for error analysis
quarantine_export = spark.read.format("delta").load(SILVER_QUARANTINE_PATH) \
    .select("UPC", "Store_ID", "Sales_Dollars", "Units_Sold", "Error_Details", "Week_End", "Quarantine_Timestamp") \
    .toPandas()
quarantine_export.to_csv("/dbfs/FileStore/control_tower_quarantine.csv", index=False)

# Audit log for trust score
audit_export = audit_summary.toPandas()
audit_export.to_csv("/dbfs/FileStore/control_tower_audit.csv", index=False)

# Product and Store masters for context
product_master_read.toPandas().to_csv("/dbfs/FileStore/control_tower_products.csv", index=False)
store_master_read.toPandas().to_csv("/dbfs/FileStore/control_tower_stores.csv", index=False)

print("✓ Data exported successfully")
print("\nDownload URLs (accessible from browser):")
print("  - Gold: https://community.cloud.databricks.com/files/control_tower_gold.csv")
print("  - Quarantine: https://community.cloud.databricks.com/files/control_tower_quarantine.csv")
print("  - Audit: https://community.cloud.databricks.com/files/control_tower_audit.csv")
print("  - Products: https://community.cloud.databricks.com/files/control_tower_products.csv")
print("  - Stores: https://community.cloud.databricks.com/files/control_tower_stores.csv")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification Queries
# MAGIC 
# MAGIC Run these queries to validate the Control Tower is working correctly.

# COMMAND ----------

# Verification Query 1: Trust Score by Layer
print("Trust Score Analysis:")
spark.read.format("delta").load(AUDIT_PATH).select(
    "layer_name", "trust_score", "input_rows", "valid_rows", "quarantine_rows"
).show(truncate=False)

# COMMAND ----------

# Verification Query 2: Top Error Types in Quarantine
print("Top Error Types:")
quarantine_analysis = spark.read.format("delta").load(SILVER_QUARANTINE_PATH)
quarantine_analysis.groupBy("Error_Details").count() \
    .orderBy(desc("count")) \
    .show(10, truncate=False)

# COMMAND ----------

# Verification Query 3: Revenue at Risk by Week
print("Revenue at Risk by Week:")
quarantine_analysis.groupBy("Week_End") \
    .agg(sum("Sales_Dollars").alias("Revenue_At_Risk")) \
    .orderBy("Week_End") \
    .show()

# COMMAND ----------

# Verification Query 4: Gold Layer Sample
print("Gold Layer Sample:")
spark.read.format("delta").load(GOLD_PATH) \
    .orderBy(desc("Total_Sales")) \
    .show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pipeline Complete!
# MAGIC 
# MAGIC The Control Tower pipeline has successfully processed the data:
# MAGIC - ✓ Bronze layer ingested with raw data
# MAGIC - ✓ Silver layer validated with quality rules
# MAGIC - ✓ Quarantine captures data quality issues
# MAGIC - ✓ Gold layer contains business aggregations
# MAGIC - ✓ Audit trail provides complete observability
# MAGIC - ✓ Data exported for Power BI visualization
# MAGIC 
# MAGIC Next Steps:
# MAGIC 1. Download the CSV files from FileStore
# MAGIC 2. Import into Power BI Desktop
# MAGIC 3. Build the Control Tower dashboard
# MAGIC 4. Present to stakeholders!
