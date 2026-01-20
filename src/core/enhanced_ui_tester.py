"""
Enhanced UI Performance Tester with Granular Point-to-Point Tracking

Provides detailed step-by-step performance measurement for workflows.
"""

from typing import List, Dict, Any, Callable, Optional
from playwright.async_api import Page
import time
import logging

from .ui_performance_tester import UIPerformanceTester
from .base_performance_tester import PerformanceMetrics, PerformanceConfig

logger = logging.getLogger(__name__)


class EnhancedUIPerformanceTester(UIPerformanceTester):
    """Enhanced UI Performance Tester with granular step tracking."""
    
    async def measure_workflow_steps(
        self,
        workflow_steps: List[Dict[str, Any]],
        test_name: str,
        iteration: int = 0,
        user_id: int = 0
    ) -> PerformanceMetrics:
        """
        Measure performance of individual workflow steps with point-to-point timing.
        
        Args:
            workflow_steps: List of dicts with 'name' and 'action' (async function)
            test_name: Name of the test
            iteration: Iteration number
            user_id: User ID for concurrent testing
            
        Returns:
            PerformanceMetrics with detailed step-by-step timing
            
        Example:
            async def step1(page):
                await page.goto("https://example.com")
            
            async def step2(page):
                await page.fill('input', 'value')
            
            steps = [
                {'name': 'navigate', 'action': step1},
                {'name': 'fill_form', 'action': step2}
            ]
            
            metrics = await tester.measure_workflow_steps(steps, "my_workflow")
        """
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time(),
            iteration=iteration,
            user_id=user_id
        )
        
        step_timings = []
        cumulative_time = 0
        
        try:
            # Clear existing performance marks
            await self.page.evaluate('performance.clearMarks(); performance.clearMeasures();')
            
            for i, step in enumerate(workflow_steps):
                step_name = step['name']
                step_action = step['action']
                
                # Browser performance marks
                mark_start = f"{step_name}-start"
                mark_end = f"{step_name}-end"
                
                # Mark start in browser
                await self.page.evaluate(f'performance.mark("{mark_start}")')
                
                # Execute step with timing
                step_start = time.time()
                try:
                    result = await step_action(self.page)
                    step_duration = time.time() - step_start
                    cumulative_time += step_duration
                    
                    # Mark end in browser
                    await self.page.evaluate(f'performance.mark("{mark_end}")')
                    
                    # Create browser measure
                    await self.page.evaluate(f'''
                        performance.measure("{step_name}", "{mark_start}", "{mark_end}")
                    ''')
                    
                    # Store step timing
                    step_timings.append({
                        'step': step_name,
                        'duration': step_duration,
                        'cumulative_time': cumulative_time,
                        'order': i,
                        'status': 'success',
                        'result': str(result) if result else None
                    })
                    
                    logger.debug(f"Step '{step_name}' completed in {step_duration:.3f}s")
                    
                    # Take screenshot if enabled
                    if self.config.screenshots:
                        await self.take_screenshot(f"{test_name}_step_{i}_{step_name}", metrics)
                    
                except Exception as step_error:
                    step_duration = time.time() - step_start
                    step_timings.append({
                        'step': step_name,
                        'duration': step_duration,
                        'cumulative_time': cumulative_time + step_duration,
                        'order': i,
                        'status': 'failed',
                        'error': str(step_error)
                    })
                    logger.error(f"Step '{step_name}' failed: {step_error}")
                    metrics.add_error(f"Step '{step_name}' failed: {step_error}")
            
            # Get all browser measures
            browser_measures = await self.page.evaluate('''() => {
                return performance.getEntriesByType('measure').map(m => ({
                    name: m.name,
                    duration: m.duration,
                    startTime: m.startTime
                }));
            }''')
            
            # Store comprehensive metrics
            metrics.metrics['step_timings'] = step_timings
            metrics.metrics['browser_measures'] = browser_measures
            metrics.metrics['total_workflow_time'] = cumulative_time
            metrics.metrics['total_steps'] = len(workflow_steps)
            metrics.metrics['successful_steps'] = len([s for s in step_timings if s['status'] == 'success'])
            metrics.metrics['failed_steps'] = len([s for s in step_timings if s['status'] == 'failed'])
            
            # Calculate step statistics
            successful_durations = [s['duration'] for s in step_timings if s['status'] == 'success']
            if successful_durations:
                metrics.metrics['avg_step_duration'] = sum(successful_durations) / len(successful_durations)
                metrics.metrics['max_step_duration'] = max(successful_durations)
                metrics.metrics['min_step_duration'] = min(successful_durations)
            
        except Exception as e:
            error_msg = f"Error in workflow measurement: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
        finally:
            metrics.finalize()
            self.add_result(metrics)
        
        return metrics
    
    async def measure_with_custom_marks(
        self,
        action_func: Callable,
        marks: List[str],
        test_name: str,
        iteration: int = 0,
        user_id: int = 0
    ) -> PerformanceMetrics:
        """
        Measure action with custom performance marks for granular tracking.
        
        Args:
            action_func: Async function that sets performance marks
            marks: List of mark names to measure between
            test_name: Name of the test
            iteration: Iteration number
            user_id: User ID
            
        Returns:
            PerformanceMetrics with custom mark measurements
            
        Example:
            async def my_action(page):
                await page.evaluate('performance.mark("start")')
                await page.goto("https://example.com")
                await page.evaluate('performance.mark("loaded")')
                await page.click('button')
                await page.evaluate('performance.mark("clicked")')
            
            metrics = await tester.measure_with_custom_marks(
                my_action,
                marks=['start', 'loaded', 'clicked'],
                test_name="custom_marks_test"
            )
        """
        metrics = PerformanceMetrics(
            test_name=test_name,
            start_time=time.time(),
            iteration=iteration,
            user_id=user_id
        )
        
        try:
            # Clear existing marks
            await self.page.evaluate('performance.clearMarks(); performance.clearMeasures();')
            
            # Execute action
            await action_func(self.page)
            
            # Create measures between consecutive marks
            for i in range(len(marks) - 1):
                mark_start = marks[i]
                mark_end = marks[i + 1]
                measure_name = f"{mark_start}_to_{mark_end}"
                
                await self.page.evaluate(f'''
                    performance.measure("{measure_name}", "{mark_start}", "{mark_end}")
                ''')
            
            # Get all marks and measures
            performance_data = await self.page.evaluate('''() => {
                return {
                    marks: performance.getEntriesByType('mark').map(m => ({
                        name: m.name,
                        startTime: m.startTime
                    })),
                    measures: performance.getEntriesByType('measure').map(m => ({
                        name: m.name,
                        duration: m.duration,
                        startTime: m.startTime
                    }))
                };
            }''')
            
            metrics.metrics['custom_marks'] = performance_data['marks']
            metrics.metrics['custom_measures'] = performance_data['measures']
            
        except Exception as e:
            error_msg = f"Error in custom marks measurement: {str(e)}"
            metrics.add_error(error_msg)
            logger.error(error_msg)
        finally:
            metrics.finalize()
            self.add_result(metrics)
        
        return metrics
