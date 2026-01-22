# Workflow Orchestration & Custom Metrics Integration

## Overview

The framework now supports performance testing for **workflow orchestration systems** and **custom server-side metrics collection**, making it a complete end-to-end performance testing solution.

---

## 🔧 Supported Workflow Orchestration Tools

### Tightly Integrated (Built-in Support)

1. **Temporal** - Modern workflow orchestration
2. **Apache Airflow** - Data pipeline orchestration
3. **Custom Workflows** - Any workflow system via extensible collectors

### Easy to Add

- Prefect
- Dagster
- Argo Workflows
- AWS Step Functions
- Azure Durable Functions
- Google Cloud Workflows

---

## 📊 Custom Metrics Collectors

### Built-in Collectors

1. **API Metrics Collector** - Collect from REST APIs
2. **Log File Collector** - Parse log files with regex
3. **Prometheus Collector** - Query Prometheus metrics
4. **Database Collector** - Run SQL queries
5. **Custom Function Collector** - Implement any logic

### Monitoring Systems Supported

- Prometheus
- Grafana
- DataDog
- New Relic
- CloudWatch
- Custom APIs

---

## 🚀 Quick Start

### 1. Test Temporal Workflow

```python
from performance.workflow_integrations import (
    TemporalWorkflowCollector,
    WorkflowPerformanceTester
)

# Create collector
collector = TemporalWorkflowCollector(
    workflow_id="my-workflow-001",
    namespace="default"
)

# Create tester
tester = WorkflowPerformanceTester(collector)

# Define workflow execution
async def execute_workflow():
    # Your Temporal workflow code
    result = await workflow_handle.result()
    return result

# Measure performance
results = await tester.measure_workflow_execution(
    workflow_func=execute_workflow,
    iterations=5
)

print(f"Avg Duration: {results['avg_duration']:.2f}s")
```

### 2. Test Airflow DAG

```python
from performance.workflow_integrations import AirflowDAGCollector

# Create collector
collector = AirflowDAGCollector(
    dag_id="etl_pipeline",
    dag_run_id="manual__2024-01-15",
    airflow_api_url="http://localhost:8080",
    auth_token="your-token"
)

# Collect metrics
metrics = await collector.collect_metrics()

print(f"DAG Duration: {metrics['execution_time']:.2f}s")
print(f"Tasks: {metrics['total_tasks']}")
```

### 3. Custom Metrics Collection

```python
from performance.custom_metrics_collectors import (
    APIMetricsCollector,
    PrometheusMetricsCollector,
    MetricsCollectorOrchestrator
)

# Create orchestrator
orchestrator = MetricsCollectorOrchestrator()

# Add API collector
orchestrator.add_collector(APIMetricsCollector(
    name="app_health",
    api_url="http://localhost:8000/health"
))

# Add Prometheus collector
orchestrator.add_collector(PrometheusMetricsCollector(
    name="prometheus",
    prometheus_url="http://localhost:9090",
    queries={
        'cpu_usage': 'rate(process_cpu_seconds_total[1m])',
        'memory_usage': 'process_resident_memory_bytes'
    }
))

# Collect during test
async def run_test():
    await asyncio.sleep(10)
    return {"status": "success"}

results = await orchestrator.collect_during_test(
    test_func=run_test,
    interval=2.0  # Collect every 2 seconds
)

print(f"Metrics Snapshots: {results['total_collections']}")
```

---

## 📝 YAML Configuration

### Workflow Performance Test

```yaml
# tests/definitions/workflow_performance_test.yml

test_info:
  test_suite_type: "workflow"

# Temporal workflows
temporal_workflows:
  data_processing: #smoke
    workflow_id: "data-wf-001"
    namespace: "default"
    iterations: 3
    thresholds:
      max_execution_time: 300

# Airflow DAGs
airflow_dags:
  etl_pipeline: #load
    dag_id: "etl_daily"
    dag_run_id: "manual__2024-01-15"
    airflow_config:
      api_url: "http://localhost:8080"
      auth_token: "${AIRFLOW_TOKEN}"
    iterations: 2

# Custom workflows
custom_workflows:
  order_processing: #load
    workflow_id: "order-flow"
    custom_collector:
      type: "api"
      api_url: "http://localhost:9090/metrics/${workflow_id}"
    iterations: 5

# Server metrics collection
server_metrics:
  enabled: true
  collection_interval: 5
  
  collectors:
    prometheus:
      enabled: true
      url: "http://localhost:9090"
      queries:
        cpu_usage: "rate(process_cpu_seconds_total[1m])"
        memory_usage: "process_resident_memory_bytes"
    
    api_metrics:
      enabled: true
      endpoints:
        - name: "health"
          url: "http://localhost:8000/health"
    
    log_monitoring:
      enabled: true
      files:
        - path: "/var/log/app/app.log"
          patterns:
            response_time: "response_time=(\\d+)ms"
```

**Run it:**
```bash
pytest tests/definitions/workflow_performance_test.yml -v
```

---

## 🎯 Use Cases

### 1. Temporal Workflow Performance

**Scenario:** Test data processing workflow

```python
collector = TemporalWorkflowCollector(
    workflow_id="data-processing-wf",
    temporal_client=client
)

# Metrics collected:
# - Workflow execution time
# - Activity execution times
# - Retry counts
# - Event history
# - Workflow status
```

### 2. Airflow DAG Performance

**Scenario:** Test ETL pipeline

```python
collector = AirflowDAGCollector(
    dag_id="etl_pipeline",
    dag_run_id="scheduled__2024-01-15",
    airflow_api_url="http://airflow:8080"
)

# Metrics collected:
# - DAG execution time
# - Task execution times
# - Task states
# - Retry counts
# - Success rate
```

### 3. Custom Workflow with API Metrics

**Scenario:** Test microservice orchestration

```python
async def collect_order_metrics(workflow_id):
    """Custom collector for order workflow."""
    # Call internal API
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://api/metrics/{workflow_id}") as resp:
            data = await resp.json()
    
    return {
        'execution_time': data['duration'],
        'orders_processed': data['count'],
        'errors': data['errors']
    }

collector = CustomWorkflowCollector(
    workflow_id="order-flow-001",
    collector_func=collect_order_metrics
)
```

### 4. Server Metrics During Load Test

**Scenario:** Monitor server health during load test

```python
orchestrator = MetricsCollectorOrchestrator()

# Add collectors
orchestrator.add_collector(PrometheusMetricsCollector(...))
orchestrator.add_collector(APIMetricsCollector(...))
orchestrator.add_collector(LogFileMetricsCollector(...))

# Run test with continuous monitoring
results = await orchestrator.collect_during_test(
    test_func=run_load_test,
    interval=5.0  # Collect every 5 seconds
)

# Analyze correlation between load and server metrics
```

---

## 🔌 Custom Collector Implementation

### Example: Custom API Collector

```python
async def collect_custom_metrics(**kwargs):
    """
    Custom metrics collector function.
    
    This can do anything:
    - Call APIs
    - Read log files
    - Query databases
    - Parse files
    - Execute shell commands
    """
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Call your API
        async with session.get("http://localhost:8000/metrics") as resp:
            data = await resp.json()
    
    # Parse and return metrics
    return {
        'active_users': data['users']['active'],
        'request_rate': data['requests']['rate'],
        'error_rate': data['errors']['rate'],
        'avg_response_time': data['performance']['avg_ms']
    }

# Use it
collector = CustomFunctionCollector(
    name="my_custom_metrics",
    collector_func=collect_custom_metrics
)
```

### Example: Log File Parser

```python
collector = LogFileMetricsCollector(
    name="app_logs",
    log_file_path="/var/log/app/application.log",
    patterns={
        'response_time': r'response_time=(\d+)ms',
        'error_count': r'ERROR',
        'request_count': r'Request processed',
        'db_query_time': r'db_query_time=(\d+)ms'
    },
    tail_lines=5000
)

metrics = await collector.collect()

# Metrics returned:
# {
#   'response_time': {'avg': 245.5, 'min': 50, 'max': 1200},
#   'error_count': {'count': 5},
#   'request_count': {'count': 1000},
#   'db_query_time': {'avg': 120.3, 'min': 10, 'max': 500}
# }
```

---

## 📈 Metrics Collected

### Workflow Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `execution_time` | Total workflow duration | All workflows |
| `activity_times` | Individual activity durations | Temporal |
| `task_times` | Individual task durations | Airflow |
| `retry_counts` | Number of retries | Temporal, Airflow |
| `success_rate` | Percentage of successful runs | All |
| `event_count` | Number of events | Temporal |
| `state_transitions` | Workflow state changes | All |

### Server Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `cpu_usage` | CPU utilization | Prometheus, API |
| `memory_usage` | Memory consumption | Prometheus, API |
| `request_rate` | Requests per second | Prometheus, Logs |
| `error_rate` | Errors per second | Prometheus, Logs |
| `response_time` | API response times | Logs, API |
| `db_connections` | Active DB connections | Database, API |
| `queue_depth` | Message queue depth | API, Custom |

---

## 🎨 Report Features

### Workflow Performance Section

```
Temporal Workflow: data-processing-wf
├── Avg Execution Time: 45.2s
├── Iterations: 5
├── Success Rate: 100%
├── Activity Breakdown:
│   ├── fetch_data: 12.3s
│   ├── process_data: 28.5s
│   └── save_results: 4.4s
└── Retries: 0
```

### Server Metrics Timeline

```
Server Metrics During Test (30s duration)
├── CPU Usage: 45% → 78% → 52%
├── Memory Usage: 2.1GB → 2.8GB → 2.3GB
├── Request Rate: 100/s → 250/s → 120/s
└── Error Rate: 0.1% → 0.3% → 0.1%
```

### Correlation Analysis

```
Performance Correlation:
├── High CPU (>70%) → Response time +45%
├── Memory spike → Error rate +0.2%
└── Request rate >200/s → Queue depth +15
```

---

## 🔧 Advanced Features

### 1. Continuous Monitoring

```python
# Collect metrics every 5 seconds during test
results = await orchestrator.collect_during_test(
    test_func=my_test,
    interval=5.0
)

# Access timeline
for snapshot in results['metrics_timeline']:
    print(f"Time: {snapshot['timestamp']}")
    print(f"CPU: {snapshot['metrics']['cpu_usage']}")
```

### 2. Multiple Collectors

```python
orchestrator = MetricsCollectorOrchestrator()

# Add multiple collectors
orchestrator.add_collector(prometheus_collector)
orchestrator.add_collector(api_collector)
orchestrator.add_collector(log_collector)
orchestrator.add_collector(custom_collector)

# Collect from all simultaneously
all_metrics = await orchestrator.collect_all()
```

### 3. Custom Parsing

```python
def parse_health_response(data):
    """Custom parser for health endpoint."""
    return {
        'status': data['status'],
        'uptime': data['uptime_seconds'],
        'connections': data['active_connections'],
        'custom_metric': data['app_specific_metric']
    }

collector = APIMetricsCollector(
    name="health",
    api_url="http://localhost:8000/health",
    parser_func=parse_health_response
)
```

---

## 📦 Dependencies

### Required
```bash
pip install aiohttp pyyaml
```

### Optional (for specific integrations)
```bash
# Temporal
pip install temporalio

# Airflow (if using Python client)
pip install apache-airflow-client

# Database collectors
pip install asyncpg  # PostgreSQL
pip install aiomysql  # MySQL
```

---

## 🎯 Best Practices

1. **Use appropriate collection intervals**
   - Fast tests: 1-2 seconds
   - Long tests: 5-10 seconds

2. **Limit log file tail lines**
   - Start with 1000 lines
   - Increase only if needed

3. **Cache API responses**
   - Avoid overwhelming APIs
   - Use reasonable intervals

4. **Custom collectors should be async**
   - Use `async def` for all collectors
   - Avoid blocking operations

5. **Handle errors gracefully**
   - Collectors should not crash tests
   - Return error info in metrics

---

## 📚 Examples

See complete examples in:
- `tests/workflow/test_workflow_examples.py`
- `tests/definitions/workflow_performance_test.yml`

---

## 🚀 Summary

**New Capabilities:**

✅ **Workflow Orchestration Testing**
- Temporal workflows
- Airflow DAGs
- Custom workflows

✅ **Server-Side Metrics**
- API endpoints
- Log files
- Prometheus
- Databases
- Custom sources

✅ **Continuous Monitoring**
- Collect during test execution
- Time-series data
- Correlation analysis

✅ **Extensible Framework**
- Easy to add new collectors
- Custom implementation support
- Flexible and powerful

**The framework is now a complete end-to-end performance testing solution!** 🎉
