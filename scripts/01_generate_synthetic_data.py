"""
Generate Synthetic CPG Data for the Control Tower Simulation

This script generates realistic Consumer Packaged Goods (CPG) Point-of-Sale data
with deliberate quality issues to demonstrate the Data Quality Control Tower.

Usage:
    python scripts/01_generate_synthetic_data.py

Output:
    - data/master/product_master.csv
    - data/master/store_master.csv
    - data/bronze/sales_transactions.csv

Author: Data Quality Control Tower Team
Date: January 2026
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cpg_data_generator import CPGDataGenerator


def main():
    """Generate all synthetic datasets for the simulation."""
    
    print("="*70)
    print("  DATA QUALITY CONTROL TOWER - Synthetic Data Generation")
    print("="*70)
    print("\n🎯 Objective: Generate CPG POS data with controlled quality issues")
    print("   to demonstrate the Data Observability Control Tower\n")
    
    # Initialize generator with fixed seed for reproducibility
    print("📌 Initializing CPG Data Generator (seed=42 for reproducibility)...")
    generator = CPGDataGenerator(seed=42)
    
    # Generate Product Master (The "Golden Record")
    print("\n" + "─"*70)
    print("1️⃣  Generating Product Master (Reference Data)")
    print("─"*70)
    product_master = generator.generate_product_master(num_products=100)
    print(f"   Brands: {product_master['Brand'].nunique()}")
    print(f"   Categories: {product_master['Category'].nunique()}")
    print(f"   Price range: ${product_master['List_Price'].min():.2f} - ${product_master['List_Price'].max():.2f}")
    
    # Generate Store Master
    print("\n" + "─"*70)
    print("2️⃣  Generating Store Master (Reference Data)")
    print("─"*70)
    store_master = generator.generate_store_master(num_stores=50)
    print(f"   Retailers: {store_master['Retailer_Name'].nunique()}")
    print(f"   Regions: {', '.join(store_master['Region'].unique())}")
    
    # Generate Sales Transactions with Entropy Injections
    print("\n" + "─"*70)
    print("3️⃣  Generating Sales Transactions with Entropy Injections")
    print("─"*70)
    print("   ⚠️  Deliberately injecting data quality issues:")
    print("      • Orphan UPCs (not in Product Master)")
    print("      • Negative Sales values")
    print("      • Missing Store IDs")
    print("      • Price spikes (decimal place errors)")
    
    sales_transactions = generator.generate_sales_transactions(
        product_master=product_master,
        store_master=store_master,
        num_transactions=10000,
        num_weeks=12,
        error_rate_orphan_upc=0.05,      # 5% orphan UPCs
        error_rate_negative_sales=0.01,   # 1% negative sales
        error_rate_missing_store=0.02,    # 2% unknown stores
        error_rate_price_spike=0.005      # 0.5% price spikes
    )
    
    # Save all datasets
    print("\n" + "─"*70)
    print("4️⃣  Saving Datasets to CSV")
    print("─"*70)
    generator.save_datasets(
        product_master=product_master,
        store_master=store_master,
        sales_transactions=sales_transactions,
        output_dir='data'
    )
    
    # Summary
    print("\n" + "="*70)
    print("✅ DATA GENERATION COMPLETE")
    print("="*70)
    print("\n📊 Summary:")
    print(f"   • Products:     {len(product_master):,}")
    print(f"   • Stores:       {len(store_master):,}")
    print(f"   • Transactions: {len(sales_transactions):,}")
    print(f"\n🎯 Next Steps:")
    print("   1. Review the generated data in the data/ directory")
    print("   2. Run the validation script: python scripts/02_validate_data_quality.py")
    print("   3. Upload to Databricks: notebooks/02_control_tower_pipeline.py")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
