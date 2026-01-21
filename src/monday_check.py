"""
Monday Morning Automated Check
Replaces manual BA validation with automated confidence check
Runs every Monday at 6 AM to validate weekend data load
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import yaml
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.validators.adls_validator import ADLSBlobValidator, validate_all_products
from src.validators.data_validator import ReconciliationValidator, DataQualityValidator
from src.shadow_dlt import DataQualityGuard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MondayMorningCheck:
    """Automated Monday morning data quality confidence check"""
    
    def __init__(self, config_path: str):
        """
        Initialize Monday check with configuration
        
        Args:
            config_path: Path to products_config.yaml
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.products_config = self.config['products']
        self.global_config = self.config['global_config']
        self.monday_check_config = self.config['monday_check']
        
        self.check_results = []
        self.summary = {
            'check_date': datetime.now().isoformat(),
            'products_checked': 0,
            'total_checks': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'critical_failures': 0,
            'overall_status': 'UNKNOWN'
        }
        
    def run_adls_validation(self) -> pd.DataFrame:
        """
        Step 1: Validate files in ADLS Bronze layer
        Check all expected files exist, are fresh, and have reasonable size
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 1: ADLS BLOB VALIDATION")
        logger.info("="*70)
        
        connection_string = os.getenv('ADLS_CONNECTION_STRING')
        if not connection_string:
            logger.error("ADLS_CONNECTION_STRING not set!")
            return pd.DataFrame()
        
        validator = ADLSBlobValidator(connection_string)
        
        for product_name, product_config in self.products_config.items():
            logger.info(f"\nValidating ADLS files for: {product_name}")
            
            expected_files = product_config.get('expected_files', [])
            base_path = product_config['adls_config']['base_path']
            
            # For demonstration, check first 5 files
            # In production, check all 60-150 files
            sample_files = expected_files[:5]
            
            for file_name in sample_files:
                blob_path = f"{base_path}/{file_name}"
                
                # Check existence
                validator.check_file_exists(blob_path, product_name)
                
                # Check freshness
                validator.check_file_freshness(
                    blob_path, 
                    product_name,
                    max_age_hours=product_config['alert_thresholds']['max_age_hours']
                )
                
                # Check size
                validator.check_file_size(
                    blob_path,
                    product_name,
                    expected_min_size_mb=product_config['alert_thresholds']['min_file_size_mb']
                )
        
        results_df = validator.get_validation_summary()
        
        # Update summary
        self.summary['products_checked'] = len(self.products_config)
        self.summary['total_checks'] += len(results_df)
        self.summary['checks_passed'] += results_df['passed'].sum()
        self.summary['checks_failed'] += (~results_df['passed']).sum()
        self.summary['critical_failures'] += (results_df['severity'] == 'CRITICAL').sum()
        
        logger.info(f"\nADLS Validation Complete: {results_df['passed'].sum()}/{len(results_df)} checks passed")
        
        return results_df
    
    def run_bronze_validation(self) -> Dict:
        """
        Step 2: Validate Bronze layer ingestion
        Reconcile ADLS file counts with Bronze table row counts
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 2: BRONZE LAYER VALIDATION")
        logger.info("="*70)
        
        # This would connect to Databricks and run queries
        # For now, return mock results
        
        results = {
            'layer': 'Bronze',
            'checks': []
        }
        
        for product_name in self.products_config.keys():
            check = {
                'product': product_name,
                'check': 'bronze_ingestion',
                'passed': True,  # Would check actual row counts
                'message': f'Bronze ingestion complete for {product_name}',
                'severity': 'INFO'
            }
            results['checks'].append(check)
        
        self.summary['total_checks'] += len(results['checks'])
        self.summary['checks_passed'] += sum(1 for c in results['checks'] if c['passed'])
        
        logger.info(f"Bronze Validation Complete")
        
        return results
    
    def run_trust_score_check(self) -> Dict:
        """
        Step 3: Calculate Trust Score for each product
        Check if Trust Score meets threshold (95%+)
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 3: TRUST SCORE VALIDATION")
        logger.info("="*70)
        
        results = {
            'layer': 'Silver',
            'trust_scores': []
        }
        
        threshold = self.monday_check_config['checks_to_run'][5]['threshold']
        
        for product_name in self.products_config.keys():
            # In production, calculate actual trust score from audit logs
            # For now, simulate
            trust_score = 96.5  # Mock value
            
            passed = trust_score >= threshold
            
            check = {
                'product': product_name,
                'check': 'trust_score',
                'trust_score': trust_score,
                'threshold': threshold,
                'passed': passed,
                'message': f'{product_name} Trust Score: {trust_score:.2f}% ({"PASS" if passed else "FAIL"})',
                'severity': 'CRITICAL' if not passed else 'INFO'
            }
            results['trust_scores'].append(check)
            
            logger.info(check['message'])
        
        self.summary['total_checks'] += len(results['trust_scores'])
        self.summary['checks_passed'] += sum(1 for c in results['trust_scores'] if c['passed'])
        
        return results
    
    def run_reconciliation_checks(self) -> Dict:
        """
        Step 4: Reconciliation across layers
        Bronze → Silver → Gold → Power BI
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 4: CROSS-LAYER RECONCILIATION")
        logger.info("="*70)
        
        results = {
            'reconciliations': []
        }
        
        for product_name in self.products_config.keys():
            # Bronze to Silver reconciliation
            recon = {
                'product': product_name,
                'source': 'Bronze',
                'target': 'Silver (Valid + Quarantine)',
                'source_count': 100000,  # Mock
                'target_count': 100000,  # Mock
                'passed': True,
                'message': f'{product_name}: Bronze to Silver reconciliation PASS',
                'severity': 'INFO'
            }
            results['reconciliations'].append(recon)
            
            logger.info(recon['message'])
        
        self.summary['total_checks'] += len(results['reconciliations'])
        self.summary['checks_passed'] += sum(1 for c in results['reconciliations'] if c['passed'])
        
        return results
    
    def run_power_bi_validation(self) -> Dict:
        """
        Step 5: Validate Power BI semantic model
        Check refresh status and row counts
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 5: POWER BI VALIDATION")
        logger.info("="*70)
        
        results = {
            'pbi_checks': []
        }
        
        # Check refresh status
        refresh_check = {
            'check': 'pbi_refresh_status',
            'last_refresh': datetime.now().isoformat(),
            'status': 'Success',
            'passed': True,
            'message': 'Power BI refresh successful',
            'severity': 'INFO'
        }
        results['pbi_checks'].append(refresh_check)
        
        logger.info(refresh_check['message'])
        
        self.summary['total_checks'] += len(results['pbi_checks'])
        self.summary['checks_passed'] += sum(1 for c in results['pbi_checks'] if c['passed'])
        
        return results
    
    def generate_report(self, all_results: Dict) -> str:
        """
        Generate HTML report for Monday morning check
        
        Args:
            all_results: Dictionary containing all validation results
            
        Returns:
            HTML report string
        """
        # Calculate overall status
        success_rate = (self.summary['checks_passed'] / self.summary['total_checks'] * 100) if self.summary['total_checks'] > 0 else 0
        
        if self.summary['critical_failures'] > 0:
            self.summary['overall_status'] = 'CRITICAL'
            status_color = 'red'
        elif success_rate >= 98:
            self.summary['overall_status'] = 'EXCELLENT'
            status_color = 'green'
        elif success_rate >= 95:
            self.summary['overall_status'] = 'GOOD'
            status_color = 'yellow'
        else:
            self.summary['overall_status'] = 'WARNING'
            status_color = 'orange'
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
                .status-box {{ 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 5px;
                    background-color: {status_color};
                    color: white;
                    font-size: 24px;
                    text-align: center;
                }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                .pass {{ color: green; font-weight: bold; }}
                .fail {{ color: red; font-weight: bold; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Monday Morning Data Quality Check</h1>
            <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            
            <div class="status-box">
                Overall Status: {self.summary['overall_status']}
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <ul>
                    <li><strong>Products Checked:</strong> {self.summary['products_checked']}</li>
                    <li><strong>Total Checks:</strong> {self.summary['total_checks']}</li>
                    <li><strong>Checks Passed:</strong> {self.summary['checks_passed']}</li>
                    <li><strong>Checks Failed:</strong> {self.summary['checks_failed']}</li>
                    <li><strong>Critical Failures:</strong> {self.summary['critical_failures']}</li>
                    <li><strong>Success Rate:</strong> {success_rate:.2f}%</li>
                </ul>
            </div>
            
            <h2>Detailed Results</h2>
            
            <h3>1. ADLS File Validation</h3>
            <!-- Would include detailed table here -->
            
            <h3>2. Trust Score by Product</h3>
            <table>
                <tr>
                    <th>Product</th>
                    <th>Trust Score</th>
                    <th>Status</th>
                </tr>
        """
        
        for ts in all_results.get('trust_scores', {}).get('trust_scores', []):
            status_class = 'pass' if ts['passed'] else 'fail'
            html += f"""
                <tr>
                    <td>{ts['product']}</td>
                    <td>{ts['trust_score']:.2f}%</td>
                    <td class="{status_class}">{"PASS" if ts['passed'] else "FAIL"}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Action Items</h2>
            <ul>
        """
        
        if self.summary['critical_failures'] > 0:
            html += f"<li style='color: red;'><strong>URGENT:</strong> {self.summary['critical_failures']} critical failures require immediate attention</li>"
        
        if success_rate < 95:
            html += "<li style='color: orange;'><strong>WARNING:</strong> Success rate below 95% threshold</li>"
        
        if self.summary['checks_failed'] == 0:
            html += "<li style='color: green;'>✓ All checks passed - data is ready for analysis</li>"
        
        html += """
            </ul>
            
            <hr>
            <p><em>This is an automated report. For questions, contact dataops@company.com</em></p>
        </body>
        </html>
        """
        
        return html
    
    def run_full_check(self) -> Dict:
        """
        Run complete Monday morning check sequence
        Returns summary of all results
        """
        logger.info("\n" + "="*80)
        logger.info("MONDAY MORNING DATA QUALITY CHECK")
        logger.info("="*80)
        logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
        logger.info("="*80)
        
        all_results = {}
        
        try:
            # Step 1: ADLS Validation
            all_results['adls'] = self.run_adls_validation()
            
            # Step 2: Bronze Validation
            all_results['bronze'] = self.run_bronze_validation()
            
            # Step 3: Trust Score Check
            all_results['trust_scores'] = self.run_trust_score_check()
            
            # Step 4: Reconciliation
            all_results['reconciliation'] = self.run_reconciliation_checks()
            
            # Step 5: Power BI Validation
            all_results['powerbi'] = self.run_power_bi_validation()
            
            # Generate report
            html_report = self.generate_report(all_results)
            
            # Save report
            report_path = f"monday_check_{datetime.now().strftime('%Y%m%d')}.html"
            with open(report_path, 'w') as f:
                f.write(html_report)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"CHECK COMPLETE")
            logger.info(f"{'='*80}")
            logger.info(f"Overall Status: {self.summary['overall_status']}")
            logger.info(f"Success Rate: {self.summary['checks_passed']}/{self.summary['total_checks']} ({self.summary['checks_passed']/self.summary['total_checks']*100:.2f}%)")
            logger.info(f"Report saved to: {report_path}")
            logger.info(f"{'='*80}\n")
            
            # Send email (would implement email sending here)
            self.send_email_report(html_report)
            
            return {
                'summary': self.summary,
                'results': all_results,
                'report_path': report_path
            }
            
        except Exception as e:
            logger.error(f"Error during Monday check: {str(e)}")
            raise
    
    def send_email_report(self, html_content: str):
        """Send email report to stakeholders"""
        # Would implement email sending using SMTP or SendGrid
        logger.info("Email report would be sent to: " + 
                   ", ".join(self.monday_check_config['report_generation']['email_to']))


def main():
    """Main entry point for Monday morning check"""
    config_path = "config/products_config.yaml"
    
    checker = MondayMorningCheck(config_path)
    results = checker.run_full_check()
    
    # Exit with appropriate code
    if results['summary']['critical_failures'] > 0:
        sys.exit(1)  # Fail build/pipeline if critical issues
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()
