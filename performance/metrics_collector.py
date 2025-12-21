"""
Metrics Collector Module

Centralized metrics collection and aggregation for performance testing.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from collections import defaultdict
import logging

from .base_performance_tester import PerformanceMetrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and aggregates performance metrics across test runs."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.all_metrics: List[PerformanceMetrics] = []
        self.metrics_by_test: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.metrics_by_user: Dict[int, List[PerformanceMetrics]] = defaultdict(list)
    
    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Add performance metrics to the collector.
        
        Args:
            metrics: PerformanceMetrics to add
        """
        self.all_metrics.append(metrics)
        self.metrics_by_test[metrics.test_name].append(metrics)
        self.metrics_by_user[metrics.user_id].append(metrics)
    
    def add_multiple_metrics(self, metrics_list: List[PerformanceMetrics]) -> None:
        """
        Add multiple performance metrics.
        
        Args:
            metrics_list: List of PerformanceMetrics to add
        """
        for metrics in metrics_list:
            self.add_metrics(metrics)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Calculate summary statistics across all metrics.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.all_metrics:
            return {}
        
        durations = [m.duration for m in self.all_metrics if m.duration > 0]
        successful = [m for m in self.all_metrics if m.is_successful()]
        failed = [m for m in self.all_metrics if not m.is_successful()]
        
        summary = {
            'total_tests': len(self.all_metrics),
            'successful_tests': len(successful),
            'failed_tests': len(failed),
            'success_rate': len(successful) / len(self.all_metrics) if self.all_metrics else 0,
            'error_rate': len(failed) / len(self.all_metrics) if self.all_metrics else 0,
        }
        
        if durations:
            summary.update({
                'avg_duration': float(np.mean(durations)),
                'min_duration': float(min(durations)),
                'max_duration': float(max(durations)),
                'median_duration': float(np.median(durations)),
                'p50_duration': float(np.percentile(durations, 50)),
                'p75_duration': float(np.percentile(durations, 75)),
                'p90_duration': float(np.percentile(durations, 90)),
                'p95_duration': float(np.percentile(durations, 95)),
                'p99_duration': float(np.percentile(durations, 99)),
                'std_dev': float(np.std(durations)),
                'variance': float(np.var(durations))
            })
        
        return summary
    
    def get_test_statistics(self, test_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Dictionary with test-specific statistics
        """
        metrics_list = self.metrics_by_test.get(test_name, [])
        
        if not metrics_list:
            return {}
        
        durations = [m.duration for m in metrics_list if m.duration > 0]
        successful = [m for m in metrics_list if m.is_successful()]
        
        stats = {
            'test_name': test_name,
            'total_runs': len(metrics_list),
            'successful_runs': len(successful),
            'failed_runs': len(metrics_list) - len(successful),
            'success_rate': len(successful) / len(metrics_list) if metrics_list else 0,
        }
        
        if durations:
            stats.update({
                'avg_duration': float(np.mean(durations)),
                'min_duration': float(min(durations)),
                'max_duration': float(max(durations)),
                'median_duration': float(np.median(durations)),
                'p95_duration': float(np.percentile(durations, 95)),
                'std_dev': float(np.std(durations))
            })
        
        return stats
    
    def get_all_test_statistics(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all tests.
        
        Returns:
            List of dictionaries with statistics for each test
        """
        return [
            self.get_test_statistics(test_name)
            for test_name in self.metrics_by_test.keys()
        ]
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific user (concurrent execution).
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user-specific statistics
        """
        metrics_list = self.metrics_by_user.get(user_id, [])
        
        if not metrics_list:
            return {}
        
        durations = [m.duration for m in metrics_list if m.duration > 0]
        
        stats = {
            'user_id': user_id,
            'total_tests': len(metrics_list),
            'successful_tests': len([m for m in metrics_list if m.is_successful()]),
        }
        
        if durations:
            stats.update({
                'avg_duration': float(np.mean(durations)),
                'total_duration': float(sum(durations))
            })
        
        return stats
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert all metrics to a pandas DataFrame.
        
        Returns:
            DataFrame with all metrics
        """
        if not self.all_metrics:
            return pd.DataFrame()
        
        data = []
        for m in self.all_metrics:
            row = {
                'test_name': m.test_name,
                'duration': m.duration,
                'iteration': m.iteration,
                'user_id': m.user_id,
                'successful': m.is_successful(),
                'error_count': len(m.errors),
                'screenshot_count': len(m.screenshots),
                'network_request_count': len(m.network_requests)
            }
            
            # Add custom metrics
            for key, value in m.metrics.items():
                if isinstance(value, (int, float, str, bool)):
                    row[f'metric_{key}'] = value
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def get_percentile_data(self, percentiles: List[int] = [50, 75, 90, 95, 99]) -> Dict[str, Dict[int, float]]:
        """
        Get percentile data for each test.
        
        Args:
            percentiles: List of percentiles to calculate
            
        Returns:
            Dictionary mapping test names to percentile data
        """
        percentile_data = {}
        
        for test_name, metrics_list in self.metrics_by_test.items():
            durations = [m.duration for m in metrics_list if m.duration > 0]
            
            if durations:
                percentile_data[test_name] = {
                    p: float(np.percentile(durations, p))
                    for p in percentiles
                }
        
        return percentile_data
    
    def get_time_series_data(self) -> pd.DataFrame:
        """
        Get time series data for visualization.
        
        Returns:
            DataFrame with time series data
        """
        if not self.all_metrics:
            return pd.DataFrame()
        
        data = []
        for m in self.all_metrics:
            data.append({
                'timestamp': m.start_time,
                'test_name': m.test_name,
                'duration': m.duration,
                'successful': m.is_successful(),
                'iteration': m.iteration,
                'user_id': m.user_id
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df.sort_values('timestamp')
    
    def compare_iterations(self, test_name: str) -> Dict[str, Any]:
        """
        Compare performance across iterations for a specific test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Dictionary with iteration comparison data
        """
        metrics_list = self.metrics_by_test.get(test_name, [])
        
        if not metrics_list:
            return {}
        
        # Group by iteration
        by_iteration = defaultdict(list)
        for m in metrics_list:
            by_iteration[m.iteration].append(m.duration)
        
        comparison = {}
        for iteration, durations in by_iteration.items():
            if durations:
                comparison[f'iteration_{iteration}'] = {
                    'count': len(durations),
                    'avg': float(np.mean(durations)),
                    'min': float(min(durations)),
                    'max': float(max(durations)),
                    'std_dev': float(np.std(durations))
                }
        
        return comparison

class InfluxDBPublisher:
    """Publishes metrics to InfluxDB for real-time monitoring."""
    
    def __init__(self, url="http://localhost:8086", token=None, org="-", bucket="k6"):
        self.client = None
        self.write_api = None
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            # For InfluxDB 1.8 compatibility
            if "/k6" not in url and not bucket: 
                # Assuming v1.8 URL format might be needed or just database as bucket
                pass
                
            self.client = InfluxDBClient(url=url, token=token, org=org, debug=False)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = bucket
            logger.info(f"InfluxDB Publisher initialized: {url} (bucket: {bucket})")
        except ImportError:
            logger.warning("influxdb-client not installed. Real-time monitoring disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")

    def publish_metric(self, measurement: str, fields: Dict[str, Any], tags: Dict[str, str] = None, timestamp=None):
        """
        Publish a single metric point to InfluxDB.
        
        Args:
            measurement: Name of the measurement (e.g., 'http_req_duration')
            fields: Dictionary of field key-values (e.g., {'value': 123.4})
            tags: Dictionary of tag key-values (e.g., {'method': 'GET'})
            timestamp: Optional timestamp
        """
        if not self.write_api:
            return

        try:
            from influxdb_client import Point
            
            p = Point(measurement)
            if tags:
                for k, v in tags.items():
                    p.tag(k, v)
            if fields:
                for k, v in fields.items():
                    p.field(k, v)
            if timestamp:
                p.time(timestamp)
                
            self.write_api.write(bucket=self.bucket, record=p)
        except Exception as e:
            logger.debug(f"Failed to publish metric to InfluxDB: {e}")

    def close(self):
        if self.client:
            self.client.close()
