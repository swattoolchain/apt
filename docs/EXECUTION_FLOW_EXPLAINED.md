# Execution Flow: Parallel Groups + Threads + Loops

## Scenario: Understanding the Complete Execution Flow

Let's break down exactly what happens with:
- **5 threads**
- **2 loops (iterations)**
- **2 workflows** in parallel execution groups

## Example Configuration

```yaml
workflows:
  workflow_A:
    group: "parallel_group_1"  # Same group = parallel execution
    iterations: 2  # Workflow runs 2 times
    steps:
      - name: api_test_A
        action: api_call
        url: "https://api.example.com/endpoint-a"
        threads: 5  # 5 concurrent threads
        iterations: 2  # Each thread iteration repeats 2 times

  workflow_B:
    group: "parallel_group_1"  # Same group = parallel execution
    iterations: 2  # Workflow runs 2 times
    steps:
      - name: api_test_B
        action: api_call
        url: "https://api.example.com/endpoint-b"
        threads: 5  # 5 concurrent threads
        iterations: 2  # Each thread iteration repeats 2 times
```

## Execution Flow Breakdown

### **Level 1: Parallel Group Execution**

```
┌─────────────────────────────────────────────────────────────┐
│ Parallel Group: "parallel_group_1"                          │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   Workflow A         │    │   Workflow B         │      │
│  │   (runs in parallel) │    │   (runs in parallel) │      │
│  └──────────────────────┘    └──────────────────────┘      │
│           ↓                            ↓                     │
│    Both start at                Both start at               │
│    the SAME time                the SAME time               │
└─────────────────────────────────────────────────────────────┘
```

### **Level 2: Workflow Iterations**

Each workflow runs `iterations: 2` times **sequentially**:

```
Workflow A:
  Iteration 1 → Iteration 2
  
Workflow B (in parallel):
  Iteration 1 → Iteration 2
```

### **Level 3: Step Iterations**

Within each workflow iteration, the step runs `iterations: 2` times:

```
Workflow A - Iteration 1:
  Step Iteration 1 → Step Iteration 2
  
Workflow A - Iteration 2:
  Step Iteration 1 → Step Iteration 2
```

### **Level 4: Thread Execution**

Within each step iteration, `threads: 5` execute **concurrently**:

```
Step Iteration 1:
  ┌─────────────────────────────────────────┐
  │  Thread 0  Thread 1  Thread 2  Thread 3  Thread 4  │
  │     ↓         ↓         ↓         ↓         ↓      │
  │  Request  Request  Request  Request  Request │
  │  (all 5 execute at the SAME time)          │
  └─────────────────────────────────────────┘
```

## Complete Execution Timeline

```
TIME →

T0: ┌─────────────────────────────────────────────────────────┐
    │ PARALLEL GROUP START                                     │
    │                                                          │
    │ Workflow A (Start)          Workflow B (Start)          │
    └─────────────────────────────────────────────────────────┘

T1: ┌─────────────────────────────────────────────────────────┐
    │ Workflow A - Iteration 1    Workflow B - Iteration 1    │
    │   Step Iteration 1            Step Iteration 1          │
    │     5 threads (concurrent)      5 threads (concurrent)  │
    │     [T0][T1][T2][T3][T4]       [T0][T1][T2][T3][T4]    │
    └─────────────────────────────────────────────────────────┘

T2: ┌─────────────────────────────────────────────────────────┐
    │ Workflow A - Iteration 1    Workflow B - Iteration 1    │
    │   Step Iteration 2            Step Iteration 2          │
    │     5 threads (concurrent)      5 threads (concurrent)  │
    │     [T0][T1][T2][T3][T4]       [T0][T1][T2][T3][T4]    │
    └─────────────────────────────────────────────────────────┘

T3: ┌─────────────────────────────────────────────────────────┐
    │ Workflow A - Iteration 2    Workflow B - Iteration 2    │
    │   Step Iteration 1            Step Iteration 1          │
    │     5 threads (concurrent)      5 threads (concurrent)  │
    │     [T0][T1][T2][T3][T4]       [T0][T1][T2][T3][T4]    │
    └─────────────────────────────────────────────────────────┘

T4: ┌─────────────────────────────────────────────────────────┐
    │ Workflow A - Iteration 2    Workflow B - Iteration 2    │
    │   Step Iteration 2            Step Iteration 2          │
    │     5 threads (concurrent)      5 threads (concurrent)  │
    │     [T0][T1][T2][T3][T4]       [T0][T1][T2][T3][T4]    │
    └─────────────────────────────────────────────────────────┘

T5: ┌─────────────────────────────────────────────────────────┐
    │ PARALLEL GROUP END                                       │
    │ (waits for both workflows to complete)                  │
    └─────────────────────────────────────────────────────────┘
```

## Total Requests Calculation

### **For Workflow A:**
```
Total Requests = threads × step_iterations × workflow_iterations
               = 5 × 2 × 2
               = 20 requests
```

### **For Workflow B:**
```
Total Requests = threads × step_iterations × workflow_iterations
               = 5 × 2 × 2
               = 20 requests
```

### **Grand Total:**
```
Total Requests = Workflow A + Workflow B
               = 20 + 20
               = 40 requests
```

## Detailed Execution Breakdown

### **Workflow A Execution:**

| Workflow Iter | Step Iter | Threads | Requests | Timing |
|---------------|-----------|---------|----------|--------|
| 1 | 1 | 5 | 5 | T1 (concurrent) |
| 1 | 2 | 5 | 5 | T2 (concurrent) |
| 2 | 1 | 5 | 5 | T3 (concurrent) |
| 2 | 2 | 5 | 5 | T4 (concurrent) |
| **Total** | | | **20** | |

### **Workflow B Execution (in parallel):**

| Workflow Iter | Step Iter | Threads | Requests | Timing |
|---------------|-----------|---------|----------|--------|
| 1 | 1 | 5 | 5 | T1 (concurrent) |
| 1 | 2 | 5 | 5 | T2 (concurrent) |
| 2 | 1 | 5 | 5 | T3 (concurrent) |
| 2 | 2 | 5 | 5 | T4 (concurrent) |
| **Total** | | | **20** | |

## Key Execution Rules

### 1. **Parallel Groups Execute Concurrently**
```yaml
workflow_A:
  group: "group_1"  # ← Same group
  
workflow_B:
  group: "group_1"  # ← Same group
```
**Result**: Both workflows start at the same time and run in parallel.

### 2. **Workflow Iterations Execute Sequentially**
```yaml
workflow_A:
  iterations: 2  # Iteration 1 → Iteration 2 (sequential)
```
**Result**: Iteration 2 starts only after Iteration 1 completes.

### 3. **Step Iterations Execute Sequentially**
```yaml
steps:
  - name: api_test
    iterations: 2  # Step Iter 1 → Step Iter 2 (sequential)
```
**Result**: Step Iteration 2 starts only after Step Iteration 1 completes.

### 4. **Threads Execute Concurrently**
```yaml
steps:
  - name: api_test
    threads: 5  # All 5 threads execute at the same time
```
**Result**: All 5 threads start simultaneously and run in parallel.

## Execution Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ PARALLEL GROUPS (Concurrent)                                │
│   ├─ Workflow A (parallel with B)                          │
│   │   └─ Workflow Iterations (Sequential)                  │
│   │       └─ Step Iterations (Sequential)                  │
│   │           └─ Threads (Concurrent) ← 5 at once         │
│   │                                                         │
│   └─ Workflow B (parallel with A)                          │
│       └─ Workflow Iterations (Sequential)                  │
│           └─ Step Iterations (Sequential)                  │
│               └─ Threads (Concurrent) ← 5 at once         │
└─────────────────────────────────────────────────────────────┘
```

## Real-World Example

### Configuration:
```yaml
workflows:
  us_region_load:
    group: "global_attack"
    iterations: 2
    steps:
      - name: us_api_test
        action: api_call
        url: "https://us-api.example.com/data"
        threads: 5
        iterations: 2

  eu_region_load:
    group: "global_attack"
    iterations: 2
    steps:
      - name: eu_api_test
        action: api_call
        url: "https://eu-api.example.com/data"
        threads: 5
        iterations: 2
```

### Execution:
```
T0: Both workflows start simultaneously
    ↓
T1: US Region: 5 concurrent requests to US API
    EU Region: 5 concurrent requests to EU API (at the same time)
    ↓
T2: US Region: 5 concurrent requests to US API (2nd step iteration)
    EU Region: 5 concurrent requests to EU API (2nd step iteration)
    ↓
T3: US Region: 5 concurrent requests to US API (2nd workflow iteration)
    EU Region: 5 concurrent requests to EU API (2nd workflow iteration)
    ↓
T4: US Region: 5 concurrent requests to US API (final)
    EU Region: 5 concurrent requests to EU API (final)
    ↓
T5: Both workflows complete
```

**Total**: 40 requests (20 to US API + 20 to EU API)

## Performance Implications

### **Peak Concurrency**
At any given moment, the maximum concurrent requests is:
```
Peak Concurrency = Sum of threads across all parallel workflows
                 = 5 (Workflow A) + 5 (Workflow B)
                 = 10 concurrent requests
```

### **Duration**
Assuming each request takes ~1 second:
```
Duration ≈ (workflow_iterations × step_iterations × avg_request_time)
         ≈ (2 × 2 × 1s)
         ≈ 4 seconds
```

**Note**: Both workflows run in parallel, so total time ≈ 4 seconds (not 8 seconds).

## Summary

### **Execution Order:**
1. **Parallel Groups** → Start simultaneously
2. **Workflow Iterations** → Sequential (one after another)
3. **Step Iterations** → Sequential (one after another)
4. **Threads** → Concurrent (all at once)

### **For Your Example (5 threads, 2 loops, 2 workflows in parallel group):**
- **Total Requests**: 40 (20 per workflow)
- **Peak Concurrency**: 10 (5 + 5 from both workflows)
- **Execution Time**: ~4 seconds (if each request takes 1s)
- **Parallelism**: Workflows run in parallel, threads within each workflow run concurrently

### **Key Takeaway:**
```
Parallel Groups = Workflows run at the SAME time
Threads = Requests run at the SAME time
Iterations = Requests run ONE AFTER ANOTHER
```

This gives you fine-grained control over load patterns!
