"""
Custom Workflow Aggregator

This module provides custom metric aggregation for workflow performance testing.
It processes workflow execution data and calculates custom metrics.
"""

from typing import Dict, List, Any
import statistics
from datetime import datetime


class WorkflowMetrics:
    """Container for workflow performance metrics"""
    
    def __init__(self):
        self.workflow_times = []
        self.step_times = {}
        self.step_success = {}
        self.errors = []
    
    def add_workflow_execution(self, workflow_data: Dict[str, Any]):
        """Add a workflow execution result"""
        total_time = workflow_data.get('total_time', 0)
        self.workflow_times.append(total_time)
        
        # Track step-level metrics
        for step in workflow_data.get('steps', []):
            step_name = step['name']
            
            if step_name not in self.step_times:
                self.step_times[step_name] = []
                self.step_success[step_name] = {'success': 0, 'total': 0}
            
            self.step_times[step_name].append(step.get('duration', 0))
            self.step_success[step_name]['total'] += 1
            
            if step.get('success', False):
                self.step_success[step_name]['success'] += 1
            else:
                self.errors.append({
                    'step': step_name,
                    'error': step.get('error', 'Unknown error'),
                    'timestamp': step.get('timestamp')
                })


def aggregate_workflow_metrics(
    workflow_results: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate workflow performance metrics.
    
    Args:
        workflow_results: List of workflow execution results
        config: Aggregator configuration
        
    Returns:
        Aggregated metrics dictionary
    """
    metrics = WorkflowMetrics()
    
    # Process all workflow executions
    for result in workflow_results:
        metrics.add_workflow_execution(result)
    
    # Calculate percentiles
    percentiles = config.get('percentiles', [50, 75, 90, 95, 99])
    workflow_percentiles = {}
    
    if metrics.workflow_times:
        sorted_times = sorted(metrics.workflow_times)
        for p in percentiles:
            idx = int(len(sorted_times) * p / 100)
            workflow_percentiles[f'p{p}'] = sorted_times[min(idx, len(sorted_times) - 1)]
    
    # Calculate step-level metrics
    step_metrics = {}
    bottlenecks = []
    
    for step_name, times in metrics.step_times.items():
        avg_time = statistics.mean(times) if times else 0
        success_data = metrics.step_success[step_name]
        success_rate = success_data['success'] / success_data['total'] if success_data['total'] > 0 else 0
        
        step_metrics[step_name] = {
            'avg_duration': avg_time,
            'min_duration': min(times) if times else 0,
            'max_duration': max(times) if times else 0,
            'success_rate': success_rate,
            'total_executions': success_data['total']
        }
        
        # Identify bottlenecks (steps taking >30% of total time)
        if config.get('calculate_bottlenecks', True):
            avg_workflow_time = statistics.mean(metrics.workflow_times) if metrics.workflow_times else 0
            if avg_workflow_time > 0 and avg_time / avg_workflow_time > 0.3:
                bottlenecks.append({
                    'step': step_name,
                    'avg_duration': avg_time,
                    'percentage_of_total': (avg_time / avg_workflow_time) * 100
                })
    
    # Sort bottlenecks by duration
    bottlenecks.sort(key=lambda x: x['avg_duration'], reverse=True)
    
    # Calculate overall metrics
    aggregated = {
        'workflow_metrics': {
            'total_executions': len(metrics.workflow_times),
            'avg_duration': statistics.mean(metrics.workflow_times) if metrics.workflow_times else 0,
            'min_duration': min(metrics.workflow_times) if metrics.workflow_times else 0,
            'max_duration': max(metrics.workflow_times) if metrics.workflow_times else 0,
            'percentiles': workflow_percentiles,
            'throughput': len(metrics.workflow_times) / sum(metrics.workflow_times) if sum(metrics.workflow_times) > 0 else 0
        },
        'step_metrics': step_metrics,
        'bottlenecks': bottlenecks,
        'errors': metrics.errors,
        'error_rate': len(metrics.errors) / (len(metrics.workflow_times) * len(metrics.step_times)) if metrics.workflow_times and metrics.step_times else 0
    }
    
    return aggregated


def calculate_step_correlation(
    step_times: Dict[str, List[float]]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlation between step execution times.
    Helps identify dependencies and cascading delays.
    """
    import numpy as np
    
    correlations = {}
    step_names = list(step_times.keys())
    
    for i, step1 in enumerate(step_names):
        correlations[step1] = {}
        for step2 in step_names[i+1:]:
            if len(step_times[step1]) == len(step_times[step2]):
                corr = np.corrcoef(step_times[step1], step_times[step2])[0, 1]
                correlations[step1][step2] = corr
    
    return correlations


# Example usage in test
if __name__ == "__main__":
    # Sample workflow results
    sample_results = [
        {
            'total_time': 2.5,
            'steps': [
                {'name': 'browse_products', 'duration': 0.5, 'success': True},
                {'name': 'add_to_cart', 'duration': 0.3, 'success': True},
                {'name': 'checkout', 'duration': 1.2, 'success': True},
                {'name': 'payment', 'duration': 0.5, 'success': True}
            ]
        },
        {
            'total_time': 3.1,
            'steps': [
                {'name': 'browse_products', 'duration': 0.6, 'success': True},
                {'name': 'add_to_cart', 'duration': 0.4, 'success': True},
                {'name': 'checkout', 'duration': 1.5, 'success': True},
                {'name': 'payment', 'duration': 0.6, 'success': True}
            ]
        }
    ]
    
    config = {
        'percentiles': [50, 90, 95, 99],
        'track_step_times': True,
        'calculate_bottlenecks': True
    }
    
    metrics = aggregate_workflow_metrics(sample_results, config)
    
    print("Workflow Metrics:")
    print(f"  Avg Duration: {metrics['workflow_metrics']['avg_duration']:.2f}s")
    print(f"  Throughput: {metrics['workflow_metrics']['throughput']:.2f} workflows/s")
    
    print("\nBottlenecks:")
    for bottleneck in metrics['bottlenecks']:
        print(f"  {bottleneck['step']}: {bottleneck['percentage_of_total']:.1f}% of total time")
