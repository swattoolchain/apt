# Temporal Workflow Performance Testing with APT

## Overview

Temporal is a workflow orchestration platform. Testing Temporal workflows requires measuring:
1. **Workflow execution time** - Total time from start to completion
2. **Activity execution time** - Time for individual activities
3. **Workflow throughput** - Workflows completed per second
4. **Activity retry metrics** - Retries, failures, timeouts
5. **Worker performance** - Task queue processing rates

## Architecture

### Temporal Components
- **Workflows**: Durable function executions
- **Activities**: Individual tasks within workflows
- **Workers**: Process workflow and activity tasks
- **Task Queues**: Distribute work to workers

## APT Integration Approaches

### Approach 1: Temporal as a Service Under Test

Test Temporal workflows like any other API service.

**Example YAML:**
```yaml
test_info:
  test_suite_name: "Temporal Workflow Load Test"
  test_suite_type: "unified"

# Use k6 to trigger workflows via Temporal's gRPC API
k6_tests:
  temporal_workflow_trigger:
    plugin: "grpc"  # Use gRPC plugin
    plugin_config:
      host_port: "localhost:7233"  # Temporal server
      proto_folder: "temporal/api"
      full_method: "temporal.api.workflowservice.v1.WorkflowService/StartWorkflowExecution"
      request_json: |
        {
          "namespace": "default",
          "workflow_id": "test-workflow-${__ITER}",
          "workflow_type": {"name": "OrderProcessingWorkflow"},
          "task_queue": {"name": "order-processing"},
          "input": {"order_id": "order-${__ITER}"}
        }
    options:
      vus: 10
      duration: "60s"

# Custom metrics for Temporal
custom_metrics:
  temporal_metrics:
    - name: "workflow_completion_time"
      description: "Time from workflow start to completion"
      source: "temporal_history"
      aggregation: "percentiles"
    
    - name: "activity_retry_rate"
      description: "Rate of activity retries"
      source: "temporal_metrics"
      aggregation: "rate"
```

### Approach 2: Instrument Temporal Workers

Add performance instrumentation to your Temporal workers.

**Python Worker Example:**
```python
# temporal_worker_instrumented.py
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
import time
import asyncio

# APT metrics collector
from performance.metrics_collector import MetricsCollector

metrics = MetricsCollector()

@activity.defn
async def process_order(order_id: str) -> str:
    """Instrumented activity"""
    start_time = time.time()
    
    try:
        # Your activity logic
        await asyncio.sleep(0.5)  # Simulate work
        result = f"Processed order {order_id}"
        
        # Record metrics
        duration = time.time() - start_time
        metrics.record_activity_execution(
            activity_name="process_order",
            duration=duration,
            success=True
        )
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        metrics.record_activity_execution(
            activity_name="process_order",
            duration=duration,
            success=False,
            error=str(e)
        )
        raise

@workflow.defn
class OrderProcessingWorkflow:
    """Instrumented workflow"""
    
    @workflow.run
    async def run(self, order_id: str) -> str:
        workflow_start = time.time()
        
        # Execute activities
        result = await workflow.execute_activity(
            process_order,
            order_id,
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Record workflow metrics
        workflow_duration = time.time() - workflow_start
        metrics.record_workflow_execution(
            workflow_name="OrderProcessingWorkflow",
            duration=workflow_duration,
            success=True
        )
        
        return result

# Export metrics for APT
async def export_metrics():
    """Export collected metrics in APT format"""
    return metrics.export_json()
```

**APT Test Configuration:**
```yaml
workflows:
  temporal_workflow_test:
    name: "Temporal Order Processing"
    type: "temporal"
    config:
      temporal_address: "localhost:7233"
      namespace: "default"
      task_queue: "order-processing"
      workflow_type: "OrderProcessingWorkflow"
    
    # Trigger configuration
    trigger:
      method: "start_workflow"
      iterations: 100
      concurrent: 10
      input_generator: "lambda i: {'order_id': f'order-{i}'}"
    
    # Metrics collection
    metrics_source:
      type: "worker_instrumentation"
      export_endpoint: "http://localhost:8080/metrics"
      poll_interval: 5
    
    aggregator: "temporal_workflow_aggregator"
```

### Approach 3: Query Temporal Metrics

Temporal exposes Prometheus metrics. Scrape and analyze them.

**Configuration:**
```yaml
custom_metrics:
  temporal_prometheus:
    source: "prometheus"
    endpoint: "http://localhost:9090"
    queries:
      - name: "workflow_execution_time"
        query: 'histogram_quantile(0.95, rate(temporal_workflow_endtoend_latency_bucket[5m]))'
      
      - name: "activity_task_latency"
        query: 'rate(temporal_activity_execution_latency_sum[5m]) / rate(temporal_activity_execution_latency_count[5m])'
      
      - name: "workflow_success_rate"
        query: 'rate(temporal_workflow_success[5m]) / rate(temporal_workflow_completed[5m])'
      
      - name: "task_queue_lag"
        query: 'temporal_task_queue_lag{task_queue="order-processing"}'
```

## Complete Temporal Testing Example

**File: `examples/temporal/temporal_workflow_test.yml`**
```yaml
test_info:
  test_suite_name: "Temporal Workflow Performance Test"
  test_suite_type: "unified"
  description: "Comprehensive Temporal workflow performance testing"

# Trigger workflows using custom Python script
workflows:
  temporal_order_processing:
    name: "Order Processing Workflow"
    type: "temporal"
    script: "examples/temporal/trigger_workflows.py"
    config:
      temporal_address: "localhost:7233"
      namespace: "default"
      task_queue: "order-processing"
      workflow_type: "OrderProcessingWorkflow"
      concurrent_workflows: 20
      total_workflows: 1000
      ramp_up_time: 10
    
    # Custom aggregator
    aggregator: "temporal_workflow_aggregator"

# Monitor Temporal server performance
k6_tests:
  temporal_server_health:
    scenarios:
      - name: "Health Check"
        url: "http://localhost:7233/health"
        method: "GET"
    options:
      vus: 1
      duration: "120s"

# Collect Temporal metrics
custom_metrics:
  temporal_metrics:
    - name: "workflow_latency"
      source: "prometheus"
      query: 'temporal_workflow_endtoend_latency'
    
    - name: "worker_task_slots"
      source: "prometheus"
      query: 'temporal_worker_task_slots_available'

reporting:
  unified_report: true
  output_dir: "performance_results/temporal_test"
  custom_dashboards:
    - type: "temporal_workflow_timeline"
    - type: "activity_breakdown"
    - type: "worker_utilization"
```

## Temporal-Specific Aggregator

**File: `custom_aggregators/temporal_aggregator.py`**
```python
def aggregate_temporal_metrics(results, config):
    """Aggregate Temporal-specific metrics"""
    
    metrics = {
        'workflow_metrics': {
            'total_started': 0,
            'total_completed': 0,
            'total_failed': 0,
            'avg_duration': 0,
            'p95_duration': 0,
            'p99_duration': 0
        },
        'activity_metrics': {},
        'worker_metrics': {
            'avg_task_processing_time': 0,
            'task_queue_lag': 0,
            'worker_utilization': 0
        },
        'retry_metrics': {
            'total_retries': 0,
            'retry_rate': 0,
            'activities_with_retries': []
        }
    }
    
    # Process workflow results
    durations = []
    for result in results:
        if result['type'] == 'workflow':
            metrics['workflow_metrics']['total_started'] += 1
            if result['status'] == 'completed':
                metrics['workflow_metrics']['total_completed'] += 1
                durations.append(result['duration'])
            elif result['status'] == 'failed':
                metrics['workflow_metrics']['total_failed'] += 1
    
    # Calculate percentiles
    if durations:
        sorted_durations = sorted(durations)
        metrics['workflow_metrics']['avg_duration'] = sum(durations) / len(durations)
        metrics['workflow_metrics']['p95_duration'] = sorted_durations[int(len(durations) * 0.95)]
        metrics['workflow_metrics']['p99_duration'] = sorted_durations[int(len(durations) * 0.99)]
    
    return metrics
```

## Key Considerations

### 1. Temporal Server Capacity
- Monitor server resource usage
- Test with realistic workflow complexity
- Consider multi-cluster setups for high load

### 2. Worker Scaling
- Test worker autoscaling behavior
- Measure task queue processing rates
- Monitor worker resource consumption

### 3. Workflow Patterns
- Test different workflow patterns (sequential, parallel, saga)
- Measure impact of workflow history size
- Test long-running workflows

### 4. Activity Retries
- Measure retry behavior under load
- Test timeout configurations
- Monitor retry storm scenarios

## Next Steps

1. **Implement Temporal Client**: Create APT integration for Temporal client
2. **Add Temporal Plugin**: Extend extensions_config.yml with Temporal support
3. **Create Dashboards**: Build Temporal-specific visualizations
4. **Add Examples**: Create more Temporal workflow test examples

## Resources

- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Metrics](https://docs.temporal.io/references/sdk-metrics)
- [Temporal Best Practices](https://docs.temporal.io/application-development/best-practices)
