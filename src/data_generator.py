"""
Synthetic CPG/Circana POS Data Generator with Deliberate Quality Issues
This module generates realistic Point-of-Sale data mimicking Circana (IRI) data structure
with intentionally injected data quality issues for Control Tower demonstration
"""

import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import json

# Initialize Faker with seed for reproducibility
Faker.seed(42)
random.seed(42)
fake = Faker()


class CircanaDataGenerator:
    """Generate synthetic Circana-style POS data with controlled quality issues"""
    
    def __init__(self, num_products=100, num_stores=50, num_transactions=10000):
        self.num_products = num_products
        self.num_stores = num_stores
        self.num_transactions = num_transactions
        self.brands = [
            "PowerCrunch", "Nature Valley", "Clif Bar", "Kind", "Quest",
            "RxBar", "Larabar", "ThinkThin", "Gatorade", "Powerade",
            "Vitaminwater", "Smartwater", "Dasani", "Aquafina", "Poland Spring",
            "Coca-Cola", "Pepsi", "Sprite", "Fanta", "Mountain Dew",
            "Summer Seltzer", "LaCroix", "Bubly", "Perrier", "San Pellegrino"
        ]
        self.categories = ["Energy Bars", "Beverages", "Sports Drinks", "Water", "Soda"]
        self.retailers = ["Walmart", "Target", "Kroger", "Safeway", "Whole Foods", "CVS", "Walgreens"]
        self.regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
        
    def generate_product_master(self) -> pd.DataFrame:
        """
        Generate the Product Master reference data (The Golden Record)
        This represents the "Truth" against which quality will be measured
        """
        products = []
        
        for i in range(self.num_products):
            # Generate valid 12-digit UPC (actually 13 with check digit)
            upc = f"{8000000000 + i:013d}"
            brand = random.choice(self.brands)
            category = random.choice(self.categories)
            
            # Ensure some brand-category alignment for realism
            if brand in ["PowerCrunch", "Nature Valley", "Clif Bar", "Kind", "Quest"]:
                category = "Energy Bars"
            elif brand in ["Gatorade", "Powerade"]:
                category = "Sports Drinks"
            elif brand in ["Summer Seltzer", "LaCroix", "Bubly", "Perrier"]:
                category = "Beverages"
                
            product = {
                'UPC': upc,
                'Brand': brand,
                'Category': category,
                'Sub_Category': f"{category}_{random.choice(['Regular', 'Premium', 'Value'])}",
                'Product_Name': f"{brand} {fake.word().title()} {random.choice(['Original', 'Lite', 'Zero', 'Plus'])}",
                'List_Price': round(random.uniform(2.99, 15.99), 2),
                'Pack_Size': random.choice([1, 6, 12, 24]),
                'Active_Flag': 'Y',
                'Last_Updated': datetime.now().strftime('%Y-%m-%d')
            }
            products.append(product)
            
        return pd.DataFrame(products)
    
    def generate_store_master(self) -> pd.DataFrame:
        """Generate the Store Master reference data"""
        stores = []
        
        for i in range(1, self.num_stores + 1):
            region = random.choice(self.regions)
            retailer = random.choice(self.retailers)
            
            store = {
                'Store_ID': f"ST{i:05d}",
                'Retailer_Name': retailer,
                'Region': region,
                'Market': f"{region}_{random.randint(1, 5)}",
                'City': fake.city(),
                'State': fake.state_abbr(),
                'Store_Type': random.choice(['Supermarket', 'Convenience', 'Drug', 'Mass Merchandiser']),
                'Active_Flag': 'Y'
            }
            stores.append(store)
            
        return pd.DataFrame(stores)
    
    def generate_sales_transactions(self, product_master: pd.DataFrame, 
                                    store_master: pd.DataFrame,
                                    inject_errors: bool = True) -> pd.DataFrame:
        """
        Generate sales transactions with deliberate quality issues
        
        Entropy Injections:
        1. Orphan UPCs (5%): UPCs not in Product Master
        2. Missing Stores (2%): Store IDs not in Store Master  
        3. Negative Sales (1%): Simulating returns processing errors
        4. Extreme Prices (0.5%): "Fat finger" decimal errors
        5. Null Values (3%): Missing critical data
        6. New Product Launch Block: Consistent unknown UPC for pattern detection
        """
        transactions = []
        valid_upcs = product_master['UPC'].tolist()
        valid_stores = store_master['Store_ID'].tolist()
        
        # Generate base date range (last 4 weeks)
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=4)
        
        for i in range(self.num_transactions):
            # Base transaction
            transaction = {
                'Transaction_ID': f"TXN{i:010d}",
                'Week_End': fake.date_between(start_date=start_date, end_date=end_date),
                'Store_ID': random.choice(valid_stores),
                'UPC': random.choice(valid_upcs),
                'Units_Sold': random.randint(1, 50),
                'Sales_Dollars': 0.0,  # Will calculate
                'Batch_ID': f"BATCH_{end_date.strftime('%Y%m%d')}_001"
            }
            
            # Calculate sales based on list price
            try:
                list_price = product_master[product_master['UPC'] == transaction['UPC']]['List_Price'].values[0]
                transaction['Sales_Dollars'] = round(transaction['Units_Sold'] * list_price * random.uniform(0.9, 1.1), 2)
            except:
                transaction['Sales_Dollars'] = round(transaction['Units_Sold'] * 5.99, 2)
            
            if inject_errors:
                # ENTROPY INJECTION 1: Orphan UPCs (5%)
                if random.random() < 0.05:
                    transaction['UPC'] = f"{9990000000 + random.randint(0, 999):013d}"
                    
                # ENTROPY INJECTION 2: Missing Store (2%)
                if random.random() < 0.02:
                    transaction['Store_ID'] = "ST99999"  # Non-existent store
                    
                # ENTROPY INJECTION 3: Negative Sales (1%) - Returns processing error
                if random.random() < 0.01:
                    transaction['Sales_Dollars'] *= -1
                    transaction['Units_Sold'] *= -1
                    
                # ENTROPY INJECTION 4: Extreme Price (0.5%) - Fat finger error
                if random.random() < 0.005:
                    transaction['Sales_Dollars'] *= 100  # $5.99 becomes $599.00
                    
                # ENTROPY INJECTION 5: Null Values (3%)
                if random.random() < 0.03:
                    null_field = random.choice(['UPC', 'Sales_Dollars', 'Units_Sold'])
                    transaction[null_field] = None
                    
            transactions.append(transaction)
        
        # ENTROPY INJECTION 6: New Product Launch Block (Consistent Unknown UPC)
        # This creates a pattern that can be detected by Decomposition Tree
        if inject_errors:
            new_product_upc = "9999990000001"  # Consistent unknown UPC
            new_product_store = random.choice(valid_stores[:10])  # Concentrate in few stores
            
            for i in range(500):  # 500 transactions for new product
                transaction = {
                    'Transaction_ID': f"TXN_NEW{i:06d}",
                    'Week_End': end_date - timedelta(days=random.randint(0, 7)),
                    'Store_ID': new_product_store if random.random() < 0.8 else random.choice(valid_stores),
                    'UPC': new_product_upc,
                    'Units_Sold': random.randint(5, 20),
                    'Sales_Dollars': round(random.randint(5, 20) * 12.99, 2),  # Premium priced new item
                    'Batch_ID': f"BATCH_{end_date.strftime('%Y%m%d')}_001"
                }
                transactions.append(transaction)
        
        df = pd.DataFrame(transactions)
        
        # Add metadata columns
        df['Ingestion_Timestamp'] = datetime.now()
        df['Source_System'] = 'Circana_Unify'
        
        return df
    
    def generate_complete_dataset(self, output_path: str = None) -> dict:
        """Generate complete dataset with all reference and transaction data"""
        print("Generating Product Master...")
        product_master = self.generate_product_master()
        
        print("Generating Store Master...")
        store_master = self.generate_store_master()
        
        print("Generating Sales Transactions with quality issues...")
        sales_transactions = self.generate_sales_transactions(
            product_master, 
            store_master, 
            inject_errors=True
        )
        
        datasets = {
            'product_master': product_master,
            'store_master': store_master,
            'sales_transactions': sales_transactions
        }
        
        # Calculate and display statistics
        total_txns = len(sales_transactions)
        orphan_upcs = sales_transactions[~sales_transactions['UPC'].isin(product_master['UPC'])].shape[0]
        missing_stores = sales_transactions[~sales_transactions['Store_ID'].isin(store_master['Store_ID'])].shape[0]
        negative_sales = sales_transactions[sales_transactions['Sales_Dollars'] < 0].shape[0] if 'Sales_Dollars' in sales_transactions.columns else 0
        null_values = sales_transactions.isnull().sum().sum()
        
        print(f"\n{'='*60}")
        print("DATA GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"Product Master Records: {len(product_master):,}")
        print(f"Store Master Records: {len(store_master):,}")
        print(f"Total Transactions: {total_txns:,}")
        print(f"\nQUALITY ISSUES INJECTED:")
        print(f"  - Orphan UPCs: {orphan_upcs:,} ({orphan_upcs/total_txns*100:.2f}%)")
        print(f"  - Missing Stores: {missing_stores:,} ({missing_stores/total_txns*100:.2f}%)")
        print(f"  - Negative Sales: {negative_sales:,} ({negative_sales/total_txns*100:.2f}%)")
        print(f"  - Null Values: {null_values:,}")
        print(f"{'='*60}\n")
        
        # Save to files if path provided
        if output_path:
            product_master.to_csv(f"{output_path}/product_master.csv", index=False)
            store_master.to_csv(f"{output_path}/store_master.csv", index=False)
            sales_transactions.to_csv(f"{output_path}/sales_transactions.csv", index=False)
            print(f"Data saved to {output_path}/")
        
        return datasets


def main():
    """Main execution for standalone testing"""
    generator = CircanaDataGenerator(
        num_products=100,
        num_stores=50,
        num_transactions=10000
    )
    
    datasets = generator.generate_complete_dataset(output_path="./data")
    
    print("Sample Product Master:")
    print(datasets['product_master'].head())
    print("\nSample Store Master:")
    print(datasets['store_master'].head())
    print("\nSample Transactions:")
    print(datasets['sales_transactions'].head(10))


if __name__ == "__main__":
    main()
