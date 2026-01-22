"""
Performance Test Definition Loader

Loads and executes performance tests from YAML definition files.
Supports scenario-level configuration and multiple test scenarios.
"""

import yaml
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import replace

from .base_performance_tester import PerformanceConfig
from .ui_performance_tester import UIPerformanceTester
from .api_performance_tester import APIPerformanceTester, APIRequest
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class PerformanceTestDefinition:
    """Represents a performance test definition from YAML."""
    
    def __init__(self, definition_path: Path):
        """
        Initialize test definition.
        
        Args:
            definition_path: Path to YAML definition file
        """
        self.definition_path = definition_path
        self.definition = self._load_definition()
        self.test_info = self.definition.get('test_info', {})
        self.scenarios = self.definition.get('scenarios', {})
        self.global_config = self.definition.get('performance_config', {})
    
    def _load_definition(self) -> Dict[str, Any]:
        """Load YAML definition file."""
        with open(self.definition_path) as f:
            return yaml.safe_load(f)
    
    def get_test_name(self) -> str:
        """Get test suite name."""
        return self.test_info.get('test_suite_name', self.definition_path.stem)
    
    def get_test_type(self) -> str:
        """Get test type (ui_performance or api_performance)."""
        return self.test_info.get('test_suite_type', 'ui_performance')
    
    def get_scenarios(self, include_tags: Optional[List[str]] = None, 
                     exclude_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get filtered scenarios based on tags.
        
        Args:
            include_tags: Tags to include
            exclude_tags: Tags to exclude
            
        Returns:
            Filtered scenarios dictionary
        """
        filtered = {}
        
        for scenario_name, scenario_data in self.scenarios.items():
            # Parse tags from scenario name comment
            tags = self._parse_tags(scenario_name)
            
            # Filter by tags
            if include_tags and not any(tag in tags for tag in include_tags):
                continue
            if exclude_tags and any(tag in tags for tag in exclude_tags):
                continue
            
            filtered[scenario_name] = scenario_data
        
        return filtered
    
    def _parse_tags(self, scenario_name: str) -> List[str]:
        """Parse tags from scenario name (e.g., 'scenario_name #tag1, tag2')."""
        if '#' in scenario_name:
            tags_part = scenario_name.split('#')[1]
            return [tag.strip() for tag in tags_part.split(',')]
        return []
    
    def get_scenario_config(self, scenario_name: str, scenario_data: List[Dict]) -> PerformanceConfig:
        """
        Build PerformanceConfig for a specific scenario.
        
        Args:
            scenario_name: Name of the scenario
            scenario_data: Scenario data from YAML
            
        Returns:
            PerformanceConfig instance
        """
        # Start with global config
        config_dict = self.global_config.copy()
        
        # Override with scenario-specific config if present
        for step in scenario_data:
            for action_name, action_data in step.items():
                if 'performance_config' in action_data:
                    scenario_config = action_data['performance_config']
                    config_dict.update(scenario_config)
                    break
        
        # Build PerformanceConfig
        return self._build_config_from_dict(config_dict)
    
    def _build_config_from_dict(self, config_dict: Dict[str, Any]) -> PerformanceConfig:
        """Build PerformanceConfig from dictionary."""
        ui_config = config_dict.get('ui', {})
        api_config = config_dict.get('api', {})
        reporting_config = config_dict.get('reporting', {})
        thresholds = config_dict.get('thresholds', {})
        
        return PerformanceConfig(
            concurrent_users=ui_config.get('concurrent_users', 5),
            iterations=ui_config.get('iterations', 3),
            ramp_up_time=ui_config.get('ramp_up_time', 0),
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


class PerformanceTestRunner:
    """Executes performance tests from YAML definitions."""
    
    def __init__(self, definition: PerformanceTestDefinition, metrics_collector: MetricsCollector):
        """
        Initialize test runner.
        
        Args:
            definition: Test definition
            metrics_collector: Metrics collector
        """
        self.definition = definition
        self.collector = metrics_collector
    
    async def run_ui_scenario(
        self, 
        scenario_name: str, 
        scenario_data: List[Dict],
        config: PerformanceConfig
    ) -> None:
        """
        Run a UI performance scenario.
        
        Args:
            scenario_name: Name of the scenario
            scenario_data: Scenario steps from YAML
            config: Performance configuration
        """
        logger.info(f"Running UI scenario: {scenario_name}")
        
        # Create tester
        tester = UIPerformanceTester(config)
        await tester.setup()
        
        try:
            # Execute each step in the scenario
            for step in scenario_data:
                for action_name, action_data in step.items():
                    await self._execute_ui_action(
                        tester, 
                        action_name, 
                        action_data, 
                        scenario_name,
                        config
                    )
            
            # Collect metrics
            self.collector.add_multiple_metrics(tester.get_results())
            
        finally:
            # Teardown
            trace_name = f"{scenario_name}_{id(tester)}"
            await tester.teardown(trace_name=trace_name)
    
    async def _execute_ui_action(
        self,
        tester: UIPerformanceTester,
        action_name: str,
        action_data: Dict[str, Any],
        scenario_name: str,
        config: PerformanceConfig
    ) -> None:
        """Execute a single UI action."""
        
        if action_name == 'measure_page_load':
            # Measure page load
            url = action_data.get('url')
            wait_until = action_data.get('wait_until', 'networkidle')
            iterations = action_data.get('iterations', config.iterations)
            
            for iteration in range(iterations):
                await tester.measure_page_load(
                    url=url,
                    test_name=f"{scenario_name}_{action_name}",
                    wait_until=wait_until,
                    iteration=iteration,
                    user_id=0
                )
        
        elif action_name == 'measure_action':
            # Measure custom action
            # This would need to be implemented based on your specific actions
            logger.warning(f"Custom action '{action_name}' not yet implemented")
        
        else:
            logger.warning(f"Unknown UI action: {action_name}")
    
    async def run_api_scenario(
        self,
        scenario_name: str,
        scenario_data: List[Dict],
        config: PerformanceConfig
    ) -> None:
        """
        Run an API performance scenario.
        
        Args:
            scenario_name: Name of the scenario
            scenario_data: Scenario steps from YAML
            config: Performance configuration
        """
        logger.info(f"Running API scenario: {scenario_name}")
        
        # Create tester
        tester = APIPerformanceTester(config)
        await tester.setup()
        
        try:
            # Execute each step in the scenario
            for step in scenario_data:
                for action_name, action_data in step.items():
                    await self._execute_api_action(
                        tester,
                        action_name,
                        action_data,
                        scenario_name,
                        config
                    )
            
            # Collect metrics
            self.collector.add_multiple_metrics(tester.get_results())
            
        finally:
            await tester.teardown()
    
    async def _execute_api_action(
        self,
        tester: APIPerformanceTester,
        action_name: str,
        action_data: Dict[str, Any],
        scenario_name: str,
        config: PerformanceConfig
    ) -> None:
        """Execute a single API action."""
        
        if action_name == 'measure_request':
            # Single API request
            request = APIRequest(
                url=action_data.get('url'),
                method=action_data.get('method', 'GET'),
                headers=action_data.get('headers'),
                body=action_data.get('body'),
                params=action_data.get('params')
            )
            
            iterations = action_data.get('iterations', config.iterations)
            
            for iteration in range(iterations):
                await tester.measure_request(
                    request=request,
                    test_name=f"{scenario_name}_{action_name}",
                    iteration=iteration,
                    user_id=0
                )
        
        elif action_name == 'measure_concurrent':
            # Concurrent requests
            request = APIRequest(
                url=action_data.get('url'),
                method=action_data.get('method', 'GET'),
                headers=action_data.get('headers'),
                body=action_data.get('body'),
                params=action_data.get('params')
            )
            
            concurrent_users = action_data.get('concurrent_users', config.concurrent_users)
            
            await tester.measure_concurrent_requests(
                request=request,
                concurrent_users=concurrent_users,
                test_name=f"{scenario_name}_concurrent",
                iteration=0
            )
        
        else:
            logger.warning(f"Unknown API action: {action_name}")
    
    async def run_all_scenarios(
        self,
        include_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None
    ) -> None:
        """
        Run all scenarios in the definition.
        
        Args:
            include_tags: Tags to include
            exclude_tags: Tags to exclude
        """
        scenarios = self.definition.get_scenarios(include_tags, exclude_tags)
        test_type = self.definition.get_test_type()
        
        for scenario_name, scenario_data in scenarios.items():
            # Get scenario-specific config
            config = self.definition.get_scenario_config(scenario_name, scenario_data)
            
            # Run based on test type
            if test_type == 'ui_performance':
                await self.run_ui_scenario(scenario_name, scenario_data, config)
            elif test_type == 'api_performance':
                await self.run_api_scenario(scenario_name, scenario_data, config)
            else:
                logger.error(f"Unknown test type: {test_type}")
