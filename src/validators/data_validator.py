"""
Data Validation Framework for QC Dashboard
This module provides core validation functionality for data reconciliation
across Circana → ADLS → Databricks Medallion → Power BI pipeline
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Represents the result of a validation check"""
    
    def __init__(self, rule_name: str, passed: bool, message: str, 
                 severity: str = "warning", details: Optional[Dict] = None):
        self.rule_name = rule_name
        self.passed = passed
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict:
        """Convert result to dictionary"""
        return {
            'rule_name': self.rule_name,
            'passed': self.passed,
            'message': self.message,
            'severity': self.severity,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
        
    def __repr__(self):
        status = "✓ PASS" if self.passed else "✗ FAIL"
        return f"[{self.severity.upper()}] {status}: {self.rule_name} - {self.message}"


class DataValidator(ABC):
    """Base class for data validators"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results: List[ValidationResult] = []
        
    @abstractmethod
    def validate(self) -> List[ValidationResult]:
        """Execute validation checks"""
        pass
        
    def add_result(self, result: ValidationResult):
        """Add a validation result"""
        self.results.append(result)
        logger.info(str(result))
        
    def get_summary(self) -> Dict:
        """Get validation summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        critical_failures = sum(1 for r in self.results 
                               if not r.passed and r.severity == "critical")
        
        return {
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'critical_failures': critical_failures,
            'success_rate': (passed / total * 100) if total > 0 else 0
        }


class ReconciliationValidator:
    """Validates data reconciliation between pipeline layers"""
    
    def __init__(self, source_layer: str, target_layer: str, config: Dict):
        self.source_layer = source_layer
        self.target_layer = target_layer
        self.config = config
        self.results: List[ValidationResult] = []
        
    def validate_row_count(self, source_count: int, target_count: int, 
                          tolerance_percent: float = 0.1) -> ValidationResult:
        """Validate row count reconciliation between layers"""
        variance = abs(source_count - target_count) / source_count * 100
        passed = variance <= tolerance_percent
        
        message = (f"Row count: Source={source_count:,}, Target={target_count:,}, "
                  f"Variance={variance:.2f}%")
        
        result = ValidationResult(
            rule_name="row_count_reconciliation",
            passed=passed,
            message=message,
            severity="critical" if not passed else "info",
            details={
                'source_count': source_count,
                'target_count': target_count,
                'variance_percent': variance,
                'tolerance_percent': tolerance_percent
            }
        )
        
        self.results.append(result)
        return result
        
    def validate_sum_reconciliation(self, source_sum: float, target_sum: float,
                                   column_name: str, 
                                   tolerance_percent: float = 0.01) -> ValidationResult:
        """Validate sum reconciliation for a numeric column"""
        variance = abs(source_sum - target_sum) / source_sum * 100 if source_sum != 0 else 0
        passed = variance <= tolerance_percent
        
        message = (f"Sum reconciliation for '{column_name}': "
                  f"Source={source_sum:,.2f}, Target={target_sum:,.2f}, "
                  f"Variance={variance:.4f}%")
        
        result = ValidationResult(
            rule_name=f"sum_reconciliation_{column_name}",
            passed=passed,
            message=message,
            severity="critical" if not passed else "info",
            details={
                'column': column_name,
                'source_sum': source_sum,
                'target_sum': target_sum,
                'variance_percent': variance
            }
        )
        
        self.results.append(result)
        return result
        
    def validate_key_match(self, source_keys: set, target_keys: set,
                          key_column: str) -> ValidationResult:
        """Validate key columns match between layers"""
        missing_in_target = source_keys - target_keys
        extra_in_target = target_keys - source_keys
        
        passed = len(missing_in_target) == 0 and len(extra_in_target) == 0
        
        message = (f"Key matching for '{key_column}': "
                  f"Missing in target={len(missing_in_target)}, "
                  f"Extra in target={len(extra_in_target)}")
        
        result = ValidationResult(
            rule_name=f"key_match_{key_column}",
            passed=passed,
            message=message,
            severity="critical" if not passed else "info",
            details={
                'key_column': key_column,
                'missing_count': len(missing_in_target),
                'extra_count': len(extra_in_target),
                'missing_keys': list(missing_in_target)[:10],  # First 10
                'extra_keys': list(extra_in_target)[:10]
            }
        )
        
        self.results.append(result)
        return result
        
    def get_reconciliation_summary(self) -> Dict:
        """Get reconciliation summary"""
        return {
            'source_layer': self.source_layer,
            'target_layer': self.target_layer,
            'total_checks': len(self.results),
            'passed': sum(1 for r in self.results if r.passed),
            'failed': sum(1 for r in self.results if not r.passed),
            'results': [r.to_dict() for r in self.results]
        }


class DataQualityValidator:
    """Validates data quality metrics"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.results: List[ValidationResult] = []
        
    def check_null_percentage(self, total_rows: int, null_counts: Dict[str, int],
                             max_null_percent: float = 1.0) -> List[ValidationResult]:
        """Check null percentages for critical columns"""
        results = []
        
        for column, null_count in null_counts.items():
            null_percent = (null_count / total_rows * 100) if total_rows > 0 else 0
            passed = null_percent <= max_null_percent
            
            message = f"Null check for '{column}': {null_percent:.2f}% null values"
            
            result = ValidationResult(
                rule_name=f"null_check_{column}",
                passed=passed,
                message=message,
                severity="warning" if not passed else "info",
                details={
                    'column': column,
                    'total_rows': total_rows,
                    'null_count': null_count,
                    'null_percent': null_percent,
                    'threshold': max_null_percent
                }
            )
            
            results.append(result)
            self.results.append(result)
            
        return results
        
    def check_data_freshness(self, last_update: datetime, 
                           max_age_hours: int = 26) -> ValidationResult:
        """Check if data is fresh based on last update timestamp"""
        age = datetime.now() - last_update
        age_hours = age.total_seconds() / 3600
        passed = age_hours <= max_age_hours
        
        message = (f"Data freshness: Last update was {age_hours:.1f} hours ago "
                  f"(threshold: {max_age_hours} hours)")
        
        result = ValidationResult(
            rule_name="data_freshness_check",
            passed=passed,
            message=message,
            severity="critical" if not passed else "info",
            details={
                'last_update': last_update.isoformat(),
                'age_hours': age_hours,
                'threshold_hours': max_age_hours
            }
        )
        
        self.results.append(result)
        return result
        
    def calculate_quality_score(self, metrics: Dict[str, float]) -> ValidationResult:
        """Calculate overall data quality score"""
        # Metrics expected: completeness, accuracy, consistency, timeliness (0-100)
        avg_score = sum(metrics.values()) / len(metrics) if metrics else 0
        min_score = self.config.get('min_score', 95)
        passed = avg_score >= min_score
        
        message = f"Data Quality Score: {avg_score:.2f}/100 (threshold: {min_score})"
        
        result = ValidationResult(
            rule_name="data_quality_score",
            passed=passed,
            message=message,
            severity="warning" if not passed else "info",
            details={
                'overall_score': avg_score,
                'min_score': min_score,
                'metrics': metrics
            }
        )
        
        self.results.append(result)
        return result
        
    def get_quality_summary(self) -> Dict:
        """Get data quality summary"""
        return {
            'total_checks': len(self.results),
            'passed': sum(1 for r in self.results if r.passed),
            'failed': sum(1 for r in self.results if not r.passed),
            'results': [r.to_dict() for r in self.results]
        }


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def generate_validation_report(validators: List[Any], output_path: str):
    """Generate comprehensive validation report"""
    report = {
        'report_generated': datetime.now().isoformat(),
        'validators': []
    }
    
    for validator in validators:
        validator_report = {
            'type': validator.__class__.__name__,
            'results': [r.to_dict() for r in validator.results]
        }
        report['validators'].append(validator_report)
        
    # Write report
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False)
        
    logger.info(f"Validation report generated: {output_path}")
    return report
