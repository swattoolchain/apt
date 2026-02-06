# Threads Support for API Calls and Custom Actions

## Overview

**ALL actions** now support the `threads` parameter for concurrent execution:
- `api_call` - HTTP API calls
- `agent_execute` - Custom validation methods and remote code execution
- `k6_test` - Already supported via `vus` parameter
- `jmeter_test` - Already supported via `threads` parameter

## Key Concept: Threads × Iterations = Total Requests

```
Total Requests = threads × step_iterations × workflow_iterations
```

### Example Calculation:
```yaml
workflows:
  my_workflow:
    iterations: 2  # Workflow runs 2 times
    steps:
      - name: api_test
        action: api_call
        url: "https://api.example.com/data"
        threads: 5      # 5 concurrent threads
        iterations: 3   # Each iteration repeats 3 times
```

**Total Requests** = 5 threads × 3 step iterations × 2 workflow iterations = **30 requests**

## Implementation Details

### 1. API Call Action

**Before (Sequential)**:
```yaml
- name: api_test
  action: api_call
  url: "https://api.example.com/data"
  iterations: 10
# Result: 10 sequential requests
```

**After (Concurrent)**:
```yaml
- name: api_test
  action: api_call
  url: "https://api.example.com/data"
  threads: 5       # NEW: 5 concurrent threads
  iterations: 10   # 10 iterations
# Result: 5 threads × 10 iterations = 50 total requests (5 at a time)
```

### 2. Agent Execute Action

**Before (Single Execution)**:
```yaml
- name: custom_validation
  action: agent_execute
  agent: jmeter-server
  context:
    env: "production"
# Result: 1 execution
```

**After (Concurrent Execution)**:
```yaml
- name: custom_validation
  action: agent_execute
  agent: jmeter-server
  threads: 10      # NEW: 10 concurrent executions
  context:
    env: "production"
# Result: 10 concurrent executions
```

## Usage Examples

### Example 1: Simple API Load Test
```yaml
workflows:
  simple_load:
    iterations: 1
    steps:
      - name: load_test
        action: api_call
        url: "https://jsonplaceholder.typicode.com/posts"
        method: GET
        threads: 20  # 20 concurrent users
# Total: 20 requests
```

### Example 2: Ramped Load Test
```yaml
workflows:
  ramped_load:
    iterations: 1
    steps:
      # Phase 1: Light load
      - name: phase_1_light
        action: api_call
        url: "https://api.example.com/data"
        threads: 5
        iterations: 10
      # Total: 5 × 10 = 50 requests
      
      # Phase 2: Medium load
      - name: phase_2_medium
        action: api_call
        url: "https://api.example.com/data"
        threads: 20
        iterations: 10
      # Total: 20 × 10 = 200 requests
      
      # Phase 3: Heavy load
      - name: phase_3_heavy
        action: api_call
        url: "https://api.example.com/data"
        threads: 50
        iterations: 10
      # Total: 50 × 10 = 500 requests
```

### Example 3: Custom Validation with Threads
```yaml
workflows:
  validation_test:
    iterations: 1
    steps:
      - name: concurrent_validation
        action: agent_execute
        agent: validation-server
        threads: 10  # 10 concurrent validations
        code: |
          import requests
          import time
          
          # This code runs 10 times concurrently
          start = time.time()
          response = requests.get('https://api.example.com/validate')
          duration = time.time() - start
          
          result = {
              'success': response.status_code == 200,
              'duration': duration,
              'data': response.json()
          }
```

### Example 4: Mixed Load Profile
```yaml
workflows:
  mixed_load:
    iterations: 3  # Repeat entire workflow 3 times
    steps:
      # API calls with different thread counts
      - name: endpoint_a
        action: api_call
        url: "https://api.example.com/endpoint-a"
        threads: 5
      # 5 threads × 3 workflow iterations = 15 requests
      
      - name: endpoint_b
        action: api_call
        url: "https://api.example.com/endpoint-b"
        threads: 10
        iterations: 2
      # 10 threads × 2 step iterations × 3 workflow iterations = 60 requests
      
      - name: endpoint_c
        action: api_call
        url: "https://api.example.com/endpoint-c"
        threads: 20
      # 20 threads × 3 workflow iterations = 60 requests
```

## How It Works

### API Call Execution Flow

1. **Parse Configuration**:
   ```python
   num_threads = step.get('threads', 1)  # Default: 1
   step_iterations = step.get('iterations', 1)  # Default: 1
   ```

2. **Execute Concurrently**:
   ```python
   for iteration in range(step_iterations):
       if num_threads > 1:
           # Create concurrent tasks
           tasks = [execute_api_call(...) for _ in range(num_threads)]
           results = await asyncio.gather(*tasks)
       else:
           # Single thread
           result = await execute_api_call(...)
   ```

3. **Track Results**:
   ```python
   total_requests = len(step_results)  # threads × iterations
   success_rate = success_count / total_requests
   ```

### Agent Execute Execution Flow

1. **Parse Configuration**:
   ```python
   num_threads = step.get('threads', 1)
   ```

2. **Execute on Agent**:
   ```python
   for iteration in range(step_iterations):
       if num_threads > 1:
           # Concurrent execution on agent
           tasks = [
               client.execute(code, context={'thread_id': i})
               for i in range(num_threads)
           ]
           results = await asyncio.gather(*tasks)
   ```

3. **Each thread gets**:
   - Unique `thread_id` in context
   - Separate result tracking
   - Individual success/failure status

## Reporting

Reports now show:

### Workflow Step Summary
```
Step: multi_thread_api_call
  Agent: local
  Threads: 5
  Iterations: 2
  Total Requests: 10  (5 threads × 2 iterations)
  Success Rate: 100%
  Total Duration: 2.5s
```

### Detailed Metrics
- **Threads**: Number of concurrent executions
- **Iterations**: Number of times to repeat
- **Total Requests**: threads × iterations × workflow_iterations
- **Success Rate**: Percentage of successful requests
- **Avg Response Time**: Average across all requests

## Default Behavior

**If `threads` parameter is NOT specified:**
- Defaults to `threads: 1` (single thread)
- Executes sequentially
- Backward compatible with existing tests

## Comparison with k6 and JMeter

| Action | Thread Parameter | Default |
|--------|------------------|---------|
| `api_call` | `threads` | 1 |
| `agent_execute` | `threads` | 1 |
| `k6_test` | `options.vus` | 1 |
| `jmeter_test` | `thread_group_config.threads` | 1 |

**All actions now have consistent thread support!**

## Best Practices

### 1. Start Small
```yaml
# Start with low thread count
- name: baseline_test
  action: api_call
  url: "https://api.example.com/data"
  threads: 1
  iterations: 10
```

### 2. Ramp Up Gradually
```yaml
# Gradually increase load
- name: ramp_phase_1
  threads: 5
  
- name: ramp_phase_2
  threads: 10
  
- name: ramp_phase_3
  threads: 20
```

### 3. Monitor Resource Usage
- Watch CPU and memory on both client and server
- Monitor network bandwidth
- Check for connection pool exhaustion

### 4. Use Realistic Thread Counts
- **Light load**: 1-10 threads
- **Medium load**: 10-50 threads
- **Heavy load**: 50-200 threads
- **Stress test**: 200+ threads

### 5. Combine with Iterations
```yaml
# Better: Moderate threads, multiple iterations
- name: sustained_load
  threads: 20
  iterations: 100
# Total: 2000 requests over time

# Avoid: Too many threads at once
- name: spike_load
  threads: 2000
  iterations: 1
# May overwhelm system
```

## Troubleshooting

### Issue: "Too many open files"
**Cause**: Thread count too high
**Solution**: Reduce `threads` or increase system limits

### Issue: Slow execution despite high thread count
**Cause**: Network/CPU bottleneck
**Solution**: Monitor resources, reduce threads

### Issue: Inconsistent results
**Cause**: Server rate limiting or resource contention
**Solution**: Add delays between iterations or reduce threads

## Migration Guide

### Existing Tests (No Changes Required)
```yaml
# This still works exactly as before
- name: old_test
  action: api_call
  url: "https://api.example.com/data"
  iterations: 10
# Executes sequentially (threads defaults to 1)
```

### Adding Concurrent Execution
```yaml
# Simply add threads parameter
- name: new_test
  action: api_call
  url: "https://api.example.com/data"
  threads: 5      # NEW
  iterations: 10
# Now executes 5 at a time
```

## Summary

✅ **All actions support `threads` parameter**
✅ **Default is 1 (backward compatible)**
✅ **Total requests = threads × iterations × workflow_iterations**
✅ **Proper tracking in reports**
✅ **Works for both local and remote execution**

**Example from your file**:
```yaml
- name: custom_validation
  action: agent_execute
  agent: jmeter-server
  threads: 5  # ← Add this to run 5 concurrent executions
  context:
    env: "production"
```

**Result**: 5 concurrent executions instead of 1!
