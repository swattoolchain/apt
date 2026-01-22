# Advanced Features Guide

## Complete Reference for All Performance Testing Features

---

## Table of Contents

1. [Granular Step-by-Step Tracking](#granular-step-by-step-tracking)
2. [Baseline Comparison & Trend Analysis](#baseline-comparison--trend-analysis)
3. [Custom Performance Marks](#custom-performance-marks)
4. [External Tool Integration](#external-tool-integration)
5. [Enhanced Reporting](#enhanced-reporting)
6. [Performance Metrics Reference](#performance-metrics-reference)

---

## Granular Step-by-Step Tracking

### Overview

Track performance of individual steps in a workflow to identify bottlenecks.

### YAML Definition

```yaml
scenarios:
  detailed_checkout: #p1
    - measure_workflow:
        name: "checkout_process"
        steps:
          - name: "load_cart"
            action: "navigate"
            url: "https://example.com/cart"
          
          - name: "fill_shipping"
            action: "fill_form"
            fields:
              address: "123 Main St"
              city: "New York"
          
          - name: "select_payment"
            action: "click"
            selector: "#credit-card"
          
          - name: "submit_order"
            action: "click"
            selector: "#submit-order"
```

### Python Implementation

```python
from performance.enhanced_ui_tester import EnhancedUIPerformanceTester

async def test_checkout_steps(performance_config):
    tester = EnhancedUIPerformanceTester(performance_config)
    await tester.setup()
    
    # Define steps
    steps = [
        {'name': 'load_cart', 'action': lambda p: p.goto("https://example.com/cart")},
        {'name': 'fill_shipping', 'action': lambda p: p.fill('#address', '123 Main St')},
        {'name': 'select_payment', 'action': lambda p: p.click('#credit-card')},
        {'name': 'submit_order', 'action': lambda p: p.click('#submit')}
    ]
    
    metrics = await tester.measure_workflow_steps(steps, "checkout")
    
    # Access step timings
    for step in metrics.metrics['step_timings']:
        print(f"{step['step']}: {step['duration']:.3f}s")
    
    await tester.teardown()
```

### Output

```
📊 Step-by-Step Performance:
============================================================
✓ load_cart                   1.234s (cumulative: 1.234s)
✓ fill_shipping               0.156s (cumulative: 1.390s)
✓ select_payment              0.089s (cumulative: 1.479s)
✓ submit_order                0.567s (cumulative: 2.046s)
============================================================
Total Workflow Time: 2.046s
```

---

## Baseline Comparison & Trend Analysis

### Save Baseline

```python
from performance.comparison_tracker import PerformanceComparison

comparison = PerformanceComparison()

# Save current performance as baseline
comparison.save_baseline(
    test_name="login_flow",
    metrics={
        'page_load': 2.1,
        'login_time': 0.5,
        'dashboard_load': 1.2
    },
    metadata={
        'environment': 'qa',
        'git_commit': 'abc123',
        'date': '2024-01-15'
    }
)
```

### Compare with Baseline

```python
# Run test and get current metrics
current_metrics = {
    'page_load': 2.5,      # 19% slower
    'login_time': 0.45,    # 10% faster
    'dashboard_load': 1.5  # 25% slower
}

# Compare
result = comparison.compare("login_flow", current_metrics, regression_threshold=10.0)

# Check for regressions
if result['summary']['has_regressions']:
    print(f"⚠️  {result['summary']['regressions']} regressions detected!")
    
    for regression in result['regressions']:
        print(f"   {regression['metric']}: {regression['change_pct']:+.1f}% slower")
        print(f"      Baseline: {regression['baseline']:.3f}s")
        print(f"      Current:  {regression['current']:.3f}s")
```

### Track Trends

```python
# Append to history after each run
comparison.append_to_history(
    test_name="login_flow",
    metrics=current_metrics,
    metadata={'build': '1234'}
)

# Get trend data
trend = comparison.get_trend("login_flow", "page_load")

print(f"Average: {trend['average']:.3f}s")
print(f"Min: {trend['min']:.3f}s")
print(f"Max: {trend['max']:.3f}s")
print(f"Data points: {trend['data_points']}")
```

---

## Custom Performance Marks

### Browser Performance Marks

Use browser's Performance API for precise measurements:

```python
async def test_with_marks(performance_config):
    tester = EnhancedUIPerformanceTester(performance_config)
    await tester.setup()
    
    async def action_with_marks(page):
        # Mark specific points
        await page.evaluate('performance.mark("start")')
        
        await page.goto("https://example.com")
        await page.evaluate('performance.mark("page-loaded")')
        
        await page.click('#button')
        await page.evaluate('performance.mark("button-clicked")')
        
        await page.wait_for_selector('.result')
        await page.evaluate('performance.mark("result-shown")')
    
    metrics = await tester.measure_with_custom_marks(
        action_func=action_with_marks,
        marks=['start', 'page-loaded', 'button-clicked', 'result-shown'],
        test_name="custom_marks"
    )
    
    # Access measures
    for measure in metrics.metrics['custom_measures']:
        print(f"{measure['name']}: {measure['duration']:.3f}ms")
    
    await tester.teardown()
```

---

## External Tool Integration

### k6 Integration

#### Generate k6 Script

```python
from performance.external_integrations import K6Integration

scenarios = [
    {
        'name': 'Get Users',
        'url': 'https://api.example.com/users',
        'method': 'GET',
        'headers': {'Authorization': 'Bearer token'}
    },
    {
        'name': 'Create User',
        'url': 'https://api.example.com/users',
        'method': 'POST',
        'headers': {'Content-Type': 'application/json'},
        'body': {'name': 'John', 'email': 'john@example.com'}
    }
]

script = K6Integration.generate_k6_script(
    test_name="API Load Test",
    scenarios=scenarios,
    options={
        'vus': 50,              # 50 virtual users
        'duration': '60s',      # Run for 60 seconds
        'thresholds': {
            'http_req_duration': ['p(95)<500'],  # 95% under 500ms
            'http_req_failed': ['rate<0.01']     # Error rate < 1%
        }
    }
)

K6Integration.save_k6_script(script, "load_test.js")
```

#### Run k6 Test

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run test
k6 run load_test.js

# Run with custom VUs
k6 run --vus 100 --duration 2m load_test.js

# Save results
k6 run --out json=results.json load_test.js
```

#### Import k6 Results

```python
# Parse k6 results
results = K6Integration.parse_k6_results("results.json")

print(f"Total Requests: {results['metrics']['total_requests']}")
print(f"Requests/sec: {results['metrics']['requests_per_second']:.2f}")
print(f"P95 Duration: {results['metrics']['http_req_duration']['p95']:.2f}ms")
print(f"Error Rate: {results['metrics']['error_rate']:.2%}")
```

### JMeter Integration

#### Generate JMeter JMX

```python
from performance.external_integrations import JMeterIntegration

scenarios = [
    {
        'name': 'Homepage',
        'url': 'https://example.com',
        'method': 'GET'
    },
    {
        'name': 'Login',
        'url': 'https://example.com/login',
        'method': 'POST'
    }
]

jmx = JMeterIntegration.generate_jmx(
    test_name="Load Test",
    scenarios=scenarios,
    thread_group_config={
        'num_threads': 20,    # 20 threads (users)
        'ramp_time': 10,      # Ramp up over 10 seconds
        'duration': 60,       # Run for 60 seconds
        'loops': 1
    }
)

JMeterIntegration.save_jmx(jmx, "load_test.jmx")
```

#### Run JMeter Test

```bash
# Install JMeter
brew install jmeter  # macOS
# or download from https://jmeter.apache.org/

# Run test (CLI mode)
jmeter -n -t load_test.jmx -l results.jtl

# Run with custom properties
jmeter -n -t load_test.jmx -l results.jtl -Jthreads=50 -Jduration=120

# Generate HTML report
jmeter -g results.jtl -o report/
```

#### Import JMeter Results

```python
# Parse JTL results
results = JMeterIntegration.parse_jtl_results("results.jtl")

summary = results['summary']
print(f"Total Samples: {summary['total_samples']}")
print(f"Success Rate: {summary['success_rate']:.2%}")
print(f"Avg Response: {summary['avg_response_time']:.2f}ms")
print(f"Min/Max: {summary['min_response_time']}/{summary['max_response_time']}ms")
```

---

## Enhanced Reporting

### Generate Enhanced Report

```python
from performance.enhanced_report_generator import EnhancedReportGenerator
from performance.metrics_collector import MetricsCollector

# After running tests
collector = MetricsCollector()
# ... collect metrics ...

generator = EnhancedReportGenerator(collector, config, output_dir)

# Generate HTML report with charts
html_report = generator.generate_html_report()

# Generate JSON report
json_report = generator.generate_json_report()

print(f"Reports generated:")
print(f"  HTML: {html_report}")
print(f"  JSON: {json_report}")
```

### Report Features

The enhanced report includes:

1. **Interactive Charts**
   - Response time distribution
   - Test performance comparison
   - Step-by-step breakdown
   - Trend analysis

2. **Tabbed Interface**
   - Overview
   - Detailed Results
   - Step Analysis
   - Baseline Comparison

3. **Visual Indicators**
   - Color-coded metrics
   - Regression alerts
   - Improvement highlights
   - Success/failure badges

4. **Baseline Comparison**
   - Side-by-side comparison
   - Percentage changes
   - Regression detection
   - Historical trends

---

## Performance Metrics Reference

### UI Metrics

#### Navigation Timing
```javascript
{
  dns_lookup: 45,              // DNS resolution (ms)
  tcp_connect: 120,            // TCP connection (ms)
  request_response: 350,       // Request/response (ms)
  dom_loading: 890,            // DOM loading (ms)
  dom_interactive: 1200,       // DOM interactive (ms)
  dom_content_loaded: 1450,    // DOMContentLoaded (ms)
  page_load: 2100              // Full page load (ms)
}
```

#### Resource Timing
```javascript
{
  name: "app.js",
  duration: 234,               // Load duration (ms)
  initiator_type: "script",    // Resource type
  transfer_size: 45678,        // Bytes transferred
  start_time: 100,
  response_end: 334
}
```

#### Core Web Vitals
```javascript
{
  lcp: 1850,    // Largest Contentful Paint (ms) - Target: <2.5s
  fid: 45,      // First Input Delay (ms) - Target: <100ms
  cls: 0.05     // Cumulative Layout Shift - Target: <0.1
}
```

#### Memory Metrics
```javascript
{
  used_js_heap_size_mb: 45.2,
  total_js_heap_size_mb: 67.8,
  js_heap_size_limit_mb: 2048
}
```

### API Metrics

```javascript
{
  ttfb: 0.234,              // Time to First Byte (s)
  total_time: 0.567,        // Total request time (s)
  status_code: 200,
  response_size: 12345,     // Bytes
  response_size_kb: 12.05
}
```

### Statistical Metrics

```javascript
{
  avg_duration: 2.345,      // Average
  min_duration: 1.234,      // Minimum
  max_duration: 4.567,      // Maximum
  median_duration: 2.123,   // P50
  p95_duration: 3.456,      // 95th percentile
  p99_duration: 4.123,      // 99th percentile
  std_dev: 0.567,           // Standard deviation
  success_rate: 0.98        // 98% success
}
```

---

## Configuration Reference

### Complete Configuration Example

```yaml
performance_config:
  ui:
    concurrent_users: 10
    iterations: 3
    ramp_up_time: 5
    headless: false
    browser_name: "chromium"
    viewport:
      width: 1920
      height: 1080
    timeout: 60000
    screenshots: true
    traces: true
    videos: false
    lightweight_mode: false
    trace_on_failure_only: false
  
  api:
    concurrent_requests: 20
    iterations: 5
    timeout: 30
  
  thresholds:
    page_load_time: 5.0
    api_response_time: 2.0
    error_rate: 0.05
    lcp: 2.5
    fid: 0.1
    cls: 0.1
  
  reporting:
    output_dir: "performance_results"
    generate_html: true
    generate_json: true
    open_browser: false
```

---

## Best Practices

### 1. Granular Tracking
- Use step-by-step tracking for complex workflows
- Identify bottlenecks with custom marks
- Focus on user-critical paths

### 2. Baseline Management
- Set baselines after stable releases
- Update baselines when intentional changes are made
- Track trends over time

### 3. External Tool Integration
- Use k6 for high-scale load testing (1000+ users)
- Use JMeter for enterprise integration
- Import results for unified reporting

### 4. Reporting
- Review enhanced reports after each run
- Share reports with stakeholders
- Track regressions in CI/CD

---

## Examples

See `tests/ui/test_complete_example.py` for complete working examples of all features.

---

## Next Steps

1. Try the examples
2. Create custom workflows
3. Set up baselines
4. Integrate with CI/CD
5. Export to k6/JMeter for scale testing
