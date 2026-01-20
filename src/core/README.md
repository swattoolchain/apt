# Performance Testing Framework

A comprehensive Playwright-based performance testing framework for UI and API testing with concurrency support, detailed metrics collection, tracing, and HTML reporting.

## Features

### UI Performance Testing
- ✅ **Page Load Metrics** - Navigation timing, resource timing, paint metrics
- ✅ **Core Web Vitals** - LCP, FID, CLS measurements
- ✅ **Memory Monitoring** - JavaScript heap size tracking
- ✅ **Network Analysis** - Request/response tracking and timing
- ✅ **Screenshots** - Automatic screenshot capture at key points
- ✅ **Trace Files** - Playwright trace files for debugging
- ✅ **Custom Actions** - Measure any user interaction

### API Performance Testing
- ✅ **Request Timing** - TTFB, total request time
- ✅ **Concurrent Testing** - Simulate multiple users
- ✅ **Throughput Measurement** - Requests per second
- ✅ **Error Tracking** - Monitor error rates
- ✅ **Response Analysis** - Size, status codes, headers

### Reporting & Analysis
- ✅ **HTML Reports** - Beautiful, responsive HTML reports
- ✅ **Statistical Analysis** - Percentiles (P50, P75, P90, P95, P99)
- ✅ **JSON Export** - Machine-readable results
- ✅ **Metrics Aggregation** - Cross-test and cross-iteration analysis
- ✅ **Threshold Validation** - Automatic pass/fail based on thresholds

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Configuration

Edit `config/performance_config.yml`:

```yaml
performance:
  ui:
    concurrent_users: 5
    iterations: 3
    headless: false
    screenshots: true
    traces: true
    
  api:
    concurrent_requests: 10
    iterations: 5
    timeout: 30
    
  thresholds:
    page_load_time: 5.0  # seconds
    api_response_time: 2.0  # seconds
    error_rate: 0.05  # 5%
```

## Usage

### Running UI Performance Tests

```bash
# Run all UI performance tests
pytest tests/performance/ui/ -v

# Run with multiple workers (parallel execution)
pytest tests/performance/ui/ -v -n 3

# Run specific test
pytest tests/performance/ui/test_grid_ui_performance.py::test_login_page_performance -v
```

### Running API Performance Tests

```bash
# Run all API performance tests
pytest tests/performance/api/ -v

# Run with specific concurrency
pytest tests/performance/api/test_api_performance.py::test_concurrent_api_requests -v
```

### Viewing Reports

After running tests, reports are generated in `performance_results/test_run_<timestamp>/`:
- `performance_report.html` - Interactive HTML report
- `performance_report.json` - Raw data in JSON format
- `screenshots/` - Test screenshots
- `traces/` - Playwright trace files

Open the HTML report:
```bash
open performance_results/test_run_*/performance_report.html
```

View trace files:
```bash
playwright show-trace performance_results/test_run_*/traces/trace_0.zip
```

## Writing Custom Tests

### UI Performance Test Example

```python
import pytest
from scripts.performance.pytest_fixtures import ui_perf_tester

@pytest.mark.performance
@pytest.mark.asyncio
async def test_my_page_performance(ui_perf_tester):
    """Test custom page performance."""
    
    # Measure page load
    metrics = await ui_perf_tester.measure_page_load(
        url="https://example.com",
        test_name="my_page",
        wait_until="networkidle"
    )
    
    # Assertions
    assert metrics.is_successful()
    assert metrics.duration < 5.0
```

### API Performance Test Example

```python
import pytest
from scripts.performance.pytest_fixtures import api_perf_tester
from scripts.performance.api_performance_tester import APIRequest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_my_api_performance(api_perf_tester):
    """Test custom API performance."""
    
    request = APIRequest(
        url="https://api.example.com/endpoint",
        method="POST",
        body={"key": "value"}
    )
    
    metrics = await api_perf_tester.measure_request(request)
    
    assert metrics.is_successful()
    assert metrics.metrics['total_time'] < 2.0
```

## Architecture

```
scripts/performance/
├── __init__.py
├── base_performance_tester.py    # Base classes and data structures
├── ui_performance_tester.py      # UI testing with Playwright
├── api_performance_tester.py     # API testing with aiohttp
├── metrics_collector.py          # Metrics aggregation and analysis
├── report_generator.py           # HTML/JSON report generation
└── pytest_fixtures.py            # Pytest integration

tests/performance/
├── ui/
│   └── test_grid_ui_performance.py
└── api/
    └── test_api_performance.py

config/
└── performance_config.yml
```

## Metrics Collected

### UI Metrics
- **Navigation Timing**: DNS lookup, TCP connect, request/response, DOM loading
- **Resource Timing**: All resources with duration, size, type
- **Paint Metrics**: First Paint, First Contentful Paint
- **Core Web Vitals**: LCP, FID, CLS
- **Memory**: JS heap size (Chrome only)
- **Network**: All requests with timing and status

### API Metrics
- **Timing**: TTFB, total request time
- **Response**: Status code, size, headers
- **Concurrency**: Performance under load
- **Throughput**: Requests per second
- **Errors**: Error rate and types

## Best Practices

1. **Use Iterations**: Run tests multiple times to get reliable averages
2. **Set Thresholds**: Define acceptable performance limits
3. **Monitor Trends**: Compare results over time
4. **Isolate Tests**: Avoid dependencies between performance tests
5. **Clean Environment**: Run on consistent hardware/network
6. **Review Traces**: Use Playwright traces to debug slow operations

## Troubleshooting

### Tests Timing Out
- Increase timeout in `performance_config.yml`
- Check network connectivity
- Verify application is responsive

### High Variance in Results
- Increase iteration count
- Run on dedicated hardware
- Disable background processes

### Missing Metrics
- Some metrics (memory, web vitals) are browser-specific
- Ensure using Chromium for full metrics support

## Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Run Performance Tests
  run: |
    pytest tests/performance/ -v --html=report.html
    
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: performance-report
    path: performance_results/
```

## Support

For issues or questions, refer to the main framework documentation or contact the automation team.
