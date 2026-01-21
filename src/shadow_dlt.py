"""
Shadow DLT: Data Quality Guard for Databricks Community Edition
Simulates Delta Live Tables (DLT) Expectations functionality without native platform support

This class implements the "Quarantine Pattern" - instead of dropping bad data or failing,
it routes invalid records to a quarantine table for analysis while allowing valid data to proceed.
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, lit, when, current_timestamp, concat_ws, array
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json


class DataQualityGuard:
    """
    Shadow DLT implementation for data quality enforcement
    Mimics Delta Live Tables expectations with Quarantine Pattern
    """
    
    def __init__(self, spark: SparkSession, batch_id: str):
        self.spark = spark
        self.batch_id = batch_id
        self.audit_records = []
        
    def validate_with_expectations(
        self,
        df: DataFrame,
        expectations: Dict[str, Dict],
        layer_name: str
    ) -> Tuple[DataFrame, DataFrame]:
        """
        Apply validation expectations and split data into valid and quarantine streams
        
        Args:
            df: Input DataFrame to validate
            expectations: Dictionary of validation rules
            layer_name: Name of the layer (e.g., "Bronze_to_Silver")
            
        Returns:
            Tuple of (valid_df, quarantine_df)
        """
        input_count = df.count()
        print(f"\n{'='*70}")
        print(f"Data Quality Guard - {layer_name}")
        print(f"{'='*70}")
        print(f"Input Records: {input_count:,}")
        
        # Add validation columns for each expectation
        validated_df = df
        validation_columns = []
        error_messages = []
        
        for rule_name, rule_config in expectations.items():
            condition = rule_config['condition']
            severity = rule_config.get('severity', 'HIGH')
            description = rule_config.get('description', rule_name)
            
            # Create validation column
            validation_col = f"_valid_{rule_name}"
            validated_df = validated_df.withColumn(
                validation_col,
                when(condition, True).otherwise(False)
            )
            validation_columns.append(validation_col)
            
            # Create error message for failures
            error_msg_col = f"_error_{rule_name}"
            validated_df = validated_df.withColumn(
                error_msg_col,
                when(~col(validation_col), 
                     lit(f"{rule_name}|{severity}|{description}")).otherwise(lit(None))
            )
            error_messages.append(error_msg_col)
            
            # Log validation statistics
            failed_count = validated_df.filter(~col(validation_col)).count()
            if failed_count > 0:
                print(f"  ✗ {rule_name}: {failed_count:,} failures ({severity})")
            else:
                print(f"  ✓ {rule_name}: All records valid")
        
        # Create master validation flag (all validations must pass)
        validated_df = validated_df.withColumn(
            "_is_valid",
            # All validation columns must be True
            col(validation_columns[0]) if len(validation_columns) == 1 
            else col(validation_columns[0])
        )
        
        # Properly combine all validation columns with AND logic
        for val_col in validation_columns[1:]:
            validated_df = validated_df.withColumn(
                "_is_valid",
                col("_is_valid") & col(val_col)
            )
        
        # Create consolidated error message
        validated_df = validated_df.withColumn(
            "_error_details",
            concat_ws("; ", *[col(err_col) for err_col in error_messages])
        )
        
        # Split into valid and quarantine streams
        valid_df = validated_df.filter(col("_is_valid"))
        quarantine_df = validated_df.filter(~col("_is_valid"))
        
        # Clean up validation columns from valid stream
        columns_to_drop = validation_columns + error_messages + ["_is_valid", "_error_details"]
        valid_df = valid_df.drop(*columns_to_drop)
        
        # Enhance quarantine stream with metadata
        quarantine_df = quarantine_df.withColumn("Quarantine_Timestamp", current_timestamp())
        quarantine_df = quarantine_df.withColumn("Batch_ID", lit(self.batch_id))
        quarantine_df = quarantine_df.withColumn("Layer_Name", lit(layer_name))
        quarantine_df = quarantine_df.withColumn("Error_Details", col("_error_details"))
        
        # Drop temporary validation columns from quarantine but keep error info
        quarantine_df = quarantine_df.drop(*validation_columns).drop(*error_messages).drop("_is_valid", "_error_details")
        
        valid_count = valid_df.count()
        quarantine_count = quarantine_df.count()
        
        # Calculate Trust Score
        trust_score = (valid_count / input_count * 100) if input_count > 0 else 0
        
        print(f"\nRESULTS:")
        print(f"  Valid Records: {valid_count:,} ({trust_score:.2f}%)")
        print(f"  Quarantined Records: {quarantine_count:,} ({100-trust_score:.2f}%)")
        print(f"  Trust Score: {trust_score:.2f}%")
        print(f"{'='*70}\n")
        
        # Log to audit trail
        self.audit_records.append({
            'batch_id': self.batch_id,
            'layer_name': layer_name,
            'timestamp': datetime.now().isoformat(),
            'input_rows': input_count,
            'valid_rows': valid_count,
            'quarantine_rows': quarantine_count,
            'trust_score': trust_score,
            'expectations_count': len(expectations)
        })
        
        return valid_df, quarantine_df
    
    def create_audit_log_entry(self) -> List[Dict]:
        """Return audit log entries for this batch"""
        return self.audit_records
    
    def get_trust_score_summary(self) -> Dict:
        """Get overall trust score summary for the batch"""
        if not self.audit_records:
            return {'trust_score': 100.0, 'total_quarantined': 0}
        
        total_input = sum(r['input_rows'] for r in self.audit_records)
        total_quarantined = sum(r['quarantine_rows'] for r in self.audit_records)
        overall_trust = ((total_input - total_quarantined) / total_input * 100) if total_input > 0 else 0
        
        return {
            'batch_id': self.batch_id,
            'trust_score': overall_trust,
            'total_input': total_input,
            'total_quarantined': total_quarantined,
            'layers_processed': len(self.audit_records)
        }


class ReconciliationEngine:
    """
    Perform reconciliation checks between pipeline layers
    Validates that transformations preserve data integrity
    """
    
    def __init__(self, spark: SparkSession, batch_id: str):
        self.spark = spark
        self.batch_id = batch_id
        self.reconciliation_results = []
        
    def reconcile_row_counts(
        self,
        source_df: DataFrame,
        target_df: DataFrame,
        source_name: str,
        target_name: str,
        tolerance_percent: float = 0.1
    ) -> Dict:
        """Reconcile row counts between source and target layers"""
        source_count = source_df.count()
        target_count = target_df.count()
        variance = abs(source_count - target_count) / source_count * 100 if source_count > 0 else 0
        
        passed = variance <= tolerance_percent
        
        result = {
            'check_type': 'row_count_reconciliation',
            'source_layer': source_name,
            'target_layer': target_name,
            'source_count': source_count,
            'target_count': target_count,
            'variance_percent': variance,
            'tolerance_percent': tolerance_percent,
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        }
        
        self.reconciliation_results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {source_name} → {target_name} Row Count")
        print(f"  Source: {source_count:,}, Target: {target_count:,}, Variance: {variance:.4f}%")
        
        return result
    
    def reconcile_sum(
        self,
        source_df: DataFrame,
        target_df: DataFrame,
        column_name: str,
        source_name: str,
        target_name: str,
        tolerance_percent: float = 0.01
    ) -> Dict:
        """Reconcile sum of a numeric column between layers"""
        from pyspark.sql.functions import sum as spark_sum
        
        source_sum = source_df.select(spark_sum(col(column_name))).collect()[0][0] or 0
        target_sum = target_df.select(spark_sum(col(column_name))).collect()[0][0] or 0
        
        variance = abs(source_sum - target_sum) / source_sum * 100 if source_sum != 0 else 0
        passed = variance <= tolerance_percent
        
        result = {
            'check_type': 'sum_reconciliation',
            'source_layer': source_name,
            'target_layer': target_name,
            'column': column_name,
            'source_sum': float(source_sum),
            'target_sum': float(target_sum),
            'variance_percent': variance,
            'tolerance_percent': tolerance_percent,
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        }
        
        self.reconciliation_results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {source_name} → {target_name} Sum({column_name})")
        print(f"  Source: ${source_sum:,.2f}, Target: ${target_sum:,.2f}, Variance: {variance:.4f}%")
        
        return result
    
    def get_reconciliation_summary(self) -> List[Dict]:
        """Get all reconciliation results"""
        return self.reconciliation_results


def define_bronze_to_silver_expectations() -> Dict[str, Dict]:
    """
    Define validation expectations for Bronze to Silver transformation
    These expectations implement the data quality rules
    """
    return {
        'upc_not_null': {
            'condition': col('UPC').isNotNull(),
            'severity': 'CRITICAL',
            'description': 'UPC must not be null'
        },
        'sales_dollars_not_null': {
            'condition': col('Sales_Dollars').isNotNull(),
            'severity': 'CRITICAL',
            'description': 'Sales_Dollars must not be null'
        },
        'units_sold_not_null': {
            'condition': col('Units_Sold').isNotNull(),
            'severity': 'HIGH',
            'description': 'Units_Sold must not be null'
        },
        'non_negative_sales': {
            'condition': col('Sales_Dollars') >= 0,
            'severity': 'HIGH',
            'description': 'Sales_Dollars must be non-negative'
        },
        'non_negative_units': {
            'condition': col('Units_Sold') >= 0,
            'severity': 'HIGH',
            'description': 'Units_Sold must be non-negative'
        },
        'reasonable_price': {
            'condition': (col('Sales_Dollars') / col('Units_Sold') <= 100) & (col('Units_Sold') > 0),
            'severity': 'MEDIUM',
            'description': 'Unit price must be reasonable (<=100)'
        }
    }


def define_master_data_expectations(product_master_df: DataFrame, store_master_df: DataFrame) -> Dict[str, Dict]:
    """
    Define expectations for master data validation
    Checks that UPCs and Store IDs exist in reference tables
    """
    # Create broadcast sets for efficient lookup
    valid_upcs = [row['UPC'] for row in product_master_df.select('UPC').collect()]
    valid_stores = [row['Store_ID'] for row in store_master_df.select('Store_ID').collect()]
    
    return {
        'upc_in_master': {
            'condition': col('UPC').isin(valid_upcs),
            'severity': 'CRITICAL',
            'description': 'UPC must exist in Product Master'
        },
        'store_in_master': {
            'condition': col('Store_ID').isin(valid_stores),
            'severity': 'CRITICAL',
            'description': 'Store ID must exist in Store Master'
        }
    }
