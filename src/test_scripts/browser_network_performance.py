#!/usr/bin/env python3
"""
Browser Network Performance Utility

Measures network call performance for UI actions in the browser.
Captures detailed metrics for all network requests during a UI action.

Features:
- Request/response timing
- Resource type analysis
- Size and compression metrics
- Waterfall data
- Failed request tracking
- Performance marks integration

Usage:
    from src.test_scripts.browser_network_performance import BrowserNetworkPerformance
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        perf = BrowserNetworkPerformance(page)
        await perf.start_monitoring()
        
        # Perform UI action
        await page.goto("https://example.com")
        await page.click("#button")
        
        metrics = await perf.get_metrics()
        print(f"Total requests: {metrics['summary']['total_requests']}")
        print(f"Total size: {metrics['summary']['total_size_kb']:.2f} KB")
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from playwright.async_api import Page, Route, Request, Response


class BrowserNetworkPerformance:
    """
    Utility to measure browser network call performance during UI actions.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the network performance monitor.
        
        Args:
            page: Playwright page instance
        """
        self.page = page
        self.requests: List[Dict[str, Any]] = []
        self.responses: Dict[str, Dict[str, Any]] = {}
        self.failed_requests: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.monitoring = False
        
    async def start_monitoring(self):
        """Start monitoring network requests."""
        self.monitoring = True
        self.start_time = datetime.now().timestamp()
        self.requests = []
        self.responses = {}
        self.failed_requests = []
        
        # Listen to network events
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)
        self.page.on("requestfailed", self._on_request_failed)
        
    async def stop_monitoring(self):
        """Stop monitoring network requests."""
        self.monitoring = False
        
        # Remove listeners
        self.page.remove_listener("request", self._on_request)
        self.page.remove_listener("response", self._on_response)
        self.page.remove_listener("requestfailed", self._on_request_failed)
        
    def _on_request(self, request: Request):
        """Handle request event."""
        if not self.monitoring:
            return
            
        request_data = {
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "headers": request.headers,
            "post_data": request.post_data,
            "timestamp": datetime.now().timestamp(),
            "request_id": id(request)
        }
        self.requests.append(request_data)
        
    def _on_response(self, response: Response):
        """Handle response event."""
        if not self.monitoring:
            return
            
        request = response.request
        request_id = id(request)
        
        response_data = {
            "url": response.url,
            "status": response.status,
            "status_text": response.status_text,
            "headers": response.headers,
            "timestamp": datetime.now().timestamp(),
            "request_id": request_id,
            "from_cache": response.from_service_worker or False
        }
        
        self.responses[str(request_id)] = response_data
        
    def _on_request_failed(self, request: Request):
        """Handle failed request event."""
        if not self.monitoring:
            return
            
        failed_data = {
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "failure": request.failure,
            "timestamp": datetime.now().timestamp()
        }
        self.failed_requests.append(failed_data)
        
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive network performance metrics.
        
        Returns:
            Dictionary containing detailed network metrics
        """
        # Get performance entries from browser
        performance_entries = await self.page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('resource');
                return entries.map(entry => ({
                    name: entry.name,
                    duration: entry.duration,
                    startTime: entry.startTime,
                    initiatorType: entry.initiatorType,
                    transferSize: entry.transferSize,
                    encodedBodySize: entry.encodedBodySize,
                    decodedBodySize: entry.decodedBodySize,
                    domainLookupStart: entry.domainLookupStart,
                    domainLookupEnd: entry.domainLookupEnd,
                    connectStart: entry.connectStart,
                    connectEnd: entry.connectEnd,
                    secureConnectionStart: entry.secureConnectionStart,
                    requestStart: entry.requestStart,
                    responseStart: entry.responseStart,
                    responseEnd: entry.responseEnd
                }));
            }
        """)
        
        # Calculate metrics
        total_requests = len(self.requests)
        total_failed = len(self.failed_requests)
        total_size = sum(entry.get('transferSize', 0) for entry in performance_entries)
        total_encoded_size = sum(entry.get('encodedBodySize', 0) for entry in performance_entries)
        total_decoded_size = sum(entry.get('decodedBodySize', 0) for entry in performance_entries)
        
        # Calculate timing metrics
        durations = [entry['duration'] for entry in performance_entries if entry['duration'] > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Group by resource type
        by_type = {}
        for entry in performance_entries:
            res_type = entry.get('initiatorType', 'other')
            if res_type not in by_type:
                by_type[res_type] = {
                    'count': 0,
                    'total_size': 0,
                    'total_duration': 0
                }
            by_type[res_type]['count'] += 1
            by_type[res_type]['total_size'] += entry.get('transferSize', 0)
            by_type[res_type]['total_duration'] += entry.get('duration', 0)
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        p50 = self._percentile(sorted_durations, 50) if sorted_durations else 0
        p75 = self._percentile(sorted_durations, 75) if sorted_durations else 0
        p90 = self._percentile(sorted_durations, 90) if sorted_durations else 0
        p95 = self._percentile(sorted_durations, 95) if sorted_durations else 0
        p99 = self._percentile(sorted_durations, 99) if sorted_durations else 0
        
        # Get status code distribution
        status_codes = {}
        for req_id, response in self.responses.items():
            status = response.get('status', 0)
            status_codes[status] = status_codes.get(status, 0) + 1
        
        # Calculate compression ratio
        compression_ratio = 0
        if total_decoded_size > 0:
            compression_ratio = ((total_decoded_size - total_encoded_size) / total_decoded_size) * 100
        
        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": total_requests - total_failed,
                "failed_requests": total_failed,
                "success_rate": (total_requests - total_failed) / total_requests if total_requests > 0 else 0,
                "total_size_bytes": total_size,
                "total_size_kb": total_size / 1024,
                "total_size_mb": total_size / (1024 * 1024),
                "total_encoded_size_kb": total_encoded_size / 1024,
                "total_decoded_size_kb": total_decoded_size / 1024,
                "compression_ratio_percent": compression_ratio,
                "monitoring_duration_seconds": datetime.now().timestamp() - self.start_time if self.start_time else 0
            },
            "timing": {
                "avg_duration_ms": avg_duration,
                "min_duration_ms": min_duration,
                "max_duration_ms": max_duration,
                "p50_ms": p50,
                "p75_ms": p75,
                "p90_ms": p90,
                "p95_ms": p95,
                "p99_ms": p99
            },
            "by_resource_type": by_type,
            "status_codes": status_codes,
            "detailed_requests": performance_entries,
            "failed_requests": self.failed_requests,
            "cached_requests": sum(1 for r in self.responses.values() if r.get('from_cache', False))
        }
    
    async def get_waterfall_data(self) -> List[Dict[str, Any]]:
        """
        Get waterfall data for visualization.
        
        Returns:
            List of requests with timing breakdown for waterfall chart
        """
        performance_entries = await self.page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('resource');
                return entries.map(entry => ({
                    name: entry.name,
                    startTime: entry.startTime,
                    duration: entry.duration,
                    dns: entry.domainLookupEnd - entry.domainLookupStart,
                    tcp: entry.connectEnd - entry.connectStart,
                    ssl: entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
                    wait: entry.responseStart - entry.requestStart,
                    download: entry.responseEnd - entry.responseStart,
                    initiatorType: entry.initiatorType
                }));
            }
        """)
        
        return performance_entries
    
    async def get_slowest_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the slowest network requests.
        
        Args:
            count: Number of slowest requests to return
            
        Returns:
            List of slowest requests with details
        """
        performance_entries = await self.page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('resource');
                return entries.map(entry => ({
                    name: entry.name,
                    duration: entry.duration,
                    transferSize: entry.transferSize,
                    initiatorType: entry.initiatorType
                }));
            }
        """)
        
        sorted_entries = sorted(performance_entries, key=lambda x: x['duration'], reverse=True)
        return sorted_entries[:count]
    
    async def get_largest_requests(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the largest network requests by size.
        
        Args:
            count: Number of largest requests to return
            
        Returns:
            List of largest requests with details
        """
        performance_entries = await self.page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('resource');
                return entries.map(entry => ({
                    name: entry.name,
                    duration: entry.duration,
                    transferSize: entry.transferSize,
                    initiatorType: entry.initiatorType
                }));
            }
        """)
        
        sorted_entries = sorted(performance_entries, key=lambda x: x.get('transferSize', 0), reverse=True)
        return sorted_entries[:count]
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0
        size = len(data)
        index = (percentile / 100) * (size - 1)
        if index.is_integer():
            return data[int(index)]
        else:
            lower = data[int(index)]
            upper = data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    async def export_har(self, filepath: str):
        """
        Export network data as HAR (HTTP Archive) format.
        
        Args:
            filepath: Path to save HAR file
        """
        # Get all performance data
        metrics = await self.get_metrics()
        
        har_data = {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "QPT Framework Browser Network Performance",
                    "version": "1.0"
                },
                "entries": []
            }
        }
        
        # Convert to HAR format
        for entry in metrics['detailed_requests']:
            har_entry = {
                "startedDateTime": datetime.fromtimestamp(self.start_time + entry['startTime'] / 1000).isoformat(),
                "time": entry['duration'],
                "request": {
                    "method": "GET",
                    "url": entry['name'],
                    "httpVersion": "HTTP/1.1",
                    "headers": [],
                    "queryString": [],
                    "headersSize": -1,
                    "bodySize": -1
                },
                "response": {
                    "status": 200,
                    "statusText": "OK",
                    "httpVersion": "HTTP/1.1",
                    "headers": [],
                    "content": {
                        "size": entry.get('transferSize', 0),
                        "mimeType": "application/octet-stream"
                    },
                    "redirectURL": "",
                    "headersSize": -1,
                    "bodySize": entry.get('transferSize', 0)
                },
                "cache": {},
                "timings": {
                    "dns": entry.get('domainLookupEnd', 0) - entry.get('domainLookupStart', 0),
                    "connect": entry.get('connectEnd', 0) - entry.get('connectStart', 0),
                    "ssl": entry.get('connectEnd', 0) - entry.get('secureConnectionStart', 0) if entry.get('secureConnectionStart', 0) > 0 else -1,
                    "send": 0,
                    "wait": entry.get('responseStart', 0) - entry.get('requestStart', 0),
                    "receive": entry.get('responseEnd', 0) - entry.get('responseStart', 0)
                }
            }
            har_data['log']['entries'].append(har_entry)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(har_data, f, indent=2)
    
    async def print_summary(self):
        """Print a formatted summary of network performance."""
        metrics = await self.get_metrics()
        
        print("\n" + "="*60)
        print("BROWSER NETWORK PERFORMANCE SUMMARY")
        print("="*60)
        
        print(f"\n📊 Request Summary:")
        print(f"  Total Requests: {metrics['summary']['total_requests']}")
        print(f"  Successful: {metrics['summary']['successful_requests']}")
        print(f"  Failed: {metrics['summary']['failed_requests']}")
        print(f"  Success Rate: {metrics['summary']['success_rate']*100:.2f}%")
        print(f"  Cached: {metrics['summary']['cached_requests']}")
        
        print(f"\n📦 Data Transfer:")
        print(f"  Total Size: {metrics['summary']['total_size_mb']:.2f} MB")
        print(f"  Encoded Size: {metrics['summary']['total_encoded_size_kb']:.2f} KB")
        print(f"  Decoded Size: {metrics['summary']['total_decoded_size_kb']:.2f} KB")
        print(f"  Compression Ratio: {metrics['summary']['compression_ratio_percent']:.2f}%")
        
        print(f"\n⏱️  Timing Metrics:")
        print(f"  Average Duration: {metrics['timing']['avg_duration_ms']:.2f} ms")
        print(f"  Min Duration: {metrics['timing']['min_duration_ms']:.2f} ms")
        print(f"  Max Duration: {metrics['timing']['max_duration_ms']:.2f} ms")
        print(f"  P50: {metrics['timing']['p50_ms']:.2f} ms")
        print(f"  P95: {metrics['timing']['p95_ms']:.2f} ms")
        print(f"  P99: {metrics['timing']['p99_ms']:.2f} ms")
        
        print(f"\n📑 By Resource Type:")
        for res_type, data in metrics['by_resource_type'].items():
            print(f"  {res_type}:")
            print(f"    Count: {data['count']}")
            print(f"    Total Size: {data['total_size']/1024:.2f} KB")
            print(f"    Avg Duration: {data['total_duration']/data['count']:.2f} ms")
        
        print(f"\n🔢 Status Codes:")
        for status, count in metrics['status_codes'].items():
            print(f"  {status}: {count}")
        
        # Show slowest requests
        slowest = await self.get_slowest_requests(5)
        print(f"\n🐌 Top 5 Slowest Requests:")
        for i, req in enumerate(slowest, 1):
            print(f"  {i}. {req['name'][:60]}...")
            print(f"     Duration: {req['duration']:.2f} ms, Size: {req.get('transferSize', 0)/1024:.2f} KB")
        
        print("\n" + "="*60 + "\n")


# Example usage
async def example_usage():
    """Example of how to use BrowserNetworkPerformance."""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Create performance monitor
        perf = BrowserNetworkPerformance(page)
        
        # Start monitoring
        await perf.start_monitoring()
        
        # Perform UI actions
        await page.goto("https://example.com")
        await page.wait_for_load_state("networkidle")
        
        # Stop monitoring
        await perf.stop_monitoring()
        
        # Get and print metrics
        await perf.print_summary()
        
        # Get specific data
        metrics = await perf.get_metrics()
        waterfall = await perf.get_waterfall_data()
        slowest = await perf.get_slowest_requests(10)
        largest = await perf.get_largest_requests(10)
        
        # Export HAR
        await perf.export_har("network_performance.har")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
