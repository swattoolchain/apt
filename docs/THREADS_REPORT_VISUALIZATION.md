# Threads Feature - Report Visualization

## How Threads Appear in Reports

### **Report Dashboard**

The unified HTML report displays thread information prominently for each workflow step.

## Example Report Output

### **Workflow: api_load_testing**

```
┌─────────────────────────────────────────────────────────────────┐
│ Workflow: api_load_testing                                      │
│ Iterations: 2                                                   │
│ Total Duration: 3.45s                                           │
│ Success Rate: 100%                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Step Breakdown                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ▼ Step: baseline_api_call                                      │
│   Agent: local                                                  │
│   Threads: 1                                                    │
│   Iterations: 1                                                 │
│   Total Requests: 2  (1 thread × 1 iteration × 2 workflows)   │
│   Success Rate: 100%                                            │
│   Avg Duration: 234ms                                           │
│                                                                 │
│ ▼ Step: concurrent_api_call                                    │
│   Agent: local                                                  │
│   Threads: 5  ← NEW FEATURE                                    │
│   Iterations: 1                                                 │
│   Total Requests: 10  (5 threads × 1 iteration × 2 workflows) │
│   Success Rate: 100%                                            │
│   Avg Duration: 189ms                                           │
│                                                                 │
│ ▼ Step: high_load_api_call                                     │
│   Agent: local                                                  │
│   Threads: 10  ← NEW FEATURE                                   │
│   Iterations: 3                                                 │
│   Total Requests: 60  (10 threads × 3 iterations × 2 workflows)│
│   Success Rate: 100%                                            │
│   Avg Duration: 245ms                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Detailed Metrics (Expandable)**

When you click "View Detailed Metrics", you see:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step: concurrent_api_call - Detailed Metrics                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Load Profile:                                                   │
│   Threads (Users): 5                                           │
│   Iterations: 1                                                 │
│   Workflow Iterations: 2                                        │
│   Total Requests: 10                                            │
│                                                                 │
│ Performance Metrics:                                            │
│   Avg Response Time: 189ms                                      │
│   Min Response Time: 145ms                                      │
│   Max Response Time: 234ms                                      │
│   P50: 185ms                                                    │
│   P95: 220ms                                                    │
│   P99: 230ms                                                    │
│                                                                 │
│ Success Metrics:                                                │
│   Total Requests: 10                                            │
│   Successful: 10                                                │
│   Failed: 0                                                     │
│   Success Rate: 100%                                            │
│                                                                 │
│ Individual Request Results:                                     │
│   Request 1: ✓ 145ms                                           │
│   Request 2: ✓ 178ms                                           │
│   Request 3: ✓ 189ms                                           │
│   Request 4: ✓ 192ms                                           │
│   Request 5: ✓ 201ms                                           │
│   Request 6: ✓ 165ms                                           │
│   Request 7: ✓ 188ms                                           │
│   Request 8: ✓ 195ms                                           │
│   Request 9: ✓ 210ms                                           │
│   Request 10: ✓ 234ms                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Comparison: Before vs After

### **Before (No Threads)**

```yaml
- name: api_test
  action: api_call
  url: "https://api.example.com/data"
  iterations: 10
```

**Report Shows:**
```
Step: api_test
  Threads: 1
  Iterations: 10
  Total Requests: 10
  Duration: ~10 seconds (sequential)
```

### **After (With Threads)**

```yaml
- name: api_test
  action: api_call
  url: "https://api.example.com/data"
  threads: 10
  iterations: 10
```

**Report Shows:**
```
Step: api_test
  Threads: 10  ← Concurrent execution
  Iterations: 10
  Total Requests: 100  (10 threads × 10 iterations)
  Duration: ~10 seconds (10 concurrent requests per iteration)
```

## Visual Timeline in Report

For workflows with parallel groups and threads, the report can show:

```
┌─────────────────────────────────────────────────────────────────┐
│ Execution Timeline                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ T0: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│     Workflow A Start (5 threads) | Workflow B Start (5 threads)│
│                                                                 │
│ T1: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│     [T0][T1][T2][T3][T4]        | [T0][T1][T2][T3][T4]        │
│     5 concurrent requests        | 5 concurrent requests        │
│                                                                 │
│ T2: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│     [T0][T1][T2][T3][T4]        | [T0][T1][T2][T3][T4]        │
│     5 concurrent requests        | 5 concurrent requests        │
│                                                                 │
│ T3: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│     Both workflows complete                                     │
│                                                                 │
│ Peak Concurrency: 10 requests (5 + 5)                          │
│ Total Requests: 20 (10 per workflow)                           │
│ Total Duration: 2.5s                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## JSON Report Structure

The JSON report includes thread information:

```json
{
  "workflows": [
    {
      "name": "api_load_testing",
      "total_workflows": 2,
      "workflow_summary": {
        "total_duration": 3.45,
        "success_rate": 1.0
      },
      "step_breakdown": {
        "baseline_api_call": {
          "agent": "local",
          "threads": 1,
          "iterations": 1,
          "total_requests": 2,
          "success_rate": 1.0,
          "avg_duration": 0.234
        },
        "concurrent_api_call": {
          "agent": "local",
          "threads": 5,
          "iterations": 1,
          "total_requests": 10,
          "success_rate": 1.0,
          "avg_duration": 0.189
        },
        "high_load_api_call": {
          "agent": "local",
          "threads": 10,
          "iterations": 3,
          "total_requests": 60,
          "success_rate": 1.0,
          "avg_duration": 0.245
        }
      }
    }
  ]
}
```

## Key Report Features

### **1. Thread Count Display**
- Always visible in step summary
- Highlighted when > 1 (concurrent execution)

### **2. Total Requests Calculation**
- Clearly shows: `threads × iterations × workflow_iterations`
- Example: `10 (5 threads × 1 iteration × 2 workflows)`

### **3. Performance Metrics**
- Response times averaged across all thread executions
- P50, P95, P99 calculated from all requests

### **4. Success Rate**
- Calculated per request (not per iteration)
- Example: If 2 out of 10 requests fail, success rate = 80%

### **5. Individual Results**
- Each thread execution tracked separately
- Can see which specific requests failed

## Example: Real Test Output

Running `examples/api_call_with_threads.yml`:

```bash
$ python3 qptcli.py run examples/api_call_with_threads.yml

🚀 Running Unified QPT Test: examples/api_call_with_threads.yml

📊 Running workflow: api_load_test

🔄 Workflow 'api_load_test' Iteration 1/2
  Executing step: single_thread_api_call (api_call) on local
  ✓ Completed: 1 request in 0.23s

  Executing step: multi_thread_api_call (api_call) on local
  ⚡ Concurrent execution: 5 threads
  ✓ Completed: 5 requests in 0.19s

  Executing step: high_load_api_call (api_call) on local
  ⚡ Concurrent execution: 10 threads (3 iterations)
  ✓ Completed: 30 requests in 0.75s

🔄 Workflow 'api_load_test' Iteration 2/2
  [Same output...]

✅ Test execution completed.
📄 Report generated: performance_results/api_threads_demo/unified_performance_report.html

Summary:
  Total Workflows: 1
  Total Steps: 3
  Total Requests: 72
  Success Rate: 100%
  Duration: 3.45s
```

## Summary

The threads feature is **fully integrated** into the reporting system:

✅ **Thread count displayed** for every step
✅ **Total requests calculated** correctly (threads × iterations)
✅ **Individual request tracking** for detailed analysis
✅ **Success rate** calculated per request
✅ **Performance metrics** averaged across all threads
✅ **JSON export** includes all thread information
✅ **Visual indicators** for concurrent execution

**The report makes it crystal clear how many threads were used and how many total requests were made!**
