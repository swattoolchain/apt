"""
API Performance Testing Module

Provides API-specific performance testing using aiohttp.
Measures request/response times, throughput, and concurrent request performance.
"""

from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
import time
import logging
from dataclasses import dataclass

from .base_performance_tester import BasePerformanceTester, PerformanceMetrics, PerformanceConfig

logger = logging.getLogger(__name__)


@dataclass
class APIRequest:
    """API request configuration."""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, str]] = None


class APIPerformanceTester(BasePerformanceTester):
    """API Performance Tester using aiohttp."""
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize API performance tester.
        
        Args:
            config: Performance test configuration
        """
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self) -> None:
        """Setup aiohttp session."""
        timeout = aiohttp.ClientTimeout(total=self.config.api_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("API session setup complete")
    
    async def teardown(self) -> None:
        """Teardown aiohttp session."""
        if self.session:
            await self.session.close()
            logger.info("API session closed")
    
    async def measure_request(
        self,
        request: APIRequest,
        test_name: Optional[str] = None,
        iteration: int = 0,
        user_id: int = 0
    ) -> PerformanceMetrics:
        """
        Measure performance of a single API request.
        
        Args:
            request: API request configuration
            test_name: Name of the test
            iteration: Iteration number
            user_id: User ID for concurrent testing
            
        Returns:
            PerformanceMetrics with API request data
        """
        if not test_name:
            test_name = f"api_request_{request.method}_{request.url.split('/')[-1]}"
        
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time(),
            iteration=iteration,
            user_id=user_id
        )
        
        if not self.session:
            metrics.add_error("Session not initialized. Call setup() first.")
            metrics.finalize()
            return metrics
        
        try:
            # Prepare request
            request_start = time.time()
            
            # Make request
            async with self.session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                json=request.body,
                params=request.params
            ) as response:
                # Time to first byte
                ttfb = time.time() - request_start
                
                # Read response
                response_text = await response.text()
                response_end = time.time()
                
                # Calculate metrics
                total_time = response_end - request_start
                response_size = len(response_text.encode('utf-8'))
                
                # Store metrics
                metrics.metrics.update({
                    'ttfb': ttfb,
                    'total_time': total_time,
                    'response_time': response_end - request_start,
                    'status_code': response.status,
                    'response_size': response_size,
                    'response_size_kb': response_size / 1024,
                    'method': request.method,
                    'url': request.url
                })
                
                # Store response headers
                metrics.metadata['response_headers'] = dict(response.headers)
                
                # Check for errors
                if response.status >= 400:
                    metrics.add_error(f"HTTP {response.status}: {response.reason}")
                
        except asyncio.TimeoutError:
            metrics.add_error(f"Request timeout after {self.config.api_timeout}s")
        except Exception as e:
            error_msg = f"Error making API request: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
        finally:
            metrics.finalize()
            self.add_result(metrics)
        
        return metrics
    
    async def measure_concurrent_requests(
        self,
        request: APIRequest,
        concurrent_users: int,
        test_name: Optional[str] = None,
        iteration: int = 0
    ) -> List[PerformanceMetrics]:
        """
        Measure performance of concurrent API requests.
        
        Args:
            request: API request configuration
            concurrent_users: Number of concurrent requests
            test_name: Name of the test
            iteration: Iteration number
            
        Returns:
            List of PerformanceMetrics for each concurrent request
        """
        if not test_name:
            test_name = f"concurrent_api_{request.method}_{concurrent_users}users"
        
        # Create tasks for concurrent execution
        tasks = []
        for user_id in range(concurrent_users):
            task = self.measure_request(
                request=request,
                test_name=f"{test_name}_user{user_id}",
                iteration=iteration,
                user_id=user_id
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, PerformanceMetrics)]
        
        # Log summary
        if valid_results:
            avg_time = sum(r.metrics.get('total_time', 0) for r in valid_results) / len(valid_results)
            logger.info(f"Concurrent test complete: {concurrent_users} users, avg time: {avg_time:.3f}s")
        
        return valid_results
    
    async def measure_throughput(
        self,
        request: APIRequest,
        duration_seconds: int,
        test_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Measure API throughput (requests per second).
        
        Args:
            request: API request configuration
            duration_seconds: How long to run the test
            test_name: Name of the test
            
        Returns:
            Dictionary with throughput metrics
        """
        if not test_name:
            test_name = f"throughput_{request.method}"
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        request_count = 0
        errors = 0
        
        logger.info(f"Starting throughput test for {duration_seconds}s")
        
        while time.time() < end_time:
            metrics = await self.measure_request(
                request=request,
                test_name=f"{test_name}_req{request_count}",
                iteration=0,
                user_id=0
            )
            
            request_count += 1
            if not metrics.is_successful():
                errors += 1
        
        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration
        error_rate = errors / request_count if request_count > 0 else 0
        
        throughput_metrics = {
            'test_name': test_name,
            'duration': actual_duration,
            'total_requests': request_count,
            'successful_requests': request_count - errors,
            'failed_requests': errors,
            'requests_per_second': throughput,
            'error_rate': error_rate
        }
        
        logger.info(f"Throughput test complete: {throughput:.2f} req/s, error rate: {error_rate:.2%}")
        
        return throughput_metrics
