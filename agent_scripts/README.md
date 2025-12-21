# Agent Scripts - Reusable Utility Functions

This directory contains reusable agent code that can be referenced from test YAML files instead of using inline code.

## Benefits

✅ **Reusability** - Write once, use in multiple tests
✅ **Maintainability** - Update in one place
✅ **Multi-language** - Python, Shell, JavaScript support
✅ **Version Control** - Track changes to test logic
✅ **Testing** - Unit test agent code separately

## Available Scripts

### Health Monitoring

#### `health_check.py`
**Language**: Python  
**Purpose**: Check API health endpoint  
**Returns**: Status code, response time, health status

**Usage**:
```yaml
- name: health_check
  action: agent_execute
  agent: my-agent
  code_file: "agent_scripts/health_check.py"
  language: python
```

#### `database_check.py`
**Language**: Python  
**Purpose**: Check PostgreSQL database connectivity  
**Returns**: Connection status, response time  
**Requirements**: `psycopg2` installed on agent

**Usage**:
```yaml
- name: db_check
  action: agent_execute
  agent: my-agent
  code_file: "agent_scripts/database_check.py"
  language: python
```

### System Metrics

#### `system_metrics.sh`
**Language**: Shell  
**Purpose**: Collect CPU, memory, disk usage  
**Returns**: System resource utilization

**Usage**:
```yaml
- name: system_check
  action: agent_execute
  agent: my-agent
  code_file: "agent_scripts/system_metrics.sh"
  language: shell
```

#### `collect_metrics.py`
**Language**: Python  
**Purpose**: Comprehensive system metrics collection  
**Returns**: CPU, memory, network, disk I/O metrics  
**Requirements**: `psutil` installed on agent

**Context Parameters**:
- `metric_type`: Type of metrics (baseline, performance)
- `duration`: Collection duration in seconds

**Usage**:
```yaml
- name: collect_metrics
  action: agent_execute
  agent: my-agent
  code_file: "agent_scripts/collect_metrics.py"
  language: python
  context:
    metric_type: "performance"
    duration: 60
```

### Load Generation

#### `generate_load.py`
**Language**: Python  
**Purpose**: Generate HTTP load with configurable RPS  
**Returns**: Request statistics, latency percentiles

**Context Parameters**:
- `target_url`: Target URL to load test
- `requests_per_second`: Desired RPS
- `duration`: Test duration in seconds

**Usage**:
```yaml
- name: generate_load
  action: agent_execute
  agent: load-generator
  code_file: "agent_scripts/generate_load.py"
  language: python
  context:
    target_url: "https://api.example.com"
    requests_per_second: 100
    duration: 120
```

### Validation

#### `validate_performance.py`
**Language**: Python  
**Purpose**: Validate performance against thresholds  
**Returns**: Pass/fail status, violations

**Context Parameters**:
- `threshold_p95`: P95 latency threshold (ms)
- `threshold_error_rate`: Error rate threshold (0-1)

**Usage**:
```yaml
- name: validate
  action: agent_execute
  agent: validator
  code_file: "agent_scripts/validate_performance.py"
  language: python
  context:
    threshold_p95: 500
    threshold_error_rate: 0.01
```

## Creating Custom Scripts

### Python Scripts

```python
"""
My custom script
Language: Python
"""
import time

def my_function():
    # Your logic here
    return {"result": "success"}

# Use context for parameters
param1 = context.get("param1", "default")

# Set result variable
result = my_function()
```

### Shell Scripts

```bash
#!/bin/bash
# My custom script
# Language: Shell

# Your logic here
output=$(command)

# Return result
echo "result = {'output': '$output'}"
```

### JavaScript Scripts (Node.js)

```javascript
/**
 * My custom script
 * Language: JavaScript
 */

async function myFunction() {
    // Your logic here
    return { result: "success" };
}

// Use context for parameters
const param1 = context.param1 || "default";

// Set result
const result = await myFunction();
```

## Context Variables

All scripts have access to a `context` dictionary/object containing parameters passed from the YAML:

```yaml
- name: my_step
  action: agent_execute
  agent: my-agent
  code_file: "agent_scripts/my_script.py"
  context:
    param1: "value1"
    param2: 123
    param3: true
```

Access in Python:
```python
param1 = context.get("param1")
param2 = context.get("param2", 0)
param3 = context.get("param3", False)
```

## Return Values

Scripts must set a `result` variable that will be returned to the test framework:

```python
result = {
    "status": "success",
    "duration": 1.23,
    "data": {...}
}
```

## Error Handling

Include proper error handling in scripts:

```python
try:
    # Your logic
    result = {"status": "success"}
except Exception as e:
    result = {
        "status": "error",
        "error": str(e)
    }
```

## Dependencies

If your script requires additional packages, install them on the agent:

```bash
# On the agent server
pip install psycopg2 psutil redis
```

Or include in agent deployment:
```yaml
# In agent package requirements.txt
psycopg2-binary==2.9.9
psutil==5.9.6
redis==5.0.1
```

## Best Practices

1. **Document** - Add docstrings and comments
2. **Validate** - Check context parameters
3. **Error handling** - Catch and report errors
4. **Logging** - Use print() for debug output
5. **Timeout** - Keep scripts under 60s by default
6. **Idempotent** - Scripts should be safe to re-run
7. **Return data** - Always set `result` variable

## Examples

See the `examples/` directory for complete test examples using these scripts:
- `06_external_agent_code.yml` - Basic external code usage
- `08_advanced_agents.yml` - Multi-agent coordination with external code
