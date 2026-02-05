"""
Unified YAML Test Definition Loader

Loads and executes unified test definitions that combine Playwright, k6, and JMeter tests.
"""

import yaml
import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .unified_runner import UnifiedTestRunner
from .unified_report_generator import UnifiedReportGenerator
from .test_definition_loader import PerformanceTestRunner
from .metrics_collector import MetricsCollector
from src.agents import AgentRegistry, AgentConfig, AgentType, AgentMode, AgentHealthMonitor

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
        
        # Initialize results storage
        self.test_results = {
            'workflow_results': [],
            'k6_results': [],
            'jmeter_results': [] 
        }
        
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
    
    def _extract_method_from_file(self, file_path: Path, method_name: str) -> str:
        """
        Extract a method and its dependencies from a Python file.
        
        This is a simple extraction that gets the entire file content
        and wraps the method call. For more complex scenarios, you might
        want to use AST parsing.
        
        Args:
            file_path: Path to the Python file
            method_name: Name of the method to extract
            
        Returns:
            Python code string with the method and a call to it
        """
        try:
            content = file_path.read_text()
            
            # Simple approach: Include entire file + call the method
            # This ensures all dependencies are available
            wrapper_code = f"""
# Auto-loaded from {file_path.name}
{content}

# Execute the method
result = {method_name}(context)
"""
            return wrapper_code
        except Exception as e:
            logger.error(f"Failed to extract method '{method_name}' from {file_path}: {e}")
            return ""
    
    def _generate_code_for_action(self, action: str, step: dict) -> str:
        """
        Auto-generate Python code for standard actions when running on remote agents.
        
        This allows actions like k6_test, api_call, etc. to run on remote agents
        without requiring explicit code.
        
        Args:
            action: Action type (api_call, k6_test, jmeter_test, etc.)
            step: Step configuration dictionary
            
        Returns:
            Python code string to execute on agent
        """
        try:
            if action == 'api_call':
                # Generate code for API call
                url = step.get('url', '')
                method = step.get('method', 'GET')
                body = step.get('body')
                headers = step.get('headers', {})
                
                code = f"""
import requests
import time
import json

url = context.get('url', '{url}')
method = context.get('method', '{method}')
body = context.get('body', {json.dumps(body)})
headers = context.get('headers', {json.dumps(headers)})

start = time.time()
try:
    if method.upper() == 'GET':
        response = requests.get(url, headers=headers, timeout=30)
    elif method.upper() == 'POST':
        response = requests.post(url, json=body, headers=headers, timeout=30)
    elif method.upper() == 'PUT':
        response = requests.put(url, json=body, headers=headers, timeout=30)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, headers=headers, timeout=30)
    else:
        response = requests.request(method, url, json=body, headers=headers, timeout=30)
    
    duration = time.time() - start
    
    result = {{
        'duration': duration,
        'status_code': response.status_code,
        'success': 200 <= response.status_code < 300,
        'url': url,
        'method': method
    }}
except Exception as e:
    result = {{
        'duration': time.time() - start,
        'status_code': 0,
        'success': False,
        'error': str(e),
        'url': url,
        'method': method
    }}
"""
                return code
            
            elif action == 'k6_test':
                # Generate code to run k6 on remote agent
                k6_config = step.get('k6_config', {})
                scenarios = k6_config.get('scenarios', [])
                options = k6_config.get('options', {})
                
                # Check for external script file
                k6_script_file = step.get('k6_script_file')
                script_content = ""
                if k6_script_file:
                    path = Path(k6_script_file)
                    if not path.is_absolute():
                        path = Path(self.yaml_file).parent / k6_script_file
                    if path.exists():
                        script_content = path.read_text()
                
                # Build the JS script part
                if not script_content:
                    js_lines = [
                        "import http from 'k6/http';",
                        "import { check } from 'k6';",
                        f"export let options = {json.dumps(options)};",
                        "export default function() {"
                    ]
                    for scenario in scenarios:
                        name = scenario.get('name', 'request')
                        method = scenario.get('method', 'get').lower()
                        url = scenario.get('url', '')
                        js_lines.append(f"  // {name}")
                        js_lines.append(f"  let res = http.{method}('{url}');")
                        js_lines.append("  check(res, { 'status is 200': (r) => r.status === 200 });")
                    js_lines.append("}")
                    script_content = "\n".join(js_lines)

                # Now build the Python code that runs k6
                py_code = [
                    "import subprocess",
                    "import time",
                    "import json",
                    "import tempfile",
                    "import os",
                    f"k6_script_content = {json.dumps(script_content)}",
                    "",
                    "with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:",
                    "    f.write(k6_script_content)",
                    "    script_path = f.name",
                    "",
                    "start = time.time()",
                    "try:",
                    "    proc = subprocess.run(['k6', 'run', '--summary-export', '/tmp/k6_summary.json', script_path], capture_output=True, text=True, timeout=300)",
                    "    duration = time.time() - start",
                    "    metrics = {}",
                    "    try:",
                    "        if os.path.exists('/tmp/k6_summary.json'):",
                    "            with open('/tmp/k6_summary.json', 'r') as sf:",
                    "                metrics = json.load(sf).get('metrics', {})",
                    "    except: pass",
                    "    result = {",
                    "        'duration': duration,",
                    "        'success': proc.returncode == 0,",
                    "        'output': proc.stdout,",
                    "        'error': proc.stderr if proc.returncode != 0 else None,",
                    "        'tool': 'k6',",
                    "        'metrics': metrics",
                    "    }",
                    "except Exception as e:",
                    "    result = { 'duration': time.time() - start, 'success': False, 'error': str(e) }",
                    "finally:",
                    "    if os.path.exists(script_path): os.unlink(script_path)",
                    "    if os.path.exists('/tmp/k6_summary.json'): os.unlink('/tmp/k6_summary.json')"
                ]
                return "\n".join(py_code)
            
            elif action == 'jmeter_test':
                # Generate code to run JMeter on remote agent
                jmeter_config = step.get('jmeter_config', {})
                scenarios = jmeter_config.get('scenarios', [])
                tg_config = jmeter_config.get('thread_group_config', {})
                
                # Check for external JMX file
                jmx_file = step.get('jmx_file')
                jmx_content = ""
                if jmx_file:
                    path = Path(jmx_file)
                    if not path.is_absolute():
                        path = Path(self.yaml_file).parent / jmx_file
                    if path.exists():
                        jmx_content = path.read_text()

                if not jmx_content:
                    # Build JMX
                    threads = tg_config.get('threads', 1)
                    ramp = tg_config.get('ramp_time', 1)
                    duration = tg_config.get('duration', 60)
                    jmx_lines = [
                        '<?xml version="1.0" encoding="UTF-8"?>',
                        '<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">',
                        '  <hashTree>',
                        '    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="API Load Test"/>',
                        '    <hashTree>',
                        '      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Users">',
                        f'        <intProp name="ThreadGroup.num_threads">{threads}</intProp>',
                        f'        <intProp name="ThreadGroup.ramp_time">{ramp}</intProp>',
                        f'        <longProp name="ThreadGroup.duration">{duration}</longProp>',
                        '        <boolProp name="ThreadGroup.scheduler">true</boolProp>',
                        '        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">',
                        '          <boolProp name="LoopController.continue_forever">false</boolProp>',
                        '          <intProp name="LoopController.loops">-1</intProp>',
                        '        </elementProp>',
                        '      </ThreadGroup>',
                        '      <hashTree>'
                    ]
                    for scenario in scenarios:
                        s_name = scenario.get('name', 'Request')
                        url = scenario.get('url', '')
                        method = scenario.get('method', 'GET').upper()
                        domain = url.split('//')[-1].split('/')[0]
                        path = "/" + "/".join(url.split('//')[-1].split('/')[1:])
                        proto = 'https' if 'https' in url else 'http'
                        jmx_lines.extend([
                            f'        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{s_name}">',
                            f'          <stringProp name="HTTPSampler.domain">{domain}</stringProp>',
                            f'          <stringProp name="HTTPSampler.path">{path}</stringProp>',
                            f'          <stringProp name="HTTPSampler.method">{method}</stringProp>',
                            f'          <stringProp name="HTTPSampler.protocol">{proto}</stringProp>',
                            '        </HTTPSamplerProxy>',
                            '        <hashTree/>'
                        ])
                    jmx_lines.extend([
                        '      </hashTree>',
                        '    </hashTree>',
                        '  </hashTree>',
                        '</jmeterTestPlan>'
                    ])
                    jmx_content = "\n".join(jmx_lines)

                py_code = [
                    "import subprocess",
                    "import time",
                    "import json",
                    "import tempfile",
                    "import os",
                    f"jmx_content_to_run = {json.dumps(jmx_content)}",
                    "",
                    "with tempfile.NamedTemporaryFile(mode='w', suffix='.jmx', delete=False) as f:",
                    "    f.write(jmx_content_to_run)",
                    "    jmx_path = f.name",
                    "results_path = jmx_path.replace('.jmx', '.jtl')",
                    "",
                    "jmeter_bin = '/home/ubuntu/jmeter-agent/apache-jmeter-5.6.3/bin/jmeter'",
                    "if not os.path.exists(jmeter_bin): jmeter_bin = 'jmeter'",
                    "",
                    "start = time.time()",
                    "try:",
                    "    proc = subprocess.run([jmeter_bin, '-n', '-t', jmx_path, '-l', results_path], capture_output=True, text=True, timeout=600)",
                    "    duration = time.time() - start",
                    "    total_reqs = 0",
                    "    success_reqs = 0",
                    "    if os.path.exists(results_path):",
                    "        with open(results_path, 'r') as rf:",
                    "            lines = rf.readlines()[1:]",
                    "            total_reqs = len(lines)",
                    "            success_reqs = sum(1 for l in lines if ',true,' in l or l.endswith(',true'))",
                    "    result = {",
                    "        'duration': duration,",
                    "        'success': proc.returncode == 0,",
                    "        'total_requests': total_reqs,",
                    "        'successful_requests': success_reqs,",
                    "        'tool': 'jmeter',",
                    "        'output': proc.stdout,",
                    "        'error': proc.stderr if proc.returncode != 0 else None",
                    "    }",
                    "except Exception as e:",
                    "    result = { 'duration': time.time() - start, 'success': False, 'error': str(e) }",
                    "finally:",
                    "    if os.path.exists(jmx_path): os.unlink(jmx_path)",
                    "    if os.path.exists(results_path): os.unlink(results_path)"
                ]
                return "\n".join(py_code)
            
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Failed to generate code for action '{action}': {e}")
            return ""


    
    def _extract_inline_tags(self) -> Dict[str, List[str]]:
        """
        Extract tags from inline YAML comments.
        Format: key: value # tag1, tag2
        
        Returns:
            Dict mapping workflow/test names to list of tags.
        """
        tag_map = {}
        try:
            import re
            content = self.yaml_file.read_text()
            
            # Regex to capture: key: ... # tags
            # Matches: "  workflow_name: # sanity, load"
            # We assume unique keys for workflows
            pattern = re.compile(r'^\s*([\w\-]+):\s*.*#\s*(.*)$', re.MULTILINE)
            
            for match in pattern.finditer(content):
                key = match.group(1).strip()
                tag_str = match.group(2).strip()
                if tag_str:
                    tags = [t.strip().lower() for t in tag_str.split(',') if t.strip()]
                    tag_map[key] = tags
                    
            return tag_map
        except Exception as e:
            logger.warning(f"Failed to extract inline tags: {e}")
            return {}

    async def run_all_tests(self, include_tags: set = None, exclude_tags: set = None) -> Dict:
        """
        Run all tests defined in the YAML file.
        
        Args:
            include_tags: Set of tags to include (if None, include all)
            exclude_tags: Set of tags to exclude
            
        Returns:
            Dictionary with all test results
        """
        logger.info(f"Running unified test suite: {self.test_info.get('test_suite_name', 'Unnamed')}")
        
        # Parse tags
        self.workflow_tags = self._extract_inline_tags()
        
        # 1. IMPLICIT PREREQUISITE: Agent Health Check and Discovery
        await self._ensure_agents_healthy()
        
        # Start continuous health monitoring for agents
        if self.agent_registry.list_agents():
            self.health_monitor = AgentHealthMonitor(self.agent_registry)
            await self.health_monitor.start()
            logger.info(f"Started continuous health monitoring for {len(self.agent_registry.list_agents())} agents")
        
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
                await self._run_workflows(include_tags, exclude_tags)
            
            # Generate reports
            return await self._generate_reports()
        
        finally:
            # Cleanup: Stop health monitoring and close agent connections
            if self.health_monitor:
                await self.health_monitor.stop()
            await self.agent_registry.cleanup()
            logger.info("Agent connections closed")
        
    async def _ensure_agents_healthy(self):
        """Check health of all agents. Attempt deployment if metadata is provided."""
        logger.info("🔍 Verifying agent health prerequisites...")
        registry = self.agent_registry
        agents_list = registry.list_agents()
        
        if not agents_list:
            logger.info("No remote agents defined.")
            return

        for agent_id in agents_list:
            client = await registry.get_client(agent_id)
            is_healthy = await client.health_check()
            
            if not is_healthy:
                logger.warning(f"⚠️ Agent '{agent_id}' is offline at {client.config.endpoint}")
                
                # Check for deployment info
                agent_def = self.definition.get('agents', {}).get(agent_id, {})
                deploy_info = agent_def.get('deploy_info')
                
                if deploy_info:
                    logger.info(f"🚀 Attempting auto-deployment for agent '{agent_id}'...")
                    await self._deploy_agent(agent_id, deploy_info)
                    
                    # Re-check health after deployment (with retries)
                    success = False
                    for i in range(5):
                        await asyncio.sleep(5)
                        if await client.health_check():
                            logger.info(f"✅ Agent '{agent_id}' is now online and healthy.")
                            success = True
                            break
                        logger.info(f"   Waiting for agent '{agent_id}' to come online... ({i+1}/5)")
                    
                    if not success:
                        raise RuntimeError(f"CRITICAL: Agent '{agent_id}' failed to start after auto-deployment.")
                else:
                    raise RuntimeError(f"CRITICAL: Agent '{agent_id}' is unreachable and no 'deploy_info' provided in YAML.")
            else:
                logger.debug(f"✅ Agent '{agent_id}' is healthy.")

    async def _deploy_agent(self, agent_id: str, deploy_info: Dict):
        """Provisions and deploys an agent based on deploy_info."""
        try:
            from src.agents.provisioner import AgentProvisioner, DeploymentMethod
            from src.agents.deployer import AgentDeployer, DeploymentTarget
            
            agent_def = self.definition.get('agents', {}).get(agent_id, {})
            
            # 1. Provision (Create package)
            provisioner = AgentProvisioner()
            method_str = deploy_info.get('type', 'shell').lower()
            method_map = {
                'docker': DeploymentMethod.DOCKER,
                'shell': DeploymentMethod.SHELL,
                'systemd': DeploymentMethod.SYSTEMD
            }
            method = method_map.get(method_str, DeploymentMethod.SHELL)
            
            # Agent server config
            agent_config = {
                'name': agent_id,
                'auth_token': deploy_info.get('auth_token', agent_def.get('auth_token', 'default_token')),
                'mode': 'serve',
                'port': 5007  # Match framework expectation
            }
            
            package_dir = provisioner.create_agent(agent_id, method, agent_config)
            logger.info(f"   Package created at: {package_dir}")
            
            # 2. Deploy
            deployer = AgentDeployer()
            target_str = deploy_info.get('target') # e.g. "ubuntu@172.31.128.182"
            ssh_key = deploy_info.get('ssh_key')
            target = DeploymentTarget.from_string(target_str, ssh_key)
            
            remote_dir = deploy_info.get('remote_dir', f'/home/ubuntu/{agent_id}')
            
            success = await deployer.deploy(
                agent_id,
                package_dir,
                target,
                method,
                remote_dir
            )
            
            if not success:
                raise RuntimeError("Deployment script failed.")
                
        except Exception as e:
            logger.error(f"Failed to deploy agent '{agent_id}': {e}")
            raise

    async def _run_workflows(self, include_tags: set = None, exclude_tags: set = None):
        """Run workflows from YAML definition with Parallel Group support and Tag Filtering."""
        logger.info("Running workflows...")
        
        import aiohttp
        from examples.run_workflow_test import execute_api_call
        from src.aggregators.selective_iteration_aggregator import aggregate_selective_iterations
        from itertools import groupby
        
        all_workflows = self.definition.get('workflows', {})
        
        # FILTER WORKFLOWS BASED ON TAGS
        workflows = {}
        for name, config in all_workflows.items():
            tags = set(self.workflow_tags.get(name, []))
            
            # Check Include
            if include_tags and not tags.intersection(include_tags):
                # If include_tags is specified, but no intersection, skip
                continue
                
            # Check Exclude
            if exclude_tags and tags.intersection(exclude_tags):
                continue
                
            workflows[name] = config
            # Attach tags to config for reporting
            config['tags'] = list(tags)

        if not workflows:
            logger.warning("No workflows matched the tag criteria.")
            print("⚠️ No workflows matched the tag criteria.")
            return

        # 1. Group Workflows by 'group' attribute for parallel execution
        # Logic: Contiguous workflows with the same group ID run in parallel. 
        # Workflows without a group run sequentially.
        
        workflow_items = list(workflows.items())
        
        # Helper to get group key
        def get_wf_group(item):
            # item is (name, config)
            return item[1].get('group')
        
        # Iterate through grouped workflows
        for group_id, group_iterator in groupby(workflow_items, key=get_wf_group):
            group_list = list(group_iterator) # [(name, config), ...]
            
            if group_id:
                # Parallel Workflows
                print(f"\n⚡ Executing Workflow Group: '{group_id}' ({len(group_list)} workflows)")
                tasks = []
                for wf_name, wf_config in group_list:
                    tasks.append(self._execute_single_workflow(wf_name, wf_config, session_factory=aiohttp.ClientSession))
                
                await asyncio.gather(*tasks)
            else:
                # Sequential Workflows (No Group)
                for wf_name, wf_config in group_list:
                    async with aiohttp.ClientSession() as session:
                        await self._execute_single_workflow(wf_name, wf_config, session=session)
            
    async def _execute_single_workflow(self, workflow_name: str, workflow_config: Dict, session=None, session_factory=None):
        """Execute a single workflow logic (extracted from _run_workflows)."""
        from examples.run_workflow_test import execute_api_call
        from src.aggregators.selective_iteration_aggregator import aggregate_selective_iterations
        from itertools import groupby
        
        logger.info(f"Running workflow: {workflow_name}")
        print(f"\n📊 Running workflow: {workflow_name}")
        
        workflow_results = []
        iterations = int(workflow_config.get('iterations', 1))
        
        # Manage session lifecycle
        local_session = False
        if session is None and session_factory:
            session = session_factory()
            local_session = True
            await session.__aenter__()
            
        try:
            for i in range(iterations):
                print(f"\n🔄 Workflow '{workflow_name}' Iteration {i+1}/{iterations}")
                iteration_steps_results = []
                steps = workflow_config.get('steps', [])
                
                # 2. Group Steps within Workflow
                def get_step_group(step): 
                    return step.get('group')

                for group_id, step_iterator in groupby(steps, key=get_step_group):
                    step_group = list(step_iterator)
                    
                    if group_id:
                        # Parallel Steps
                        print(f"  ⚡ Executing Step Group: '{group_id}' ({len(step_group)} steps)")
                        tasks = []
                        for step in step_group:
                            # Mark as parallel execution for logging suppression/prefixing
                            step['_parallel_context'] = True
                            tasks.append(self._execute_step(step, session, i))
                        
                        group_results = await asyncio.gather(*tasks)
                        # Filter out None results
                        iteration_steps_results.extend([r for r in group_results if r])
                    
                    else:
                        # Sequential Steps
                        for step in step_group:
                            result = await self._execute_step(step, session, i)
                            if result:
                                iteration_steps_results.append(result)

                workflow_results.append({
                    'workflow_num': i,
                    'iteration': i,
                    'duration': sum(s['total_duration'] for s in iteration_steps_results),
                    'total_duration': sum(s['total_duration'] for s in iteration_steps_results),
                    'steps': iteration_steps_results
                })
        
        finally:
            if local_session and session:
                await session.__aexit__(None, None, None)

        # Aggregate and store
        aggregated = aggregate_selective_iterations(workflow_results, {})
        self.test_results['workflow_results'].append(aggregated)
        
        # Add to runner.results for reporting
        if 'workflows' not in self.unified_runner.results:
            self.unified_runner.results['workflows'] = []
            
        workflow_data = {
            'name': workflow_config.get('name', workflow_name),
            'tags': workflow_config.get('tags', []),
            'total_workflows': iterations,
            'workflow_summary': aggregated.get('workflow_summary', {}),
            'step_breakdown': aggregated.get('step_breakdown', {}),
            'workflow_executions': workflow_results
        }
        self.unified_runner.results['workflows'].append(workflow_data)

    async def _execute_step(self, step: Dict, session: Any, workflow_iteration: int) -> Optional[Dict]:
        """Execute a single workflow step."""
        step_name = step.get('name', 'unnamed_step')
        action = step.get('action', 'custom')
        agent_id = step.get('agent')
        step_iterations = int(step.get('iterations', 1))
        
        # Determine execution location
        exec_location = f"agent:{agent_id}" if agent_id else "local"
        # Only print if not running in parallel (to avoid console scramble), or prefix
        # For now, simplistic logging
        if not step.get('_parallel_context'):
             print(f"  Executing step: {step_name} ({action}) on {exec_location}")
        
        step_results = []
        
        if agent_id:
            # REMOTE EXECUTION
            code = step.get('code', '')
            code_file = step.get('code_file')
            context = step.get('context', {})
            tags = step.get('tags', {})
            timeout = step.get('timeout')
            
            # Smart resolution
            if not code and not code_file:
                # Reuse the extraction logic (simplified for brevity here, ideally shared)
                yaml_dir = Path(self.yaml_file).parent
                perf_scripts = yaml_dir / "performance_scripts.py"
                
                if perf_scripts.exists() and f"def {step_name}(" in perf_scripts.read_text():
                     code = self._extract_method_from_file(perf_scripts, step_name)
                
                if not code:
                    agent_script = yaml_dir / "agent_scripts" / f"{step_name}.py"
                    if agent_script.exists():
                        code = agent_script.read_text()
                
                if not code and action != 'custom':
                    code = self._generate_code_for_action(action, step)
                
                if not code:
                    logger.error(f"No code found for step '{step_name}'")
                    return None

            elif code_file and not code:
                # Load from file
                code_path = Path(code_file)
                if not code_path.is_absolute():
                     code_path = Path(self.yaml_file).parent / code_file
                if code_path.exists():
                    code = code_path.read_text()
            
            # Execute on agent
            try:
                client = await self.agent_registry.get_client(agent_id)
                for j in range(step_iterations):
                    start_t = time.time()
                    result = await client.execute(
                        code=code,
                        context={**context, 'action': action, 'step_config': step},
                        tags={**tags, 'step': step_name, 'iteration': str(j)},
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
                step_results.append({'duration': 0, 'success': False, 'error': str(e)})

        else:
            # LOCAL EXECUTION
            if action == 'api_call':
                for j in range(step_iterations):
                    # Re-import locally if needed or reuse execute_api_call
                    from examples.run_workflow_test import execute_api_call
                    res = await execute_api_call(session, step.get('url'), step.get('method', 'GET'), step.get('body'), step.get('headers'))
                    step_results.append(res)
            
            elif action == 'k6_test':
                k6_conf = step.get('k6_config', {})
                for j in range(step_iterations):
                    start_t = time.time()
                    k6_res = await self.unified_runner.run_k6_test(f"{step_name}_{workflow_iteration}_{j}", k6_conf.get('scenarios', []), k6_conf.get('options', {}))
                    step_results.append({'duration': time.time() - start_t, 'success': k6_res['status']=='success', 'data': k6_res})
                    
            elif action == 'jmeter_test':
                jm_conf = step.get('jmeter_config', {})
                for j in range(step_iterations):
                    start_t = time.time()
                    jm_res = await self.unified_runner.run_jmeter_test(f"{step_name}_{workflow_iteration}_{j}", jm_conf.get('scenarios', []), jm_conf.get('thread_group_config', {}))
                    step_results.append({'duration': time.time() - start_t, 'success': jm_res['status']=='success', 'data': jm_res})

        # Summarize results
        total_duration = sum(r['duration'] for r in step_results)
        success_count = sum(1 for r in step_results if r['success'])
        
        return {
            'name': step_name,
            'agent': agent_id or 'local',
            'iterations': step_iterations,
            'total_duration': total_duration,
            'success_rate': success_count / step_iterations if step_iterations > 0 else 0,
            'iteration_results': step_results
        }
            
    
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
