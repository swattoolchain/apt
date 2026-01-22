# Tool-Specific Metrics & Iterations Guide

## Overview

The unified YAML test now supports:
1. **Tool-specific metrics** - Different metrics for UI, k6, and JMeter
2. **Workflow-level iterations** - Repeat entire workflows
3. **Action-level iterations** - Repeat specific steps within workflows

---

## Tool-Specific Metrics

### UI Testing (Playwright)

**Primary Metrics:**
- `page_load_time` - Total page load time
- `dom_interactive` - Time to DOM interactive
- `dom_content_loaded` - DOMContentLoaded event
- `first_contentful_paint` - FCP
- `largest_contentful_paint` - LCP (Core Web Vital)

**Workflow Metrics:**
- `step_duration` - How long each step took
- `cumulative_time` - Running total
- `step_success_rate` - Success rate per step
- `total_workflow_time` - End-to-end time

### API Testing (k6)

**Primary Metrics:**
- `http_req_duration` - Request duration (avg, p50, p95, p99)
- `http_reqs` - Total requests & throughput
- `http_req_failed` - Failed request rate
- `vus` - Virtual users (concurrency)

**Percentiles:**
- p50, p75, p90, p95, p99

### API Testing (JMeter)

**Primary Metrics:**
- `avg_response_time` - Average response time
- `min_response_time` - Minimum
- `max_response_time` - Maximum
- `total_samples` - Total requests
- `success_rate` - Success percentage

---

## Iterations

### Workflow-Level Iterations

Repeat the **entire workflow** multiple times:

```yaml
ui_tests:
  login_workflow:
    - measure_workflow:
        name: "login_flow"
        iterations: 3              # Run whole workflow 3 times
        steps:
          - name: "navigate"
            action: "navigate"
            url: "https://example.com"
          - name: "login"
            action: "click"
            selector: "#login-btn"
```

**Report shows:**
- Average across all 3 workflow runs
- P50, P95, P99 for workflow completion time
- Success rate across iterations

### Action-Level Iterations

Repeat **specific actions** within a workflow:

```yaml
ui_tests:
  search_test:
    - measure_workflow:
        name: "search_flow"
        iterations: 2              # Run workflow 2 times
        steps:
          - name: "navigate"
            action: "navigate"
            url: "https://example.com"
            iterations: 1          # Navigate once per workflow
          
          - name: "search"
            action: "fill"
            selector: "#search"
            value: "test query"
            iterations: 5          # Search 5 times per workflow
          
          - name: "click_result"
            action: "click"
            selector: ".result:first"
            iterations: 3          # Click 3 different results
```

**Report shows:**
- Per-action timing (each search, each click)
- Cumulative time
- Action-level success rates

---

## Complete Example

```yaml
test_info:
  test_suite_name: "Complete Performance Test"
  test_suite_type: "unified"

# UI Tests with iterations
ui_tests:
  homepage_load: #smoke
    - measure_page_load:
        url: "https://example.com"
        iterations: 5              # Load page 5 times
        performance_config:
          ui:
            concurrent_users: 3
            headless: true

  login_workflow: #smoke
    - measure_workflow:
        name: "login_flow"
        iterations: 3              # Repeat workflow 3 times
        performance_config:
          ui:
            concurrent_users: 2
        steps:
          - name: "navigate"
            action: "navigate"
            url: "https://example.com/login"
            iterations: 1
          
          - name: "fill_username"
            action: "fill"
            selector: "#username"
            value: "admin"
            iterations: 1
          
          - name: "fill_password"
            action: "fill"
            selector: "#password"
            value: "password"
            iterations: 1
          
          - name: "click_login"
            action: "click"
            selector: "#login-btn"
            iterations: 2          # Try clicking twice (test retry)

# k6 Tests
k6_tests:
  api_load:
    tool: "k6"
    scenarios:
      - name: "Health Check"
        url: "https://api.example.com/health"
        method: "GET"
    options:
      vus: 10
      duration: "30s"

# JMeter Tests
jmeter_tests:
  api_stress:
    tool: "jmeter"
    scenarios:
      - name: "API Endpoint"
        url: "https://api.example.com/data"
        method: "GET"
    thread_group_config:
      num_threads: 20
      duration: 60

# Reporting with tool-specific metrics
reporting:
  unified_report: true
  metrics:
    ui:
      primary:
        - page_load_time
        - largest_contentful_paint
      workflow:
        - step_duration
        - cumulative_time
        - total_workflow_time
    
    k6:
      primary:
        - http_req_duration
        - http_reqs
      percentiles:
        - p50
        - p95
        - p99
    
    jmeter:
      primary:
        - avg_response_time
        - total_samples
        - success_rate
```

---

## Report Output

### UI Performance Section

```
Homepage Load (5 iterations)
├── Avg: 2.34s
├── P50: 2.21s
├── P95: 2.89s
├── P99: 3.12s
└── Metrics:
    ├── Page Load Time: 2.34s
    ├── DOM Interactive: 1.45s
    ├── FCP: 0.89s
    └── LCP: 1.67s

Login Workflow (3 iterations)
├── Total Workflow Time: 4.56s (avg)
├── Step Breakdown:
│   ├── navigate: 1.23s (100% success)
│   ├── fill_username: 0.12s (100% success)
│   ├── fill_password: 0.11s (100% success)
│   └── click_login: 0.45s × 2 = 0.90s (100% success)
└── Cumulative: 4.56s
```

### k6 Performance Section

```
API Load Test (10 VUs, 30s)
├── Total Requests: 1,234
├── Throughput: 41.13 req/s
├── HTTP Request Duration:
│   ├── Avg: 243ms
│   ├── P50: 221ms
│   ├── P95: 456ms
│   └── P99: 678ms
└── Failed Requests: 0.2%
```

### JMeter Performance Section

```
API Stress Test (20 threads, 60s)
├── Total Samples: 2,456
├── Avg Response Time: 312ms
├── Min/Max: 89ms / 1,234ms
├── Success Rate: 99.8%
└── Throughput: 40.93 req/s
```

---

## Benefits

✅ **Tool-Specific Metrics** - Each tool shows its relevant metrics
✅ **Workflow Iterations** - Test reliability with multiple runs
✅ **Action Iterations** - Test specific interactions repeatedly
✅ **Meaningful Reports** - Clear breakdown of what was tested and how
✅ **Statistical Validity** - Multiple iterations provide better data

---

## Run It

```bash
pytest tests/definitions/unified_performance_test.yml -v -s
```

View the unified report with all tool-specific metrics!
