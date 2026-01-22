"""
Custom Metrics Collector Framework

Extensible framework for collecting server-side and custom metrics from any source:
- API endpoints
- Log files
- Databases
- Monitoring systems (Prometheus, Grafana, DataDog, New Relic)
- Custom implementations
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class BaseMetricsCollector:
    """Base class for custom metrics collectors."""
    
    def __init__(self, name: str):
        """
        Initialize metrics collector.
        
        Args:
            name: Collector name/identifier
        """
        self.name = name
        self.metrics = {}
        self.collection_time = None
    
    async def collect(self) -> Dict[str, Any]:
        """
        Collect metrics from source.
        
        Returns:
            Dictionary of collected metrics
        """
        raise NotImplementedError("Subclasses must implement collect()")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            'collector': self.name,
            'collection_time': self.collection_time.isoformat() if self.collection_time else None,
            'metrics': self.metrics
        }


class APIMetricsCollector(BaseMetricsCollector):
    """Collect metrics from API endpoints."""
    
    def __init__(
        self,
        name: str,
        api_url: str,
        headers: Optional[Dict] = None,
        parser_func: Optional[Callable] = None
    ):
        """
        Initialize API metrics collector.
        
        Args:
            name: Collector name
            api_url: API endpoint URL
            headers: HTTP headers
            parser_func: Function to parse API response
        """
        super().__init__(name)
        self.api_url = api_url
        self.headers = headers or {}
        self.parser_func = parser_func
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics from API endpoint."""
        import aiohttp
        
        try:
            self.collection_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, headers=self.headers) as resp:
                    data = await resp.json()
            
            # Parse response
            if self.parser_func:
                self.metrics = self.parser_func(data)
            else:
                self.metrics = data
            
            return self.get_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting from API {self.api_url}: {e}")
            return {'error': str(e), 'collector': self.name}


class LogFileMetricsCollector(BaseMetricsCollector):
    """Collect metrics from log files."""
    
    def __init__(
        self,
        name: str,
        log_file_path: str,
        patterns: Dict[str, str],
        tail_lines: int = 1000
    ):
        """
        Initialize log file metrics collector.
        
        Args:
            name: Collector name
            log_file_path: Path to log file
            patterns: Dict of metric_name: regex_pattern
            tail_lines: Number of lines to read from end
        """
        super().__init__(name)
        self.log_file_path = Path(log_file_path)
        self.patterns = patterns
        self.tail_lines = tail_lines
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics from log file."""
        try:
            self.collection_time = datetime.now()
            
            # Read last N lines
            lines = await self._tail_file(self.log_file_path, self.tail_lines)
            
            # Extract metrics using patterns
            for metric_name, pattern in self.patterns.items():
                matches = []
                for line in lines:
                    match = re.search(pattern, line)
                    if match:
                        matches.append(match.group(1) if match.groups() else match.group(0))
                
                if matches:
                    # Try to convert to numbers
                    try:
                        numeric_matches = [float(m) for m in matches]
                        self.metrics[metric_name] = {
                            'count': len(numeric_matches),
                            'avg': sum(numeric_matches) / len(numeric_matches),
                            'min': min(numeric_matches),
                            'max': max(numeric_matches),
                            'latest': numeric_matches[-1]
                        }
                    except ValueError:
                        self.metrics[metric_name] = {
                            'count': len(matches),
                            'values': matches[-10:]  # Last 10 values
                        }
            
            return self.get_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting from log file {self.log_file_path}: {e}")
            return {'error': str(e), 'collector': self.name}
    
    async def _tail_file(self, file_path: Path, n: int) -> List[str]:
        """Read last n lines from file."""
        try:
            with open(file_path, 'r') as f:
                return f.readlines()[-n:]
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return []


class PrometheusMetricsCollector(BaseMetricsCollector):
    """Collect metrics from Prometheus."""
    
    def __init__(
        self,
        name: str,
        prometheus_url: str,
        queries: Dict[str, str]
    ):
        """
        Initialize Prometheus metrics collector.
        
        Args:
            name: Collector name
            prometheus_url: Prometheus server URL
            queries: Dict of metric_name: PromQL query
        """
        super().__init__(name)
        self.prometheus_url = prometheus_url.rstrip('/')
        self.queries = queries
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics from Prometheus."""
        import aiohttp
        
        try:
            self.collection_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                for metric_name, query in self.queries.items():
                    url = f"{self.prometheus_url}/api/v1/query"
                    params = {'query': query}
                    
                    async with session.get(url, params=params) as resp:
                        data = await resp.json()
                    
                    if data['status'] == 'success':
                        result = data['data']['result']
                        if result:
                            # Extract value
                            value = float(result[0]['value'][1])
                            self.metrics[metric_name] = value
            
            return self.get_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting from Prometheus: {e}")
            return {'error': str(e), 'collector': self.name}


class DatabaseMetricsCollector(BaseMetricsCollector):
    """Collect metrics from database queries."""
    
    def __init__(
        self,
        name: str,
        connection_string: str,
        queries: Dict[str, str],
        db_type: str = "postgresql"
    ):
        """
        Initialize database metrics collector.
        
        Args:
            name: Collector name
            connection_string: Database connection string
            queries: Dict of metric_name: SQL query
            db_type: Database type (postgresql, mysql, etc.)
        """
        super().__init__(name)
        self.connection_string = connection_string
        self.queries = queries
        self.db_type = db_type
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics from database."""
        try:
            self.collection_time = datetime.now()
            
            if self.db_type == "postgresql":
                import asyncpg
                conn = await asyncpg.connect(self.connection_string)
                
                for metric_name, query in self.queries.items():
                    result = await conn.fetch(query)
                    self.metrics[metric_name] = [dict(row) for row in result]
                
                await conn.close()
            
            # Add support for other databases as needed
            
            return self.get_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting from database: {e}")
            return {'error': str(e), 'collector': self.name}


class CustomFunctionCollector(BaseMetricsCollector):
    """
    Collect metrics using a custom function.
    
    This is the most flexible collector - users can implement any logic.
    """
    
    def __init__(
        self,
        name: str,
        collector_func: Callable,
        **kwargs
    ):
        """
        Initialize custom function collector.
        
        Args:
            name: Collector name
            collector_func: Async function that returns metrics dict
            **kwargs: Additional arguments passed to collector_func
        """
        super().__init__(name)
        self.collector_func = collector_func
        self.kwargs = kwargs
    
    async def collect(self) -> Dict[str, Any]:
        """Collect metrics using custom function."""
        try:
            self.collection_time = datetime.now()
            
            # Call custom function
            self.metrics = await self.collector_func(**self.kwargs)
            
            return self.get_metrics()
            
        except Exception as e:
            logger.error(f"Error in custom collector {self.name}: {e}")
            return {'error': str(e), 'collector': self.name}


class MetricsCollectorOrchestrator:
    """Orchestrate multiple metrics collectors."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.collectors: List[BaseMetricsCollector] = []
        self.results = {}
    
    def add_collector(self, collector: BaseMetricsCollector):
        """Add a metrics collector."""
        self.collectors.append(collector)
    
    async def collect_all(self) -> Dict[str, Any]:
        """
        Collect metrics from all registered collectors.
        
        Returns:
            Dictionary with all collected metrics
        """
        tasks = [collector.collect() for collector in self.collectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.results = {
            'collection_time': datetime.now().isoformat(),
            'total_collectors': len(self.collectors),
            'collectors': {}
        }
        
        for collector, result in zip(self.collectors, results):
            if isinstance(result, Exception):
                self.results['collectors'][collector.name] = {
                    'status': 'error',
                    'error': str(result)
                }
            else:
                self.results['collectors'][collector.name] = result
        
        return self.results
    
    async def collect_during_test(
        self,
        test_func: Callable,
        interval: float = 5.0,
        **test_kwargs
    ) -> Dict[str, Any]:
        """
        Collect metrics continuously during test execution.
        
        Args:
            test_func: Async function to execute (the test)
            interval: Collection interval in seconds
            **test_kwargs: Arguments for test_func
            
        Returns:
            Test results with time-series metrics
        """
        metrics_timeline = []
        test_running = True
        test_result = None
        test_error = None
        
        async def collect_loop():
            """Background task to collect metrics."""
            while test_running:
                metrics = await self.collect_all()
                metrics_timeline.append({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                })
                await asyncio.sleep(interval)
        
        async def run_test():
            """Run the actual test."""
            nonlocal test_result, test_error, test_running
            try:
                test_result = await test_func(**test_kwargs)
            except Exception as e:
                test_error = str(e)
            finally:
                test_running = False
        
        # Run test and collection concurrently
        await asyncio.gather(
            run_test(),
            collect_loop()
        )
        
        return {
            'test_result': test_result,
            'test_error': test_error,
            'metrics_timeline': metrics_timeline,
            'total_collections': len(metrics_timeline)
        }
