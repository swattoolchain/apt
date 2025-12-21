"""
k6 Integration for Performance Testing

Convert performance test definitions to k6 scripts and import k6 results.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class K6Integration:
    """Integration with k6 load testing tool."""
    
    @staticmethod
    def generate_k6_script(
        test_name: str,
        scenarios: List[Dict[str, Any]],
        options: Optional[Dict] = None
    ) -> str:
        """
        Generate k6 JavaScript test script from test definition.
        
        Args:
            test_name: Name of the test
            scenarios: List of test scenarios
            options: k6 options (VUs, duration, etc.)
            
        Returns:
            k6 JavaScript code as string
        """
        default_options = {
            'vus': 10,
            'duration': '30s',
            'thresholds': {
                'http_req_duration': ['p(95)<500'],
                'http_req_failed': ['rate<0.01']
            }
        }
        
        options = {**default_options, **(options or {})}
        
        script = f'''// k6 load test script generated from {test_name}
import http from 'k6/http';
import {{ check, sleep }} from 'k6';
import {{ Rate, Trend }} from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTrend = new Trend('response_time');

// Test configuration
export const options = {json.dumps(options, indent=2)};

'''
        
        # Generate scenario functions
        for i, scenario in enumerate(scenarios):
            script += K6Integration._generate_scenario_function(scenario, i)
        
        # Generate main test function
        script += '''
export default function() {
    // Execute scenarios
'''
        
        for i in range(len(scenarios)):
            script += f'    scenario_{i}();\n'
        
        script += '''    
    sleep(1);
}
'''
        
        return script
    
    @staticmethod
    def _generate_scenario_function(scenario: Dict[str, Any], index: int) -> str:
        """Generate k6 function for a scenario."""
        name = scenario.get('name', f'scenario_{index}')
        url = scenario.get('url', '')
        method = scenario.get('method', 'GET').upper()
        headers = scenario.get('headers', {})
        body = scenario.get('body')
        
        func = f'''
function scenario_{index}() {{
    // {name}
    const params = {{
        headers: {json.dumps(headers, indent=8)},
        tags: {{ name: '{name}' }}
    }};
    
'''
        
        if method == 'GET':
            func += f"    const response = http.get('{url}', params);\n"
        elif method == 'POST':
            body_str = json.dumps(body) if body else 'null'
            func += f"    const response = http.post('{url}', {body_str}, params);\n"
        elif method == 'PUT':
            body_str = json.dumps(body) if body else 'null'
            func += f"    const response = http.put('{url}', {body_str}, params);\n"
        elif method == 'DELETE':
            func += f"    const response = http.del('{url}', null, params);\n"
        
        func += '''    
    // Validate response
    const result = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500
    });
    
    errorRate.add(!result);
    responseTrend.add(response.timings.duration);
}
'''
        
        return func
    
    @staticmethod
    def save_k6_script(script: str, output_path: str):
        """Save k6 script to file."""
        Path(output_path).write_text(script)
        logger.info(f"k6 script saved to {output_path}")
    
    @staticmethod
    def parse_k6_results(results_file: str) -> Dict[str, Any]:
        """
        Parse k6 JSON results file (NDJSON format).
        
        k6 outputs NDJSON (newline-delimited JSON) where each line is a separate JSON object.
        The last line typically contains the summary metrics.
        
        Args:
            results_file: Path to k6 JSON output file
            
        Returns:
            Parsed results dictionary
        """
        try:
            # k6 outputs NDJSON - read all lines and parse the last one (summary)
            with open(results_file) as f:
                lines = f.readlines()
            
            # Find the last non-empty line (usually the summary)
            data = None
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if 'metrics' in data:  # Found the summary
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not data or 'metrics' not in data:
                return {'error': 'No valid k6 summary found in results file'}
            
            metrics = data.get('metrics', {})
            
            parsed = {
                'test_name': 'k6_test',
                'metrics': {},
                'summary': {}
            }
            
            # Extract key metrics
            if 'http_req_duration' in metrics:
                duration_data = metrics['http_req_duration']
                parsed['metrics']['http_req_duration'] = {
                    'avg': duration_data.get('avg'),
                    'min': duration_data.get('min'),
                    'max': duration_data.get('max'),
                    'p50': duration_data.get('p(50)'),
                    'p90': duration_data.get('p(90)'),
                    'p95': duration_data.get('p(95)'),
                    'p99': duration_data.get('p(99)')
                }
            
            if 'http_reqs' in metrics:
                parsed['metrics']['total_requests'] = metrics['http_reqs'].get('count')
                parsed['metrics']['requests_per_second'] = metrics['http_reqs'].get('rate')
            
            if 'http_req_failed' in metrics:
                parsed['metrics']['error_rate'] = metrics['http_req_failed'].get('rate')
            
            if 'vus' in metrics:
                parsed['metrics']['vus_max'] = metrics['vus'].get('max')
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing k6 results: {e}")
            return {'error': str(e)}


class JMeterIntegration:
    """Integration with Apache JMeter."""
    
    @staticmethod
    def generate_jmx(
        test_name: str,
        scenarios: List[Dict[str, Any]],
        thread_group_config: Optional[Dict] = None,
        plugin: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate JMeter JMX test plan.
        
        Args:
            test_name: Name of the test
            scenarios: List of test scenarios
            thread_group_config: Thread group configuration
            plugin: Plugin name (e.g., 'grpc', 'mqtt') if using a plugin
            plugin_config: Plugin-specific configuration
            
        Returns:
            JMX XML as string
        """
        # If plugin is specified, use plugin generator
        if plugin:
            from .jmeter_plugins import JMeterPluginSupport
            plugin_support = JMeterPluginSupport()
            return JMeterIntegration._generate_plugin_jmx(
                test_name, plugin, plugin_config or {}, thread_group_config, plugin_support
            )
        
        # Standard HTTP sampler generation
        default_config = {
            'num_threads': 10,
            'ramp_time': 10,
            'duration': 60,
            'loops': 1
        }
        
        config = {**default_config, **(thread_group_config or {})}
        
        jmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{test_name}" enabled="true">
      <stringProp name="TestPlan.comments">Generated performance test plan</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">{config['num_threads']}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">{config['ramp_time']}</stringProp>
        <longProp name="ThreadGroup.duration">{config['duration']}</longProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">{config['loops']}</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
'''
        
        # Add HTTP samplers for each scenario
        for scenario in scenarios:
            jmx += JMeterIntegration._generate_http_sampler(scenario)
        
        # Add listeners
        jmx += '''
        <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time>
              <latency>true</latency>
              <timestamp>true</timestamp>
              <success>true</success>
              <label>true</label>
              <code>true</code>
              <message>true</message>
              <threadName>true</threadName>
              <dataType>true</dataType>
              <encoding>false</encoding>
              <assertions>true</assertions>
              <subresults>true</subresults>
              <responseData>false</responseData>
              <samplerData>false</samplerData>
              <xml>false</xml>
              <fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders>
              <requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave>
              <bytes>true</bytes>
              <sentBytes>true</sentBytes>
              <url>true</url>
              <threadCounts>true</threadCounts>
              <idleTime>true</idleTime>
              <connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename">results.jtl</stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
'''
        
        return jmx
    
    @staticmethod
    def _generate_plugin_jmx(
        test_name: str,
        plugin: str,
        plugin_config: Dict[str, Any],
        thread_group_config: Optional[Dict],
        plugin_support
    ) -> str:
        """Generate JMX with plugin sampler"""
        default_config = {
            'num_threads': 10,
            'ramp_time': 10,
            'duration': 60,
            'loops': 1
        }
        
        config = {**default_config, **(thread_group_config or {})}
        
        # Validate plugin config
        is_valid, errors = plugin_support.validate_plugin_config(plugin, plugin_config)
        if not is_valid:
            raise ValueError(f"Invalid plugin configuration: {', '.join(errors)}")
        
        # Generate plugin sampler XML
        plugin_sampler = plugin_support.generate_plugin_sampler(
            plugin, f"{plugin} Request", plugin_config
        )
        
        jmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
<TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{test_name}" enabled="true">
  <stringProp name="TestPlan.comments">Generated {plugin} test plan</stringProp>
  <boolProp name="TestPlan.functional_mode">false</boolProp>
  <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
  <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
    <collectionProp name="Arguments.arguments"/>
  </elementProp>
</TestPlan>
<hashTree>
  <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
    <stringProp name="ThreadGroup.num_threads">{config['num_threads']}</stringProp>
    <stringProp name="ThreadGroup.ramp_time">{config['ramp_time']}</stringProp>
    <longProp name="ThreadGroup.duration">{config['duration']}</longProp>
    <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
    <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
      <boolProp name="LoopController.continue_forever">false</boolProp>
      <stringProp name="LoopController.loops">{config['loops']}</stringProp>
    </elementProp>
  </ThreadGroup>
  <hashTree>
{plugin_sampler}
    <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
      <boolProp name="ResultCollector.error_logging">false</boolProp>
      <objProp>
        <name>saveConfig</name>
        <value class="SampleSaveConfiguration">
          <time>true</time>
          <latency>true</latency>
          <timestamp>true</timestamp>
          <success>true</success>
          <label>true</label>
          <code>true</code>
          <message>true</message>
          <threadName>true</threadName>
          <dataType>true</dataType>
          <encoding>false</encoding>
          <assertions>true</assertions>
          <subresults>true</subresults>
          <responseData>false</responseData>
          <samplerData>false</samplerData>
          <xml>false</xml>
          <fieldNames>true</fieldNames>
          <responseHeaders>false</responseHeaders>
          <requestHeaders>false</requestHeaders>
          <responseDataOnError>false</responseDataOnError>
          <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
          <assertionsResultsToSave>0</assertionsResultsToSave>
          <bytes>true</bytes>
          <sentBytes>true</sentBytes>
          <url>true</url>
          <threadCounts>true</threadCounts>
          <idleTime>true</idleTime>
          <connectTime>true</connectTime>
        </value>
      </objProp>
      <stringProp name="filename">results.jtl</stringProp>
    </ResultCollector>
    <hashTree/>
  </hashTree>
</hashTree>
  </hashTree>
</jmeterTestPlan>
'''
        return jmx
    
    @staticmethod
    def _generate_http_sampler(scenario: Dict[str, Any]) -> str:
        """Generate JMeter HTTP sampler XML."""
        name = scenario.get('name', 'HTTP Request')
        url = scenario.get('url', '')
        method = scenario.get('method', 'GET')
        
        # Parse URL
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        sampler = f'''
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">{parsed.netloc}</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">{parsed.scheme}</stringProp>
          <stringProp name="HTTPSampler.path">{parsed.path}</stringProp>
          <stringProp name="HTTPSampler.method">{method}</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
        </HTTPSamplerProxy>
        <hashTree/>
'''
        
        return sampler
    
    @staticmethod
    def save_jmx(jmx: str, output_path: str):
        """Save JMeter JMX file."""
        Path(output_path).write_text(jmx)
        logger.info(f"JMeter JMX saved to {output_path}")
    
    @staticmethod
    def parse_jtl_results(jtl_file: str) -> Dict[str, Any]:
        """
        Parse JMeter JTL results file (CSV format).
        
        Args:
            jtl_file: Path to JTL file
            
        Returns:
            Parsed results dictionary
        """
        try:
            import csv
            
            results = {
                'samples': [],
                'summary': {}
            }
            
            with open(jtl_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results['samples'].append({
                        'timestamp': int(row.get('timeStamp', 0)),
                        'elapsed': int(row.get('elapsed', 0)),
                        'label': row.get('label', ''),
                        'success': row.get('success', 'true') == 'true',
                        'bytes': int(row.get('bytes', 0))
                    })
            
            # Calculate summary
            if results['samples']:
                elapsed_times = [s['elapsed'] for s in results['samples']]
                success_count = len([s for s in results['samples'] if s['success']])
                
                results['summary'] = {
                    'total_samples': len(results['samples']),
                    'success_count': success_count,
                    'error_count': len(results['samples']) - success_count,
                    'success_rate': success_count / len(results['samples']),
                    'avg_response_time': sum(elapsed_times) / len(elapsed_times),
                    'min_response_time': min(elapsed_times),
                    'max_response_time': max(elapsed_times)
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing JTL results: {e}")
            return {'error': str(e)}
