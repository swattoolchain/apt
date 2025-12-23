# APT Framework - Allied Performance Testing

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**APT (Allied Performance Testing)** is a unified performance testing framework that seamlessly integrates Playwright, k6, JMeter, and custom workflows into a single, powerful testing platform with real-time monitoring and distributed agent support.

## 🚀 Key Features

- **🎭 Multi-Tool Support**: Playwright (UI), k6 (API), JMeter (Load), Custom Workflows
- **📊 Real-Time Monitoring**: InfluxDB + Grafana integration
- **🌍 Distributed Testing**: Remote agent system for multi-region testing
- **📈 Unified Reporting**: Single HTML report for all test types
- **🔧 YAML-Driven**: Simple, declarative test definitions
- **🤖 CLI Tool**: `aptcli` for agent management and deployment
- **🌐 Browser RUM**: Real User Monitoring SDK for production

## 📦 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/swattoolchain/apt.git
cd apt

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Make CLI executable
chmod +x aptcli.py
sudo ln -s $(pwd)/aptcli.py /usr/local/bin/aptcli
```

### Run Your First Test

```bash
# Run example test
pytest examples/01_simple_api_test.yml

# View report
open performance_results/unified_test/unified_performance_report.html
```

## 📚 Documentation

### Getting Started
- **[Getting Started](GETTING_STARTED.md)** - Complete beginner's guide with installation and first test
- **[Quick Reference](performance/QUICKSTART.md)** - Quick reference for common tasks

### Core Concepts
- **[YAML Syntax](docs/YAML_SYNTAX.md)** - Test definition reference and syntax guide
- **[Unified Testing](docs/UNIFIED_TESTING.md)** - Multi-tool unified testing approach
- **[Metrics & Iterations](docs/METRICS_AND_ITERATIONS.md)** - Metrics collection and iteration control

### Agent System
- **[Agent Usage](docs/AGENT_USAGE.md)** - Remote agent system guide and examples
- **[Agent Deployment](docs/AGENT_DEPLOYMENT.md)** - Manual deployment instructions
- **[Agent Scripts](agent_scripts/README.md)** - Reusable utility scripts documentation

### CLI & Tools
- **[CLI Installation](docs/CLI_INSTALLATION.md)** - aptcli installation and setup
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command reference

### Monitoring & Reporting
- **[Real-Time Monitoring](docs/REAL_TIME_MONITORING.md)** - InfluxDB and Grafana setup

### Advanced
- **[Advanced Features](docs/ADVANCED_FEATURES.md)** - Advanced features reference
- **[Framework Architecture](performance/README.md)** - Internal architecture and design

### Examples
- **[Examples Guide](examples/README.md)** - Comprehensive examples with feature matrix

## 🎯 Use Cases

### 1. API Performance Testing
```yaml
k6_tests:
  api_test:
    scenarios:
      - name: "GET /users"
        url: "https://api.example.com/users"
    options:
      vus: 10
      duration: "30s"
```

### 2. Multi-Region Latency Testing
```bash
# Create and deploy agents
aptcli agent create --name us-east --type docker --mode emit
aptcli agent deploy --name us-east --target ubuntu@us-server.com --type docker

# Run distributed test
pytest examples/03_multi_region_test.yml
```

### 3. Real User Monitoring
```html
<script>
  window.APTBrowserAgentConfig = {
    name: 'my-website',
    mode: 'emit',
    emitTarget: 'https://metrics.company.com/browser-metrics'
  };
</script>
<script src="apt-browser-agent.min.js"></script>
```

## 🏗️ Architecture

```
APT Framework
├── Playwright (UI Testing)
├── k6 (API Load Testing)
├── JMeter (Protocol Testing)
├── Custom Workflows (Python)
├── Remote Agents (Distributed)
└── Browser Agent (RUM)
     ↓
  InfluxDB (Metrics Storage)
     ↓
  Grafana (Real-Time Dashboards)
     ↓
  HTML Reports (Post-Test Analysis)
```

## 🛠️ Components

### Core Testing
- **Playwright**: Browser automation and UI testing
- **k6**: High-performance API and load testing
- **JMeter**: Protocol-level performance testing
- **Custom Workflows**: Python-based test orchestration

### Monitoring & Reporting
- **InfluxDB**: Time-series metrics storage
- **Grafana**: Real-time visualization
- **HTML Reports**: Comprehensive test results

### Distributed Testing
- **Remote Agents**: Deploy agents anywhere (Docker/cron/systemd)
- **Agent Provisioner**: Auto-generate deployment packages
- **Agent Deployer**: SSH-based deployment automation
- **Browser Agent**: JavaScript SDK for RUM

### CLI Tool
- **aptcli**: Command-line interface for agent management
  - `create` - Generate agent packages
  - `deploy` - Deploy to remote servers
  - `status` - Check agent health
  - `logs` - Fetch remote logs
  - `remove` - Clean up deployments

## 📊 Example Workflow

```bash
# 1. Create agent for production monitoring
aptcli agent create --name prod-monitor --type docker --mode emit

# 2. Deploy to production server
aptcli agent deploy --name prod-monitor --target admin@prod.com --type docker

# 3. Run tests using the agent
pytest examples/04_production_monitoring.yml

# 4. View real-time metrics
open http://localhost:3000  # Grafana

# 5. View detailed report
open performance_results/unified_test/unified_performance_report.html
```

## 🌟 Advanced Features

### Selective Step Iterations
```yaml
workflows:
  cart_stress_test:
    steps:
      - name: login
        iterations: 1  # Once
      - name: add_to_cart
        iterations: 100  # Stress test
      - name: checkout
        iterations: 1  # Once
```

### JMeter Plugin Support
```yaml
jmeter_tests:
  grpc_test:
    plugin: "grpc"
    plugin_config:
      host_port: "localhost:50051"
      full_method: "UserService/GetUser"
```

### Web Vitals Monitoring
```typescript
const agent = new APTBrowserAgent({
  name: 'my-app',
  mode: 'emit',
  emitTarget: 'https://metrics.company.com/browser-metrics'
});
agent.init();
```

## 🐳 Docker Support

```bash
# Build image
docker build -t apt-framework .

# Run with monitoring stack
docker-compose up -d

# Run tests
docker run apt-framework pytest examples/01_simple_api_test.yml
```

## 📈 Monitoring Stack

```bash
# Start InfluxDB + Grafana
docker-compose up -d

# Access Grafana
open http://localhost:3000
# Default: admin/admin

# Metrics flow automatically from:
# - k6 tests
# - Custom workflows
# - Remote agents
# - Browser agents
```

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/your-org/neuron-perf-test/issues)

## 💡 Support

- **Documentation**: Check [docs/](docs/) folder
- **Examples**: See [examples/](examples/) for use cases
- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions in GitHub Discussions

---

**Built with ❤️ for performance engineers**
