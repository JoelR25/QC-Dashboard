"""
ADLS Blob Storage Validator
Validates files in Azure Data Lake Storage (ADLS) Gen2
Checks for file existence, freshness, size, and structure
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from azure.storage.blob import BlobServiceClient, ContainerClient
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


class ADLSBlobValidator:
    """Validates data files in ADLS Bronze layer"""
    
    def __init__(self, connection_string: str, container_name: str = "bronze"):
        """
        Initialize ADLS Blob Validator
        
        Args:
            connection_string: Azure Storage connection string
            container_name: Container name (default: bronze)
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = container_name
        self.container_client = self.blob_service_client.get_container_client(container_name)
        self.validation_results = []
        
    def check_file_exists(self, blob_path: str, product_name: str) -> Dict:
        """
        Check if expected file exists in ADLS
        
        Args:
            blob_path: Path to blob (e.g., "circana/product1/weekly/file.csv")
            product_name: Product identifier
            
        Returns:
            Validation result dictionary
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            exists = blob_client.exists()
            
            result = {
                'product': product_name,
                'check_type': 'file_existence',
                'blob_path': blob_path,
                'passed': exists,
                'message': f"File {'found' if exists else 'NOT FOUND'}: {blob_path}",
                'severity': 'CRITICAL' if not exists else 'INFO',
                'timestamp': datetime.now().isoformat()
            }
            
            if exists:
                # Get file metadata
                properties = blob_client.get_blob_properties()
                result['file_size_bytes'] = properties.size
                result['last_modified'] = properties.last_modified.isoformat()
                
            self.validation_results.append(result)
            logger.info(result['message'])
            return result
            
        except Exception as e:
            result = {
                'product': product_name,
                'check_type': 'file_existence',
                'blob_path': blob_path,
                'passed': False,
                'message': f"Error checking file: {str(e)}",
                'severity': 'CRITICAL',
                'timestamp': datetime.now().isoformat()
            }
            self.validation_results.append(result)
            logger.error(result['message'])
            return result
    
    def check_file_freshness(self, blob_path: str, product_name: str, 
                            max_age_hours: int = 26) -> Dict:
        """
        Check if file was updated recently (within max_age_hours)
        
        Args:
            blob_path: Path to blob
            product_name: Product identifier
            max_age_hours: Maximum acceptable age in hours (default: 26 for weekly + buffer)
            
        Returns:
            Validation result dictionary
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            
            if not blob_client.exists():
                return {
                    'product': product_name,
                    'check_type': 'file_freshness',
                    'blob_path': blob_path,
                    'passed': False,
                    'message': f"File not found: {blob_path}",
                    'severity': 'CRITICAL',
                    'timestamp': datetime.now().isoformat()
                }
            
            properties = blob_client.get_blob_properties()
            last_modified = properties.last_modified
            age_hours = (datetime.now(last_modified.tzinfo) - last_modified).total_seconds() / 3600
            
            passed = age_hours <= max_age_hours
            
            result = {
                'product': product_name,
                'check_type': 'file_freshness',
                'blob_path': blob_path,
                'passed': passed,
                'message': f"File age: {age_hours:.1f} hours ({'fresh' if passed else 'STALE'})",
                'severity': 'CRITICAL' if not passed else 'INFO',
                'age_hours': age_hours,
                'max_age_hours': max_age_hours,
                'last_modified': last_modified.isoformat(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            logger.info(result['message'])
            return result
            
        except Exception as e:
            result = {
                'product': product_name,
                'check_type': 'file_freshness',
                'blob_path': blob_path,
                'passed': False,
                'message': f"Error checking freshness: {str(e)}",
                'severity': 'CRITICAL',
                'timestamp': datetime.now().isoformat()
            }
            self.validation_results.append(result)
            logger.error(result['message'])
            return result
    
    def check_file_size(self, blob_path: str, product_name: str,
                       expected_min_size_mb: float = 1.0,
                       variance_threshold: float = 50.0) -> Dict:
        """
        Check if file size is within expected range
        
        Args:
            blob_path: Path to blob
            product_name: Product identifier
            expected_min_size_mb: Minimum expected size in MB
            variance_threshold: Max % variance from historical average
            
        Returns:
            Validation result dictionary
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            
            if not blob_client.exists():
                return {
                    'product': product_name,
                    'check_type': 'file_size',
                    'blob_path': blob_path,
                    'passed': False,
                    'message': f"File not found: {blob_path}",
                    'severity': 'CRITICAL',
                    'timestamp': datetime.now().isoformat()
                }
            
            properties = blob_client.get_blob_properties()
            size_mb = properties.size / (1024 * 1024)
            
            # Check minimum size
            passed = size_mb >= expected_min_size_mb
            
            result = {
                'product': product_name,
                'check_type': 'file_size',
                'blob_path': blob_path,
                'passed': passed,
                'message': f"File size: {size_mb:.2f} MB ({'OK' if passed else 'TOO SMALL'})",
                'severity': 'WARNING' if not passed else 'INFO',
                'size_mb': size_mb,
                'expected_min_mb': expected_min_size_mb,
                'timestamp': datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            logger.info(result['message'])
            return result
            
        except Exception as e:
            result = {
                'product': product_name,
                'check_type': 'file_size',
                'blob_path': blob_path,
                'passed': False,
                'message': f"Error checking size: {str(e)}",
                'severity': 'WARNING',
                'timestamp': datetime.now().isoformat()
            }
            self.validation_results.append(result)
            logger.error(result['message'])
            return result
    
    def validate_file_structure(self, blob_path: str, product_name: str,
                                expected_columns: List[str],
                                sample_rows: int = 100) -> Dict:
        """
        Validate CSV file structure (columns) without loading entire file
        
        Args:
            blob_path: Path to blob
            product_name: Product identifier
            expected_columns: List of expected column names
            sample_rows: Number of rows to sample for validation
            
        Returns:
            Validation result dictionary
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            
            if not blob_client.exists():
                return {
                    'product': product_name,
                    'check_type': 'file_structure',
                    'blob_path': blob_path,
                    'passed': False,
                    'message': f"File not found: {blob_path}",
                    'severity': 'CRITICAL',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Download first few KB to check structure
            stream = blob_client.download_blob(max_concurrency=1, length=1024*100)  # 100KB
            content = stream.readall()
            
            # Parse CSV header
            import io
            df_sample = pd.read_csv(io.BytesIO(content), nrows=sample_rows)
            actual_columns = df_sample.columns.tolist()
            
            # Compare columns
            missing_columns = set(expected_columns) - set(actual_columns)
            extra_columns = set(actual_columns) - set(expected_columns)
            
            passed = len(missing_columns) == 0
            
            result = {
                'product': product_name,
                'check_type': 'file_structure',
                'blob_path': blob_path,
                'passed': passed,
                'message': f"Structure check: {len(missing_columns)} missing columns, {len(extra_columns)} extra columns",
                'severity': 'CRITICAL' if len(missing_columns) > 0 else ('WARNING' if len(extra_columns) > 0 else 'INFO'),
                'expected_columns': expected_columns,
                'actual_columns': actual_columns,
                'missing_columns': list(missing_columns),
                'extra_columns': list(extra_columns),
                'timestamp': datetime.now().isoformat()
            }
            
            self.validation_results.append(result)
            logger.info(result['message'])
            return result
            
        except Exception as e:
            result = {
                'product': product_name,
                'check_type': 'file_structure',
                'blob_path': blob_path,
                'passed': False,
                'message': f"Error validating structure: {str(e)}",
                'severity': 'CRITICAL',
                'timestamp': datetime.now().isoformat()
            }
            self.validation_results.append(result)
            logger.error(result['message'])
            return result
    
    def validate_product_extract_set(self, product_name: str, 
                                    expected_files: List[str],
                                    base_path: str = "circana") -> Dict:
        """
        Validate complete set of extracts for a product (60-150 files)
        
        Args:
            product_name: Product identifier
            expected_files: List of expected file names/patterns
            base_path: Base path in ADLS (default: circana)
            
        Returns:
            Summary validation result
        """
        logger.info(f"Validating extract set for product: {product_name}")
        
        product_path = f"{base_path}/{product_name}/weekly"
        total_expected = len(expected_files)
        files_found = 0
        files_missing = []
        files_stale = []
        
        for file_name in expected_files:
            blob_path = f"{product_path}/{file_name}"
            
            # Check existence
            exist_result = self.check_file_exists(blob_path, product_name)
            if exist_result['passed']:
                files_found += 1
                
                # Check freshness
                fresh_result = self.check_file_freshness(blob_path, product_name)
                if not fresh_result['passed']:
                    files_stale.append(file_name)
            else:
                files_missing.append(file_name)
        
        completeness_pct = (files_found / total_expected * 100) if total_expected > 0 else 0
        passed = files_found == total_expected and len(files_stale) == 0
        
        summary = {
            'product': product_name,
            'check_type': 'extract_set_validation',
            'total_expected': total_expected,
            'files_found': files_found,
            'files_missing': len(files_missing),
            'files_stale': len(files_stale),
            'completeness_pct': completeness_pct,
            'passed': passed,
            'message': f"{product_name}: {files_found}/{total_expected} files found ({completeness_pct:.1f}%)",
            'severity': 'CRITICAL' if not passed else 'INFO',
            'missing_files': files_missing[:10],  # First 10
            'stale_files': files_stale[:10],  # First 10
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results.append(summary)
        logger.info(summary['message'])
        return summary
    
    def get_validation_summary(self) -> pd.DataFrame:
        """Get all validation results as DataFrame"""
        if not self.validation_results:
            return pd.DataFrame()
        return pd.DataFrame(self.validation_results)
    
    def export_results(self, output_path: str):
        """Export validation results to CSV"""
        df = self.get_validation_summary()
        df.to_csv(output_path, index=False)
        logger.info(f"Validation results exported to: {output_path}")


def validate_all_products(products_config: Dict, connection_string: str) -> pd.DataFrame:
    """
    Validate ADLS extracts for all products
    
    Args:
        products_config: Dict with product definitions
        connection_string: ADLS connection string
        
    Returns:
        DataFrame with all validation results
    """
    validator = ADLSBlobValidator(connection_string)
    
    all_results = []
    
    for product_name, config in products_config.items():
        logger.info(f"\n{'='*70}")
        logger.info(f"VALIDATING PRODUCT: {product_name}")
        logger.info(f"{'='*70}")
        
        expected_files = config.get('expected_files', [])
        
        # Validate extract set
        summary = validator.validate_product_extract_set(
            product_name=product_name,
            expected_files=expected_files
        )
        
        all_results.append(summary)
    
    return pd.DataFrame(all_results)
