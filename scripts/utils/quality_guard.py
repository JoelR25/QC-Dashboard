"""
Data Quality Guard - Shadow DLT Implementation

This module implements a "Shadow Delta Live Tables" pattern for data quality
enforcement in environments without native DLT support (like Databricks Community Edition).

It mimics the DLT Expectations pattern with validate(), split(), and log() operations.

Author: Data Quality Control Tower Team
Date: January 2026
"""

from datetime import datetime
from typing import Dict, Tuple, Optional
import pandas as pd


class DataQualityGuard:
    """
    Simulates Delta Live Tables (DLT) Expectations for data quality enforcement.
    Implements the Quarantine Pattern to route invalid data for analysis.
    
    This class is designed to work with both Pandas DataFrames (local) and
    PySpark DataFrames (Databricks) through duck typing.
    
    Attributes:
        df: Input DataFrame (Pandas or PySpark)
        expectations (dict): Rule name -> validation condition mapping
        batch_id (int): Unique identifier for this data batch
        engine (str): 'pandas' or 'pyspark'
    """
    
    def __init__(self, df, expectations: Dict[str, str], batch_id: int = 1, engine='pandas'):
        """
        Initialize the Data Quality Guard.
        
        Args:
            df: Input DataFrame to validate
            expectations (dict): Dictionary of {rule_name: validation_expression}
                Example: {"upc_not_null": "UPC.notna()", "sales_positive": "Sales_Dollars >= 0"}
            batch_id (int): Batch identifier for audit logging
            engine (str): Either 'pandas' or 'pyspark'
        """
        self.df = df
        self.expectations = expectations
        self.batch_id = batch_id
        self.engine = engine
        self._validated = False
        self._split_done = False
        self.clean_df = None
        self.quarantine_df = None
        self.validation_results = {}
    
    def validate(self):
        """
        Apply all expectations and tag each row as valid or invalid.
        
        Returns:
            self: For method chaining
        """
        df = self.df.copy() if self.engine == 'pandas' else self.df
        
        # Apply each validation rule
        for rule_name, condition in self.expectations.items():
            if self.engine == 'pandas':
                # Evaluate pandas expression
                df[f'valid_{rule_name}'] = df.eval(condition)
            else:
                # For PySpark (Databricks), use SQL expressions
                from pyspark.sql.functions import expr
                df = df.withColumn(f'valid_{rule_name}', expr(condition))
        
        # Combine all validation flags into a single 'is_valid' column
        valid_cols = [f'valid_{rule}' for rule in self.expectations.keys()]
        
        if self.engine == 'pandas':
            df['is_valid'] = df[valid_cols].all(axis=1)
        else:
            # PySpark: AND all validation columns
            from pyspark.sql.functions import col
            from functools import reduce
            df = df.withColumn(
                'is_valid',
                reduce(lambda a, b: a & b, [col(c) for c in valid_cols])
            )
        
        self.df = df
        self._validated = True
        return self
    
    def split(self) -> Tuple:
        """
        Route data to Clean or Quarantine based on validation results.
        
        Returns:
            tuple: (clean_df, quarantine_df)
        """
        if not self._validated:
            raise RuntimeError("Must call validate() before split()")
        
        if self.engine == 'pandas':
            self.clean_df = self.df[self.df['is_valid'] == True].copy()
            self.quarantine_df = self.df[self.df['is_valid'] == False].copy()
        else:
            # PySpark
            from pyspark.sql.functions import col
            self.clean_df = self.df.filter(col('is_valid') == True)
            self.quarantine_df = self.df.filter(col('is_valid') == False)
        
        # Add error metadata to quarantine records
        if self.engine == 'pandas' and len(self.quarantine_df) > 0:
            # Identify which rules failed for each row
            error_reasons = []
            for idx, row in self.quarantine_df.iterrows():
                failed_rules = [
                    rule for rule in self.expectations.keys() 
                    if not row[f'valid_{rule}']
                ]
                error_reasons.append(', '.join(failed_rules))
            
            self.quarantine_df['Error_Reason'] = error_reasons
            self.quarantine_df['Batch_ID'] = self.batch_id
            self.quarantine_df['Quarantine_Timestamp'] = datetime.now()
        
        self._split_done = True
        return self.clean_df, self.quarantine_df
    
    def get_metrics(self) -> Dict:
        """
        Calculate data quality metrics.
        
        Returns:
            dict: Metrics including counts and trust score
        """
        if not self._split_done:
            self.split()
        
        if self.engine == 'pandas':
            input_rows = len(self.df)
            valid_rows = len(self.clean_df)
            quarantine_rows = len(self.quarantine_df)
        else:
            # PySpark
            input_rows = self.df.count()
            valid_rows = self.clean_df.count()
            quarantine_rows = self.quarantine_df.count()
        
        trust_score = (valid_rows / input_rows * 100) if input_rows > 0 else 0
        
        metrics = {
            'batch_id': self.batch_id,
            'input_rows': input_rows,
            'valid_rows': valid_rows,
            'quarantine_rows': quarantine_rows,
            'trust_score_pct': round(trust_score, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        return metrics
    
    def log_metrics(self, output_file: Optional[str] = None) -> Dict:
        """
        Log metrics to console and optionally to a file.
        
        Args:
            output_file (str): Optional path to append metrics (CSV format)
            
        Returns:
            dict: The metrics that were logged
        """
        metrics = self.get_metrics()
        
        # Console output
        print(f"\n{'='*60}")
        print(f"📊 Data Quality Metrics - Batch {metrics['batch_id']}")
        print(f"{'='*60}")
        print(f"   Input Rows:       {metrics['input_rows']:,}")
        print(f"   ✅ Valid Rows:     {metrics['valid_rows']:,} ({metrics['valid_rows']/metrics['input_rows']*100:.1f}%)")
        print(f"   ⚠️  Quarantine:     {metrics['quarantine_rows']:,} ({metrics['quarantine_rows']/metrics['input_rows']*100:.1f}%)")
        print(f"   🎯 Trust Score:    {metrics['trust_score_pct']:.2f}%")
        print(f"{'='*60}\n")
        
        # File output
        if output_file:
            import os
            metrics_df = pd.DataFrame([metrics])
            
            # Append to existing file or create new
            if os.path.exists(output_file):
                metrics_df.to_csv(output_file, mode='a', header=False, index=False)
            else:
                metrics_df.to_csv(output_file, index=False)
            
            print(f"📝 Metrics logged to: {output_file}")
        
        return metrics
    
    def get_error_summary(self) -> pd.DataFrame:
        """
        Get a summary of errors by type.
        
        Returns:
            pd.DataFrame: Error counts by rule
        """
        if not self._split_done:
            self.split()
        
        if self.engine == 'pandas' and len(self.quarantine_df) > 0:
            error_summary = []
            for rule_name in self.expectations.keys():
                failed_count = (~self.quarantine_df[f'valid_{rule_name}']).sum()
                if failed_count > 0:
                    error_summary.append({
                        'Rule': rule_name,
                        'Failed_Count': failed_count,
                        'Percentage': round(failed_count / len(self.df) * 100, 2)
                    })
            
            return pd.DataFrame(error_summary).sort_values('Failed_Count', ascending=False)
        
        return pd.DataFrame()


# PySpark-specific implementation (for Databricks notebooks)
class DataQualityGuardSpark:
    """
    PySpark-optimized version of DataQualityGuard for Databricks environments.
    
    This version uses native PySpark operations for better performance on large datasets.
    """
    
    def __init__(self, spark_df, expectations: Dict[str, str], batch_id: int = 1):
        """
        Initialize the PySpark Data Quality Guard.
        
        Args:
            spark_df: PySpark DataFrame
            expectations (dict): Dictionary of {rule_name: SQL_expression}
            batch_id (int): Batch identifier
        """
        from pyspark.sql import DataFrame
        
        if not isinstance(spark_df, DataFrame):
            raise TypeError("spark_df must be a PySpark DataFrame")
        
        self.df = spark_df
        self.expectations = expectations
        self.batch_id = batch_id
        self._validated = False
        self._split_done = False
        self.clean_df = None
        self.quarantine_df = None
    
    def validate(self):
        """Apply all expectations using PySpark SQL expressions."""
        from pyspark.sql.functions import expr, col
        from functools import reduce
        
        df = self.df
        
        # Apply each validation rule
        for rule_name, sql_condition in self.expectations.items():
            df = df.withColumn(f'valid_{rule_name}', expr(sql_condition))
        
        # Combine all validation flags
        valid_cols = [col(f'valid_{rule}') for rule in self.expectations.keys()]
        df = df.withColumn('is_valid', reduce(lambda a, b: a & b, valid_cols))
        
        self.df = df
        self._validated = True
        return self
    
    def split(self) -> Tuple:
        """Route to Clean or Quarantine."""
        from pyspark.sql.functions import col, lit, current_timestamp, concat_ws, array, when
        
        if not self._validated:
            raise RuntimeError("Must call validate() before split()")
        
        self.clean_df = self.df.filter(col('is_valid') == True)
        self.quarantine_df = self.df.filter(col('is_valid') == False)
        
        # Add error metadata to quarantine
        if self.quarantine_df.count() > 0:
            # Build error reason string dynamically
            error_conditions = [
                when(~col(f'valid_{rule}'), lit(rule))
                for rule in self.expectations.keys()
            ]
            
            self.quarantine_df = self.quarantine_df.withColumn(
                'Error_Reason',
                concat_ws(', ', array(*error_conditions))
            ).withColumn(
                'Batch_ID', lit(self.batch_id)
            ).withColumn(
                'Quarantine_Timestamp', current_timestamp()
            )
        
        self._split_done = True
        return self.clean_df, self.quarantine_df
    
    def log_metrics(self, audit_table_name: str = "audit_log"):
        """
        Log metrics to a Delta table.
        
        Args:
            audit_table_name (str): Name of the audit table
        """
        if not self._split_done:
            self.split()
        
        from pyspark.sql import Row
        from pyspark.sql.functions import current_timestamp
        
        input_rows = self.df.count()
        valid_rows = self.clean_df.count()
        quarantine_rows = self.quarantine_df.count()
        trust_score = (valid_rows / input_rows * 100) if input_rows > 0 else 0
        
        # Create audit log entry
        audit_entry = Row(
            batch_id=self.batch_id,
            input_rows=input_rows,
            valid_rows=valid_rows,
            quarantine_rows=quarantine_rows,
            trust_score_pct=round(trust_score, 2),
            timestamp=datetime.now()
        )
        
        spark = self.df.sparkSession
        audit_df = spark.createDataFrame([audit_entry])
        
        # Append to audit table (Delta)
        audit_df.write.format("delta").mode("append").saveAsTable(audit_table_name)
        
        print(f"✅ Metrics logged to {audit_table_name}")
        print(f"   Trust Score: {trust_score:.2f}% ({valid_rows:,}/{input_rows:,} valid)")


if __name__ == "__main__":
    # Example usage with Pandas
    print("Testing DataQualityGuard with sample data...\n")
    
    # Create sample data with intentional issues
    sample_data = pd.DataFrame({
        'UPC': ['123456789012', '987654321098', None, '111111111111', '222222222222'],
        'Store_ID': ['STORE_0001', 'STORE_0002', 'STORE_0003', 'STORE_999', 'STORE_0004'],
        'Sales_Dollars': [50.00, -10.00, 75.00, 100.00, 200.00],
        'Units_Sold': [10, 2, 15, 20, 40]
    })
    
    # Define expectations
    expectations = {
        'upc_not_null': 'UPC.notna()',
        'sales_positive': 'Sales_Dollars >= 0',
        'store_valid': 'Store_ID != "STORE_999"'
    }
    
    # Run the guard
    guard = DataQualityGuard(sample_data, expectations, batch_id=1)
    guard.validate()
    clean, quarantine = guard.split()
    
    # Log metrics
    metrics = guard.log_metrics(output_file='data/audit_log.csv')
    
    # Show error summary
    print("\n📋 Error Summary:")
    print(guard.get_error_summary())
    
    print("\n🟢 Clean Records:")
    print(clean[['UPC', 'Store_ID', 'Sales_Dollars']].to_string())
    
    print("\n🔴 Quarantined Records:")
    print(quarantine[['UPC', 'Store_ID', 'Sales_Dollars', 'Error_Reason']].to_string())
