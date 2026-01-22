"""
Workflow Test Runner

Executes workflow tests with selective step iterations.
This is a simplified implementation to demonstrate the concept.
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, List, Any
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from custom_aggregators.selective_iteration_aggregator import aggregate_selective_iterations


async def execute_api_call(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    body: Dict = None,
    headers: Dict = None
) -> Dict[str, Any]:
    """Execute a single API call and measure performance"""
    start_time = time.time()
    
    try:
        async with session.request(method, url, json=body, headers=headers) as response:
            duration = time.time() - start_time
            data = await response.json() if response.content_type == 'application/json' else {}
            
            return {
                'duration': duration,
                'success': response.status < 400,
                'status_code': response.status,
                'response_data': data
            }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'duration': duration,
            'success': False,
            'error': str(e)
        }


async def execute_workflow_step(
    session: aiohttp.ClientSession,
    step: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a workflow step with its configured iterations"""
    step_name = step['name']
    iterations = step.get('iterations', 1)
    iteration_config = step.get('iteration_config', {})
    
    print(f"  Executing step: {step_name} ({iterations} iteration{'s' if iterations > 1 else ''})")
    
    iteration_results = []
    
    for i in range(iterations):
        # Execute the API call
        result = await execute_api_call(
            session,
            step['url'],
            step.get('method', 'GET'),
            step.get('body'),
            step.get('headers')
        )
        
        iteration_results.append(result)
        
        # Delay between iterations if configured
        if i < iterations - 1:
            delay = iteration_config.get('delay_between', 0)
            if delay > 0:
                await asyncio.sleep(delay)
        
        # Print progress for high-iteration steps
        if iterations > 10 and (i + 1) % 10 == 0:
            success_count = sum(1 for r in iteration_results if r['success'])
            print(f"    Progress: {i+1}/{iterations} ({success_count} successful)")
    
    # Calculate step summary
    total_duration = sum(r['duration'] for r in iteration_results)
    success_count = sum(1 for r in iteration_results if r['success'])
    
    print(f"    ✓ Completed: {success_count}/{iterations} successful, {total_duration:.2f}s total")
    
    return {
        'name': step_name,
        'iterations': iterations,
        'iteration_results': iteration_results,
        'total_duration': total_duration,
        'success_rate': success_count / iterations if iterations > 0 else 0
    }


async def execute_workflow(workflow_config: Dict[str, Any], workflow_num: int) -> Dict[str, Any]:
    """Execute a complete workflow"""
    print(f"\n🔄 Workflow #{workflow_num + 1}")
    
    workflow_start = time.time()
    step_results = []
    
    async with aiohttp.ClientSession() as session:
        for step in workflow_config['steps']:
            step_result = await execute_workflow_step(session, step)
            step_results.append(step_result)
    
    total_duration = time.time() - workflow_start
    
    return {
        'workflow_num': workflow_num,
        'total_duration': total_duration,
        'steps': step_results
    }


async def run_workflow_test(config_file: str):
    """Run workflow test from YAML configuration"""
    import yaml
    
    # Load configuration
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    workflow_config = config['workflows']['demo_workflow']
    iterations = workflow_config.get('iterations', 1)
    
    print(f"🚀 Starting Workflow Test: {workflow_config['name']}")
    print(f"   Total workflow iterations: {iterations}")
    print(f"=" * 60)
    
    # Execute all workflow iterations
    workflow_results = []
    for i in range(iterations):
        result = await execute_workflow(workflow_config, i)
        workflow_results.append(result)
    
    print(f"\n" + "=" * 60)
    print(f"✅ All workflows completed!")
    print(f"\n📊 Aggregating metrics...")
    
    # Aggregate results
    aggregated = aggregate_selective_iterations(workflow_results, {})
    
    # Print summary
    print_results_summary(aggregated)
    
    # Save results
    output_dir = Path("performance_results/selective_iteration_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "results.json", 'w') as f:
        json.dump({
            'workflow_results': workflow_results,
            'aggregated_metrics': aggregated
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_dir}/results.json")
    
    # Generate HTML report
    generate_html_report(workflow_config, aggregated, output_dir, workflow_results)


def generate_html_report(workflow_config: Dict[str, Any], aggregated: Dict[str, Any], output_dir: Path, workflow_results: List[Dict[str, Any]]):
    """Generate HTML report with workflow results"""
    from performance.unified_report_generator import UnifiedReportGenerator
    
    # Prepare workflow data for report
    workflow_data = {
        'name': workflow_config['name'],
        'total_workflows': aggregated['workflow_summary']['total_workflows'],
        'workflow_summary': aggregated['workflow_summary'],
        'step_breakdown': aggregated['step_breakdown'],
        'workflow_executions': workflow_results  # Individual workflow results
    }
    
    # Prepare unified results structure
    unified_results = {
        'results': [],  # No test results
        'workflows': [workflow_data],
        'summary': {
            'total_tests': 0,
            'success_rate': 1.0,
            'ui_tests': 0,
            'api_tests': 0,
            'avg_response_time': aggregated['workflow_summary']['avg_duration']
        }
    }
    
    # Generate report
    report_path = output_dir / "workflow_report.html"
    generator = UnifiedReportGenerator(unified_results, output_dir)
    generator.generate_unified_html_report("workflow_report.html")
    
    print(f"📊 HTML Report generated: {report_path}")
    print(f"   Open in browser: file://{report_path.absolute()}")
    
    # Auto-open in browser
    import subprocess
    subprocess.run(['open', str(report_path.absolute())], check=False)


def print_results_summary(aggregated: Dict[str, Any]):
    """Print a formatted summary of results"""
    print(f"\n{'=' * 80}")
    print(f"📈 WORKFLOW PERFORMANCE SUMMARY")
    print(f"{'=' * 80}")
    
    # Workflow summary
    wf_metrics = aggregated['workflow_summary']
    print(f"\n🔄 Overall Workflow Metrics:")
    print(f"   Total Workflows: {wf_metrics['total_workflows']}")
    print(f"   Avg Duration: {wf_metrics['avg_duration']:.2f}s")
    print(f"   Min Duration: {wf_metrics['min_duration']:.2f}s")
    print(f"   Max Duration: {wf_metrics['max_duration']:.2f}s")
    
    # Step breakdown table
    print(f"\n📋 Step-by-Step Breakdown:")
    print(f"{'─' * 80}")
    print(f"{'Step':<20} {'Iterations':<15} {'Avg Time':<12} {'Success':<15} {'Total':<10}")
    print(f"{'─' * 80}")
    
    for step_name, data in aggregated['step_breakdown'].items():
        iterations_display = data['iteration_config']['display']
        avg_time = f"{data['timing']['avg_duration']:.3f}s"
        success = data['success']['success_percentage']
        total_time = f"{data['timing']['total_time']:.2f}s"
        
        print(f"{step_name:<20} {iterations_display:<15} {avg_time:<12} {success:<15} {total_time:<10}")
    
    print(f"{'─' * 80}")
    
    # Detailed analysis for high-iteration steps
    if aggregated['high_iteration_steps']:
        print(f"\n🔍 Detailed Analysis (High-Iteration Steps):")
        
        for step_name, step_data in aggregated['high_iteration_steps'].items():
            print(f"\n   📊 {step_name}:")
            print(f"      Total Iterations: {step_data['iteration_config']['total_iterations']}")
            print(f"      Avg Duration: {step_data['timing']['avg_duration']:.3f}s")
            print(f"      P95: {step_data['timing']['p95']:.3f}s")
            print(f"      P99: {step_data['timing']['p99']:.3f}s")
            print(f"      Throughput: {step_data['throughput']['iterations_per_second']:.2f} req/s")
            
            # Show degradation if detected
            if 'degradation' in step_data:
                deg = step_data['degradation']
                if deg.get('degradation_detected'):
                    print(f"      ⚠️  Performance Degradation: {deg['degradation_percentage']:.1f}%")
                    print(f"          First iteration avg: {deg['first_iteration_avg']:.3f}s")
                    print(f"          Last iteration avg: {deg['last_iteration_avg']:.3f}s")
            
            # Show recommendations
            if step_name in aggregated['detailed_analysis']:
                recommendations = aggregated['detailed_analysis'][step_name].get('recommendations', [])
                if recommendations:
                    print(f"      💡 Recommendations:")
                    for rec in recommendations:
                        print(f"         {rec}")


if __name__ == "__main__":
    config_file = "examples/yaml_definitions/09_selective_iteration_demo.yml"
    asyncio.run(run_workflow_test(config_file))
