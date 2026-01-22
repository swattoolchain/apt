"""
Programmatic Unified Performance Test Runner
Demonstrates how to run unified tests using Python code instead of YAML.
"""
import asyncio
import logging
from pathlib import Path
from performance.unified_runner import UnifiedTestRunner
from performance.unified_report_generator import UnifiedReportGenerator
from examples.run_workflow_test import execute_workflow, execute_api_call # Using the helper from examples
from custom_aggregators.selective_iteration_aggregator import aggregate_selective_iterations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_programmatic_test():
    """Execute complete unified test programmatically."""
    output_dir = Path("performance_results/programmatic_test")
    runner = UnifiedTestRunner(output_dir)
    
    print("\n" + "="*70)
    print("🚀 PROGRAMMATIC UNIFIED TEST")
    print("="*70)
    
    # ========================================
    # 1. Run k6 Test
    # ========================================
    print("\n📊 Running k6 load test...")
    k6_scenarios = [
        {"name": "User API", "url": "https://jsonplaceholder.typicode.com/users", "method": "GET"},
        {"name": "Posts API", "url": "https://jsonplaceholder.typicode.com/posts", "method": "GET"}
    ]
    await runner.run_k6_test("api_load_test", k6_scenarios, {"vus": 5, "duration": "5s"})
    
    # ========================================
    # 2. Run JMeter Test
    # ========================================
    print("\n📊 Running JMeter stress test...")
    await runner.run_jmeter_test(
        "api_stress_test", 
        [{"name": "Comments API", "url": "https://jsonplaceholder.typicode.com/comments", "method": "GET"}],
        {"num_threads": 5, "duration": 5}
    )
    
    # ========================================
    # 3. Run Custom Workflow
    # ========================================
    print("\n📊 Running custom workflow...")
    workflow_config = {
        "name": "User Journey Workflow",
        "steps": [
            {"name": "login", "url": "https://jsonplaceholder.typicode.com/users/1", "action": "api_call"},
            {"name": "browse", "url": "https://jsonplaceholder.typicode.com/posts", "action": "api_call", "iterations": 5},
            {"name": "logout", "url": "https://jsonplaceholder.typicode.com/users/1", "action": "api_call"}
        ]
    }
    
    workflow_results = []
    iterations = 2
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...")
            # Simplified workflow execution logic for example
            # Execute steps
            iteration_steps_results = []
            for step in workflow_config['steps']:
                step_name = step['name']
                count = step.get('iterations', 1)
                
                step_results = []
                for _ in range(count):
                    res = await execute_api_call(session, step['url'])
                    step_results.append(res)
                
                total_duration = sum(r['duration'] for r in step_results)
                success_count = sum(1 for r in step_results if r['success'])
                
                iteration_steps_results.append({
                    'name': step_name,
                    'iterations': count,
                    'total_duration': total_duration,
                    'success_rate': success_count / count if count > 0 else 0,
                    'iteration_results': step_results
                })
            
            # Record workflow iteration result
            workflow_results.append({
                'workflow_num': i,
                'iteration': i,
                'duration': sum(s['total_duration'] for s in iteration_steps_results),
                'total_duration': sum(s['total_duration'] for s in iteration_steps_results),
                'steps': iteration_steps_results,
                'success': all(s['success_rate'] == 1.0 for s in iteration_steps_results)
            })

    # Aggregate workflow results
    aggregated = aggregate_selective_iterations(workflow_results, {})

    # Add workflow results to runner for reporting
    workflow_data = {
        'name': workflow_config['name'],
        'total_workflows': iterations,
        'workflow_summary': aggregated['workflow_summary'],
        'step_breakdown': aggregated['step_breakdown'],
        'workflow_executions': workflow_results
    }
    
    if 'workflows' not in runner.results:
        runner.results['workflows'] = []
    runner.results['workflows'].append(workflow_data)
    # For this example, we'll demonstrate saving the report
    print("\n📊 Generating report...")
    report_gen = UnifiedReportGenerator(runner.get_all_results(), output_dir)
    report_path = report_gen.generate_unified_html_report()
    
    print(f"\n✅ Test Completed. Report: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_programmatic_test())
