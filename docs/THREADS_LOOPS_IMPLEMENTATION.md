# JMeter Report Enhancement Documentation

## Overview
This document explains the critical enhancements made to properly track and report threads (users), loops, and total requests in performance tests.

## The Problem
Previously, reports only showed **iteration counts (loops)** without showing:
- **Threads/Users**: How many concurrent virtual users were running
- **Loop Count**: How many times each user repeated the test  
- **Total Requests**: The actual number of HTTP requests made

This made it impossible to understand the true load profile of a test.

## The Solution

### 1. Enhanced JMeter JTL Parser (`external_integrations.py`)

**What Changed:**
- Added `jmx_file` parameter to `parse_jtl_results()` method
- Extracts thread configuration from JMX XML file
- Parses all ThreadGroups to get:
  - `num_threads`: Number of concurrent users
  - `loops`: Number of iterations per user
  - `ramp_time`: Ramp-up period
- Calculates `expected_requests = threads × loops`
- Groups requests by label for per-request statistics

**New Data Structure:**
```python
{
    'load_profile': {
        'thread_groups': [
            {'name': 'Fleet Summary thread', 'threads': 5, 'loops': 1, 'ramp_time': 0}
        ],
        'total_threads': 5,
        'total_loops': 1,
        'expected_requests': 5
    },
    'request_details': [
        {
            'name': 'Fleet Summary',
            'total_requests': 5,
            'success_count': 5,
            'error_count': 0,
            'success_rate': 1.0,
            'avg_response_time': 1234.5,
            'p50': 1200,
            'p95': 1400,
            'p99': 1450
        }
    ]
}
```

### 2. Updated Unified Runner (`unified_runner.py`)

**What Changed:**
- Pass JMX file path to parser: `parse_jtl_results(str(results_file), str(jmx_path))`
- This allows extraction of thread/loop configuration

### 3. Enhanced Report Generator (`unified_report_generator.py`)

**What Changed:**
- Normalized JMeter results now include `load_profile` and `request_details`
- Added visual Load Profile section showing:
  - **Threads (Users)**: Concurrent virtual users
  - **Loop Count**: Iterations per user
  - **Expected Requests**: threads × loops
- Added Request-by-Request Breakdown table showing:
  - Request name
  - Total requests
  - Success/error counts
  - Average, P95 response times
  - Success rate percentage

**Visual Display:**
```
⚙️ Load Profile
┌─────────────────┬─────────────────┬─────────────────┐
│ Threads (Users) │   Loop Count    │  Expected Reqs  │
│       5         │        1        │        5        │
└─────────────────┴─────────────────┴─────────────────┘

📋 Request-by-Request Breakdown
┌──────────────┬───────┬─────────┬────────┬─────────┬─────────┬───────────┐
│ Request Name │ Total │ Success │ Errors │ Avg(ms) │ P95(ms) │ Success % │
├──────────────┼───────┼─────────┼────────┼─────────┼─────────┼───────────┤
│ Fleet Summary│   5   │    5    │   0    │  1234   │  1400   │   100.0%  │
└──────────────┴───────┴─────────┴────────┴─────────┴─────────┴───────────┘
```

## How It Works for Different Test Types

### For JMeter (File Mode or Direct JMX)
1. JMX file is parsed to extract ThreadGroup configuration
2. JTL results file is parsed for actual request data
3. Both are combined to show complete picture

### For k6 Tests
- k6 already tracks VUs (virtual users) in metrics
- We extract `vus.max` from k6 summary
- Iterations are tracked via `http_reqs.count`

### For Any Test Type
The report now clearly shows:
- **How many users** were simulated
- **How many loops/iterations** each user performed
- **How many total requests** were made
- **Detailed breakdown** per request type/endpoint

## Example Scenarios

### Scenario 1: Low Concurrency, High Repetition
- **Threads**: 5
- **Loops**: 100
- **Total Requests**: 500
- **Interpretation**: 5 users each making 100 requests sequentially

### Scenario 2: High Concurrency, Low Repetition
- **Threads**: 100
- **Loops**: 5
- **Total Requests**: 500
- **Interpretation**: 100 users each making 5 requests concurrently

**Both scenarios generate 500 requests, but performance characteristics are COMPLETELY different!**

## Benefits

1. **Complete Load Profile Visibility**: See exactly how the load was generated
2. **Per-Request Insights**: Understand which endpoints are slow or failing
3. **Accurate Reporting**: No more confusion about iteration vs. total requests
4. **Better Analysis**: Can correlate performance issues with load patterns
5. **Compliance**: Meets industry standards for performance test reporting

## Files Modified

1. `/src/core/external_integrations.py` - Enhanced JMeter parser
2. `/src/core/unified_runner.py` - Pass JMX file to parser
3. `/src/core/unified_report_generator.py` - Display load profile and request details

## Testing

To verify the changes work:
```bash
# Run a JMeter test
qpt run examples/01_simple_api_test.yml

# Check the generated report
# Look for:
# - ⚙️ Load Profile section with threads/loops
# - 📋 Request-by-Request Breakdown table
```

## Future Enhancements

1. Add thread ramp-up visualization
2. Show requests-per-second over time
3. Add thread group timeline chart
4. Support for distributed JMeter tests
5. Real-time load profile monitoring
