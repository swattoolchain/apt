# YAML-Based Performance Test Definitions

## Overview

Define performance tests using YAML files with scenario-level configuration. This approach provides:

- ✅ **Declarative test definitions** - No code required for common scenarios
- ✅ **Scenario-level configuration** - Override settings per scenario
- ✅ **Tag-based filtering** - Run specific test subsets
- ✅ **Lightweight mode** - Optimize for high concurrency
- ✅ **Selective tracing** - Save traces only for failures

---

## File Structure

```
tests/performance/definitions/
├── ui_grid_performance.yml          # UI performance tests
├── api_visualization_performance.yml # API performance tests
└── custom_scenarios.yml             # Your custom tests
```

---

## YAML Test Definition Format

```yaml
test_info:
  test_suite_name: "My Performance Tests"
  test_suite_type: "ui_performance"  # or "api_performance"
  module: "Module Name"
  description: "Test description"

# Global configuration (applies to all scenarios unless overridden)
performance_config:
  ui:
    concurrent_users: 5
    iterations: 3
    headless: false
    screenshots: true
    traces: true
    lightweight_mode: false
    trace_on_failure_only: false
  
  thresholds:
    page_load_time: 5.0
    error_rate: 0.05

scenarios:
  scenario_name: #tag1, tag2, tag3
    - action_name:
        # Action parameters
        url: "https://example.com"
        iterations: 3
        
        # Scenario-specific config (overrides global)
        performance_config:
          ui:
            concurrent_users: 10
            lightweight_mode: true
```

---

## UI Performance Test Actions

### 1. measure_page_load

Measure page load performance.

```yaml
scenarios:
  login_page_load:
    - measure_page_load:
        url: "https://example.com/login"
        wait_until: "networkidle"  # or "load", "domcontentloaded"
        iterations: 3
```

### 2. measure_action

Measure custom user actions (requires implementation).

```yaml
scenarios:
  user_workflow:
    - measure_action:
        name: "complete_checkout"
        iterations: 2
```

---

## API Performance Test Actions

### 1. measure_request

Measure single API request.

```yaml
scenarios:
  api_test:
    - measure_request:
        url: "https://api.example.com/endpoint"
        method: "POST"
        headers:
          Content-Type: "application/json"
        body:
          key: "value"
        iterations: 5
```

### 2. measure_concurrent

Measure concurrent API requests.

```yaml
scenarios:
  load_test:
    - measure_concurrent:
        url: "https://api.example.com/endpoint"
        method: "GET"
        concurrent_users: 20
```

---

## Scenario-Level Configuration

Override global config for specific scenarios:

```yaml
scenarios:
  # Lightweight scenario for high concurrency
  high_concurrency_test:
    - measure_page_load:
        url: "https://example.com"
        performance_config:
          ui:
            concurrent_users: 50
            headless: true
            screenshots: false
            traces: false
            lightweight_mode: true  # Skip heavy metrics
  
  # Detailed scenario with full metrics
  detailed_test:
    - measure_page_load:
        url: "https://example.com/dashboard"
        performance_config:
          ui:
            concurrent_users: 2
            screenshots: true
            traces: true
            trace_on_failure_only: true  # Only save traces if test fails
            lightweight_mode: false
```

---

## Configuration Options

### UI Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `concurrent_users` | int | 5 | Number of concurrent browser instances |
| `iterations` | int | 3 | Number of times to run each test |
| `headless` | bool | false | Run browser in headless mode |
| `screenshots` | bool | true | Capture screenshots |
| `traces` | bool | true | Generate Playwright traces |
| `lightweight_mode` | bool | false | Skip heavy metrics (for high concurrency) |
| `trace_on_failure_only` | bool | false | Only save traces for failed tests |
| `viewport` | dict | {width: 1920, height: 1080} | Browser viewport size |
| `timeout` | int | 60000 | Page load timeout (milliseconds) |

### API Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `concurrent_requests` | int | 10 | Number of concurrent requests |
| `iterations` | int | 5 | Number of times to run each test |
| `timeout` | int | 30 | Request timeout (seconds) |

### Thresholds

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `page_load_time` | float | 5.0 | Max page load time (seconds) |
| `api_response_time` | float | 2.0 | Max API response time (seconds) |
| `error_rate` | float | 0.05 | Max error rate (5%) |

---

## Running Tests

### Run All Tests

```bash
pytest tests/performance/definitions/ -v
```

### Run Specific File

```bash
pytest tests/performance/definitions/ui_grid_performance.yml -v
```

### Filter by Tags

```bash
# Run only smoke and p1 tests
pytest tests/performance/definitions/ --perf-tags=smoke,p1 -v

# Exclude disabled tests
pytest tests/performance/definitions/ --perf-exclude-tags=disabled -v

# Combine filters
pytest tests/performance/definitions/ --perf-tags=smoke --perf-exclude-tags=disabled,wip -v
```

### Parallel Execution

```bash
# Run with 4 parallel workers
pytest tests/performance/definitions/ -v -n 4
```

---

## Tag Examples

Add tags to scenario names using `#` syntax:

```yaml
scenarios:
  login_test: #smoke, p1, regression
    - measure_page_load:
        url: "https://example.com/login"
  
  stress_test: #load, p3, disabled
    - measure_concurrent:
        concurrent_users: 100
```

**Common Tags:**
- `smoke` - Quick smoke tests
- `p1`, `p2`, `p3` - Priority levels
- `regression` - Regression test suite
- `load` - Load testing scenarios
- `stress` - Stress testing scenarios
- `disabled` - Temporarily disabled tests
- `wip` - Work in progress

---

## Lightweight Mode for High Concurrency

When testing with 50+ concurrent users, use lightweight mode:

```yaml
scenarios:
  high_load_test:
    - measure_page_load:
        url: "https://example.com"
        performance_config:
          ui:
            concurrent_users: 100
            headless: true
            screenshots: false
            traces: false
            lightweight_mode: true  # Only collect basic timing metrics
```

**Lightweight mode skips:**
- Resource timing (can be 100+ resources)
- Memory metrics
- Core Web Vitals
- Screenshots
- Traces

**Lightweight mode keeps:**
- Navigation timing (DNS, TCP, DOM loading)
- Page load duration
- Error tracking

---

## Selective Tracing

Save disk space by only generating traces for failed tests:

```yaml
scenarios:
  my_test:
    - measure_page_load:
        url: "https://example.com"
        performance_config:
          ui:
            traces: true
            trace_on_failure_only: true  # Only save if test fails
```

---

## Template Variables

Use Jinja2-style templates for dynamic values:

```yaml
scenarios:
  api_test:
    - measure_request:
        url: "https://api.example.com/data"
        body:
          timeRange:
            fromTimestamp: "{{get_timestamp(-24,'hours')}}"
            toTimestamp: "{{get_timestamp(0,'hours')}}"
```

**Available functions:**
- `{{get_timestamp(offset, unit)}}` - Get timestamp with offset

---

## Example: Complete Test Definition

```yaml
test_info:
  test_suite_name: "E-commerce Performance Tests"
  test_suite_type: "ui_performance"
  module: "E-commerce"

performance_config:
  ui:
    concurrent_users: 3
    iterations: 2
    headless: false
    screenshots: true
    traces: true
  
  thresholds:
    page_load_time: 3.0
    error_rate: 0.02

scenarios:
  # Quick smoke test
  homepage_load: #smoke, p1
    - measure_page_load:
        url: "https://shop.example.com"
        wait_until: "networkidle"
        iterations: 3
  
  # Load test with high concurrency
  checkout_load_test: #load, p2
    - measure_page_load:
        url: "https://shop.example.com/checkout"
        iterations: 1
        performance_config:
          ui:
            concurrent_users: 20
            headless: true
            lightweight_mode: true
            screenshots: false
            traces: false
  
  # Detailed test with full metrics
  product_page: #regression, p1
    - measure_page_load:
        url: "https://shop.example.com/products/123"
        iterations: 2
        performance_config:
          ui:
            concurrent_users: 2
            screenshots: true
            traces: true
            trace_on_failure_only: true
```

---

## Best Practices

1. **Use lightweight mode for high concurrency** (50+ users)
2. **Enable trace_on_failure_only** to save disk space
3. **Tag scenarios** for easy filtering
4. **Set realistic thresholds** based on your SLAs
5. **Run smoke tests frequently**, load tests periodically
6. **Use headless mode in CI/CD** for faster execution
7. **Keep iterations low** for quick feedback (2-3 iterations)

---

## Troubleshooting

### Tests not discovered

Ensure YAML files are in `tests/performance/definitions/` directory.

### Tags not working

Check tag syntax: `scenario_name: #tag1, tag2` (space after colon, comma-separated).

### High memory usage

Enable lightweight mode and disable traces/screenshots for high concurrency tests.

### Slow test execution

- Use `headless: true`
- Reduce `iterations`
- Use `wait_until: "domcontentloaded"` instead of `"networkidle"`

---

## Next Steps

1. Create your own YAML test definitions
2. Run tests: `pytest tests/performance/definitions/ -v`
3. View reports: `open performance_results/test_run_*/performance_report.html`
4. Integrate with CI/CD pipeline
