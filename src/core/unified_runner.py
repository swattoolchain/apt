"""
Unified Test Runner - Execute k6, JMeter, and Playwright tests together

Runs all performance testing tools and collects results for unified reporting.
"""

import asyncio
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .external_integrations import K6Integration, JMeterIntegration
from .metrics_collector import MetricsCollector
from .base_performance_tester import PerformanceConfig

logger = logging.getLogger(__name__)


class UnifiedTestRunner:
    """Run and coordinate tests across multiple tools."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize unified test runner.
        
        Args:
            output_dir: Directory for test results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'playwright': [],
            'k6': [],
            'jmeter': [],
            'metadata': {
                'start_time': None,
                'end_time': None,
                'total_duration': 0
            }
        }
        
        # Initialize InfluxDB Publisher if configured
        self.influx_publisher = None
        influx_url = os.environ.get("INFLUXDB_URL")
        if influx_url:
            from .metrics_collector import InfluxDBPublisher
            self.influx_publisher = InfluxDBPublisher(url=influx_url, bucket=os.environ.get("INFLUXDB_DB", "k6"))

    
        # Load existing results for cumulative reporting (UnifiedTestRunner)
        self.load_existing_results()
    
    def load_existing_results(self, filename: str = "unified_results.json"):
        """Load existing results from JSON file to enable cumulative reporting."""
        results_file = self.output_dir / filename
        
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    existing_results = json.load(f)
                
                # Merge existing results
                if 'playwright' in existing_results:
                    self.results['playwright'].extend(existing_results['playwright'])
                if 'k6' in existing_results:
                    self.results['k6'].extend(existing_results['k6'])
                if 'jmeter' in existing_results:
                    self.results['jmeter'].extend(existing_results['jmeter'])
                if 'workflows' in existing_results:
                    if 'workflows' not in self.results:
                        self.results['workflows'] = []
                    self.results['workflows'].extend(existing_results['workflows'])
                
                logger.info(f"Loaded existing results from {results_file}")
                logger.info(f"  k6: {len(existing_results.get('k6', []))}, JMeter: {len(existing_results.get('jmeter', []))}, Workflows: {len(existing_results.get('workflows', []))}")
            except Exception as e:
                logger.warning(f"Could not load existing results: {e}")
    
    async def run_k6_test(
        self,
        test_name: str,
        scenarios: List[Dict[str, Any]],
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run k6 load test within the framework.
        
        Args:
            test_name: Name of the test
            scenarios: List of API scenarios
            options: k6 options (vus, duration, etc.)
            
        Returns:
            k6 test results
        """
        logger.info(f"Running k6 test: {test_name}")
        
        # Generate k6 script
        script = K6Integration.generate_k6_script(test_name, scenarios, options)
        script_path = self.output_dir / f"{test_name}_k6.js"
        K6Integration.save_k6_script(script, str(script_path))
        
        # Prepare output file
        results_file = self.output_dir / f"{test_name}_k6_results.json"
        
        # Run k6
        try:
            cmd = [
                'k6', 'run',
                '--out', f'json={results_file}',
                '--summary-export', str(self.output_dir / f"{test_name}_k6_summary.json"),
                str(script_path)
            ]
            
            # Add InfluxDB output if configured
            if self.influx_publisher:
                # k6 native influxdb support requires URL
                influx_url = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
                # Ensure database name is in URL for v1.x (e.g. http://localhost:8086/k6)
                db_name = os.environ.get("INFLUXDB_DB", "k6")
                cmd.extend(["--out", f"influxdb={influx_url}/{db_name}"])
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"k6 test completed successfully: {test_name}")
                
                # Parse results - prefer summary file over results file
                # Summary file has aggregated metrics, results file has individual points
                summary_file = self.output_dir / f"{test_name}_k6_summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file) as f:
                            content = f.read()
                        # Use JSONDecoder to parse only the first JSON object
                        # This handles cases where k6 outputs extra data after JSON
                        from json import JSONDecoder
                        decoder = JSONDecoder()
                        summary, idx = decoder.raw_decode(content)
                        results = self._parse_k6_summary(summary)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"JSON decode error in summary: {e}")
                        results = {'error': f'JSON parsing failed: {str(e)}'}
                elif results_file.exists():
                    # Fallback to results file (contains individual metric points)
                    results = K6Integration.parse_k6_results(str(results_file))
                else:
                    results = {'error': 'No k6 results or summary file found'}
                
                results['test_name'] = test_name
                results['tool'] = 'k6'
                results['stdout'] = stdout.decode()
                # Set status based on whether there's an error
                results['status'] = 'error' if 'error' in results else 'success'
                
                self.results['k6'].append(results)
                return results
            else:
                error_msg = stderr.decode()
                logger.error(f"k6 test failed: {error_msg}")
                
                results = {
                    'test_name': test_name,
                    'tool': 'k6',
                    'status': 'failed',
                    'error': error_msg
                }
                
                self.results['k6'].append(results)
                return results
                
        except FileNotFoundError:
            error_msg = "k6 not found. Install with: brew install k6"
            logger.error(error_msg)
            
            results = {
                'test_name': test_name,
                'tool': 'k6',
                'status': 'error',
                'error': error_msg
            }
            
            self.results['k6'].append(results)
            return results
    
    async def run_jmeter_test(
        self,
        test_name: str,
        scenarios: List[Dict[str, Any]],
        thread_group_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run JMeter test within the framework.
        
        Args:
            test_name: Name of the test
            scenarios: List of HTTP scenarios
            thread_group_config: Thread group configuration
            
        Returns:
            JMeter test results
        """
        logger.info(f"Running JMeter test: {test_name}")
        
        # Generate JMX
        jmx = JMeterIntegration.generate_jmx(test_name, scenarios, thread_group_config)
        jmx_path = self.output_dir / f"{test_name}_jmeter.jmx"
        JMeterIntegration.save_jmx(jmx, str(jmx_path))
        
        # Prepare output file
        results_file = self.output_dir / f"{test_name}_jmeter_results.jtl"
        
        # Run JMeter
        try:
            cmd = [
                'jmeter',
                '-n',  # Non-GUI mode
                '-t', str(jmx_path),
                '-l', str(results_file)
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"JMeter test completed successfully: {test_name}")
                
                # Parse results
                if results_file.exists():
                    results = JMeterIntegration.parse_jtl_results(str(results_file))
                else:
                    results = {'error': 'No results file found'}
                
                results['test_name'] = test_name
                results['tool'] = 'jmeter'
                results['stdout'] = stdout.decode()
                results['status'] = 'success'
                
                self.results['jmeter'].append(results)
                return results
            else:
                error_msg = stderr.decode()
                logger.error(f"JMeter test failed: {error_msg}")
                
                results = {
                    'test_name': test_name,
                    'tool': 'jmeter',
                    'status': 'failed',
                    'error': error_msg
                }
                
                self.results['jmeter'].append(results)
                return results
                
        except FileNotFoundError:
            error_msg = "JMeter not found. Install with: brew install jmeter"
            logger.error(error_msg)
            
            results = {
                'test_name': test_name,
                'tool': 'jmeter',
                'status': 'error',
                'error': error_msg
            }
            
            self.results['jmeter'].append(results)
            return results
    
    def add_playwright_results(self, metrics_collector: MetricsCollector):
        """
        Add Playwright test results.
        
        Args:
            metrics_collector: MetricsCollector with Playwright results
        """
        for metrics in metrics_collector.all_metrics:
            result = {
                'test_name': metrics.test_name,
                'tool': 'playwright',
                'type': 'ui',
                'duration': metrics.duration,
                'status': 'success' if metrics.is_successful() else 'failed',
                'metrics': metrics.metrics,
                'errors': metrics.errors
            }
            
            self.results['playwright'].append(result)
    
    def _parse_k6_summary(self, summary: Dict) -> Dict:
        """Parse k6 summary JSON."""
        metrics = summary.get('metrics', {})
        
        return {
            'metrics': {
                'http_req_duration': metrics.get('http_req_duration', {}),
                'http_reqs': metrics.get('http_reqs', {}),
                'http_req_failed': metrics.get('http_req_failed', {}),
                'vus': metrics.get('vus', {})
            }
        }
    
    def get_all_results(self) -> Dict:
        """Get all test results."""
        return self.results
    
    def save_results(self, filename: str = "unified_results.json"):
        """Save all results to JSON file."""
        output_file = self.output_dir / filename
        
        # Get all results including workflows
        all_results = self.get_all_results()
        
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Unified results saved to {output_file}")
        return output_file
