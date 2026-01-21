"""
Create Gold Layer - Aggregated Analytics

This script creates the Gold layer by aggregating validated Silver data
into business-ready analytics tables.

Usage:
    python scripts/03_create_gold_layer.py

Prerequisites:
    - Run 02_validate_data_quality.py first

Author: Data Quality Control Tower Team
Date: January 2026
"""

import pandas as pd
import os


def main():
    """Create Gold layer aggregations from Silver clean data."""
    
    print("="*70)
    print("  DATA QUALITY CONTROL TOWER - Gold Layer Creation")
    print("="*70)
    print("\n🎯 Objective: Aggregate validated data for analytics\n")
    
    # Load data
    print("📂 Loading data...")
    try:
        silver_clean = pd.read_csv('data/silver/sales_clean.csv')
        product_master = pd.read_csv('data/master/product_master.csv')
        store_master = pd.read_csv('data/master/store_master.csv')
        print(f"   ✅ Loaded {len(silver_clean):,} clean transactions\n")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Please run: python scripts/02_validate_data_quality.py")
        return
    
    # Merge with master data to enrich
    print("🔗 Enriching data with master tables...")
    sales_enriched = silver_clean.merge(
        product_master[['UPC', 'Brand', 'Category', 'Sub_Category']], 
        on='UPC', 
        how='left'
    ).merge(
        store_master[['Store_ID', 'Retailer_Name', 'Region', 'State']], 
        on='Store_ID', 
        how='left'
    )
    
    # Check for any rows that couldn't be enriched (shouldn't happen if validation worked)
    missing_brand = sales_enriched['Brand'].isna().sum()
    missing_region = sales_enriched['Region'].isna().sum()
    
    if missing_brand > 0 or missing_region > 0:
        print(f"   ⚠️ Warning: {missing_brand} rows missing Brand, {missing_region} missing Region")
    else:
        print(f"   ✅ All rows successfully enriched")
    
    # Create Gold Layer: Brand x Region Analytics
    print("\n" + "─"*70)
    print("📊 Creating Gold Layer: Brand x Region Analytics")
    print("─"*70)
    
    gold_brand_analytics = sales_enriched.groupby(['Brand', 'Region']).agg({
        'Sales_Dollars': ['sum', 'mean'],
        'Units_Sold': ['sum', 'mean'],
        'Transaction_ID': 'count',
        'List_Price': 'mean'
    }).reset_index()
    
    # Flatten column names
    gold_brand_analytics.columns = [
        'Brand', 'Region', 
        'Total_Revenue', 'Avg_Revenue_Per_Transaction',
        'Total_Units', 'Avg_Units_Per_Transaction',
        'Transaction_Count',
        'Avg_List_Price'
    ]
    
    # Round decimals
    gold_brand_analytics['Total_Revenue'] = gold_brand_analytics['Total_Revenue'].round(2)
    gold_brand_analytics['Avg_Revenue_Per_Transaction'] = gold_brand_analytics['Avg_Revenue_Per_Transaction'].round(2)
    gold_brand_analytics['Avg_Units_Per_Transaction'] = gold_brand_analytics['Avg_Units_Per_Transaction'].round(1)
    gold_brand_analytics['Avg_List_Price'] = gold_brand_analytics['Avg_List_Price'].round(2)
    
    print(f"   ✅ Aggregated to {len(gold_brand_analytics)} Brand x Region combinations")
    
    # Show top performers
    print("\n📈 Top 5 Brand x Region by Revenue:")
    top_5 = gold_brand_analytics.nlargest(5, 'Total_Revenue')[
        ['Brand', 'Region', 'Total_Revenue', 'Total_Units']
    ]
    print(top_5.to_string(index=False))
    
    # Save Gold layer
    print("\n" + "─"*70)
    print("💾 Saving Gold Layer")
    print("─"*70)
    
    os.makedirs('data/gold', exist_ok=True)
    gold_brand_analytics.to_csv('data/gold/brand_analytics.csv', index=False)
    
    print(f"   ✅ Gold layer saved: data/gold/brand_analytics.csv ({len(gold_brand_analytics)} rows)")
    
    # Reconciliation check
    print("\n" + "─"*70)
    print("🔍 Reconciliation Check")
    print("─"*70)
    
    silver_revenue = silver_clean['Sales_Dollars'].sum()
    gold_revenue = gold_brand_analytics['Total_Revenue'].sum()
    variance = ((gold_revenue - silver_revenue) / silver_revenue * 100) if silver_revenue > 0 else 0
    
    print(f"   Silver Total Revenue:  ${silver_revenue:,.2f}")
    print(f"   Gold Total Revenue:    ${gold_revenue:,.2f}")
    print(f"   Variance:              {variance:+.4f}%")
    
    if abs(variance) < 0.01:
        print(f"   ✅ Reconciliation PASSED (variance within tolerance)")
    else:
        print(f"   ⚠️ WARNING: Reconciliation variance detected")
    
    # Summary
    print("\n" + "="*70)
    print("✅ GOLD LAYER CREATION COMPLETE")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • Input (Silver Clean):  {len(silver_clean):,} transactions")
    print(f"   • Output (Gold):         {len(gold_brand_analytics)} aggregated rows")
    print(f"   • Dimensions:            Brand x Region")
    print(f"   • Total Revenue:         ${gold_revenue:,.2f}")
    
    print(f"\n🎯 Next Steps:")
    print("   1. Review the gold layer: data/gold/brand_analytics.csv")
    print("   2. Import into Power BI for dashboard creation")
    print("   3. Build visualizations using DAX measures from powerbi/DAX_Measures.txt")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
