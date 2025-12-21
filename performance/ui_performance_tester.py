"""
UI Performance Testing Module

Provides UI-specific performance testing using Playwright.
Measures page load times, component rendering, network requests, and browser metrics.
"""

from typing import Optional, Dict, Any, Callable
from playwright.async_api import Page, Browser, BrowserContext, async_playwright
import asyncio
import time
import logging
from pathlib import Path

from .base_performance_tester import BasePerformanceTester, PerformanceMetrics, PerformanceConfig

logger = logging.getLogger(__name__)


class UIPerformanceTester(BasePerformanceTester):
    """UI Performance Tester using Playwright."""
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize UI performance tester.
        
        Args:
            config: Performance test configuration
        """
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    async def setup(self) -> None:
        """Setup browser and context."""
        self._playwright = await async_playwright().start()
        
        # Launch browser
        browser_type = getattr(self._playwright, self.config.browser_name)
        self.browser = await browser_type.launch(
            headless=self.config.headless,
            args=['--disable-gpu', '--no-sandbox']
        )
        
        # Create context
        context_options = {
            "viewport": self.config.viewport,
            "record_video_dir": str(self.videos_dir) if self.config.videos else None
        }
        
        self.context = await self.browser.new_context(**context_options)
        
        # Start tracing if enabled
        if self.config.traces:
            await self.context.tracing.start(
                screenshots=True,
                snapshots=True,
                sources=True
            )
        
        # Create page
        self.page = await self.context.new_page()
        
        logger.info(f"Browser setup complete: {self.config.browser_name}, headless={self.config.headless}")
    
    async def teardown(self, trace_name: Optional[str] = None) -> None:
        """
        Teardown browser and save traces.
        
        Args:
            trace_name: Name for the trace file
        """
        # Stop tracing if enabled
        if self.config.traces and self.context:
            trace_path = self.traces_dir / f"{trace_name or 'trace'}.zip"
            await self.context.tracing.stop(path=str(trace_path))
            logger.info(f"Trace saved to {trace_path}")
        
        # Close browser
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def capture_page_metrics(self, metrics: PerformanceMetrics) -> None:
        """
        Capture comprehensive page performance metrics.
        
        Args:
            metrics: PerformanceMetrics object to populate
        """
        if not self.page:
            logger.warning("No page available for metrics capture")
            return
        
        try:
            # Always get basic navigation timing (lightweight)
            navigation_timing = await self.page.evaluate('''() => {
                const timing = performance.timing || {};
                const navigationStart = timing.navigationStart || 0;
                return {
                    dns_lookup: timing.domainLookupEnd - timing.domainLookupStart,
                    tcp_connect: timing.connectEnd - timing.connectStart,
                    request_response: timing.responseEnd - timing.requestStart,
                    dom_loading: timing.domComplete - timing.domLoading,
                    dom_interactive: timing.domInteractive - navigationStart,
                    dom_content_loaded: timing.domContentLoadedEventEnd - navigationStart,
                    page_load: timing.loadEventEnd - navigationStart
                };
            }''')
            metrics.metrics['navigation_timing'] = navigation_timing
            
            # Skip heavy metrics in lightweight mode
            if self.config.lightweight_mode:
                logger.debug("Lightweight mode: skipping heavy metrics collection")
                return
            
            # Get resource timing (can be heavy with many resources)
            resource_timing = await self.page.evaluate('''() => {
                const resources = performance.getEntriesByType('resource') || [];
                return resources.map(r => ({
                    name: r.name,
                    duration: r.duration,
                    initiator_type: r.initiatorType,
                    transfer_size: r.transferSize || 0,
                    start_time: r.startTime,
                    response_end: r.responseEnd
                }));
            }''')
            metrics.metrics['resource_timing'] = resource_timing
            
            # Calculate total resource size
            total_size = sum(r.get('transfer_size', 0) for r in resource_timing)
            metrics.metrics['total_transfer_size'] = total_size
            
            # Get paint metrics
            paint_metrics = await self.page.evaluate('''() => {
                const entries = performance.getEntriesByType('paint') || [];
                const metrics = {};
                for (const entry of entries) {
                    metrics[entry.name] = entry.startTime;
                }
                return metrics;
            }''')
            metrics.metrics['paint_metrics'] = paint_metrics
            
            # Get memory metrics (Chrome only)
            try:
                memory = await self.page.evaluate('''() => {
                    const memory = window.performance.memory;
                    return memory ? {
                        used_js_heap_size: memory.usedJSHeapSize,
                        total_js_heap_size: memory.totalJSHeapSize,
                        js_heap_size_limit: memory.jsHeapSizeLimit
                    } : null;
                }''')
                if memory:
                    metrics.metrics['memory'] = {
                        'used_js_heap_size_mb': memory['used_js_heap_size'] / (1024 * 1024),
                        'total_js_heap_size_mb': memory['total_js_heap_size'] / (1024 * 1024),
                        'js_heap_size_limit_mb': memory['js_heap_size_limit'] / (1024 * 1024)
                    }
            except Exception as e:
                logger.debug(f"Memory metrics not available: {e}")
            
            # Get Core Web Vitals (can be slow)
            try:
                web_vitals = await self.page.evaluate('''() => {
                    return new Promise((resolve) => {
                        const vitals = {};
                        
                        // LCP - Largest Contentful Paint
                        const lcpObserver = new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            const lastEntry = entries[entries.length - 1];
                            vitals.lcp = lastEntry.renderTime || lastEntry.loadTime;
                        });
                        lcpObserver.observe({entryTypes: ['largest-contentful-paint']});
                        
                        // FID - First Input Delay
                        const fidObserver = new PerformanceObserver((list) => {
                            const entries = list.getEntries();
                            entries.forEach((entry) => {
                                vitals.fid = entry.processingStart - entry.startTime;
                            });
                        });
                        fidObserver.observe({entryTypes: ['first-input']});
                        
                        // CLS - Cumulative Layout Shift
                        let clsValue = 0;
                        const clsObserver = new PerformanceObserver((list) => {
                            for (const entry of list.getEntries()) {
                                if (!entry.hadRecentInput) {
                                    clsValue += entry.value;
                                }
                            }
                            vitals.cls = clsValue;
                        });
                        clsObserver.observe({entryTypes: ['layout-shift']});
                        
                        // Wait a bit for observers to collect data
                        setTimeout(() => {
                            resolve(vitals);
                        }, 1000);
                    });
                }''')
                metrics.metrics['web_vitals'] = web_vitals
            except Exception as e:
                logger.debug(f"Web vitals not available: {e}")
            
        except Exception as e:
            error_msg = f"Error capturing page metrics: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
    
    async def take_screenshot(self, step_name: str, metrics: Optional[PerformanceMetrics] = None) -> Optional[str]:
        """
        Take a screenshot and optionally add to metrics.
        
        Args:
            step_name: Name of the step
            metrics: Optional PerformanceMetrics to add screenshot to
            
        Returns:
            Path to screenshot file
        """
        if not self.config.screenshots or not self.page:
            return None
        
        try:
            screenshot_path = self.screenshots_dir / f"{step_name}_{int(time.time())}.png"
            await self.page.screenshot(path=str(screenshot_path), full_page=True)
            
            if metrics:
                metrics.add_screenshot(step_name, str(screenshot_path))
            
            logger.debug(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def measure_page_load(
        self, 
        url: str, 
        test_name: Optional[str] = None,
        wait_until: str = "networkidle",
        iteration: int = 0,
        user_id: int = 0
    ) -> PerformanceMetrics:
        """
        Measure page load performance.
        
        Args:
            url: URL to load
            test_name: Name of the test
            wait_until: Wait condition (load, domcontentloaded, networkidle)
            iteration: Iteration number
            user_id: User ID for concurrent testing
            
        Returns:
            PerformanceMetrics with page load data
        """
        if not test_name:
            test_name = f"page_load_{url.split('//')[-1].replace('/', '_')}"
        
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time(),
            iteration=iteration,
            user_id=user_id
        )
        
        try:
            # Setup network monitoring
            network_requests = []
            
            def handle_request(request):
                network_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "timestamp": time.time(),
                    "type": "request",
                    "resource_type": request.resource_type
                })
            
            def handle_response(response):
                network_requests.append({
                    "url": response.url,
                    "status": response.status,
                    "timestamp": time.time(),
                    "type": "response",
                    "headers": dict(response.headers)
                })
            
            self.page.on("request", handle_request)
            self.page.on("response", handle_response)
            
            # Navigate to page
            response = await self.page.goto(url, wait_until=wait_until, timeout=self.config.timeout)
            
            # Capture metrics
            await self.capture_page_metrics(metrics)
            
            # Store network requests
            metrics.network_requests = network_requests
            
            # Add response status
            if response:
                metrics.metadata['response_status'] = response.status
                metrics.metadata['response_url'] = response.url
            
            # Take screenshot
            await self.take_screenshot("page_loaded", metrics)
            
        except Exception as e:
            error_msg = f"Error measuring page load for {url}: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
        finally:
            metrics.finalize()
            self.add_result(metrics)
        
        return metrics
    
    async def measure_action(
        self,
        action_func: Callable,
        test_name: str,
        iteration: int = 0,
        user_id: int = 0,
        take_screenshots: bool = True
    ) -> PerformanceMetrics:
        """
        Measure performance of a custom action.
        
        Args:
            action_func: Async function to execute (receives self.page as argument)
            test_name: Name of the test
            iteration: Iteration number
            user_id: User ID for concurrent testing
            take_screenshots: Whether to take before/after screenshots
            
        Returns:
            PerformanceMetrics with action performance data
        """
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time(),
            iteration=iteration,
            user_id=user_id
        )
        
        try:
            # Take before screenshot
            if take_screenshots:
                await self.take_screenshot(f"{test_name}_before", metrics)
            
            # Execute action
            action_start = time.time()
            result = await action_func(self.page)
            action_duration = time.time() - action_start
            
            metrics.metrics['action_duration'] = action_duration
            metrics.metadata['action_result'] = str(result) if result else None
            
            # Wait for any pending updates
            await self.page.wait_for_timeout(500)
            
            # Capture metrics after action
            await self.capture_page_metrics(metrics)
            
            # Take after screenshot
            if take_screenshots:
                await self.take_screenshot(f"{test_name}_after", metrics)
            
        except Exception as e:
            error_msg = f"Error measuring action {test_name}: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
        finally:
            metrics.finalize()
            self.add_result(metrics)
        
        return metrics
