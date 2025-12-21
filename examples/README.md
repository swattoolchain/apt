# APT Framework Examples

Comprehensive examples demonstrating every feature of the APT Performance Testing Framework.

## Quick Start

```bash
# Run any example
pytest examples/01_simple_api_test.yml

# View report
open performance_results/*/unified_performance_report.html
```

## 📚 Complete Feature Matrix

| Example | k6 | JMeter | Workflows | Agents | External Code | Selective Iterations | Real-Time | Complexity |
|---------|----|----|-----------|--------|---------------|---------------------|-----------|------------|
| 01 - Simple API | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ⭐ Beginner |
| 02 - Hybrid | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ⭐⭐ Intermediate |
| 03 - Multi-Region | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ⭐⭐⭐ Advanced |
| 04 - Production | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ⭐⭐⭐ Advanced |
| 05 - Selective | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ⭐⭐ Intermediate |
| 06 - External Code | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ⭐⭐⭐ Advanced |
| 07 - Complete | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ⭐⭐⭐ Advanced |
| 08 - Advanced Agents | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ⭐⭐⭐⭐ Expert |

## 📖 Detailed Examples

### 1. Simple API Test ([01_simple_api_test.yml](01_simple_api_test.yml))

**Use Case**: Basic API endpoint performance testing  
**Tools**: k6  
**Duration**: 30 seconds  
**Complexity**: ⭐ Beginner

**What it demonstrates**:
- Basic k6 test configuration
- Simple GET request testing
- Threshold configuration
- HTML report generation

**Run**:
```bash
pytest examples/01_simple_api_test.yml
```

**Key Features**:
- 10 virtual users
- 30-second duration
- P95 latency threshold < 500ms
- Real-time InfluxDB metrics

---

### 2. Hybrid Multi-Tool Test ([02_hybrid_multi_tool.yml](02_hybrid_multi_tool.yml))

**Use Case**: Comprehensive testing with multiple tools  
**Tools**: k6 + JMeter + Custom Workflows  
**Duration**: 1 minute  
**Complexity**: ⭐⭐ Intermediate

**What it demonstrates**:
- Unified testing approach
- k6 for API load testing
- JMeter for protocol testing
- Custom workflows for complex scenarios
- Selective step iterations

**Run**:
```bash
pytest examples/02_hybrid_multi_tool.yml
```

**Key Features**:
- 20 VUs for k6
- 10 threads for JMeter
- 5 workflow iterations
- Selective step iterations (3x on one step)
- Combined HTML report

---

### 3. Multi-Region Distributed Test ([03_multi_region_test.yml](03_multi_region_test.yml))

**Use Case**: Test API latency from multiple geographic regions  
**Tools**: Remote Agents  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐ Advanced

**What it demonstrates**:
- Distributed testing architecture
- Multi-region latency comparison
- Agent-based execution
- Geographic performance analysis

**Prerequisites**:
```bash
# Deploy agents in different regions
aptcli agent create --name us-east --type docker --mode emit
aptcli agent deploy --name us-east --target user@us-server.com --type docker

aptcli agent create --name eu-west --type docker --mode emit
aptcli agent deploy --name eu-west --target user@eu-server.com --type docker

# Set environment variables
export US_EAST_ENDPOINT="http://us-server.com:9090"
export US_EAST_TOKEN="your-token"
export EU_WEST_ENDPOINT="http://eu-server.com:9090"
export EU_WEST_TOKEN="your-token"
```

**Run**:
```bash
pytest examples/03_multi_region_test.yml
```

**Key Features**:
- 2+ remote agents
- Parallel execution from multiple regions
- Latency comparison
- Geographic insights

---

### 4. Production Monitoring ([04_production_monitoring.yml](04_production_monitoring.yml))

**Use Case**: Monitor production application from internal network  
**Tools**: Remote Agent  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐ Advanced

**What it demonstrates**:
- Production health monitoring
- Internal API checks
- Database connectivity
- Redis cache status
- External dependency monitoring

**Prerequisites**:
```bash
# Deploy agent on production network
aptcli agent create --name prod-monitor --type docker --mode emit
aptcli agent deploy --name prod-monitor --target admin@prod-server.com --type docker

export PROD_MONITOR_ENDPOINT="http://prod-server.com:9090"
export PROD_MONITOR_TOKEN="your-token"
```

**Run**:
```bash
pytest examples/04_production_monitoring.yml
```

**Key Features**:
- Internal API health checks
- Database connectivity verification
- Cache status monitoring
- External API dependency checks
- Production-safe monitoring

---

### 5. Selective Step Iterations ([05_selective_iterations.yml](05_selective_iterations.yml))

**Use Case**: Stress test specific workflow steps  
**Tools**: Custom Workflows  
**Duration**: Variable  
**Complexity**: ⭐⭐ Intermediate

**What it demonstrates**:
- Per-step iteration control
- Stress testing specific operations
- Realistic user journey simulation
- Performance degradation detection

**Run**:
```bash
pytest examples/05_selective_iterations.yml
```

**Key Features**:
- Login: 1 iteration (once per workflow)
- Add to cart: 100 iterations (stress test)
- Checkout: 1 iteration (once per workflow)
- Delay configuration between iterations
- Individual iteration tracking

---

### 6. External Agent Code Files ([06_external_agent_code.yml](06_external_agent_code.yml))

**Use Case**: Using external code files instead of inline code  
**Tools**: Remote Agents with external scripts  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐ Advanced

**What it demonstrates**:
- External code file support
- Multi-language scripts (Python, Shell)
- Code reusability
- Better maintainability
- Version-controlled test logic

**Prerequisites**:
```bash
aptcli agent create --name prod-agent --type docker --mode emit
aptcli agent deploy --name prod-agent --target user@server.com --type docker

export PROD_AGENT_ENDPOINT="http://server.com:9090"
export PROD_AGENT_TOKEN="your-token"
```

**Run**:
```bash
pytest examples/06_external_agent_code.yml
```

**Key Features**:
- Python scripts: `health_check.py`, `database_check.py`
- Shell scripts: `system_metrics.sh`
- Reusable utility functions
- Multi-language support
- Context parameter passing

**Agent Scripts Used**:
- `agent_scripts/health_check.py` - API health monitoring
- `agent_scripts/database_check.py` - Database connectivity
- `agent_scripts/system_metrics.sh` - System resource usage

---

### 7. Complete Feature Showcase ([07_complete_showcase.yml](07_complete_showcase.yml))

**Use Case**: Demonstrate ALL framework features in one test  
**Tools**: k6 + JMeter + Workflows + Monitoring  
**Duration**: 2 minutes  
**Complexity**: ⭐⭐⭐ Advanced

**What it demonstrates**:
- k6 API load testing
- JMeter protocol testing
- Custom workflows
- Selective step iterations
- Real-time monitoring
- Advanced reporting options

**Run**:
```bash
# Start monitoring stack
docker-compose up -d

# Run test
pytest examples/07_complete_showcase.yml

# View Grafana
open http://localhost:3000
```

**Key Features**:
- 50 VUs for k6
- 30 threads for JMeter
- 10 workflow iterations
- Selective iterations (1x, 50x, 10x, 1x)
- InfluxDB metrics
- Grafana dashboards
- CSV/JSON export

---

### 8. Advanced Agent Scenarios ([08_advanced_agents.yml](08_advanced_agents.yml))

**Use Case**: Complex multi-agent testing scenarios  
**Tools**: Multiple Remote Agents  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐⭐ Expert

**What it demonstrates**:
- Multi-agent coordination
- Data passing between agents
- External code files
- Complex workflows
- Performance validation
- Agent specialization

**Prerequisites**:
```bash
# Deploy multiple specialized agents
aptcli agent create --name data-collector --type docker --mode emit
aptcli agent deploy --name data-collector --target user@collector.com --type docker

aptcli agent create --name load-generator --type docker --mode emit
aptcli agent deploy --name load-generator --target user@loadgen.com --type docker

aptcli agent create --name validator --type docker --mode emit
aptcli agent deploy --name validator --target user@validator.com --type docker

# Set environment variables
export DATA_COLLECTOR_ENDPOINT="http://collector.com:9090"
export DATA_COLLECTOR_TOKEN="token1"
export LOAD_GENERATOR_ENDPOINT="http://loadgen.com:9090"
export LOAD_GENERATOR_TOKEN="token2"
export VALIDATOR_ENDPOINT="http://validator.com:9090"
export VALIDATOR_TOKEN="token3"
```

**Run**:
```bash
pytest examples/08_advanced_agents.yml
```

**Key Features**:
- 3 specialized agents
- Coordinated workflow execution
- Baseline → Load → Performance → Validation
- External Python scripts
- Context parameter passing
- Agent query for results aggregation

**Agent Scripts Used**:
- `agent_scripts/collect_metrics.py` - System metrics collection
- `agent_scripts/generate_load.py` - HTTP load generation
- `agent_scripts/validate_performance.py` - Performance validation

---

## 🎯 Use Case Guide

### When to use which example:

**Learning the framework?**
→ Start with **Example 01** (Simple API Test)

**Need to test multiple tools?**
→ Use **Example 02** (Hybrid Multi-Tool)

**Testing from multiple locations?**
→ Use **Example 03** (Multi-Region)

**Monitoring production?**
→ Use **Example 04** (Production Monitoring)

**Stress testing specific operations?**
→ Use **Example 05** (Selective Iterations)

**Want reusable test code?**
→ Use **Example 06** (External Code Files)

**Need comprehensive testing?**
→ Use **Example 07** (Complete Showcase)

**Complex multi-agent scenarios?**
→ Use **Example 08** (Advanced Agents)

## 🚀 Running Examples

### Single Example
```bash
pytest examples/01_simple_api_test.yml
```

### All Examples
```bash
pytest examples/*.yml
```

### With Real-Time Monitoring
```bash
# Start monitoring stack
docker-compose up -d

# Run test
pytest examples/01_simple_api_test.yml

# View Grafana
open http://localhost:3000
```

### With Custom Parameters
```bash
# Override VUs
pytest examples/01_simple_api_test.yml --vus=20

# Override duration
pytest examples/01_simple_api_test.yml --duration=60s
```

## 📊 Viewing Reports

```bash
# HTML Report
open performance_results/01_simple_api/unified_performance_report.html

# Find latest
find performance_results -name "unified_performance_report.html" -exec open {} \;
```

## 🛠️ Creating Custom Examples

Use existing examples as templates:

```yaml
test_info:
  test_suite_name: "My Custom Test"
  description: "Description here"
  version: "1.0"

# Add your tests here
k6_tests:
  my_test:
    scenarios:
      - name: "My Scenario"
        url: "https://api.example.com/endpoint"

reporting:
  output_dir: "performance_results/my_test"
```

## 📚 Documentation

- **YAML Syntax**: [../docs/YAML_SYNTAX.md](../docs/YAML_SYNTAX.md)
- **Agent Usage**: [../docs/AGENT_USAGE.md](../docs/AGENT_USAGE.md)
- **Agent Scripts**: [../agent_scripts/README.md](../agent_scripts/README.md)
- **CLI Reference**: [../docs/CLI_REFERENCE.md](../docs/CLI_REFERENCE.md)

## 💡 Support

- Check [../docs/](../docs/) for detailed documentation
- Report issues on GitHub
- See [../README.md](../README.md) for general information


## Quick Start

```bash
# Run any example
pytest examples/01_simple_api_test.yml

# View report
open performance_results/*/unified_performance_report.html
```

## Examples Overview

### 1. Simple API Test ([01_simple_api_test.yml](01_simple_api_test.yml))
**Use Case**: Basic API endpoint performance testing  
**Tools**: k6  
**Duration**: 30 seconds  
**Complexity**: ⭐ Beginner

Simple k6 test for API endpoint performance. Great starting point.

```bash
pytest examples/01_simple_api_test.yml
```

### 2. Hybrid Multi-Tool Test ([02_hybrid_multi_tool.yml](02_hybrid_multi_tool.yml))
**Use Case**: Comprehensive testing with multiple tools  
**Tools**: k6 + JMeter + Custom Workflows  
**Duration**: 1 minute  
**Complexity**: ⭐⭐ Intermediate

Demonstrates unified testing approach combining k6, JMeter, and custom workflows.

```bash
pytest examples/02_hybrid_multi_tool.yml
```

### 3. Multi-Region Distributed Test ([03_multi_region_test.yml](03_multi_region_test.yml))
**Use Case**: Test API latency from multiple geographic regions  
**Tools**: Remote Agents  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐ Advanced

**Prerequisites:**
```bash
# Deploy agents in different regions
aptcli agent create --name us-east --type docker --mode emit
aptcli agent deploy --name us-east --target user@us-server.com --type docker

# Set environment variables
export US_EAST_ENDPOINT="http://us-server.com:9090"
export US_EAST_TOKEN="your-token"
```

**Run:**
```bash
pytest examples/03_multi_region_test.yml
```

### 4. Production Monitoring ([04_production_monitoring.yml](04_production_monitoring.yml))
**Use Case**: Monitor production application from internal network  
**Tools**: Remote Agent  
**Duration**: Variable  
**Complexity**: ⭐⭐⭐ Advanced

Monitor production health, database connectivity, cache status, and external dependencies.

**Prerequisites:**
```bash
# Deploy agent on production network
aptcli agent create --name prod-monitor --type docker --mode emit
aptcli agent deploy --name prod-monitor --target admin@prod-server.com --type docker

# Set environment variable
export PROD_MONITOR_ENDPOINT="http://prod-server.com:9090"
export PROD_MONITOR_TOKEN="your-token"
```

**Run:**
```bash
pytest examples/04_production_monitoring.yml
```

### 5. Selective Step Iterations ([05_selective_iterations.yml](05_selective_iterations.yml))
**Use Case**: Stress test specific workflow steps  
**Tools**: Custom Workflows  
**Duration**: Variable  
**Complexity**: ⭐⭐ Intermediate

Demonstrates per-step iteration control. Login/checkout run once, add-to-cart runs 100 times.

```bash
pytest examples/05_selective_iterations.yml
```

### 6. Agent Test (Browser RUM) ([agent_test.yml](agent_test.yml))
**Use Case**: Remote agent execution examples  
**Tools**: Remote Agents  
**Duration**: Variable  
**Complexity**: ⭐⭐ Intermediate

Examples of remote code execution with context variables and parameterization.

## Use Case Matrix

| Example | k6 | JMeter | Workflows | Agents | Complexity |
|---------|----|----|-----------|--------|------------|
| 01 - Simple API | ✅ | ❌ | ❌ | ❌ | ⭐ |
| 02 - Hybrid | ✅ | ✅ | ✅ | ❌ | ⭐⭐ |
| 03 - Multi-Region | ❌ | ❌ | ✅ | ✅ | ⭐⭐⭐ |
| 04 - Production | ❌ | ❌ | ✅ | ✅ | ⭐⭐⭐ |
| 05 - Selective | ❌ | ❌ | ✅ | ❌ | ⭐⭐ |
| 06 - Agent Test | ❌ | ❌ | ✅ | ✅ | ⭐⭐ |

## Running Examples

### Single Example
```bash
pytest examples/01_simple_api_test.yml
```

### All Examples
```bash
pytest examples/*.yml
```

### With Real-Time Monitoring
```bash
# Start monitoring stack
docker-compose up -d

# Run test
pytest examples/01_simple_api_test.yml

# View Grafana
open http://localhost:3000
```

## Viewing Reports

```bash
# HTML Report
open performance_results/01_simple_api/unified_performance_report.html

# Or find latest
find performance_results -name "unified_performance_report.html" -exec open {} \;
```

## Creating Custom Examples

Use existing examples as templates:

```yaml
test_info:
  test_suite_name: "My Custom Test"
  description: "Description here"
  version: "1.0"

# Add your tests here
k6_tests:
  my_test:
    scenarios:
      - name: "My Scenario"
        url: "https://api.example.com/endpoint"

reporting:
  output_dir: "performance_results/my_test"
```

## Advanced Examples

For more advanced scenarios, see:
- **JMeter Plugins**: [yaml_definitions/06_grpc_native_plugin.yml](yaml_definitions/06_grpc_native_plugin.yml)
- **Selective Iterations**: [yaml_definitions/08_selective_step_iterations.yml](yaml_definitions/08_selective_step_iterations.yml)
- **Programmatic**: [run_programmatic_test.py](run_programmatic_test.py)

## Documentation

- **YAML Syntax**: [../docs/YAML_SYNTAX.md](../docs/YAML_SYNTAX.md)
- **Agent Usage**: [../docs/AGENT_USAGE.md](../docs/AGENT_USAGE.md)
- **CLI Reference**: [../docs/CLI_REFERENCE.md](../docs/CLI_REFERENCE.md)

## Support

- Check [../docs/](../docs/) for detailed documentation
- Report issues on GitHub
- See [../README.md](../README.md) for general information
