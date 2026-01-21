-- SQL Validation Scripts for Data Quality Control Tower
-- Run these queries in Databricks SQL to validate pipeline health

-- =====================================================================
-- 1. TRUST SCORE VALIDATION
-- =====================================================================

-- Calculate overall trust score across all batches
SELECT 
    COUNT(DISTINCT batch_id) as total_batches,
    SUM(valid_rows) as total_valid,
    SUM(quarantine_rows) as total_quarantined,
    SUM(input_rows) as total_input,
    ROUND((SUM(valid_rows) * 100.0 / SUM(input_rows)), 2) as overall_trust_score_pct
FROM audit_log;

-- Trust score by batch
SELECT 
    batch_id,
    layer_name,
    timestamp,
    input_rows,
    valid_rows,
    quarantine_rows,
    ROUND(trust_score, 2) as trust_score_pct,
    CASE 
        WHEN trust_score >= 98 THEN 'Excellent'
        WHEN trust_score >= 95 THEN 'Good'
        WHEN trust_score >= 90 THEN 'Warning'
        ELSE 'Critical'
    END as status
FROM audit_log
ORDER BY timestamp DESC;

-- =====================================================================
-- 2. RECONCILIATION VALIDATION
-- =====================================================================

-- Verify Bronze = Silver_Valid + Silver_Quarantine (no data loss)
SELECT 
    batch_id,
    Bronze_Total as bronze_count,
    Silver_Valid as silver_valid_count,
    Silver_Quarantine as silver_quarantine_count,
    (Silver_Valid + Silver_Quarantine) as silver_total,
    Bronze_Total - (Silver_Valid + Silver_Quarantine) as data_loss,
    CASE 
        WHEN Bronze_Total = (Silver_Valid + Silver_Quarantine) THEN 'PASS'
        ELSE 'FAIL - DATA LOSS DETECTED'
    END as reconciliation_status
FROM audit_log;

-- Row count comparison across layers
SELECT 
    'Bronze' as layer,
    COUNT(*) as row_count
FROM bronze_sales
UNION ALL
SELECT 
    'Silver_Valid' as layer,
    COUNT(*) as row_count
FROM silver_sales
UNION ALL
SELECT 
    'Silver_Quarantine' as layer,
    COUNT(*) as row_count
FROM silver_quarantine
UNION ALL
SELECT 
    'Gold' as layer,
    COUNT(*) as row_count
FROM gold_brand_analytics;

-- =====================================================================
-- 3. DATA QUALITY ANALYSIS
-- =====================================================================

-- Top error types in quarantine
SELECT 
    CASE 
        WHEN Error_Details LIKE '%upc_in_master%' THEN 'Orphan UPC'
        WHEN Error_Details LIKE '%store_in_master%' THEN 'Unknown Store'
        WHEN Error_Details LIKE '%non_negative_sales%' THEN 'Negative Sales'
        WHEN Error_Details LIKE '%reasonable_price%' THEN 'Extreme Price'
        WHEN Error_Details LIKE '%upc_not_null%' THEN 'Null UPC'
        WHEN Error_Details LIKE '%sales_not_null%' THEN 'Null Sales'
        WHEN Error_Details LIKE '%units_not_null%' THEN 'Null Units'
        ELSE 'Other'
    END as error_type,
    COUNT(*) as error_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM silver_quarantine), 2) as pct_of_total,
    SUM(Sales_Dollars) as revenue_at_risk
FROM silver_quarantine
GROUP BY error_type
ORDER BY error_count DESC;

-- Error severity breakdown
SELECT 
    CASE 
        WHEN Error_Details LIKE '%CRITICAL%' THEN 'CRITICAL'
        WHEN Error_Details LIKE '%HIGH%' THEN 'HIGH'
        WHEN Error_Details LIKE '%MEDIUM%' THEN 'MEDIUM'
        ELSE 'UNKNOWN'
    END as severity,
    COUNT(*) as error_count
FROM silver_quarantine
GROUP BY severity
ORDER BY 
    CASE 
        WHEN severity = 'CRITICAL' THEN 1
        WHEN severity = 'HIGH' THEN 2
        WHEN severity = 'MEDIUM' THEN 3
        ELSE 4
    END;

-- =====================================================================
-- 4. REVENUE AT RISK ANALYSIS
-- =====================================================================

-- Total revenue at risk
SELECT 
    ROUND(SUM(Sales_Dollars), 2) as total_revenue_at_risk,
    COUNT(*) as quarantined_transactions
FROM silver_quarantine
WHERE Sales_Dollars IS NOT NULL;

-- Revenue at risk by week
SELECT 
    Week_End,
    COUNT(*) as quarantined_records,
    ROUND(SUM(Sales_Dollars), 2) as revenue_at_risk
FROM silver_quarantine
WHERE Sales_Dollars IS NOT NULL
GROUP BY Week_End
ORDER BY Week_End DESC;

-- Revenue at risk by error type
SELECT 
    CASE 
        WHEN Error_Details LIKE '%upc_in_master%' THEN 'Orphan UPC'
        WHEN Error_Details LIKE '%store_in_master%' THEN 'Unknown Store'
        WHEN Error_Details LIKE '%non_negative_sales%' THEN 'Negative Sales'
        ELSE 'Other'
    END as error_type,
    COUNT(*) as record_count,
    ROUND(SUM(Sales_Dollars), 2) as revenue_at_risk
FROM silver_quarantine
WHERE Sales_Dollars IS NOT NULL
GROUP BY error_type
ORDER BY revenue_at_risk DESC;

-- =====================================================================
-- 5. PATTERN DETECTION
-- =====================================================================

-- Identify orphan UPCs (new products not in master)
SELECT 
    UPC,
    COUNT(*) as transaction_count,
    ROUND(SUM(Sales_Dollars), 2) as potential_revenue
FROM silver_quarantine
WHERE Error_Details LIKE '%upc_in_master%'
GROUP BY UPC
ORDER BY transaction_count DESC
LIMIT 20;

-- Stores with most quality issues
SELECT 
    q.Store_ID,
    s.Retailer_Name,
    s.Region,
    COUNT(*) as error_count,
    ROUND(SUM(q.Sales_Dollars), 2) as revenue_at_risk
FROM silver_quarantine q
LEFT JOIN store_master s ON q.Store_ID = s.Store_ID
GROUP BY q.Store_ID, s.Retailer_Name, s.Region
ORDER BY error_count DESC
LIMIT 10;

-- =====================================================================
-- 6. TREND ANALYSIS
-- =====================================================================

-- Trust score trend over time
SELECT 
    DATE_TRUNC('week', timestamp) as week,
    ROUND(AVG(trust_score), 2) as avg_trust_score,
    SUM(quarantine_rows) as total_quarantined
FROM audit_log
GROUP BY week
ORDER BY week DESC;

-- Quarantine volume trend
SELECT 
    Week_End,
    COUNT(*) as quarantined_count,
    LAG(COUNT(*)) OVER (ORDER BY Week_End) as prev_week_count,
    ROUND((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY Week_End)) * 100.0 / 
          NULLIF(LAG(COUNT(*)) OVER (ORDER BY Week_End), 0), 2) as pct_change
FROM silver_quarantine
GROUP BY Week_End
ORDER BY Week_End DESC;

-- =====================================================================
-- 7. GOLD LAYER VALIDATION
-- =====================================================================

-- Validate gold aggregations sum correctly
SELECT 
    'Gold Total Sales' as metric,
    ROUND(SUM(Total_Sales), 2) as value
FROM gold_brand_analytics
UNION ALL
SELECT 
    'Silver Valid Sales' as metric,
    ROUND(SUM(Sales_Dollars), 2) as value
FROM silver_sales;

-- Brand performance summary
SELECT 
    Brand,
    COUNT(DISTINCT Region) as regions_sold,
    SUM(Transaction_Count) as total_transactions,
    ROUND(SUM(Total_Sales), 2) as total_sales,
    ROUND(SUM(Total_Units), 0) as total_units
FROM gold_brand_analytics
GROUP BY Brand
ORDER BY total_sales DESC
LIMIT 10;

-- =====================================================================
-- 8. MASTER DATA VALIDATION
-- =====================================================================

-- Check for UPCs in transactions but not in master
SELECT 
    b.UPC,
    COUNT(*) as transaction_count,
    SUM(b.Sales_Dollars) as total_sales
FROM bronze_sales b
LEFT JOIN product_master p ON b.UPC = p.UPC
WHERE p.UPC IS NULL
  AND b.UPC IS NOT NULL
GROUP BY b.UPC
ORDER BY transaction_count DESC
LIMIT 20;

-- Check for stores in transactions but not in master
SELECT 
    b.Store_ID,
    COUNT(*) as transaction_count,
    SUM(b.Sales_Dollars) as total_sales
FROM bronze_sales b
LEFT JOIN store_master s ON b.Store_ID = s.Store_ID
WHERE s.Store_ID IS NULL
GROUP BY b.Store_ID
ORDER BY transaction_count DESC
LIMIT 10;

-- =====================================================================
-- 9. DATA FRESHNESS CHECK
-- =====================================================================

-- Check data age
SELECT 
    MAX(timestamp) as last_batch_timestamp,
    ROUND(TIMESTAMPDIFF(HOUR, MAX(timestamp), CURRENT_TIMESTAMP()), 2) as hours_since_last_batch,
    CASE 
        WHEN TIMESTAMPDIFF(HOUR, MAX(timestamp), CURRENT_TIMESTAMP()) <= 24 THEN 'Fresh'
        WHEN TIMESTAMPDIFF(HOUR, MAX(timestamp), CURRENT_TIMESTAMP()) <= 48 THEN 'Acceptable'
        WHEN TIMESTAMPDIFF(HOUR, MAX(timestamp), CURRENT_TIMESTAMP()) <= 168 THEN 'Stale'
        ELSE 'Critical - Data Too Old'
    END as freshness_status
FROM audit_log;

-- =====================================================================
-- 10. ALERT THRESHOLD CHECKS
-- =====================================================================

-- Check if any alert thresholds are breached
SELECT 
    'Trust Score Alert' as alert_type,
    CASE 
        WHEN (SUM(valid_rows) * 100.0 / SUM(input_rows)) < 95 THEN 'TRIGGERED'
        ELSE 'OK'
    END as status,
    ROUND((SUM(valid_rows) * 100.0 / SUM(input_rows)), 2) as current_value,
    95.0 as threshold
FROM audit_log
WHERE timestamp >= CURRENT_DATE - INTERVAL 1 DAY
UNION ALL
SELECT 
    'Revenue Risk Alert' as alert_type,
    CASE 
        WHEN SUM(Sales_Dollars) > 10000 THEN 'TRIGGERED'
        ELSE 'OK'
    END as status,
    ROUND(SUM(Sales_Dollars), 2) as current_value,
    10000.0 as threshold
FROM silver_quarantine
WHERE Quarantine_Timestamp >= CURRENT_DATE - INTERVAL 1 DAY;

-- =====================================================================
-- 11. DIAGNOSTIC QUERIES
-- =====================================================================

-- Sample of quarantined records for investigation
SELECT 
    Transaction_ID,
    UPC,
    Store_ID,
    Sales_Dollars,
    Units_Sold,
    Week_End,
    Error_Details,
    Quarantine_Timestamp
FROM silver_quarantine
LIMIT 100;

-- Records with multiple errors
SELECT 
    Transaction_ID,
    UPC,
    Store_ID,
    LENGTH(Error_Details) - LENGTH(REPLACE(Error_Details, ';', '')) + 1 as error_count,
    Error_Details
FROM silver_quarantine
WHERE Error_Details LIKE '%;%'
ORDER BY error_count DESC
LIMIT 20;

-- =====================================================================
-- 12. PERFORMANCE METRICS
-- =====================================================================

-- Pipeline processing statistics
SELECT 
    batch_id,
    layer_name,
    input_rows,
    valid_rows,
    quarantine_rows,
    ROUND((valid_rows * 1.0 / input_rows) * 100, 2) as processing_efficiency_pct,
    timestamp
FROM audit_log
ORDER BY timestamp DESC;

-- =====================================================================
-- 13. EXECUTIVE SUMMARY QUERY
-- =====================================================================

-- Single comprehensive view for leadership
SELECT 
    (SELECT MAX(timestamp) FROM audit_log) as report_date,
    (SELECT ROUND((SUM(valid_rows) * 100.0 / SUM(input_rows)), 2) FROM audit_log) as trust_score_pct,
    (SELECT COUNT(*) FROM silver_quarantine) as quarantined_records,
    (SELECT ROUND(SUM(Sales_Dollars), 2) FROM silver_quarantine) as revenue_at_risk,
    (SELECT COUNT(*) FROM silver_sales) as valid_transactions,
    (SELECT ROUND(SUM(Total_Sales), 2) FROM gold_brand_analytics) as total_realized_revenue,
    (SELECT COUNT(DISTINCT Brand) FROM gold_brand_analytics) as active_brands,
    (SELECT COUNT(DISTINCT Region) FROM gold_brand_analytics) as active_regions;
