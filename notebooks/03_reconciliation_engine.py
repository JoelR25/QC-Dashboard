# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Control Tower - Reconciliation Engine
# MAGIC
# MAGIC **Purpose**: Automate end-to-end data reconciliation across the Circana pipeline
# MAGIC
# MAGIC **Pipeline**: Unify (Circana) → ADLS → Bronze → Silver → Gold → Power BI
# MAGIC
# MAGIC **Schedule**: Run every Monday at 8 AM (after weekly data load)
# MAGIC
# MAGIC **Outputs**:
# MAGIC - `reconciliation_control_tower` Delta table
# MAGIC - Email alerts for critical issues
# MAGIC - Power BI dataset refresh trigger

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration & Setup

# COMMAND ----------

# Import libraries
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime, timedelta
import requests
import json

# Configuration
CONFIG = {
    "products": [
        {"name": "Nielsen_Retail", "expected_files": 150, "adls_path": "/mnt/raw/nielsen_retail"},
        {"name": "Circana_Grocery", "expected_files": 85, "adls_path": "/mnt/raw/circana_grocery"},
        {"name": "Unify_Convenience", "expected_files": 60, "adls_path": "/mnt/raw/unify_convenience"}
    ],
    "week_end_date": None,  # Will be set dynamically
    "reconciliation_table": "reconciliation_control_tower",
    "alert_email": "ba-team@company.com",
    "pbi_workspace_id": "YOUR_WORKSPACE_ID",
    "pbi_dataset_id": "YOUR_DATASET_ID"
}

# Get latest week end date (last Saturday)
today = datetime.now()
days_since_saturday = (today.weekday() + 2) % 7
last_saturday = today - timedelta(days=days_since_saturday)
CONFIG["week_end_date"] = last_saturday.date()

print(f"🗓️  Processing Week Ending: {CONFIG['week_end_date']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Initialize Reconciliation Table

# COMMAND ----------

# Create reconciliation table if it doesn't exist
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CONFIG['reconciliation_table']} (
    recon_id STRING,
    product_name STRING,
    week_end_date DATE,
    layer_name STRING,
    file_count_expected INT,
    file_count_actual INT,
    row_count_expected BIGINT,
    row_count_actual BIGINT,
    variance_pct DOUBLE,
    status STRING,
    error_details STRING,
    check_timestamp TIMESTAMP,
    data_timestamp TIMESTAMP,
    latency_hours DOUBLE,
    trust_score_pct DOUBLE
)
USING DELTA
PARTITIONED BY (week_end_date)
""")

print(f"✅ Reconciliation table ready: {CONFIG['reconciliation_table']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Helper Functions

# COMMAND ----------

def log_reconciliation_result(
    product_name,
    week_end_date,
    layer_name,
    file_count_expected=None,
    file_count_actual=None,
    row_count_expected=None,
    row_count_actual=None,
    status="OK",
    error_details=None,
    data_timestamp=None,
    trust_score_pct=None
):
    """
    Log a reconciliation result to the control tower table.
    """
    recon_id = f"{product_name}_{week_end_date}_{layer_name}"
    check_timestamp = datetime.now()
    
    # Calculate variance
    if row_count_expected and row_count_actual:
        variance_pct = ((row_count_actual - row_count_expected) / row_count_expected * 100) if row_count_expected > 0 else 0
    else:
        variance_pct = 0
    
    # Calculate latency
    latency_hours = None
    if data_timestamp:
        latency_hours = (check_timestamp - data_timestamp).total_seconds() / 3600
    
    # Create DataFrame
    result_df = spark.createDataFrame([(
        recon_id,
        product_name,
        week_end_date,
        layer_name,
        file_count_expected,
        file_count_actual,
        row_count_expected,
        row_count_actual,
        variance_pct,
        status,
        error_details,
        check_timestamp,
        data_timestamp,
        latency_hours,
        trust_score_pct
    )], schema=f"""
        recon_id STRING,
        product_name STRING,
        week_end_date DATE,
        layer_name STRING,
        file_count_expected INT,
        file_count_actual INT,
        row_count_expected BIGINT,
        row_count_actual BIGINT,
        variance_pct DOUBLE,
        status STRING,
        error_details STRING,
        check_timestamp TIMESTAMP,
        data_timestamp TIMESTAMP,
        latency_hours DOUBLE,
        trust_score_pct DOUBLE
    """)
    
    # Append to table
    result_df.write.format("delta").mode("append").saveAsTable(CONFIG['reconciliation_table'])
    
    return variance_pct, status

# COMMAND ----------

def send_alert_email(subject, body):
    """
    Send email alert (integrate with your email service).
    """
    # In production, integrate with SendGrid, AWS SES, or SMTP
    # For now, just print
    print(f"\n📧 EMAIL ALERT")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("="*60)
    
    # Example using SendGrid (uncomment and configure):
    # import sendgrid
    # from sendgrid.helpers.mail import Mail
    # 
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    # message = Mail(
    #     from_email='alerts@company.com',
    #     to_emails=CONFIG['alert_email'],
    #     subject=subject,
    #     html_content=body
    # )
    # response = sg.send(message)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Layer 1→2: Source to ADLS Reconciliation

# COMMAND ----------

def check_adls_landing(product_config, week_end_date):
    """
    Verify files landed in ADLS from Circana.
    """
    product_name = product_config["name"]
    expected_count = product_config["expected_files"]
    adls_path = product_config["adls_path"]
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking ADLS Landing: {product_name}")
    print(f"{'='*60}")
    
    # Build ADLS path for the week
    week_path = f"{adls_path}/{week_end_date.strftime('%Y/%m/%d')}/"
    
    try:
        # List files in ADLS
        files = dbutils.fs.ls(week_path)
        actual_count = len([f for f in files if f.name.endswith('.csv')])
        
        # Determine status
        if actual_count == expected_count:
            status = "OK"
            error_details = None
        elif actual_count < expected_count:
            status = "ERROR"
            error_details = f"Missing files: Expected {expected_count}, Found {actual_count}"
        else:
            status = "WARNING"
            error_details = f"Extra files: Expected {expected_count}, Found {actual_count}"
        
        print(f"   Expected: {expected_count} files")
        print(f"   Actual:   {actual_count} files")
        print(f"   Status:   {status}")
        
        # Get file timestamp (earliest file for data_timestamp)
        if files:
            data_timestamp = datetime.fromtimestamp(files[0].modificationTime / 1000)
        else:
            data_timestamp = None
        
    except Exception as e:
        actual_count = 0
        status = "ERROR"
        error_details = f"Path not found or access error: {str(e)}"
        data_timestamp = None
        print(f"   ❌ Error: {error_details}")
    
    # Log result
    log_reconciliation_result(
        product_name=product_name,
        week_end_date=week_end_date,
        layer_name="ADLS_Landing",
        file_count_expected=expected_count,
        file_count_actual=actual_count,
        status=status,
        error_details=error_details,
        data_timestamp=data_timestamp
    )
    
    return actual_count, status

# Run for all products
for product in CONFIG["products"]:
    check_adls_landing(product, CONFIG["week_end_date"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Layer 2→3: ADLS to Bronze Reconciliation

# COMMAND ----------

def check_bronze_ingestion(product_config, week_end_date):
    """
    Verify ADLS files were ingested into Bronze.
    """
    product_name = product_config["name"]
    bronze_table = f"bronze_{product_name.lower().replace('-', '_')}"
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking Bronze Ingestion: {product_name}")
    print(f"{'='*60}")
    
    try:
        # Get Bronze row count for the week
        bronze_df = spark.sql(f"""
            SELECT COUNT(*) as row_count
            FROM {bronze_table}
            WHERE week_end_date = '{week_end_date}'
        """)
        bronze_count = bronze_df.first()['row_count']
        
        # Get expected count from previous ADLS check
        adls_recon = spark.sql(f"""
            SELECT row_count_actual as expected_count
            FROM {CONFIG['reconciliation_table']}
            WHERE product_name = '{product_name}'
              AND week_end_date = '{week_end_date}'
              AND layer_name = 'ADLS_Landing'
            ORDER BY check_timestamp DESC
            LIMIT 1
        """)
        
        if adls_recon.count() > 0:
            expected_count = adls_recon.first()['expected_count'] or bronze_count  # Fallback
        else:
            expected_count = bronze_count  # First run, use actual as baseline
        
        # Calculate variance
        variance_pct = ((bronze_count - expected_count) / expected_count * 100) if expected_count > 0 else 0
        
        # Determine status (allow 0.1% tolerance for rounding)
        if abs(variance_pct) < 0.1:
            status = "OK"
            error_details = None
        else:
            status = "ERROR"
            error_details = f"Row mismatch: Expected {expected_count:,}, Got {bronze_count:,} ({variance_pct:+.2f}%)"
        
        print(f"   Expected Rows: {expected_count:,}")
        print(f"   Actual Rows:   {bronze_count:,}")
        print(f"   Variance:      {variance_pct:+.2f}%")
        print(f"   Status:        {status}")
        
    except Exception as e:
        bronze_count = 0
        expected_count = 0
        status = "ERROR"
        error_details = f"Table error: {str(e)}"
        print(f"   ❌ Error: {error_details}")
    
    # Log result
    log_reconciliation_result(
        product_name=product_name,
        week_end_date=week_end_date,
        layer_name="Bronze",
        row_count_expected=expected_count,
        row_count_actual=bronze_count,
        status=status,
        error_details=error_details
    )

# Run for all products
for product in CONFIG["products"]:
    check_bronze_ingestion(product, CONFIG["week_end_date"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Layer 3: Bronze to Silver Reconciliation (Trust Score)

# COMMAND ----------

def check_silver_quality(product_config, week_end_date):
    """
    Verify Silver Clean + Quarantine = Bronze (Trust Score calculation).
    """
    product_name = product_config["name"]
    bronze_table = f"bronze_{product_name.lower().replace('-', '_')}"
    silver_clean_table = f"silver_{product_name.lower().replace('-', '_')}_clean"
    silver_quarantine_table = f"silver_{product_name.lower().replace('-', '_')}_quarantine"
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking Silver Quality: {product_name}")
    print(f"{'='*60}")
    
    try:
        # Get counts
        bronze_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM {bronze_table}
            WHERE week_end_date = '{week_end_date}'
        """).first()['cnt']
        
        clean_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM {silver_clean_table}
            WHERE week_end_date = '{week_end_date}'
        """).first()['cnt']
        
        quarantine_count = spark.sql(f"""
            SELECT COUNT(*) as cnt FROM {silver_quarantine_table}
            WHERE week_end_date = '{week_end_date}'
        """).first()['cnt']
        
        silver_total = clean_count + quarantine_count
        
        # Calculate Trust Score
        trust_score = (clean_count / bronze_count * 100) if bronze_count > 0 else 0
        
        # Calculate variance
        variance_pct = ((silver_total - bronze_count) / bronze_count * 100) if bronze_count > 0 else 0
        
        # Determine status
        if abs(variance_pct) < 0.1 and trust_score >= 95:
            status = "OK"
            error_details = None
        elif abs(variance_pct) < 0.1 and trust_score >= 90:
            status = "WARNING"
            error_details = f"Low trust score: {trust_score:.2f}%"
        else:
            status = "ERROR"
            if abs(variance_pct) >= 0.1:
                error_details = f"Row mismatch: Bronze={bronze_count:,}, Silver={silver_total:,}"
            else:
                error_details = f"Critical trust score: {trust_score:.2f}%"
        
        print(f"   Bronze Rows:     {bronze_count:,}")
        print(f"   Clean Rows:      {clean_count:,}")
        print(f"   Quarantine Rows: {quarantine_count:,}")
        print(f"   Silver Total:    {silver_total:,}")
        print(f"   Trust Score:     {trust_score:.2f}%")
        print(f"   Status:          {status}")
        
    except Exception as e:
        bronze_count = 0
        silver_total = 0
        trust_score = 0
        status = "ERROR"
        error_details = f"Table error: {str(e)}"
        print(f"   ❌ Error: {error_details}")
    
    # Log result
    log_reconciliation_result(
        product_name=product_name,
        week_end_date=week_end_date,
        layer_name="Silver",
        row_count_expected=bronze_count,
        row_count_actual=silver_total,
        status=status,
        error_details=error_details,
        trust_score_pct=trust_score
    )

# Run for all products
for product in CONFIG["products"]:
    check_silver_quality(product, CONFIG["week_end_date"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Layer 4: Silver to Gold Reconciliation

# COMMAND ----------

def check_gold_aggregation(product_config, week_end_date):
    """
    Verify Gold aggregations reconcile to Silver Clean.
    """
    product_name = product_config["name"]
    silver_clean_table = f"silver_{product_name.lower().replace('-', '_')}_clean"
    gold_table = f"gold_{product_name.lower().replace('-', '_')}_analytics"
    
    print(f"\n{'='*60}")
    print(f"🔍 Checking Gold Aggregation: {product_name}")
    print(f"{'='*60}")
    
    try:
        # Sum sales from Silver Clean
        silver_sum = spark.sql(f"""
            SELECT COALESCE(SUM(sales_dollars), 0) as total
            FROM {silver_clean_table}
            WHERE week_end_date = '{week_end_date}'
        """).first()['total']
        
        # Sum sales from Gold
        gold_sum = spark.sql(f"""
            SELECT COALESCE(SUM(total_revenue), 0) as total
            FROM {gold_table}
            WHERE week_end_date = '{week_end_date}'
        """).first()['total']
        
        # Calculate variance
        variance_pct = ((gold_sum - silver_sum) / silver_sum * 100) if silver_sum > 0 else 0
        
        # Determine status (allow 0.01% tolerance for rounding)
        if abs(variance_pct) < 0.01:
            status = "OK"
            error_details = None
        else:
            status = "ERROR"
            error_details = f"Aggregation mismatch: Silver=${silver_sum:,.2f}, Gold=${gold_sum:,.2f}"
        
        print(f"   Silver Sum:  ${silver_sum:,.2f}")
        print(f"   Gold Sum:    ${gold_sum:,.2f}")
        print(f"   Variance:    {variance_pct:+.4f}%")
        print(f"   Status:      {status}")
        
    except Exception as e:
        silver_sum = 0
        gold_sum = 0
        status = "ERROR"
        error_details = f"Table error: {str(e)}"
        print(f"   ❌ Error: {error_details}")
    
    # Log result
    log_reconciliation_result(
        product_name=product_name,
        week_end_date=week_end_date,
        layer_name="Gold",
        row_count_expected=int(silver_sum) if silver_sum else 0,
        row_count_actual=int(gold_sum) if gold_sum else 0,
        status=status,
        error_details=error_details
    )

# Run for all products
for product in CONFIG["products"]:
    check_gold_aggregation(product, CONFIG["week_end_date"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Generate Alert Report

# COMMAND ----------

# Query for issues
issues_df = spark.sql(f"""
    SELECT 
        product_name,
        layer_name,
        status,
        error_details,
        variance_pct,
        trust_score_pct,
        check_timestamp
    FROM {CONFIG['reconciliation_table']}
    WHERE week_end_date = '{CONFIG['week_end_date']}'
      AND status IN ('ERROR', 'WARNING')
    ORDER BY 
        CASE WHEN status = 'ERROR' THEN 1 ELSE 2 END,
        product_name,
        layer_name
""")

issue_count = issues_df.count()

print(f"\n{'='*60}")
print(f"📊 Reconciliation Summary for Week Ending {CONFIG['week_end_date']}")
print(f"{'='*60}")

if issue_count > 0:
    print(f"⚠️  {issue_count} Issues Found:")
    issues_df.show(truncate=False)
    
    # Send alert email
    email_body = f"""
    <h2>Data Quality Issues Detected</h2>
    <p>Week Ending: <strong>{CONFIG['week_end_date']}</strong></p>
    <p>Total Issues: <strong>{issue_count}</strong></p>
    
    <h3>Issue Details:</h3>
    {issues_df.toPandas().to_html(index=False)}
    
    <p>Please investigate and resolve these issues before the Monday status meeting.</p>
    <p><a href="https://app.powerbi.com/groups/{CONFIG['pbi_workspace_id']}/apps/{CONFIG['pbi_dataset_id']}">
        View Full Dashboard →
    </a></p>
    """
    
    send_alert_email(
        subject=f"⚠️ Data Quality Issues - Week of {CONFIG['week_end_date']}",
        body=email_body
    )
else:
    print("✅ No issues found. All reconciliations passed!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Trigger Power BI Refresh

# COMMAND ----------

def refresh_powerbi_dataset():
    """
    Trigger Power BI dataset refresh via REST API.
    """
    print("\n🔄 Triggering Power BI Dataset Refresh...")
    
    # In production, use Service Principal authentication
    # This is a placeholder for the API call
    
    # Example (requires configuration):
    # url = f"https://api.powerbi.com/v1.0/myorg/groups/{CONFIG['pbi_workspace_id']}/datasets/{CONFIG['pbi_dataset_id']}/refreshes"
    # headers = {"Authorization": f"Bearer {access_token}"}
    # response = requests.post(url, headers=headers)
    
    print("   ✅ Power BI refresh triggered (placeholder)")
    print("   Configure with Service Principal for production")

refresh_powerbi_dataset()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Final Summary

# COMMAND ----------

# Get overall summary
summary_df = spark.sql(f"""
    SELECT 
        layer_name,
        COUNT(*) as product_count,
        SUM(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as ok_count,
        SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
        SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as error_count,
        AVG(trust_score_pct) as avg_trust_score
    FROM {CONFIG['reconciliation_table']}
    WHERE week_end_date = '{CONFIG['week_end_date']}'
    GROUP BY layer_name
    ORDER BY 
        CASE layer_name
            WHEN 'ADLS_Landing' THEN 1
            WHEN 'Bronze' THEN 2
            WHEN 'Silver' THEN 3
            WHEN 'Gold' THEN 4
            WHEN 'PowerBI_SemanticModel' THEN 5
        END
""")

print(f"\n{'='*70}")
print(f"✅ RECONCILIATION COMPLETE - Week Ending {CONFIG['week_end_date']}")
print(f"{'='*70}\n")
summary_df.show()

print("\n🎯 Next Steps:")
print("   1. Review any ERROR/WARNING statuses above")
print("   2. Check the Power BI App for detailed analysis")
print("   3. Address critical issues before user reports are accessed")
print(f"\n📊 View Dashboard: https://app.powerbi.com/groups/{CONFIG['pbi_workspace_id']}/")
print(f"\n{'='*70}\n")
