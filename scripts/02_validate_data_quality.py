"""
Validate Data Quality - Test the DataQualityGuard

This script validates the generated synthetic data using the DataQualityGuard class,
demonstrating how the quarantine pattern works.

Usage:
    python scripts/02_validate_data_quality.py

Prerequisites:
    - Run 01_generate_synthetic_data.py first

Author: Data Quality Control Tower Team
Date: January 2026
"""

import sys
import os
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.quality_guard import DataQualityGuard


def main():
    """Validate data quality and demonstrate the quarantine pattern."""
    
    print("="*70)
    print("  DATA QUALITY CONTROL TOWER - Validation & Quarantine Demo")
    print("="*70)
    print("\n🎯 Objective: Apply quality checks and route data to Clean/Quarantine\n")
    
    # Load data
    print("📂 Loading data...")
    try:
        product_master = pd.read_csv('data/master/product_master.csv')
        store_master = pd.read_csv('data/master/store_master.csv')
        sales_transactions = pd.read_csv('data/bronze/sales_transactions.csv')
        print(f"   ✅ Loaded {len(sales_transactions):,} transactions\n")
    except FileNotFoundError:
        print("❌ Error: Data files not found!")
        print("   Please run: python scripts/01_generate_synthetic_data.py")
        return
    
    # Get valid reference values
    valid_upcs = set(product_master['UPC'].astype(str))
    valid_stores = set(store_master['Store_ID'])
    
    # Define quality expectations
    print("📋 Defining Quality Expectations...")
    
    # For pandas, we use expressions that can be evaluated
    # Note: We'll check membership manually since eval() doesn't support .isin() directly
    sales_transactions['UPC'] = sales_transactions['UPC'].astype(str)
    sales_transactions['upc_in_master'] = sales_transactions['UPC'].isin(valid_upcs)
    sales_transactions['store_in_master'] = sales_transactions['Store_ID'].isin(valid_stores)
    
    expectations = {
        'upc_exists': 'upc_in_master == True',
        'store_exists': 'store_in_master == True',
        'sales_positive': 'Sales_Dollars >= 0',
        'units_positive': 'Units_Sold > 0'
    }
    
    print("   Quality Rules:")
    for rule_name, condition in expectations.items():
        print(f"      • {rule_name}: {condition}")
    
    # Apply Data Quality Guard
    print("\n" + "─"*70)
    print("🛡️  Applying Data Quality Guard")
    print("─"*70)
    
    guard = DataQualityGuard(
        df=sales_transactions,
        expectations=expectations,
        batch_id=1,
        engine='pandas'
    )
    
    # Validate and split
    guard.validate()
    clean_df, quarantine_df = guard.split()
    
    # Log metrics
    metrics = guard.log_metrics(output_file='data/audit_log.csv')
    
    # Show error breakdown
    print("\n📋 Error Breakdown by Rule:")
    error_summary = guard.get_error_summary()
    if not error_summary.empty:
        print(error_summary.to_string(index=False))
    else:
        print("   No errors found!")
    
    # Save clean and quarantine data
    print("\n" + "─"*70)
    print("💾 Saving Results")
    print("─"*70)
    
    os.makedirs('data/silver', exist_ok=True)
    os.makedirs('data/quarantine', exist_ok=True)
    
    # Drop validation helper columns before saving
    clean_df_save = clean_df.drop(columns=['upc_in_master', 'store_in_master'], errors='ignore')
    quarantine_df_save = quarantine_df.drop(columns=['upc_in_master', 'store_in_master'], errors='ignore')
    
    clean_df_save.to_csv('data/silver/sales_clean.csv', index=False)
    quarantine_df_save.to_csv('data/quarantine/sales_quarantine.csv', index=False)
    
    print(f"   ✅ Clean data saved:      data/silver/sales_clean.csv ({len(clean_df):,} rows)")
    print(f"   ⚠️  Quarantine data saved: data/quarantine/sales_quarantine.csv ({len(quarantine_df):,} rows)")
    print(f"   📊 Audit log saved:       data/audit_log.csv")
    
    # Show sample quarantine records
    if len(quarantine_df) > 0:
        print("\n" + "─"*70)
        print("🔍 Sample Quarantine Records (First 10)")
        print("─"*70)
        sample_cols = ['UPC', 'Store_ID', 'Sales_Dollars', 'Error_Reason']
        print(quarantine_df[sample_cols].head(10).to_string(index=False))
    
    # Financial impact analysis
    print("\n" + "─"*70)
    print("💰 Financial Impact Analysis")
    print("─"*70)
    
    total_sales = sales_transactions['Sales_Dollars'].sum()
    clean_sales = clean_df[clean_df['Sales_Dollars'] > 0]['Sales_Dollars'].sum()
    quarantine_sales_abs = quarantine_df['Sales_Dollars'].abs().sum()
    
    print(f"   Total Sales (All Data):         ${total_sales:,.2f}")
    print(f"   Clean Sales:                    ${clean_sales:,.2f}")
    print(f"   Revenue at Risk (Quarantine):   ${quarantine_sales_abs:,.2f}")
    print(f"   % of Total:                     {quarantine_sales_abs/abs(total_sales)*100:.2f}%")
    
    # Summary
    print("\n" + "="*70)
    print("✅ VALIDATION COMPLETE")
    print("="*70)
    print(f"\n🎯 Trust Score: {metrics['trust_score_pct']:.2f}%")
    
    if metrics['trust_score_pct'] < 95:
        print("   ⚠️  WARNING: Trust Score below 95% threshold!")
        print("   Action Required: Investigate quarantine records")
    elif metrics['trust_score_pct'] < 98:
        print("   ⚠️  CAUTION: Trust Score below 98% target")
    else:
        print("   ✅ Trust Score meets quality standards")
    
    print(f"\n📈 Next Steps:")
    print("   1. Review quarantine records: data/quarantine/sales_quarantine.csv")
    print("   2. Analyze error patterns by Error_Reason")
    print("   3. Upload to Power BI for dashboard visualization")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
