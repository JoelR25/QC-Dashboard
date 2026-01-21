"""
CPG Data Generator for Circana POS Simulation

This module generates synthetic Consumer Packaged Goods (CPG) Point-of-Sale data
that mimics real-world Circana (formerly IRI) data feeds with deliberate quality issues.

Author: Data Quality Control Tower Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random


class CPGDataGenerator:
    """
    Generates synthetic CPG Point-of-Sale data with controlled entropy injections.
    
    This class creates realistic Product Master, Store Master, and Sales Transaction
    data with deliberate quality issues to demonstrate the Data Quality Control Tower.
    
    Attributes:
        seed (int): Random seed for reproducibility
        fake (Faker): Faker instance for generating realistic names
    """
    
    def __init__(self, seed=42):
        """
        Initialize the CPG Data Generator.
        
        Args:
            seed (int): Random seed for deterministic data generation
        """
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        # CPG-specific reference data
        self.brands = [
            "PowerCrunch", "Nature Valley", "KIND", "CLIF", "Quest",
            "RX Bar", "LÄRABAR", "NutriGrain", "Special K", "Fiber One",
            "Quaker", "General Mills", "Kellogg's", "Post", "Nature's Path",
            "Back to Nature", "Annie's", "Cascadian Farm", "Kashi", "Bear Naked"
        ]
        
        self.categories = [
            "Protein Bars", "Granola Bars", "Breakfast Bars", "Energy Bars",
            "Snack Bars", "Meal Replacement", "Nutritional Supplements"
        ]
        
        self.retailers = [
            "Walmart", "Target", "Kroger", "Albertsons", "Publix",
            "Whole Foods", "Trader Joe's", "Costco", "Sam's Club", "CVS"
        ]
        
        self.regions = [
            "Northeast", "Southeast", "Midwest", "Southwest", 
            "West", "Pacific Northwest", "Mountain", "South Central"
        ]
        
        self.states = {
            "Northeast": ["NY", "MA", "PA", "NJ", "CT", "RI", "VT", "NH", "ME"],
            "Southeast": ["FL", "GA", "NC", "SC", "VA", "AL", "TN", "KY"],
            "Midwest": ["IL", "OH", "MI", "IN", "WI", "MN", "IA", "MO"],
            "Southwest": ["TX", "AZ", "NM", "OK"],
            "West": ["CA", "NV", "UT", "CO"],
            "Pacific Northwest": ["WA", "OR", "ID"],
            "Mountain": ["MT", "WY", "ND", "SD"],
            "South Central": ["LA", "AR", "MS"]
        }
    
    def generate_product_master(self, num_products=100):
        """
        Generate the Product Master reference data (the "Golden Record").
        
        Args:
            num_products (int): Number of products to generate
            
        Returns:
            pd.DataFrame: Product Master with columns [UPC, Brand, Category, Sub_Category, List_Price]
        """
        products = []
        
        for i in range(num_products):
            # Generate a realistic 13-digit UPC (EAN-13 format)
            upc = f"{random.randint(100000000000, 999999999999)}"
            brand = np.random.choice(self.brands)
            category = np.random.choice(self.categories)
            
            # Sub-categories based on category
            if "Protein" in category:
                sub_category = np.random.choice(["Whey", "Plant-Based", "Collagen", "Casein"])
            elif "Granola" in category or "Snack" in category:
                sub_category = np.random.choice(["Chewy", "Crunchy", "Soft-Baked", "Organic"])
            else:
                sub_category = np.random.choice(["Standard", "Premium", "Value"])
            
            # Price distribution with some high-end products
            if np.random.random() < 0.8:
                list_price = round(np.random.uniform(1.99, 6.99), 2)
            else:
                list_price = round(np.random.uniform(7.00, 15.99), 2)
            
            products.append({
                "UPC": upc,
                "Brand": brand,
                "Category": category,
                "Sub_Category": sub_category,
                "List_Price": list_price
            })
        
        df = pd.DataFrame(products)
        print(f"✅ Generated Product Master: {len(df)} products")
        return df
    
    def generate_store_master(self, num_stores=50):
        """
        Generate the Store Master reference data.
        
        Args:
            num_stores (int): Number of stores to generate
            
        Returns:
            pd.DataFrame: Store Master with columns [Store_ID, Retailer_Name, Region, City, State]
        """
        stores = []
        
        for i in range(num_stores):
            store_id = f"STORE_{str(i+1).zfill(4)}"
            retailer = np.random.choice(self.retailers)
            region = np.random.choice(self.regions)
            state = np.random.choice(self.states[region])
            city = self.fake.city()
            
            stores.append({
                "Store_ID": store_id,
                "Retailer_Name": retailer,
                "Region": region,
                "City": city,
                "State": state
            })
        
        df = pd.DataFrame(stores)
        print(f"✅ Generated Store Master: {len(df)} stores across {df['Region'].nunique()} regions")
        return df
    
    def generate_sales_transactions(
        self,
        product_master,
        store_master,
        num_transactions=10000,
        num_weeks=12,
        error_rate_orphan_upc=0.05,
        error_rate_negative_sales=0.01,
        error_rate_missing_store=0.02,
        error_rate_price_spike=0.005
    ):
        """
        Generate Sales Transaction data with deliberate quality issues (Entropy Injections).
        
        This is the core of the simulation - we intentionally introduce data quality
        issues that the Control Tower will detect and quarantine.
        
        Args:
            product_master (pd.DataFrame): Reference product data
            store_master (pd.DataFrame): Reference store data
            num_transactions (int): Number of transaction records to generate
            num_weeks (int): Number of weeks to simulate
            error_rate_orphan_upc (float): % of transactions with unknown UPCs
            error_rate_negative_sales (float): % of transactions with negative sales
            error_rate_missing_store (float): % of transactions with unknown stores
            error_rate_price_spike (float): % of transactions with price anomalies
            
        Returns:
            pd.DataFrame: Sales transactions with columns [Transaction_ID, UPC, Store_ID, 
                          Week_End, Units_Sold, Sales_Dollars, List_Price]
        """
        transactions = []
        
        # Create a date range for the simulation
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=num_weeks)
        weeks = pd.date_range(start=start_date, end=end_date, freq='W-SAT')
        
        # Get valid UPCs and Store IDs
        valid_upcs = product_master['UPC'].tolist()
        valid_stores = store_master['Store_ID'].tolist()
        
        # Pre-generate error indices for consistent patterns
        error_indices_orphan_upc = set(random.sample(range(num_transactions), int(num_transactions * error_rate_orphan_upc)))
        error_indices_negative = set(random.sample(range(num_transactions), int(num_transactions * error_rate_negative_sales)))
        error_indices_missing_store = set(random.sample(range(num_transactions), int(num_transactions * error_rate_missing_store)))
        error_indices_price_spike = set(random.sample(range(num_transactions), int(num_transactions * error_rate_price_spike)))
        
        # CRITICAL: Create a "pattern error" - 500 transactions for a specific unknown UPC
        # This allows the Decomposition Tree in Power BI to identify a cluster
        pattern_error_upc = "999999001"
        pattern_error_count = 500
        
        for i in range(num_transactions):
            transaction_id = f"TXN_{str(i+1).zfill(8)}"
            
            # ENTROPY INJECTION 1: Orphan UPC (including pattern error)
            if i < pattern_error_count:
                # First 500 transactions use the consistent pattern UPC
                upc = pattern_error_upc
            elif i in error_indices_orphan_upc:
                # Random orphan UPCs
                upc = f"{random.randint(100000000000, 999999999999)}"
            else:
                # Valid UPC from master
                upc = np.random.choice(valid_upcs)
            
            # ENTROPY INJECTION 2: Missing Store
            if i in error_indices_missing_store:
                store_id = "STORE_999"  # Consistent unknown store for pattern detection
            else:
                store_id = np.random.choice(valid_stores)
            
            # Select a week
            week_end = np.random.choice(weeks).date()
            
            # Generate units sold (Poisson distribution for realism)
            units_sold = max(1, int(np.random.poisson(lam=5)))
            
            # Get list price (or estimate if orphan UPC)
            if upc in valid_upcs:
                list_price = product_master[product_master['UPC'] == upc]['List_Price'].values[0]
            else:
                list_price = round(np.random.uniform(2.0, 8.0), 2)
            
            # ENTROPY INJECTION 3: Price Spike (Fat Finger Error)
            if i in error_indices_price_spike:
                # Simulate decimal place error: $5.00 becomes $500.00
                actual_price = list_price * 100
            else:
                # Normal price with small variance (promotions/discounts)
                actual_price = list_price * np.random.uniform(0.85, 1.05)
            
            sales_dollars = round(units_sold * actual_price, 2)
            
            # ENTROPY INJECTION 4: Negative Sales (Returns or Data Error)
            if i in error_indices_negative:
                sales_dollars = -abs(sales_dollars)
            
            transactions.append({
                "Transaction_ID": transaction_id,
                "UPC": upc,
                "Store_ID": store_id,
                "Week_End": week_end,
                "Units_Sold": units_sold,
                "Sales_Dollars": sales_dollars,
                "List_Price": list_price
            })
        
        df = pd.DataFrame(transactions)
        
        # Summary of injected errors
        orphan_count = len([t for t in transactions if t['UPC'] not in valid_upcs])
        negative_count = len([t for t in transactions if t['Sales_Dollars'] < 0])
        missing_store_count = len([t for t in transactions if t['Store_ID'] not in valid_stores])
        
        print(f"\n✅ Generated Sales Transactions: {len(df)} records")
        print(f"   📊 Error Injections:")
        print(f"      🔴 Orphan UPCs: {orphan_count} ({orphan_count/len(df)*100:.1f}%)")
        print(f"         - Pattern UPC ({pattern_error_upc}): {pattern_error_count} transactions")
        print(f"      🔴 Negative Sales: {negative_count} ({negative_count/len(df)*100:.1f}%)")
        print(f"      🔴 Missing Stores: {missing_store_count} ({missing_store_count/len(df)*100:.1f}%)")
        print(f"      🔴 Price Spikes: {len(error_indices_price_spike)} ({len(error_indices_price_spike)/len(df)*100:.1f}%)")
        print(f"\n   ⚠️  Expected Trust Score: ~{100 - (orphan_count + negative_count + missing_store_count)/len(df)*100:.1f}%")
        
        return df
    
    def save_datasets(self, product_master, store_master, sales_transactions, output_dir='data'):
        """
        Save all generated datasets to CSV files.
        
        Args:
            product_master (pd.DataFrame): Product master data
            store_master (pd.DataFrame): Store master data
            sales_transactions (pd.DataFrame): Sales transaction data
            output_dir (str): Directory to save files
        """
        import os
        
        # Create directories
        os.makedirs(f"{output_dir}/master", exist_ok=True)
        os.makedirs(f"{output_dir}/bronze", exist_ok=True)
        
        # Save master data
        product_master.to_csv(f"{output_dir}/master/product_master.csv", index=False)
        store_master.to_csv(f"{output_dir}/master/store_master.csv", index=False)
        
        # Save transaction data
        sales_transactions.to_csv(f"{output_dir}/bronze/sales_transactions.csv", index=False)
        
        print(f"\n✅ Datasets saved to {output_dir}/")
        print(f"   📁 {output_dir}/master/product_master.csv")
        print(f"   📁 {output_dir}/master/store_master.csv")
        print(f"   📁 {output_dir}/bronze/sales_transactions.csv")


if __name__ == "__main__":
    # Example usage
    generator = CPGDataGenerator(seed=42)
    
    product_master = generator.generate_product_master(num_products=100)
    store_master = generator.generate_store_master(num_stores=50)
    sales_transactions = generator.generate_sales_transactions(
        product_master=product_master,
        store_master=store_master,
        num_transactions=10000
    )
    
    generator.save_datasets(product_master, store_master, sales_transactions)
