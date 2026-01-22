# Neuron API Performance Test

This directory contains the onboarded JMX test for Neuron API performance testing.

## 📁 Files

- **`api_test_plan.jmx`** - Original JMeter test plan with 3 thread groups
- **`../tests/definitions/neuron_api_performance_test.yml`** - APT framework test definition

## 🎯 Test Overview

### Thread Groups

1. **Fleet Summary** (5 threads, no ramp-up, 1 loop)
   - Endpoint: `/neuron-api/visualization/api/fleet-summary/get-metrics/v3`
   - Tests fleet metrics including packet loss and login availability

2. **IFE Events** (10 threads, 1s ramp-up, 1 loop)
   - Endpoint: `/neuron-api/ife-visualization/api/events/list/v2`
   - Tests event listing for 3-day and 10-day time ranges
   - Filters: Active flights, Alarm category, Open/Pending/Waiting tickets

3. **Analytics IFE Overview** (10 threads, no ramp-up, 1 loop)
   - Endpoint: `/neuron-api/ife-visualization/api/ryg/summary/list`
   - Tests analytics summary with and without DSS metrics
   - Time ranges: 3 days and 10 days

## 🚀 Running the Test

### Option 1: Using the JMX file directly

```bash
# Using JMeter command line
jmeter -n -t jmx_files/api_test_plan.jmx \
  -l results/neuron_api_results.jtl \
  -e -o results/neuron_api_report

# Using Docker
docker run -v $(pwd):/tests justb4/jmeter:latest \
  -n -t /tests/jmx_files/api_test_plan.jmx \
  -l /tests/results/neuron_api_results.jtl
```

### Option 2: Using QPT Framework

```bash
# Using pytest
pytest tests/definitions/neuron_api_performance_test.yml

# Using qpt
./qpt.py run tests/definitions/neuron_api_performance_test.yml

# With custom output directory
./qpt.py run tests/definitions/neuron_api_performance_test.yml \
  --output-dir custom_results/neuron_api
```

### Option 3: Using QPT Framework with Environment Variables

```bash
# Set authentication token
export AUTH_TOKEN="your_bearer_token_here"

# Run the test
pytest tests/definitions/neuron_api_performance_test.yml
```

## 📊 Test Results

Results will be generated in:
- **HTML Report**: `performance_results/neuron_api_test/jmeter/index.html`
- **CSV Data**: `performance_results/neuron_api_test/jmeter/results.csv`
- **JSON Summary**: `performance_results/neuron_api_test/jmeter/summary.json`

## ⚙️ Configuration

### Authentication

The JMX file contains hardcoded Bearer tokens. For production use:

1. **Option A**: Update the JMX file to use JMeter variables
   ```xml
   <stringProp name="Header.value">Bearer ${AUTH_TOKEN}</stringProp>
   ```

2. **Option B**: Use the YAML format in the test definition (see `jmeter_tests_yaml_format` section)

3. **Option C**: Pass as environment variable
   ```bash
   export AUTH_TOKEN="your_token"
   jmeter -n -t jmx_files/api_test_plan.jmx \
     -JAUTH_TOKEN="${AUTH_TOKEN}"
   ```

### Modifying Test Parameters

Edit `tests/definitions/neuron_api_performance_test.yml`:

```yaml
thread_group_config:
  num_threads: 20      # Increase concurrent users
  ramp_time: 10        # Gradual ramp-up
  duration: 300        # Run for 5 minutes
  loops: -1            # Infinite loops (use with duration)
```

### Performance Thresholds

Current thresholds:
- **P95 Response Time**: < 2000ms
- **P99 Response Time**: < 5000ms
- **Error Rate**: < 1%
- **Throughput**: > 10 req/s

## 📈 Metrics Collected

### Fleet Summary
- Packet loss metrics
- Login availability
- Response times and throughput

### IFE Events
- Event listing performance
- Time range impact (3 days vs 10 days)
- Filter performance

### Analytics IFE Overview
- Summary aggregation performance
- DSS metrics impact
- Time range scalability

## 🔍 Viewing Reports

### JMeter HTML Dashboard

```bash
# Open the HTML report
open performance_results/neuron_api_test/jmeter/index.html

# Or on Linux
xdg-open performance_results/neuron_api_test/jmeter/index.html
```

### QPT Framework Report

The APT framework generates a unified report combining all test results:

```bash
# View the unified report
open performance_results/neuron_api_test/index.html
```

## 🐛 Troubleshooting

### JMeter Not Found

```bash
# Install JMeter
brew install jmeter  # macOS
# or use Docker (see Option 1 above)
```

### Authentication Errors

The Bearer tokens in the JMX file may be expired. Update them:

1. Get a new token from your authentication service
2. Replace tokens in `jmx_files/api_test_plan.jmx`
3. Or use environment variables (see Configuration section)

### Connection Errors

Ensure you can reach the gamma environment:

```bash
curl -I https://gamma.hub.quvia.ai
```

## 📝 Notes

- **Token Expiry**: The hardcoded tokens in the JMX file will expire. Update them regularly.
- **Environment**: Tests are configured for the `gamma` environment
- **Time Ranges**: Tests use specific date ranges (Jan 2026). Update as needed.
- **Load**: Current configuration is for functional testing. Increase threads for load testing.

## 🔄 Migrating to YAML Format

The test definition includes a YAML-based version (`jmeter_tests_yaml_format`) which provides:
- Better version control
- Easier parameter management
- Environment variable support
- No JMX file dependency

To use YAML format exclusively, rename `jmeter_tests_yaml_format` to `jmeter_tests` in the test definition.

## 📚 Additional Resources

- [QPT Framework Documentation](../../docs/)
- [JMeter Documentation](../../docs/JMETER_PLUGINS.md)
- [APTCLI Guide](../../docs/QPTCLI_GUIDE.md)
