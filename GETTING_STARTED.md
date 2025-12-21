# APT - Allied Performance Testing
## Complete Beginner's Guide

Welcome! This guide will help you get started with performance testing, even if you've never done it before.

---

## 📚 Table of Contents

1. [What is Performance Testing?](#what-is-performance-testing)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Your First Test](#your-first-test)
4. [Understanding Results](#understanding-results)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## What is Performance Testing?

Performance testing measures how fast and reliable your application is. Think of it like a health checkup for your website or API.

**What we measure:**
- ⏱️ **Speed** - How long does it take to load a page?
- 📊 **Capacity** - How many users can use it at once?
- 🎯 **Reliability** - Does it work consistently?
- 📈 **Scalability** - Can it handle growth?

---

## Getting Started with APT

This guide will help you set up and run your first performance test with APT (Allied Performance Testing).

## Prerequisites

- **Python 3.8+**
- **k6**: [Installation Guide](https://k6.io/docs/get-started/installation/)
- **JMeter**: [Installation Guide](https://jmeter.apache.org/download_jmeter.cgi) (Ensure `jmeter` is in your PATH)

## 1. Installation

Clone the repository and install Python dependencies:

```bash
git clone https://github.com/swattoolchain/apt.git
cd apt
pip install -r requirements.txt
```

## 2. Running Your First Test

We have provided a complete unified example that demonstrates all capabilities in a single YAML file.

Run it using pytest:

```bash
pytest examples/unified_performance_test.yml
```

This will:
1.  Run a **k6 load test** against placeholder APIs
2.  Run a **JMeter stress test**
3.  Execute a **Custom Python Workflow**
4.  Generate a **Unified HTML Report**

## 3. Viewing Results

After the test completes, open the generated report:

```bash
open performance_results/unified_test/unified_performance_report.html
```

You'll see tabs for k6, JMeter, and Workflows, with detailed metrics for each.

## 4. Creating Your Own Test

Create a new YAML file `my_test.yml`:

```yaml
test_info:
  test_suite_name: "My App Performance"

k6_tests:
  login_load:
    scenarios:
      - name: "Login Endpoint"
        url: "https://api.myapp.com/login"
        method: "POST"
    options:
      vus: 10
      duration: "30s"

jmeter_tests:
  complex_stress:
    scenarios:
      - name: "heavy_query"
        url: "https://api.myapp.com/search"
    thread_group_config:
      num_threads: 50
      duration: 60

# Optional: Add custom workflows
workflows:
  user_checkout:
    steps:
      - name: "add_to_cart"
        url: "https://api.myapp.com/cart"
        method: "POST"
```

Run it:
```bash
pytest my_test.yml
```

## 5. Advanced Usage

For more complex scenarios where you need full programmatic control, you can use the Python API.

See `examples/run_programmatic_test.py` for a complete example.

```bash
python examples/run_programmatic_test.py
```

## Troubleshooting

- **k6 not found**: Ensure `k6` is installed and in your PATH.
- **JMeter not found**: Ensure `jmeter` command works in terminal.
- **Missing dependencies**: Run `pip install -r requirements.txt` again.

---

## Your First Test

### Option 1: YAML Test (Easiest - No Coding!)

Create a file `tests/definitions/my_first_test.yml`:

```yaml
test_info:
  test_suite_name: "My First Performance Test"
  test_suite_type: "ui_performance"
  description: "Testing my website's homepage"

# Configuration
performance_config:
  ui:
    concurrent_users: 3      # Test with 3 users at once
    iterations: 2            # Run each test 2 times
    headless: false          # Show browser (set true to hide)
    screenshots: true        # Take screenshots
    traces: true            # Save debugging traces

scenarios:
  # Test 1: Load homepage
  homepage_load: #smoke, p1
    - measure_page_load:
        url: "https://example.com"
        wait_until: "networkidle"  # Wait for page to fully load
        iterations: 3

  # Test 2: Load about page
  about_page: #smoke, p2
    - measure_page_load:
        url: "https://example.com/about"
        wait_until: "domcontentloaded"  # Faster, just wait for HTML
        iterations: 2
```

**Run it:**
```bash
pytest tests/definitions/my_first_test.yml -v
```

### Option 2: Python Test (More Control)

Create a file `tests/ui/test_my_website.py`:

```python
import pytest
from performance.enhanced_ui_tester import EnhancedUIPerformanceTester

@pytest.mark.performance
@pytest.mark.asyncio
async def test_homepage_performance(performance_config):
    """Test homepage loading performance."""
    
    # Create tester
    tester = EnhancedUIPerformanceTester(performance_config)
    await tester.setup()
    
    try:
        # Measure page load
        metrics = await tester.measure_page_load(
            url="https://example.com",
            test_name="homepage"
        )
        
        # Check if test passed
        assert metrics.is_successful(), "Test failed!"
        assert metrics.duration < 5.0, "Page took too long to load!"
        
        print(f"✓ Page loaded in {metrics.duration:.2f} seconds")
        
    finally:
        await tester.teardown()
```

**Run it:**
```bash
pytest tests/ui/test_my_website.py -v
```

---

## Understanding Results

### The HTML Report

After running tests, open `performance_results/test_run_*/performance_report.html`:

#### 1. **Executive Summary** 📊
- **Total Tests**: How many tests ran
- **Success Rate**: Percentage that passed
- **Avg Duration**: Average time taken
- **P95 Duration**: 95% of tests were faster than this
- **P99 Duration**: 99% of tests were faster than this

#### 2. **Charts** 📈
- **Response Time Distribution**: Visual comparison of test speeds
- **Test Performance Comparison**: See which tests are slowest

#### 3. **Detailed Results** 📋
Table showing:
- **Test Name**: What was tested
- **Runs**: How many times it ran
- **Success Rate**: How reliable it is
- **Avg/Min/Max**: Speed statistics
- **P50/P95/P99**: Percentile measurements

### What Do Percentiles Mean?

Think of percentiles like grades in school:

- **P50 (Median)**: Half of users experience this speed or better
- **P95**: 95% of users experience this speed or better (only 5% slower)
- **P99**: 99% of users experience this speed or better (only 1% slower)

**Example:**
- P50 = 2.0s → Half your users wait 2 seconds or less
- P95 = 4.0s → 95% of users wait 4 seconds or less
- P99 = 6.0s → 99% of users wait 6 seconds or less

---

## Advanced Features

### 1. Step-by-Step Performance Tracking

Measure each step of a user workflow:

```python
async def test_login_workflow(performance_config):
    tester = EnhancedUIPerformanceTester(performance_config)
    await tester.setup()
    
    # Define workflow steps
    async def navigate(page):
        await page.goto("https://example.com/login")
    
    async def fill_username(page):
        await page.fill('input[name="username"]', 'admin')
    
    async def fill_password(page):
        await page.fill('input[name="password"]', 'password')
    
    async def submit(page):
        await page.click('button[type="submit"]')
    
    async def wait_dashboard(page):
        await page.wait_for_selector('.dashboard')
    
    # Measure each step
    steps = [
        {'name': 'navigate', 'action': navigate},
        {'name': 'fill_username', 'action': fill_username},
        {'name': 'fill_password', 'action': fill_password},
        {'name': 'submit', 'action': submit},
        {'name': 'wait_dashboard', 'action': wait_dashboard}
    ]
    
    metrics = await tester.measure_workflow_steps(
        workflow_steps=steps,
        test_name="login_flow"
    )
    
    # See timing for each step
    for step in metrics.metrics['step_timings']:
        print(f"{step['step']}: {step['duration']:.3f}s")
    
    await tester.teardown()
```

### 2. Baseline Comparison

Track performance over time and detect regressions:

```python
from performance.comparison_tracker import PerformanceComparison

# First run - set baseline
comparison = PerformanceComparison()
comparison.save_baseline("login_test", {
    'page_load': 2.1,
    'login_time': 0.5
})

# Later runs - compare
result = comparison.compare("login_test", {
    'page_load': 2.5,  # 19% slower - REGRESSION!
    'login_time': 0.45  # 10% faster - IMPROVEMENT!
})

if result['summary']['has_regressions']:
    print("⚠️ Performance regression detected!")
    for regression in result['regressions']:
        print(f"  {regression['metric']}: {regression['change_pct']:.1f}% slower")
```

### 3. API Performance Testing

Test API endpoints:

```yaml
test_info:
  test_suite_name: "API Performance Tests"
  test_suite_type: "api_performance"

scenarios:
  # Single API request
  get_users: #smoke
    - measure_request:
        url: "https://api.example.com/users"
        method: "GET"
        iterations: 5

  # Load test with many concurrent requests
  load_test: #load
    - measure_concurrent:
        url: "https://api.example.com/users"
        method: "GET"
        concurrent_users: 20
```

### 4. High Concurrency Testing

Test with many users (50-100+):

```yaml
scenarios:
  stress_test: #stress
    - measure_page_load:
        url: "https://example.com"
        performance_config:
          ui:
            concurrent_users: 100
            headless: true           # Hide browser for speed
            screenshots: false       # Don't save screenshots
            traces: false           # Don't save traces
            lightweight_mode: true  # Only collect basic metrics
```

---

## Best Practices

### 1. Start Small
- Begin with 1-3 concurrent users
- Run 2-3 iterations
- Test one feature at a time

### 2. Use Tags
Organize tests with tags:
- `#smoke` - Quick tests (run often)
- `#p1` - Critical features (high priority)
- `#load` - Load tests (run less often)
- `#disabled` - Temporarily skip

```bash
# Run only smoke tests
pytest tests/definitions/ --perf-tags=smoke -v

# Run p1 tests, exclude disabled
pytest tests/definitions/ --perf-tags=p1 --perf-exclude-tags=disabled -v
```

### 3. Set Realistic Thresholds

```yaml
performance_config:
  thresholds:
    page_load_time: 5.0      # Max 5 seconds
    api_response_time: 2.0   # Max 2 seconds
    error_rate: 0.05         # Max 5% errors
```

### 4. Run Tests Regularly
- **Smoke tests**: Every commit/PR
- **Load tests**: Daily or weekly
- **Stress tests**: Before releases

### 5. Track Trends
Save baselines and compare over time:

```python
# After each test run
comparison.append_to_history("my_test", {
    'avg_duration': 2.3,
    'p95_duration': 4.1
})

# View trend
trend = comparison.get_trend("my_test", "avg_duration")
print(f"Average over time: {trend['average']:.2f}s")
```

---

## Troubleshooting

### Tests Not Running?

**Problem**: `ModuleNotFoundError: No module named 'playwright'`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
playwright install chromium
```

**Problem**: `ERROR: Could not open requirements file`
```bash
# Solution: Make sure you're in the right directory
cd neuron-perf-test
ls requirements.txt  # Should exist
```

### Tests Failing?

**Problem**: Page timeout errors
```yaml
# Solution: Increase timeout
performance_config:
  ui:
    timeout: 120000  # 2 minutes (in milliseconds)
```

**Problem**: Too slow with many users
```yaml
# Solution: Use lightweight mode
performance_config:
  ui:
    lightweight_mode: true
    headless: true
```

### Can't Find Reports?

```bash
# Find latest report
ls -lt performance_results/

# Open latest report
open performance_results/test_run_*/performance_report.html
```

---

## Common Scenarios

### Scenario 1: Test Login Flow

```yaml
scenarios:
  login_flow: #smoke, p1
    - measure_page_load:
        url: "https://example.com/login"
        iterations: 3
        performance_config:
          ui:
            concurrent_users: 5
            screenshots: true
```

### Scenario 2: Load Test Homepage

```yaml
scenarios:
  homepage_load_test: #load
    - measure_page_load:
        url: "https://example.com"
        iterations: 1
        performance_config:
          ui:
            concurrent_users: 50
            headless: true
            lightweight_mode: true
```

### Scenario 3: API Stress Test

```yaml
scenarios:
  api_stress: #stress
    - measure_concurrent:
        url: "https://api.example.com/health"
        method: "GET"
        concurrent_users: 100
```

---

## Next Steps

1. ✅ **Run the examples** - Try the sample tests
2. ✅ **Create your own test** - Use the templates above
3. ✅ **Set baselines** - Track performance over time
4. ✅ **Integrate with CI/CD** - Automate testing
5. ✅ **Share results** - Show reports to your team

---

## Need Help?

- 📖 **Detailed Docs**: See `performance/README.md`
- 🚀 **Quick Reference**: See `performance/QUICKSTART.md`
- 🏗️ **Architecture**: See `docs/architecture.md`
- 📝 **YAML Guide**: See `tests/definitions/README.md`

---

## Glossary

- **Concurrent Users**: Number of users testing at the same time
- **Iteration**: How many times to repeat a test
- **Headless**: Run browser without showing it (faster)
- **Lightweight Mode**: Skip heavy metrics for speed
- **P50/P95/P99**: Percentile measurements (speed experienced by X% of users)
- **Baseline**: Reference performance to compare against
- **Regression**: Performance got worse
- **Throughput**: Requests per second

---

**Happy Testing!** 🚀

Remember: Performance testing is a journey, not a destination. Start simple, measure consistently, and improve gradually!
