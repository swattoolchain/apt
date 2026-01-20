# Performance Testing Quick Start Guide

## Installation

```bash
# Install dependencies (if needed)
pip install pytest-xdist pytest-html pytest-asyncio

# Verify installation
python3 -c "from scripts.performance.base_performance_tester import PerformanceConfig; print('✅ Ready')"
```

## Running Tests

### UI Performance Tests
```bash
# Run all UI tests
pytest tests/performance/ui/ -v

# Run with parallel execution (3 workers)
pytest tests/performance/ui/ -v -n 3

# Run specific test
pytest tests/performance/ui/test_grid_ui_performance.py::test_login_page_performance -v
```

### API Performance Tests
```bash
# Run all API tests
pytest tests/performance/api/ -v

# Run concurrent load test
pytest tests/performance/api/test_api_performance.py::test_concurrent_api_requests -v
```

## Viewing Results

```bash
# Open HTML report
open performance_results/test_run_*/performance_report.html

# View Playwright trace
playwright show-trace performance_results/test_run_*/traces/trace_0.zip

# View JSON data
cat performance_results/test_run_*/performance_report.json | jq
```

## Writing Custom Tests

### UI Test Template
```python
import pytest
from scripts.performance.pytest_fixtures import ui_perf_tester

@pytest.mark.performance
@pytest.mark.asyncio
async def test_my_page(ui_perf_tester):
    metrics = await ui_perf_tester.measure_page_load(
        url="https://example.com",
        test_name="my_test"
    )
    assert metrics.is_successful()
```

### API Test Template
```python
import pytest
from scripts.performance.pytest_fixtures import api_perf_tester
from scripts.performance.api_performance_tester import APIRequest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_my_api(api_perf_tester):
    request = APIRequest(
        url="https://api.example.com/endpoint",
        method="GET"
    )
    metrics = await api_perf_tester.measure_request(request)
    assert metrics.is_successful()
```

## Configuration

Edit `config/performance_config.yml`:

```yaml
performance:
  ui:
    concurrent_users: 5  # Number of concurrent browser instances
    iterations: 3        # Iterations per test
    headless: false      # Run in headless mode
    screenshots: true    # Capture screenshots
    traces: true         # Generate trace files
    
  thresholds:
    page_load_time: 5.0      # Max page load time (seconds)
    api_response_time: 2.0   # Max API response time (seconds)
    error_rate: 0.05         # Max error rate (5%)
```

## Key Metrics

### UI Metrics
- Page load time
- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Time to Interactive (TTI)
- Memory usage
- Network requests

### API Metrics
- Time to First Byte (TTFB)
- Total request time
- Response size
- Status codes
- Throughput (req/s)

## Troubleshooting

**Import errors?**
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Tests timing out?**
- Increase timeout in config
- Check network connectivity
- Verify application is running

**Missing dependencies?**
```bash
pip install -r requirements.txt
```

## Documentation

- Full README: `scripts/performance/README.md`
- Implementation Plan: See artifacts
- Walkthrough: See artifacts

## Support

For questions or issues, refer to the main documentation or contact the automation team.
