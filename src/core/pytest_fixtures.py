"""
Pytest Fixtures for Performance Testing

Provides fixtures and hooks for performance testing integration.
"""

import pytest
import asyncio
import yaml
import logging
from pathlib import Path
from typing import Generator, Dict, Any
import webbrowser

from scripts.performance.base_performance_tester import PerformanceConfig
from scripts.performance.ui_performance_tester import UIPerformanceTester
from scripts.performance.api_performance_tester import APIPerformanceTester
from scripts.performance.metrics_collector import MetricsCollector
from scripts.performance.report_generator import PerformanceReportGenerator

logger = logging.getLogger(__name__)


# Session-scoped metrics collector
_session_metrics_collector = None
_session_config = None


def get_performance_config() -> PerformanceConfig:
    """
    Load performance test configuration.
    
    Returns:
        PerformanceConfig instance
    """
    global _session_config
    
    if _session_config is not None:
        return _session_config
    
    config_path = Path("config/performance_config.yml")
    
    if config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
            
            # Merge UI and API configs
            perf_config = config_data.get('performance', {})
            ui_config = perf_config.get('ui', {})
            api_config = perf_config.get('api', {})
            reporting_config = perf_config.get('reporting', {})
            thresholds = perf_config.get('thresholds', {})
            
            # Create config
            _session_config = PerformanceConfig(
                concurrent_users=ui_config.get('concurrent_users', 5),
                iterations=ui_config.get('iterations', 3),
                headless=ui_config.get('headless', False),
                browser_name=ui_config.get('browser_name', 'chromium'),
                viewport=ui_config.get('viewport'),
                timeout=ui_config.get('timeout', 60000),
                screenshots=ui_config.get('screenshots', True),
                traces=ui_config.get('traces', True),
                videos=ui_config.get('videos', False),
                api_timeout=api_config.get('timeout', 30),
                output_dir=reporting_config.get('output_dir', 'performance_results'),
                generate_html=reporting_config.get('generate_html', True),
                generate_json=reporting_config.get('generate_json', True),
                open_browser=reporting_config.get('open_browser', False),
                thresholds=thresholds
            )
            
            logger.info("Performance config loaded from file")
    else:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        _session_config = PerformanceConfig()
    
    return _session_config


def get_metrics_collector() -> MetricsCollector:
    """
    Get or create session metrics collector.
    
    Returns:
        MetricsCollector instance
    """
    global _session_metrics_collector
    
    if _session_metrics_collector is None:
        _session_metrics_collector = MetricsCollector()
    
    return _session_metrics_collector


@pytest.fixture(scope="session")
def performance_config() -> PerformanceConfig:
    """Fixture for performance configuration."""
    return get_performance_config()


@pytest.fixture(scope="session")
def metrics_collector() -> MetricsCollector:
    """Fixture for metrics collector."""
    return get_metrics_collector()


@pytest.fixture
async def ui_perf_tester(
    performance_config: PerformanceConfig,
    metrics_collector: MetricsCollector
) -> Generator[UIPerformanceTester, None, None]:
    """
    Fixture providing UIPerformanceTester instance.
    
    Args:
        performance_config: Performance configuration
        metrics_collector: Metrics collector
        
    Yields:
        UIPerformanceTester instance
    """
    tester = UIPerformanceTester(performance_config)
    await tester.setup()
    
    yield tester
    
    # Collect metrics
    metrics_collector.add_multiple_metrics(tester.get_results())
    
    # Teardown
    await tester.teardown(trace_name=f"ui_test_{id(tester)}")


@pytest.fixture
async def api_perf_tester(
    performance_config: PerformanceConfig,
    metrics_collector: MetricsCollector
) -> Generator[APIPerformanceTester, None, None]:
    """
    Fixture providing APIPerformanceTester instance.
    
    Args:
        performance_config: Performance configuration
        metrics_collector: Metrics collector
        
    Yields:
        APIPerformanceTester instance
    """
    tester = APIPerformanceTester(performance_config)
    await tester.setup()
    
    yield tester
    
    # Collect metrics
    metrics_collector.add_multiple_metrics(tester.get_results())
    
    # Teardown
    await tester.teardown()


def generate_performance_report():
    """Generate performance report at end of session."""
    collector = get_metrics_collector()
    config = get_performance_config()
    
    if not collector.all_metrics:
        logger.info("No performance metrics collected, skipping report generation")
        return
    
    # Generate reports
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(config.output_dir) / f"test_run_{timestamp}"
    
    generator = PerformanceReportGenerator(collector, config, output_dir)
    
    if config.generate_html:
        html_report = generator.generate_html_report()
        logger.info(f"HTML report generated: {html_report}")
        
        if config.open_browser:
            webbrowser.open(f"file://{html_report.absolute()}")
    
    if config.generate_json:
        json_report = generator.generate_json_report()
        logger.info(f"JSON report generated: {json_report}")
