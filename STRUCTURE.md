# APT Framework - Repository Structure

## 📁 New Organized Structure

```
neuron-perf-test/
├── README.md                    # Main documentation
├── LICENSE                      # License file
├── GETTING_STARTED.md          # Quick start guide
├── setup.py                    # Python package setup
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── conftest.py                 # Pytest fixtures
├── aptcli.py                   # CLI tool (main entry point)
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
│
├── config/                     # Configuration files
│   ├── extensions_config.yml  # Extensions configuration
│   └── performance_config.yml # Performance settings
│
├── src/                        # Source code
│   ├── core/                   # Core framework (formerly performance/)
│   │   ├── __init__.py
│   │   ├── unified_yaml_loader.py
│   │   ├── unified_runner.py
│   │   ├── unified_report_generator.py
│   │   ├── api_performance_tester.py
│   │   ├── ui_performance_tester.py
│   │   ├── metrics_collector.py
│   │   ├── report_generator.py
│   │   ├── comparison_tracker.py
│   │   ├── jmeter_plugins.py
│   │   ├── external_integrations.py
│   │   ├── workflow_integrations.py
│   │   ├── performance_scripts.py  # Convention-over-configuration
│   │   ├── README.md
│   │   └── QUICKSTART.md
│   │
│   ├── agents/                 # Agent system (formerly performance/agents/)
│   │   ├── __init__.py
│   │   ├── agent_server.py    # Legacy agent server
│   │   ├── agent_server_async.py  # ⭐ NEW: Async agent with job queue
│   │   ├── agent_client.py
│   │   ├── async_agent_client.py  # ⭐ NEW: Async client with polling
│   │   ├── config.example.json    # ⭐ NEW: Agent configuration
│   │   ├── provisioner.py
│   │   ├── deployer.py
│   │   └── health_monitor.py
│   │
│   ├── aggregators/            # Custom aggregators (formerly custom_aggregators/)
│   │   ├── __init__.py
│   │   ├── selective_iteration_aggregator.py
│   │   └── workflow_aggregator.py
│   │
│   └── test_scripts/           # Reusable test scripts (formerly agent_scripts/ + scripts/)
│       ├── collect_metrics.py
│       ├── database_check.py
│       ├── distributed_ui_test.py
│       ├── generate_load.py
│       ├── health_check.py
│       ├── validate_performance.py
│       ├── system_metrics.sh
│       ├── pytest_perf_plugin.py
│       ├── docker-quickstart.sh
│       └── setup_distributed_test.sh
│
├── ui/                         # User interfaces
│   ├── api/                    # API/Browser agent
│   │   └── browser-agent/
│   │       ├── src/
│   │       ├── package.json
│   │       └── README.md
│   │
│   ├── desktop/                # Desktop application
│   │   └── apt-desktop/
│   │       ├── src/
│   │       ├── src-tauri/
│   │       ├── package.json
│   │       └── README.md
│   │
│   └── web/                    # Web interface
│       └── web-ui/
│           └── backend/
│               └── main.py
│
├── examples/                   # Example test files
│   ├── 01_simple_api_test.yml
│   ├── 02_hybrid_multi_tool.yml
│   ├── 03_multi_region_test.yml
│   ├── 04_production_monitoring.yml
│   ├── 05_selective_iterations.yml
│   ├── 06_external_agent_code.yml
│   ├── 07_complete_showcase.yml
│   ├── 08_advanced_agents.yml
│   ├── 09_async_distributed_browsers.yml  # ⭐ NEW: Async agents + browser contexts
│   ├── 10_weighted_load_distribution.yml  # ⭐ NEW: Weighted distribution
│   ├── agent_test.yml
│   ├── unified_performance_test.yml
│   └── README.md
│
├── tests/                      # Test definitions
│   ├── definitions/            # YAML test definitions
│   │   ├── api_visualization_performance.yml
│   │   ├── ui_grid_performance.yml
│   │   ├── unified_performance_test.yml
│   │   └── workflow_performance_test.yml
│   └── __init__.py
│
├── docs/                       # Documentation
│   ├── ADVANCED_FEATURES.md
│   ├── AGENT_DEPLOYMENT.md
│   ├── AGENT_USAGE.md
│   ├── APTCLI_GUIDE.md        # ⭐ NEW: Complete CLI guide
│   ├── CLI_INSTALLATION.md
│   ├── CLI_REFERENCE.md
│   ├── DOCKER_USAGE.md
│   ├── JMETER_PLUGINS.md
│   ├── K6_JMETER_INSTALLATION.md
│   ├── METRICS_AND_ITERATIONS.md
│   ├── REAL_TIME_MONITORING.md
│   ├── TEMPORAL_TESTING.md
│   ├── UNIFIED_TESTING.md
│   ├── WORKFLOW_AND_CUSTOM_METRICS.md
│   └── architecture.md
│
└── docker/                     # Docker configurations
    ├── grafana/
    └── prometheus.yml
```

---

## 🎯 Key Changes

### **1. Consolidated Source Code** (`src/`)

**Before**:
- `performance/` - Core framework
- `custom_aggregators/` - Aggregators
- `agent_scripts/` - Test scripts
- `scripts/` - Automation scripts

**After**:
- `src/core/` - All core framework code
- `src/agents/` - All agent-related code
- `src/aggregators/` - All custom aggregators
- `src/test_scripts/` - All reusable scripts (test + automation)

**Benefits**:
- ✅ Single source directory
- ✅ Clear separation of concerns
- ✅ Easier imports
- ✅ Professional structure

---

### **2. Unified UI Directory** (`ui/`)

**Before**:
- `apt-desktop/` - Desktop app
- `browser-agent/` - Browser agent
- `web-ui/` - Web interface

**After**:
- `ui/desktop/apt-desktop/` - Desktop application
- `ui/api/browser-agent/` - API/Browser agent
- `ui/web/web-ui/` - Web interface

**Benefits**:
- ✅ All UI code in one place
- ✅ Clear separation from core framework
- ✅ Easier to manage UI projects

---

### **3. Configuration Directory** (`config/`)

**Before**:
- `extensions_config.yml` (root)
- `config/performance_config.yml`

**After**:
- `config/extensions_config.yml`
- `config/performance_config.yml`

**Benefits**:
- ✅ All config files in one place
- ✅ Clean root directory

---

### **4. Clean Root Directory**

**Before**: 14 files in root (messy)

**After**: 10 essential files only
- README.md, LICENSE, GETTING_STARTED.md
- setup.py, requirements.txt, pytest.ini, conftest.py
- aptcli.py (CLI entry point)
- Dockerfile, docker-compose.yml

**Benefits**:
- ✅ Professional appearance
- ✅ Easy to navigate
- ✅ Clear entry points

---

## 📦 Import Changes

### **Old Imports**

```python
from performance.unified_yaml_loader import UnifiedYAMLLoader
from performance.agents.agent_client import AgentClient
from custom_aggregators.workflow_aggregator import WorkflowAggregator
```

### **New Imports**

```python
from src.core.unified_yaml_loader import UnifiedYAMLLoader
from src.agents.agent_client import AgentClient
from src.aggregators.workflow_aggregator import WorkflowAggregator
```

---

## 🚀 New Features

### **1. Async Agent Server** (`src/agents/agent_server_async.py`)

- Job queue with configurable concurrency
- Priority-based scheduling (urgent/high/normal/low)
- Automatic background scheduler
- Queue position tracking
- Real-time stats endpoint
- Solves AWS ELB/NAT timeout issues

### **2. Async Agent Client** (`src/agents/async_agent_client.py`)

- Polling pattern for long-running tests
- Progress tracking
- No long-lived HTTP connections
- Works with AWS infrastructure

### **3. New Examples**

- `examples/09_async_distributed_browsers.yml` - Async agents with browser contexts
- `examples/10_weighted_load_distribution.yml` - Weighted load distribution

### **4. Complete CLI Guide**

- `docs/APTCLI_GUIDE.md` - Comprehensive aptcli.py documentation

---

## 📖 Usage

### **Running Tests**

```bash
# Using pytest (recommended)
pytest examples/01_simple_api_test.yml

# Using CLI
./aptcli.py run examples/01_simple_api_test.yml
```

### **Agent Management**

```bash
# Create agent
./aptcli.py agent create --name my-agent --type docker --mode serve

# Deploy agent
./aptcli.py agent deploy --name my-agent --target user@host --type docker

# Check status
./aptcli.py agent status --endpoint http://host:9090 --auth-token token
```

### **Importing Framework**

```python
# Core framework
from src.core.unified_yaml_loader import UnifiedYAMLLoader
from src.core.unified_runner import UnifiedRunner

# Agents
from src.agents.async_agent_client import AsyncAgentClient

# Aggregators
from src.aggregators.workflow_aggregator import WorkflowAggregator
```

---

## 🎯 Benefits of New Structure

1. **Professional Organization**
   - Clear separation of concerns
   - Industry-standard structure
   - Easy to navigate

2. **Scalability**
   - Easy to add new modules
   - Clear where things belong
   - Modular architecture

3. **Maintainability**
   - Easier to find code
   - Clear dependencies
   - Better for teams

4. **Production-Ready**
   - Clean root directory
   - Proper packaging
   - Professional appearance

---

## 📚 See Also

- [Getting Started](GETTING_STARTED.md)
- [APTCLI Guide](docs/APTCLI_GUIDE.md)
- [Agent Deployment](docs/AGENT_DEPLOYMENT.md)
- [Examples](examples/README.md)
