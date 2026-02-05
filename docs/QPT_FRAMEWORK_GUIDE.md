# QPT Framework - Complete Guide (2026 Edition)

## 🎯 Overview

**QPT (Quvia Performance Toolkit)** is a unified performance testing framework that supports:
- **Multiple Tools**: k6, JMeter, Playwright
- **Distributed Testing**: Remote agent architecture
- **Unified Reporting**: Single consolidated report from all tools
- **YAML-Driven**: Declarative test definitions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   QPT CLI (qptcli.py)                   │
│  Commands: agent create|deploy|status, run <test.yml>  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼────────┐
│  Local Runner  │           │  Remote Agents  │
│  - k6          │           │  - Agent 1 (k6) │
│  - JMeter      │           │  - Agent 2 (JMeter) │
│  - Playwright  │           │  - Agent N      │
└───────┬────────┘           └────────┬────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
              ┌────────▼─────────┐
              │ Unified Reporter │
              │  - JSON          │
              │  - HTML          │
              │  - InfluxDB      │
              └──────────────────┘
```

---

## 📝 Test File Structure

### **Basic YAML Test**

```yaml
test_info:
  test_suite_name: "My Performance Test"
  description: "Load testing API endpoints"
  version: "1.0"
  test_suite_type: "unified"  # Required for multi-tool tests

# Define remote agents (optional)
agents:
  agent-1:
    endpoint: "http://agent1.example.com:9090"
    auth_token: "your-secret-token"
    timeout: 300

# k6 Tests
k6_tests:
  api_load:
    scenarios:
      - name: "GET Users"
        url: "https://api.example.com/users"
        method: "GET"
        vus: 10
        duration: "30s"

# JMeter Tests
jmeter_tests:
  stress_test:
    scenarios:
      - name: "POST Create"
        url: "https://api.example.com/create"
        method: "POST"
        threads: 20
        ramp_time: 10
        duration: 60

# Workflows (Custom Logic)
workflows:
  user_journey:
    iterations: 5
    steps:
      - name: "login"
        action: api_call
        url: "https://api.example.com/login"
        method: POST
        body:
          username: "test"
          password: "pass"
      
      - name: "fetch_data"
        action: api_call
        url: "https://api.example.com/data"
        method: GET

# Reporting
reporting:
  output_dir: "performance_results/my_test"
  include:
    - k6
    - jmeter
    - workflows
  formats:
    - html
    - json
```

---

## 🤖 Agent System

### **1. Create Agent Package**

```bash
python3 qptcli.py agent create \
  --name "my-agent" \
  --type shell \  # or docker, systemd, cron
  --mode serve \  # or emit
  --auth-token "custom-token-123"  # optional
```

**Output:** `~/.qpt/agents/my-agent/`
- `agent_server.py` - FastAPI server
- `config.json` - Agent configuration
- `start_agent.sh` - Startup script
- `requirements.txt` - Python dependencies

### **2. Deploy Agent**

```bash
python3 qptcli.py agent deploy \
  --name "my-agent" \
  --target user@remote-host \
  --ssh-key ~/.ssh/id_rsa \
  --type shell \
  --remote-dir /opt/qpt-agent
```

### **3. Check Agent Status**

```bash
python3 qptcli.py agent status \
  --endpoint "http://remote-host:9090" \
  --auth-token "your-token"
```

### **4. Agent Modes**

- **serve**: Store metrics locally, query via `/metrics` endpoint
- **emit**: Forward metrics to central collector (InfluxDB, etc.)

---

## 🔧 Workflow Actions

### **Available Actions:**

1. **`api_call`** - Make HTTP requests
   ```yaml
   - name: "get_users"
     action: api_call
     url: "https://api.example.com/users"
     method: GET
     headers:
       Authorization: "Bearer token"
   ```

2. **`agent_execute`** - Run code on remote agent
   ```yaml
   - name: "remote_test"
     action: agent_execute
     agent: agent-1
     code: |
       import subprocess
       result = subprocess.run(['k6', 'run', 'test.js'], capture_output=True)
   ```

3. **`agent_query`** - Fetch metrics from agent
   ```yaml
   - name: "get_metrics"
     action: agent_query
     agent: agent-1
   ```

---

## 📊 Running Tests

### **Via Pytest**

```bash
# Run single test
pytest examples/my_test.yml -v -s

# Run with tags
pytest examples/ --perf-tags=smoke,p1 -v

# Generate HTML report
pytest examples/my_test.yml --html=report.html --self-contained-html
```

### **Via QPT CLI** (if implemented)

```bash
python3 qptcli.py run examples/15_comprehensive_demo.yml
```

---

## ⚡ Parallel Execution & Smart Resolution

### **Parallel Groups**

To run multiple workflows or steps in parallel, assign them the same `group` ID.

```yaml
workflows:
  us_load:
    group: "attack_phase"  # Runs with eu_load
    steps: [...]
    
  eu_load:
    group: "attack_phase"  # Runs with us_load
    steps: [...]
```

### **Smart Code Resolution**

The `agent_execute` action can automatically find code to run:
1. **Inline**: Use the `code: |` block.
2. **Method Match**: Looks for `def <step_name>` in `performance_scripts.py`.
3. **File Match**: Looks for `<step_name>.py` in `agent_scripts/`.

---

## 📈 Unified Reporting

### **Output Structure:**

```
performance_results/
└── my_test/
    ├── unified_results.json          # Raw data
    ├── unified_performance_report.html  # Visual report
    ├── k6_results/                   # k6-specific outputs
    ├── jmeter_results/               # JMeter-specific outputs
    └── workflow_results/             # Workflow execution logs
```

### **JSON Schema:**

```json
{
  "playwright": [],
  "k6": [
    {
      "test_name": "api_load",
      "total_requests": 1500,
      "successful_requests": 1498,
      "avg_response_time_ms": 45.2,
      "p95_response_time_ms": 120.5,
      "throughput_rps": 50.0
    }
  ],
  "jmeter": [...],
  "workflows": [
    {
      "name": "user_journey",
      "total_workflows": 5,
      "step_breakdown": {
        "login": {
          "success_rate": 1.0,
          "avg_duration": 0.234
        }
      }
    }
  ]
}
```

---

## 🔐 Security

### **Agent Authentication:**

All agent requests require an `X-Auth-Token` header:

```python
headers = {
    "X-Auth-Token": "your-secret-token"
}
```

### **Restricted Execution:**

Agents run code in a sandboxed environment with limited builtins:
- ✅ Allowed: `print`, `len`, `range`, `dict`, `list`, `subprocess`, `json`, `time`
- ❌ Blocked: `eval`, `exec` (outside sandbox), file system access (except `/tmp`)

---

## 🚀 Best Practices

### **1. Test Organization**

```
tests/
├── definitions/          # YAML test definitions
│   ├── smoke/
│   ├── regression/
│   └── stress/
├── scripts/             # k6/JMeter scripts
└── workflows/           # Custom workflow logic
```

### **2. Agent Naming Convention**

```
<tool>-<region>-<purpose>
Examples:
  - jmeter-us-east-load
  - k6-eu-west-spike
  - playwright-local-ui
```

### **3. Tagging Tests**

```yaml
scenarios:
  "Login Flow #smoke,p0":
    ...
  "Checkout Process #regression,p1":
    ...
```

Run specific tags:
```bash
pytest tests/ --perf-tags=smoke
pytest tests/ --perf-exclude-tags=slow
```

---

## 🐛 Troubleshooting

### **Agent Not Responding**

```bash
# Check agent health
curl http://agent-host:9090/health

# View agent logs
ssh user@agent-host "tail -f /path/to/agent/agent.log"

# Restart agent
ssh user@agent-host "cd /path/to/agent && ./start_agent.sh"
```

### **Import Errors**

Ensure all imports use `src.` prefix:
```python
# ❌ Wrong
from custom_aggregators.module import func

# ✅ Correct
from src.aggregators.module import func
```

### **SSH Tunnel Issues**

```bash
# Kill existing tunnels
lsof -ti:9091 | xargs kill

# Create new tunnel
ssh -f -N -L 9091:localhost:9090 user@remote-host

# Test tunnel
curl http://localhost:9091/health
```

---

## 📚 Examples

### **Comprehensive Feature Showcase**

This example (`examples/15_comprehensive_demo.yml`) demonstrates the full power of QPT:

```yaml
# QPT Comprehensive Demo
test_info:
  test_suite_name: "QPT Full Feature Showcase"
  description: "Demonstrating Parallelism, Smart Resolution, and Multi-Mode Agents"
  version: "3.0"
  test_suite_type: "unified"

agents:
  jmeter-server:
    endpoint: "http://172.31.128.182:5007"
    auth_token: "default_token"
    deploy_info: { type: "shell", target: "ubuntu@172.31.128.182", ssh_key: "~/pems/world-cloud.pem", remote_dir: "/home/ubuntu/jmeter-agent" }
  
  k6-server:
    endpoint: "http://172.31.128.185:5007"
    auth_token: "rtkbC6b35jrChrvWyJtdUL0mhyMWEfcS5rYhDMBHkgQ"
    deploy_info: { type: "shell", target: "ubuntu@172.31.128.185", ssh_key: "~/pems/world-cloud.pem", remote_dir: "/home/ubuntu/k6-agent" }

workflows:
  # ⚡ PARALLEL LOAD TESTING
  parallel_load_phase_us:
    group: "global_load_attack"
    steps:
      - name: jmeter_declarative_load
        action: jmeter_test
        agent: jmeter-server
        jmeter_config:
          thread_group_config: { threads: 5, duration: 5 }
          scenarios: [{ name: "Declarative API", url: "https://httpbin.org/get", method: "GET" }]

  parallel_load_phase_eu:
    group: "global_load_attack"
    steps:
      - name: k6_file_based_load
        action: k6_test
        agent: k6-server
        k6_script_file: "examples/scripts/my_k6_test.js"

  # 🧠 SMART RESOLUTION (Sequential)
  maintenance_flow:
    steps:
      # Finds 'custom_validation' in examples/performance_scripts.py
      - name: custom_validation
        action: agent_execute
        agent: jmeter-server
        context: { env: "production" }

      # Finds 'remote_cleanup.py' in examples/agent_scripts/
      - name: remote_cleanup
        action: agent_execute
        agent: k6-server
      
      # Inline Code
      - name: inline_check
        action: agent_execute
        agent: jmeter-server
        code: |
          import platform
          print(f"I am running on {platform.node()}")
          result = {"host": platform.node(), "status": "online"}
```

### **Simple API Test**

See: `examples/01_simple_api_test.yml`

### **Hybrid Multi-Tool**

See: `examples/02_hybrid_multi_tool.yml`

---

## 🔄 Latest Changes (2026)

1. **Rebranded**: APT → QPT (Quvia Performance Toolkit)
2. **New Directory Structure**: `src/` instead of `performance/`
3. **Enhanced Agent Security**: Added `__import__` and `open` to sandbox
4. **Improved Error Handling**: Better timeout and connection management
5. **SSH Port Forwarding Support**: For VPN-based deployments

---

## 📞 Support

For issues or questions:
1. Check logs: `performance_results/*/unified_results.json`
2. Review agent logs: `agent.log` on remote VMs
3. Validate YAML: Use online YAML validators
4. Test connectivity: `curl http://agent:9090/health`

---

**Last Updated:** 2026-02-05
**Version:** 2.0.0
