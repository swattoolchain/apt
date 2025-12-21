"""
Selective Iteration Aggregator

Processes workflow results where different steps have different iteration counts.
Provides intelligent breakdown and analysis of per-step performance.
"""

from typing import Dict, List, Any
import statistics
import numpy as np


class SelectiveIterationMetrics:
    """Tracks metrics for workflows with selective step iterations"""
    
    def __init__(self):
        self.workflows = []
        self.step_iterations = {}  # step_name -> list of iteration results
        self.step_configs = {}  # step_name -> iteration config
    
    def add_workflow_result(self, workflow_result: Dict[str, Any]):
        """Add a complete workflow execution result"""
        self.workflows.append(workflow_result)
        
        for step in workflow_result.get('steps', []):
            step_name = step['name']
            
            if step_name not in self.step_iterations:
                self.step_iterations[step_name] = []
                self.step_configs[step_name] = {
                    'iterations_per_workflow': step.get('iterations', 1),
                    'total_iterations': 0
                }
            
            # Add all iterations for this step
            for iteration in step.get('iteration_results', []):
                self.step_iterations[step_name].append(iteration)
                self.step_configs[step_name]['total_iterations'] += 1


def aggregate_selective_iterations(
    workflow_results: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate metrics for workflows with selective step iterations.
    
    Args:
        workflow_results: List of workflow execution results
        config: Aggregator configuration
        
    Returns:
        Comprehensive metrics breakdown
    """
    metrics = SelectiveIterationMetrics()
    
    # Process all workflow results
    for result in workflow_results:
        metrics.add_workflow_result(result)
    
    # Calculate overall workflow metrics
    workflow_durations = [w['total_duration'] for w in metrics.workflows]
    workflow_metrics = {
        'total_workflows': len(metrics.workflows),
        'avg_duration': statistics.mean(workflow_durations) if workflow_durations else 0,
        'min_duration': min(workflow_durations) if workflow_durations else 0,
        'max_duration': max(workflow_durations) if workflow_durations else 0,
        'total_duration': sum(workflow_durations)
    }
    
    # Calculate per-step metrics
    step_breakdown = {}
    
    for step_name, iterations in metrics.step_iterations.items():
        if not iterations:
            continue
        
        durations = [it['duration'] for it in iterations]
        successes = [it for it in iterations if it.get('success', False)]
        failures = [it for it in iterations if not it.get('success', False)]
        
        config_info = metrics.step_configs[step_name]
        iterations_per_workflow = config_info['iterations_per_workflow']
        total_iterations = len(iterations)
        
        # Calculate statistics
        sorted_durations = sorted(durations)
        
        step_breakdown[step_name] = {
            'iteration_config': {
                'iterations_per_workflow': iterations_per_workflow,
                'total_workflows': len(metrics.workflows),
                'total_iterations': total_iterations,
                'display': f"{iterations_per_workflow}x{len(metrics.workflows)}"
            },
            'timing': {
                'avg_duration': statistics.mean(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'median_duration': statistics.median(durations),
                'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0,
                'total_time': sum(durations),
                'p50': sorted_durations[int(len(sorted_durations) * 0.50)],
                'p95': sorted_durations[int(len(sorted_durations) * 0.95)],
                'p99': sorted_durations[int(len(sorted_durations) * 0.99)]
            },
            'success': {
                'total_success': len(successes),
                'total_failures': len(failures),
                'success_rate': len(successes) / total_iterations if total_iterations > 0 else 0,
                'success_percentage': f"{(len(successes) / total_iterations * 100):.1f}%" if total_iterations > 0 else "0%"
            },
            'throughput': {
                'iterations_per_second': total_iterations / sum(durations) if sum(durations) > 0 else 0,
                'avg_time_per_iteration': sum(durations) / total_iterations if total_iterations > 0 else 0
            }
        }
        
        # Performance degradation analysis (for steps with multiple iterations)
        if iterations_per_workflow > 1:
            degradation = analyze_performance_degradation(iterations, iterations_per_workflow)
            step_breakdown[step_name]['degradation'] = degradation
    
    # Identify high-iteration steps (steps with >1 iteration)
    high_iteration_steps = {
        name: data for name, data in step_breakdown.items()
        if data['iteration_config']['iterations_per_workflow'] > 1
    }
    
    # Generate detailed analysis for high-iteration steps
    detailed_analysis = {}
    for step_name, step_data in high_iteration_steps.items():
        iterations = metrics.step_iterations[step_name]
        detailed_analysis[step_name] = generate_detailed_step_analysis(
            step_name, iterations, step_data
        )
    
    return {
        'workflow_summary': workflow_metrics,
        'step_breakdown': step_breakdown,
        'high_iteration_steps': high_iteration_steps,
        'detailed_analysis': detailed_analysis,
        'report_metadata': {
            'total_steps': len(step_breakdown),
            'steps_with_multiple_iterations': len(high_iteration_steps),
            'total_iterations_across_all_steps': sum(
                data['iteration_config']['total_iterations']
                for data in step_breakdown.values()
            )
        }
    }


def analyze_performance_degradation(
    iterations: List[Dict[str, Any]],
    iterations_per_workflow: int
) -> Dict[str, Any]:
    """
    Analyze if performance degrades over iterations within a workflow.
    
    Returns metrics showing if the Nth iteration is slower than the 1st.
    """
    # Group iterations by workflow
    workflows = []
    current_workflow = []
    
    for i, iteration in enumerate(iterations):
        current_workflow.append(iteration['duration'])
        if (i + 1) % iterations_per_workflow == 0:
            workflows.append(current_workflow)
            current_workflow = []
    
    if not workflows:
        return {'degradation_detected': False}
    
    # Calculate average duration for each iteration position (1st, 2nd, 3rd, etc.)
    iteration_position_avgs = []
    for pos in range(iterations_per_workflow):
        durations_at_position = [w[pos] for w in workflows if len(w) > pos]
        if durations_at_position:
            iteration_position_avgs.append(statistics.mean(durations_at_position))
    
    if len(iteration_position_avgs) < 2:
        return {'degradation_detected': False}
    
    # Calculate degradation percentage
    first_avg = iteration_position_avgs[0]
    last_avg = iteration_position_avgs[-1]
    degradation_pct = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
    
    # Detect trend using linear regression
    x = np.array(range(len(iteration_position_avgs)))
    y = np.array(iteration_position_avgs)
    slope, _ = np.polyfit(x, y, 1)
    
    return {
        'degradation_detected': degradation_pct > 5,  # >5% slower is significant
        'degradation_percentage': degradation_pct,
        'first_iteration_avg': first_avg,
        'last_iteration_avg': last_avg,
        'trend_slope': slope,
        'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
        'iteration_position_averages': iteration_position_avgs
    }


def generate_detailed_step_analysis(
    step_name: str,
    iterations: List[Dict[str, Any]],
    step_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate detailed analysis for a high-iteration step"""
    
    durations = [it['duration'] for it in iterations]
    
    # Identify outliers (>2 std dev from mean)
    mean = statistics.mean(durations)
    std_dev = statistics.stdev(durations) if len(durations) > 1 else 0
    outliers = [
        {'iteration': i, 'duration': d, 'deviation': abs(d - mean) / std_dev if std_dev > 0 else 0}
        for i, d in enumerate(durations)
        if std_dev > 0 and abs(d - mean) > 2 * std_dev
    ]
    
    # Calculate iteration buckets (group into ranges)
    total_iterations = len(durations)
    bucket_size = max(1, total_iterations // 10)  # 10 buckets
    buckets = []
    
    for i in range(0, total_iterations, bucket_size):
        bucket_durations = durations[i:i+bucket_size]
        if bucket_durations:
            buckets.append({
                'range': f"{i+1}-{min(i+bucket_size, total_iterations)}",
                'avg_duration': statistics.mean(bucket_durations),
                'count': len(bucket_durations)
            })
    
    return {
        'summary': {
            'step_name': step_name,
            'total_iterations': total_iterations,
            'avg_duration': step_data['timing']['avg_duration'],
            'success_rate': step_data['success']['success_rate']
        },
        'outliers': {
            'count': len(outliers),
            'details': outliers[:10]  # Top 10 outliers
        },
        'iteration_buckets': buckets,
        'recommendations': generate_recommendations(step_data, outliers)
    }


def generate_recommendations(
    step_data: Dict[str, Any],
    outliers: List[Dict[str, Any]]
) -> List[str]:
    """Generate performance recommendations based on analysis"""
    recommendations = []
    
    # Check for high failure rate
    if step_data['success']['success_rate'] < 0.95:
        recommendations.append(
            f"⚠️ Success rate is {step_data['success']['success_percentage']}. "
            "Investigate failures and add retry logic."
        )
    
    # Check for performance degradation
    if 'degradation' in step_data and step_data['degradation'].get('degradation_detected'):
        deg_pct = step_data['degradation']['degradation_percentage']
        recommendations.append(
            f"📉 Performance degrades by {deg_pct:.1f}% over iterations. "
            "Check for memory leaks or resource exhaustion."
        )
    
    # Check for high variance
    timing = step_data['timing']
    if timing['std_dev'] / timing['avg_duration'] > 0.5:  # CV > 50%
        recommendations.append(
            "📊 High variance in response times. "
            "Consider connection pooling or caching."
        )
    
    # Check for outliers
    total_iterations = step_data['iteration_config']['total_iterations']
    if len(outliers) > total_iterations * 0.05:
        recommendations.append(
            f"🎯 {len(outliers)} outliers detected (>5%). "
            "Investigate timeout configurations and network stability."
        )
    
    if not recommendations:
        recommendations.append("✅ Performance looks good! No major issues detected.")
    
    return recommendations


# Example usage
if __name__ == "__main__":
    # Sample data with selective iterations
    sample_results = [
        {
            'total_duration': 15.2,
            'steps': [
                {
                    'name': 'login',
                    'iterations': 1,
                    'iteration_results': [
                        {'duration': 0.5, 'success': True}
                    ]
                },
                {
                    'name': 'add_to_cart',
                    'iterations': 100,
                    'iteration_results': [
                        {'duration': 0.1 + i * 0.001, 'success': True}
                        for i in range(100)
                    ]
                },
                {
                    'name': 'checkout',
                    'iterations': 1,
                    'iteration_results': [
                        {'duration': 0.8, 'success': True}
                    ]
                }
            ]
        }
    ]
    
    config = {}
    result = aggregate_selective_iterations(sample_results, config)
    
    print("Step Breakdown:")
    for step_name, data in result['step_breakdown'].items():
        print(f"\n{step_name}:")
        print(f"  Iterations: {data['iteration_config']['display']}")
        print(f"  Avg Time: {data['timing']['avg_duration']:.3f}s")
        print(f"  Success: {data['success']['success_percentage']}")
