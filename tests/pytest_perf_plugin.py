"""
Pytest plugin for running YAML-based performance test definitions.

Usage:
    pytest tests/performance/definitions/ -v
    pytest tests/performance/definitions/ui_grid_performance.yml -v
    pytest tests/performance/definitions/ --perf-tags=smoke,p1 -v
"""

import pytest
import asyncio
from pathlib import Path
import yaml
import logging

from performance.test_definition_loader import PerformanceTestRunner
from performance.unified_yaml_loader import UnifiedYAMLTestRunner

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--perf-tags",
        action="store",
        default="",
        help="Run only tests with these tags (comma-separated)"
    )
    parser.addoption(
        "--perf-exclude-tags",
        action="store",
        default="",
        help="Exclude tests with these tags (comma-separated)"
    )


def pytest_collect_file(parent, file_path):
    """Collect YAML test definition files."""
    # Collect from tests/definitions, examples, etc.
    if file_path.suffix == ".yml":
        parent_name = file_path.parent.name
        allowed_parents = {"definitions", "yaml_definitions", "examples", "advanced_scenarios"}
        if parent_name in allowed_parents:
            return YAMLTestFile.from_parent(parent, path=file_path)


class YAMLTestFile(pytest.File):
    """Represents a YAML test definition file."""
    
    def collect(self):
        """Collect test items from YAML file."""
        with open(self.path) as f:
            definition = yaml.safe_load(f)
        
        test_info = definition.get('test_info', {})
        test_type = test_info.get('test_suite_type', 'ui_performance')
        
        # Check if this is a unified test (multi-tool)
        if test_type == 'unified':
            # Create single test item for unified test
            yield UnifiedYAMLTestItem.from_parent(
                self,
                name=test_info.get('test_suite_name', 'unified_test'),
                definition=definition
            )
        else:
            # Regular performance test - collect scenarios
            scenarios = definition.get('scenarios', {})
            
            # Get tag filters from command line
            include_tags = self.config.getoption("--perf-tags")
            exclude_tags = self.config.getoption("--perf-exclude-tags")
            
            include_tags = set(include_tags.split(',')) if include_tags else set()
            exclude_tags = set(exclude_tags.split(',')) if exclude_tags else set()
            
            # Create test items for each scenario
            for scenario_name, scenario_def in scenarios.items():
                # Extract tags from scenario name
                tags = set()
                if '#' in scenario_name:
                    name_part, tags_part = scenario_name.split('#', 1)
                    scenario_name = name_part.strip()
                    tags = set(tag.strip() for tag in tags_part.split(','))
                
                # Apply tag filtering
                if include_tags and not tags.intersection(include_tags):
                    continue
                if exclude_tags and tags.intersection(exclude_tags):
                    continue
                
                yield YAMLTestItem.from_parent(
                    self,
                    name=scenario_name,
                    definition=definition,
                    scenario_name=scenario_name,
                    scenario_def=scenario_def
                )


class YAMLTestItem(pytest.Item):
    """Represents a single test scenario from YAML."""
    
    def __init__(self, name, parent, definition, scenario_name, scenario_def):
        super().__init__(name, parent)
        self.definition = definition
        self.scenario_name = scenario_name
        self.scenario_def = scenario_def
    
    def runtest(self):
        """Run the test scenario."""
        # Run async test
        asyncio.run(self._run_async())
    
    async def _run_async(self):
        """Run test asynchronously."""
        runner = PerformanceTestRunner(self.path)
        
        # Run only this specific scenario
        await runner.run_scenario(self.scenario_name, self.scenario_def)
        
        # Check if test passed
        results = runner.metrics_collector.all_metrics
        if not all(m.is_successful() for m in results):
            raise AssertionError(f"Performance test '{self.scenario_name}' failed")
    
    def repr_failure(self, excinfo):
        """Represent test failure."""
        return f"Performance test failed: {excinfo.value}"
    
    def reportinfo(self):
        """Report test info."""
        return self.path, 0, f"perf: {self.name}"


class UnifiedYAMLTestItem(pytest.Item):
    """Represents a unified multi-tool test from YAML."""
    
    def __init__(self, name, parent, definition):
        super().__init__(name, parent)
        self.definition = definition
    
    def runtest(self):
        """Run the unified test."""
        asyncio.run(self._run_async())
    
    async def _run_async(self):
        """Run unified test asynchronously."""
        runner = UnifiedYAMLTestRunner(self.path)
        results = await runner.run_all_tests()
        
        if results['status'] != 'completed':
            raise AssertionError(f"Unified test failed: {results.get('error', 'Unknown error')}")
        
        # Print report location
        if results.get('unified_report'):
            print(f"\n✅ Unified Report: {results['unified_report']}")
    
    def repr_failure(self, excinfo):
        """Represent test failure."""
        return f"Unified test failed: {excinfo.value}"
    
    def reportinfo(self):
        """Report test info."""
        return self.path, 0, f"unified: {self.name}"


def pytest_sessionfinish(session, exitstatus):
    """Generate consolidated report after all tests."""
    if hasattr(session.config, '_perf_results'):
        # Generate HTML report
        output_dir = Path("performance_results")
        # ... generate report
        pass
        # Generate report
        from datetime import datetime
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("performance_results") / f"test_run_{timestamp}"
        
        # Use default config for report generation
        from performance.base_performance_tester import PerformanceConfig
        config = PerformanceConfig()
        
        generator = PerformanceReportGenerator(collector, config, output_dir)
        
        if config.generate_html:
            html_report = generator.generate_html_report()
            print(f"\n📊 Performance Report: {html_report}")
        
        if config.generate_json:
            json_report = generator.generate_json_report()
            print(f"📄 JSON Report: {json_report}")
