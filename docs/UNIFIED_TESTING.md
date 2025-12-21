# Unified Multi-Tool Performance Testing - Quick Guide

## Overview

Run UI tests (Playwright), API tests (k6), and API tests (JMeter) together and get a **single unified report** with standard metrics.

---

## Installation

### 1. Install k6 (Optional - for API load testing)

```bash
# macOS
brew install k6

# Or download from https://k6.io/
```

### 2. Install JMeter (Optional - for API load testing)

```bash
# macOS
brew install jmeter

# Or download from https://jmeter.apache.org/
```

---

## Quick Start

### Run Complete Unified Test Suite

```bash
# Run all tools together (Playwright + k6 + JMeter)
pytest tests/ui/test_unified_example.py::test_unified_performance_suite -v -s
```

**This will:**
1. ✅ Run UI tests with Playwright
2. ✅ Run API load tests with k6
3. ✅ Run API load tests with JMeter
4. ✅ Generate a **unified HTML report** combining all results

### Run Individual Tools

```bash
# Only k6
pytest tests/ui/test_unified_example.py::test_k6_only -v -s

# Only JMeter
pytest tests/ui/test_unified_example.py::test_jmeter_only -v -s
```

---

## Unified Report Features

The unified report shows:

### 📊 Executive Summary
- Total tests across all tools
- Overall success rate
- UI vs API test breakdown
- Average response time
- Tools used

### 🎯 Test Results by Type

**UI Tests (Playwright):**
- Page load times
- Workflow step breakdowns
- Screenshots and traces

**API Tests (k6):**
- Response times (avg, P50, P95, P99)
- Throughput (requests/second)
- Total requests
- Success rate

**API Tests (JMeter):**
- Response times
- Total samples
- Success rate
- Throughput

### 📈 Visualizations
- Response time comparison across tools
- Color-coded by tool (Playwright, k6, JMeter)
- Interactive charts

### 📋 Detailed Comparison Table
Side-by-side metrics for all tests with standard format

---

## Standard Metrics (All Tools)

Every test reports these standard metrics:

| Metric | Description | Unit |
|--------|-------------|------|
| `avg_response_time` | Average response time | seconds |
| `min_response_time` | Minimum response time | seconds |
| `max_response_time` | Maximum response time | seconds |
| `p50` | 50th percentile (median) | seconds |
| `p95` | 95th percentile | seconds |
| `p99` | 99th percentile | seconds |
| `total_requests` | Total number of requests | count |
| `success_rate` | Percentage of successful requests | 0-1 |
| `throughput` | Requests per second | req/s |

---

## Example: Custom Unified Test

```python
from performance.unified_runner import UnifiedTestRunner
from performance.unified_report_generator import UnifiedReportGenerator

async def my_unified_test():
    runner = UnifiedTestRunner(Path("results"))
    
    # 1. Run Playwright UI tests
    # ... (your Playwright tests)
    runner.add_playwright_results(collector)
    
    # 2. Run k6 API tests
    await runner.run_k6_test(
        test_name="my_k6_test",
        scenarios=[{
            'name': 'API Test',
            'url': 'https://api.example.com/endpoint',
            'method': 'GET'
        }],
        options={'vus': 50, 'duration': '60s'}
    )
    
    # 3. Run JMeter tests
    await runner.run_jmeter_test(
        test_name="my_jmeter_test",
        scenarios=[{
            'name': 'Load Test',
            'url': 'https://example.com',
            'method': 'GET'
        }],
        thread_group_config={'num_threads': 20, 'duration': 60}
    )
    
    # 4. Generate unified report
    report_gen = UnifiedReportGenerator(runner.get_all_results(), Path("results"))
    html_report = report_gen.generate_unified_html_report()
    
    print(f"Report: {html_report}")
```

---

## When to Use Each Tool

### Playwright (UI Testing)
- **Use for:** Browser-based UI testing
- **Best for:** 1-50 concurrent users
- **Metrics:** Page load, rendering, Core Web Vitals
- **Example:** Login flows, page navigation, form submissions

### k6 (API Load Testing)
- **Use for:** High-scale API load testing
- **Best for:** 50-10,000+ concurrent users
- **Metrics:** API response times, throughput, error rates
- **Example:** REST API endpoints, GraphQL, WebSocket

### JMeter (Enterprise Testing)
- **Use for:** Enterprise environments, existing JMeter infrastructure
- **Best for:** 10-1,000 concurrent users
- **Metrics:** HTTP requests, response times, throughput
- **Example:** Legacy systems, enterprise APIs, complex protocols

---

## Report Output

After running tests, you'll get:

```
performance_results/unified_test/
├── unified_performance_report.html    # Main unified report
├── unified_results.json               # Raw JSON data
├── api_load_test_k6.js               # Generated k6 script
├── api_load_test_k6_results.json     # k6 results
├── api_load_test_jmeter.jmx          # Generated JMeter JMX
├── api_load_test_jmeter_results.jtl  # JMeter results
└── traces/                            # Playwright traces
```

---

## Benefits

✅ **Single Report** - All tools in one place
✅ **Standard Metrics** - Compare apples to apples
✅ **Tool-Specific Details** - Each tool's unique metrics preserved
✅ **No Manual Integration** - Automatic execution and reporting
✅ **Flexible** - Use all tools or just one
✅ **CI/CD Ready** - Easy to integrate into pipelines

---

## Troubleshooting

### k6 not found
```bash
brew install k6
# or download from https://k6.io/
```

### JMeter not found
```bash
brew install jmeter
# or download from https://jmeter.apache.org/
```

### Tests run but no k6/JMeter results
- Check if tools are installed: `k6 version` and `jmeter --version`
- Check error messages in test output
- Verify scenarios are correctly formatted

---

## Next Steps

1. **Run the example:**
   ```bash
   pytest tests/ui/test_unified_example.py::test_unified_performance_suite -v -s
   ```

2. **View the unified report:**
   ```bash
   open performance_results/unified_test/unified_performance_report.html
   ```

3. **Create your own unified tests** using the example as a template

4. **Integrate into CI/CD** for continuous performance monitoring

---

## Summary

You now have a **unified performance testing framework** that:
- Runs Playwright, k6, and JMeter tests together
- Generates a single comprehensive report
- Shows standard metrics for easy comparison
- Works within your existing pytest framework
- No need to run tools separately!

**One command. One report. All tools.** 🚀
