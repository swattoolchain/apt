"""
Unified YAML Test Definition Loader

Loads and executes unified test definitions that combine Playwright, k6, and JMeter tests.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from .unified_runner import UnifiedTestRunner
from .unified_report_generator import UnifiedReportGenerator
from .test_definition_loader import PerformanceTestRunner
from .metrics_collector import MetricsCollector
from .agents import AgentRegistry, AgentConfig, AgentType, AgentMode, AgentHealthMonitor

logger = logging.getLogger(__name__)


class UnifiedYAMLTestRunner:
    """Load and execute unified YAML test definitions."""
    
    def __init__(self, yaml_file: Path):
        """
        Initialize unified YAML test runner.
        
        Args:
            yaml_file: Path to YAML test definition
        """
        self.yaml_file = Path(yaml_file)
        self.definition = self._load_yaml()
        self.test_info = self.definition.get('test_info', {})
        self.reporting_config = self.definition.get('reporting', {})
        
        # Determine output directory
        self.output_dir = Path(self.reporting_config.get('output_dir', 'performance_results/unified_test'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.unified_runner = UnifiedTestRunner(self.output_dir)
        
        # Initialize agent registry and health monitor
        self.agent_registry = AgentRegistry()
        self.health_monitor = None
        self._load_agents()
    
    def _load_yaml(self) -> Dict:
        """Load YAML test definition."""
        with open(self.yaml_file) as f:
            return yaml.safe_load(f)
    
    def _load_agents(self):
        """Load and register agents from YAML definition."""
        agents_config = self.definition.get('agents', {})
        
        if not agents_config:
            return
        
        import os
        
        for agent_id, agent_def in agents_config.items():
            # Expand environment variables in endpoint and auth_token
            endpoint = agent_def.get('endpoint', '')
            endpoint = os.path.expandvars(endpoint)
            
            auth_token = agent_def.get('auth_token')
            if auth_token:
                auth_token = os.path.expandvars(auth_token)
            
            # Create agent config
            config = AgentConfig(
                agent_id=agent_id,
                type=AgentType.REMOTE,  # Browser agents in Phase 2
                endpoint=endpoint,
                mode=AgentMode.EMIT,  # Default, can be overridden
                auth_token=auth_token,
                timeout=agent_def.get('timeout', 300),
                health_check_interval=agent_def.get('health_check_interval', 60)
            )
            
            # Register agent
            self.agent_registry.register(config)
            logger.info(f"Registered agent: {agent_id} at {endpoint}")

    
    async def run_all_tests(self) -> Dict:
        """
        Run all tests defined in the YAML file.
        
        Returns:
            Dictionary with all test results
        """
        logger.info(f"Running unified test suite: {self.test_info.get('test_suite_name', 'Unnamed')}")
        
        # Start health monitoring for agents
        if self.agent_registry.list_agents():
            self.health_monitor = AgentHealthMonitor(self.agent_registry)
            await self.health_monitor.start()
            logger.info(f"Started health monitoring for {len(self.agent_registry.list_agents())} agents")
        
        try:
            # Determine which tools to run
            include_tools = self.reporting_config.get('include', ['playwright', 'k6', 'jmeter'])
            
            # Run UI tests (Playwright)
            if 'playwright' in include_tools and 'ui_tests' in self.definition:
                await self._run_playwright_tests()
            
            # Run k6 tests
            if 'k6' in include_tools and 'k6_tests' in self.definition:
                await self._run_k6_tests()
            
            if 'jmeter' in include_tools and 'jmeter_tests' in self.definition:
                await self._run_jmeter_tests()
            
            # Run Workflows
            if 'workflows' in self.definition:
                await self._run_workflows()
            
            # Generate reports
            return await self._generate_reports()
        
        finally:
            # Cleanup: Stop health monitoring and close agent connections
            if self.health_monitor:
                await self.health_monitor.stop()
            await self.agent_registry.cleanup()
            logger.info("Agent connections closed")
    
    async def _run_workflows(self):
        """Run workflows from YAML definition."""
        logger.info("Running workflows...")
        
        import aiohttp
        from examples.run_workflow_test import execute_api_call
        from custom_aggregators.selective_iteration_aggregator import aggregate_selective_iterations
        import time
        
        workflows = self.definition.get('workflows', {})
        
        for workflow_name, workflow_config in workflows.items():
            logger.info(f"Running workflow: {workflow_name}")
            print(f"\n📊 Running workflow: {workflow_name}")
            
            # Execute workflow iterations
            workflow_results = []
            iterations = int(workflow_config.get('iterations', 1))
            
            async with aiohttp.ClientSession() as session:
                for i in range(iterations):
                    print(f"\n🔄 Workflow Iteration {i+1}/{iterations}")
                    iteration_steps_results = []
                    
                    steps = workflow_config.get('steps', [])
                    for step in steps:
                        step_name = step.get('name', 'unnamed_step')
                        action = step.get('action', 'api_call')
                        step_iterations = int(step.get('iterations', 1))
                        
                        print(f"  Executing step: {step_name} ({action})")
                        
                        step_results = []
                        
                        # Handle different actions
                        if action == 'api_call':
                            url = step.get('url')
                            method = step.get('method', 'GET')
                            body = step.get('body')
                            headers = step.get('headers')
                            
                            for j in range(step_iterations):
                                result = await execute_api_call(
                                    session, url, method, body, headers
                                )
                                step_results.append(result)
                        
                        elif action == 'k6_test':
                            k6_config = step.get('k6_config', {})
                            scenarios = k6_config.get('scenarios', [])
                            options = k6_config.get('options', {})
                            
                            for j in range(step_iterations):
                                start_t = time.time()
                                k6_res = await self.unified_runner.run_k6_test(
                                    f"{step_name}_{i}_{j}", 
                                    scenarios, 
                                    options
                                )
                                duration = time.time() - start_t
                                step_results.append({
                                    'duration': duration,
                                    'success': k6_res['status'] == 'success',
                                    'data': k6_res
                                })

                        elif action == 'jmeter_test':
                            jmeter_config = step.get('jmeter_config', {})
                            scenarios = jmeter_config.get('scenarios', [])
                            tg_config = jmeter_config.get('thread_group_config', {})
                            
                            for j in range(step_iterations):
                                start_t = time.time()
                                jm_res = await self.unified_runner.run_jmeter_test(
                                    f"{step_name}_{i}_{j}",
                                    scenarios,
                                    tg_config
                                )
                                duration = time.time() - start_t
                                step_results.append({
                                    'duration': duration,
                                    'success': jm_res['status'] == 'success',
                                    'data': jm_res
                                })
                        
                        elif action == 'agent_execute':
                            # Execute code on remote agent
                            agent_id = step.get('agent')
                            code = step.get('code', '')
                            code_file = step.get('code_file')  # NEW: Support external files
                            language = step.get('language', 'python')  # NEW: Language support
                            context = step.get('context', {})
                            tags = step.get('tags', {})
                            timeout = step.get('timeout')
                            
                            if not agent_id:
                                logger.error(f"No agent specified for step: {step_name}")
                                continue
                            
                            # Load code from file if specified
                            if code_file:
                                code_path = Path(code_file)
                                if not code_path.is_absolute():
                                    # Resolve relative to YAML file directory
                                    yaml_dir = Path(self.yaml_file).parent
                                    code_path = yaml_dir / code_file
                                
                                if code_path.exists():
                                    code = code_path.read_text()
                                    logger.info(f"Loaded code from {code_path}")
                                else:
                                    logger.error(f"Code file not found: {code_path}")
                                    continue
                            
                            try:
                                client = await self.agent_registry.get_client(agent_id)
                                
                                for j in range(step_iterations):
                                    start_t = time.time()
                                    result = await client.execute(
                                        code=code,
                                        context=context,
                                        tags={**tags, 'step': step_name, 'iteration': str(j), 'language': language},
                                        timeout=timeout
                                    )
                                    duration = time.time() - start_t
                                    
                                    step_results.append({
                                        'duration': result.get('duration', duration),
                                        'success': result.get('status') != 'error',
                                        'data': result
                                    })
                            except Exception as e:
                                logger.error(f"Agent execution failed for {step_name}: {e}")
                                step_results.append({
                                    'duration': 0,
                                    'success': False,
                                    'error': str(e)
                                })
                        
                        elif action == 'agent_query':
                            # Query metrics from agent (serve mode)
                            agent_id = step.get('agent')
                            metric = step.get('metric')
                            timerange = step.get('timerange', 'last_1h')
                            filters = step.get('filters', {})
                            limit = step.get('limit', 1000)
                            
                            if not agent_id:
                                logger.error(f"No agent specified for step: {step_name}")
                                continue
                            
                            try:
                                client = await self.agent_registry.get_client(agent_id)
                                
                                start_t = time.time()
                                metrics = await client.query_metrics(
                                    metric=metric,
                                    timerange=timerange,
                                    filters=filters,
                                    limit=limit
                                )
                                duration = time.time() - start_t
                                
                                step_results.append({
                                    'duration': duration,
                                    'success': True,
                                    'data': {
                                        'metrics_count': len(metrics),
                                        'metrics': metrics
                                    }
                                })
                            except Exception as e:
                                logger.error(f"Agent query failed for {step_name}: {e}")
                                step_results.append({
                                    'duration': 0,
                                    'success': False,
                                    'error': str(e)
                                })

                        
                        # Calculate step stats
                        total_duration = sum(r['duration'] for r in step_results)
                        success_count = sum(1 for r in step_results if r['success'])
                        
                        iteration_steps_results.append({
                            'name': step_name,
                            'iterations': step_iterations,
                            'total_duration': total_duration,
                            'success_rate': success_count / step_iterations if step_iterations > 0 else 0,
                            'iteration_results': step_results
                        })

                        # Publish to InfluxDB
                        if self.unified_runner.influx_publisher:
                            self.unified_runner.influx_publisher.publish_metric(
                                "workflow_step", 
                                {
                                    "duration": total_duration, 
                                    "success_count": success_count,
                                    "total_count": step_iterations
                                }, 
                                {
                                    "step": step_name, 
                                    "workflow": workflow_name, 
                                    "action": action,
                                    "iteration": str(i)
                                }
                            )
                    
                    workflow_results.append({
                        'workflow_num': i,  # Required for report generator
                        'iteration': i,
                        'duration': sum(s['total_duration'] for s in iteration_steps_results),
                        'total_duration': sum(s['total_duration'] for s in iteration_steps_results),  # Added for aggregator
                        'steps': iteration_steps_results,
                        'success': all(s['success_rate'] == 1.0 for s in iteration_steps_results)
                    })
            
            print(f"✓ Workflow completed: {iterations} iterations")
            
            # Aggregate workflow results
            aggregated = aggregate_selective_iterations(workflow_results, {})
            
            workflow_data = {
                'name': workflow_config.get('name', workflow_name),
                'total_workflows': iterations,
                'workflow_summary': aggregated['workflow_summary'],
                'step_breakdown': aggregated['step_breakdown'],
                'workflow_executions': workflow_results
            }
            
            # Add to runner.results
            if 'workflows' not in self.unified_runner.results:
                self.unified_runner.results['workflows'] = []
            self.unified_runner.results['workflows'].append(workflow_data)
        
        logger.info("Workflows completed")
    
    async def _generate_reports(self) -> Dict:
        """Run Playwright UI tests from YAML definition."""
        logger.info("Running Playwright UI tests...")
        
        ui_tests = self.definition.get('ui_tests', {})
        
        # Use existing PerformanceTestRunner for Playwright tests
        # Create a temporary YAML with just UI tests
        temp_definition = {
            'test_info': self.test_info,
            'scenarios': ui_tests
        }
        
        # Save temp YAML
        temp_yaml = self.output_dir / "temp_ui_tests.yml"
        with open(temp_yaml, 'w') as f:
            yaml.dump(temp_definition, f)
        
        # Run using existing test runner
        runner = PerformanceTestRunner(temp_yaml)
        await runner.run_all_scenarios()
        
        # Collect results
        self.unified_runner.add_playwright_results(runner.metrics_collector)
        
        # Clean up temp file
        temp_yaml.unlink()
        
        logger.info("Playwright tests completed")
    
    async def _run_k6_tests(self):
        """Run k6 API tests from YAML definition."""
        logger.info("Running k6 API tests...")
        
        k6_tests = self.definition.get('k6_tests', {})
        
        for test_name, test_config in k6_tests.items():
            if test_config.get('tool') == 'k6':
                scenarios = test_config.get('scenarios', [])
                options = test_config.get('options', {})
                
                await self.unified_runner.run_k6_test(
                    test_name=test_name,
                    scenarios=scenarios,
                    options=options
                )
        
        logger.info("k6 tests completed")
    
    async def _run_jmeter_tests(self):
        """Run JMeter tests from YAML definition."""
        logger.info("Running JMeter tests...")
        
        jmeter_tests = self.definition.get('jmeter_tests', {})
        
        for test_name, test_config in jmeter_tests.items():
            if test_config.get('tool') == 'jmeter':
                scenarios = test_config.get('scenarios', [])
                thread_config = test_config.get('thread_group_config', {})
                
                await self.unified_runner.run_jmeter_test(
                    test_name=test_name,
                    scenarios=scenarios,
                    thread_group_config=thread_config
                )
        
        logger.info("JMeter tests completed")
    
    async def _generate_reports(self) -> Dict:
        """Generate unified and individual reports."""
        logger.info("Generating reports...")
        
        # Save raw results
        self.unified_runner.save_results()
        
        # Generate unified report
        if self.reporting_config.get('unified_report', True):
            report_gen = UnifiedReportGenerator(
                self.unified_runner.get_all_results(),
                self.output_dir
            )
            
            report_name = self.reporting_config.get('report_name', 'unified_performance_report.html')
            html_report = report_gen.generate_unified_html_report(report_name)
            
            logger.info(f"Unified report generated: {html_report}")
        
        # TODO: Generate individual tool reports if requested
        # if self.reporting_config.get('individual_reports', False):
        #     ...
        
        return {
            'status': 'completed',
            'output_dir': str(self.output_dir),
            'unified_report': str(self.output_dir / report_name) if self.reporting_config.get('unified_report', True) else None,
            'results': self.unified_runner.get_all_results()
        }


async def run_unified_yaml_test(yaml_file: Path) -> Dict:
    """
    Convenience function to run a unified YAML test.
    
    Args:
        yaml_file: Path to YAML test definition
        
    Returns:
        Test results dictionary
    """
    runner = UnifiedYAMLTestRunner(yaml_file)
    return await runner.run_all_tests()
