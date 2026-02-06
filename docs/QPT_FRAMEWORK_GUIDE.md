# QPT Framework - Complete Beginner's Guide (2026 Edition)

## 🎯 Overview

**QPT (Quvia Performance Toolkit)** is a unified performance testing framework that supports:
- **Multiple Tools**: k6, JMeter, Playwright
- **Distributed Testing**: Remote agent architecture
- **Unified Reporting**: Single consolidated report from all tools
- **YAML-Driven**: Declarative test definitions
- **Smart Resolution**: Automatic code discovery from files
- **Tag-Based Filtering**: Run specific test subsets
- **Report Grouping**: Organize results by tags or agents

---

## 🚀 Getting Started (For Complete Beginners)

### **Step 1: Prerequisites**

Before you begin, ensure you have:

```bash
# Python 3.8+
python3 --version

# Git (to clone the repository)
git --version

# SSH access to remote agents (if using distributed testing)
ssh -i ~/pems/your-key.pem user@remote-host
```

### **Step 2: Clone and Setup**

```bash
# Clone the repository
cd ~/neuron-automation-repos/neuron-e2e-grid-revamp
git clone https://bitbucket.org/espacenetworks/qpt.git neuron-perf-test
cd neuron-perf-test

# Install dependencies
pip3 install -r requirements.txt

# Verify installation
python3 qptcli.py --help
```

### **Step 3: Run Your First Test (Comprehensive Demo)**

The comprehensive demo (`examples/15_comprehensive_demo.yml`) is the **best starting point** to understand QPT's capabilities.

```bash
# Run the comprehensive demo
python3 qptcli.py run examples/15_comprehensive_demo.yml

# Expected output:
# 🚀 Running Unified QPT Test: examples/15_comprehensive_demo.yml
# ⚡ Executing Workflow Group: 'global_load_attack' (2 workflows)
# 📊 Running workflow: parallel_load_phase_us
# ...
# ✅ Test execution completed.
```

**What just happened?**
1. QPT checked if remote agents are online
2. If offline, it **auto-deployed** them to the remote servers
3. Executed **parallel load tests** from 2 regions simultaneously
4. Ran **sequential maintenance workflows** with smart code resolution
5. Generated a **unified HTML report** at `performance_results/comprehensive_demo/unified_performance_report.html`

### **Step 4: View the Report**

```bash
# Open the report in your browser
open performance_results/comprehensive_demo/unified_performance_report.html
```

**Report Features:**
- **Dark Navy Header** with Neuron logo
- **Dashboard**: Summary metrics (total tests, duration, success rate)
- **Tabs**: Playwright, k6, JMeter, Workflows
- **Group By**: Organize workflows by Tags or Agent
- **Collapsible Details**: Expand/collapse step metrics
- **No Footer**: Clean, professional design

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

## 🧠 Smart Resolution: How QPT Finds Your Code

One of QPT's most powerful features is **Smart Resolution** - the ability to automatically discover and execute code without explicit file paths.

### **The Resolution Hierarchy**

When you define a workflow step like this:

```yaml
workflows:
  maintenance_flow:
    steps:
      - name: custom_validation  # ← No code specified!
        action: agent_execute
        agent: jmeter-server
```

QPT searches for code in this order:

#### **1. Inline Code (Highest Priority)**

```yaml
- name: inline_check
  action: agent_execute
  agent: jmeter-server
  code: |
    import platform
    print(f"Running on {platform.node()}")
    result = {"host": platform.node(), "status": "online"}
```

**When to use:** Quick checks, debugging, or simple logic that doesn't need reuse.

#### **2. Method Matching (Second Priority)**

QPT looks for a **function with the same name** in `performance_scripts.py`:

**File:** `examples/performance_scripts.py`
```python
def custom_validation(context):
    """This function will be auto-discovered by QPT"""
    env = context.get('env', 'unknown')
    print(f"Validating environment: {env}")
    
    # Your validation logic here
    result = {
        "validation_status": "passed",
        "environment": env,
        "timestamp": time.time()
    }
    return result
```

**How it works:**
1. QPT reads `performance_scripts.py`
2. Searches for `def custom_validation(`
3. Extracts the entire function (including imports at the top)
4. Sends it to the remote agent for execution

**When to use:** Reusable functions that you want to call from multiple workflows.

#### **3. File Matching (Third Priority)**

QPT looks for a **file with the same name** in `agent_scripts/`:

**File:** `examples/agent_scripts/remote_cleanup.py`
```python
#!/usr/bin/env python3
import os
import shutil

# This entire file will be executed on the remote agent
print("Starting cleanup...")

# Cleanup logic
temp_dir = "/tmp/qpt_test_data"
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
    print(f"Removed {temp_dir}")

result = {"cleanup_status": "completed", "files_removed": 42}
```

**How it works:**
1. QPT checks if `agent_scripts/remote_cleanup.py` exists
2. Reads the entire file
3. Sends it to the remote agent for execution

**When to use:** Standalone scripts, complex logic, or when you need full control over imports and execution flow.

#### **4. Action-Based Code Generation (Fallback)**

If none of the above match, QPT generates code based on the `action` type:

```yaml
- name: api_health_check
  action: api_call  # ← QPT generates HTTP request code
  url: "https://api.example.com/health"
  method: GET
```

**Generated code:**
```python
import aiohttp
async with aiohttp.ClientSession() as session:
    async with session.get("https://api.example.com/health") as response:
        result = {"status": response.status, "body": await response.text()}
```

### **Smart Resolution Example Walkthrough**

Let's trace how QPT resolves the `custom_validation` step:

**YAML:**
```yaml
- name: custom_validation
  action: agent_execute
  agent: jmeter-server
  context: { env: "production" }
```

**Resolution Process:**

```
1. Check for inline code: ❌ Not found
2. Check performance_scripts.py:
   - Read file: examples/performance_scripts.py
   - Search for: "def custom_validation("
   - ✅ FOUND at line 15
   - Extract function + imports
   
3. Send to agent:
   POST http://172.31.128.182:5007/execute
   {
     "code": "import time\ndef custom_validation(context):\n    ...",
     "context": {"env": "production"},
     "timeout": 300
   }
   
4. Agent executes and returns:
   {
     "status": "success",
     "duration": 0.234,
     "validation_status": "passed",
     "environment": "production"
   }
```

---

## 🏷️ Tag-Based Filtering

Tags allow you to run specific subsets of tests without modifying your YAML files.

### **Defining Tags**

Add tags as **inline comments** in your YAML:

```yaml
workflows:
  parallel_load_phase_us:  # sanity, load
    group: "global_load_attack"
    steps: [...]
  
  parallel_load_phase_eu:  # load
    group: "global_load_attack"
    steps: [...]
  
  maintenance_flow:  # maintenance
    steps: [...]
```

**Tag Rules:**
- Tags are **comma-separated**
- Tags are **case-insensitive** (`Sanity` = `sanity` = `SANITY`)
- Multiple tags per workflow are supported
- Workflows without tags can be grouped under "No Tags"

### **Running Tagged Tests**

```bash
# Run only "sanity" tests
python3 qptcli.py run examples/15_comprehensive_demo.yml --tags sanity

# Run "load" tests
python3 qptcli.py run examples/15_comprehensive_demo.yml --tags load

# Run multiple tags (OR logic)
python3 qptcli.py run examples/15_comprehensive_demo.yml --tags sanity,load

# Exclude specific tags
python3 qptcli.py run examples/15_comprehensive_demo.yml --exclude-tags maintenance

# Combine include and exclude
python3 qptcli.py run examples/15_comprehensive_demo.yml --tags load --exclude-tags maintenance
```

### **How Tag Filtering Works Internally**

```python
# 1. Parse tags from YAML comments
workflow_tags = {
    "parallel_load_phase_us": ["sanity", "load"],
    "parallel_load_phase_eu": ["load"],
    "maintenance_flow": ["maintenance"]
}

# 2. Filter workflows
include_tags = {"sanity"}  # From --tags sanity
exclude_tags = set()

filtered_workflows = {}
for name, config in all_workflows.items():
    tags = set(workflow_tags.get(name, []))
    
    # Check include (must have at least one matching tag)
    if include_tags and not tags.intersection(include_tags):
        continue  # Skip
    
    # Check exclude (must not have any excluded tags)
    if exclude_tags and tags.intersection(exclude_tags):
        continue  # Skip
    
    filtered_workflows[name] = config

# Result: Only "parallel_load_phase_us" runs
```

---

## 📊 Report Grouping

The HTML report includes a **"Group Workflows By"** dropdown with three options:

### **1. None (List View)**

Default view - shows all workflows in a flat list.

### **2. Group By: Tags**

Organizes workflows into collapsible groups by tag:

```
▼ Sanity (1 workflow)
  - parallel_load_phase_us
  
▼ Load (2 workflows)
  - parallel_load_phase_us
  - parallel_load_phase_eu
  
▼ Maintenance (1 workflow)
  - maintenance_flow
```

**Note:** Workflows with multiple tags appear in **multiple groups** (cloned in the UI).

### **3. Group By: Agent**

Organizes workflows by the primary agent used:

```
▼ jmeter-server (2 workflows)
  - parallel_load_phase_us
  - maintenance_flow
  
▼ k6-server (1 workflow)
  - parallel_load_phase_eu
```

### **How Grouping Works (JavaScript)**

```javascript
function groupWorkflows() {
    const mode = document.getElementById('groupBySelect').value;
    const allWorkflows = document.querySelectorAll('.workflow-details');
    
    if (mode === 'tags') {
        // 1. Extract tags from data-tags attribute
        // 2. Split by comma: "sanity,load" → ["sanity", "load"]
        // 3. Create a group for each unique tag
        // 4. Clone workflow nodes into multiple groups
        
        groups = {
            "Sanity": [workflow1_clone],
            "Load": [workflow1_clone, workflow2_clone]
        }
    }
    
    // Render collapsible <details> for each group
}
```

---

## 📝 Test File Structure
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

## 🔀 Concurrent Execution with Threads

### **Overview**

ALL workflow actions now support the `threads` parameter for concurrent execution:
- `api_call` - Concurrent HTTP requests
- `agent_execute` - Concurrent remote code execution
- `k6_test` - Uses `vus` (virtual users)
- `jmeter_test` - Uses `threads` in thread_group_config

### **The Threads Parameter**

The `threads` parameter controls how many **concurrent executions** happen simultaneously.

**Default**: If not specified, `threads` defaults to `1` (sequential execution).

### **Total Requests Formula**

```
Total Requests = threads × step_iterations × workflow_iterations
```

### **Examples**

#### **1. API Call with Threads**

```yaml
workflows:
  api_load_test:
    iterations: 2  # Workflow runs 2 times
    steps:
      # Single thread (default)
      - name: baseline_api_call
        action: api_call
        url: "https://api.example.com/users"
        method: GET
        # threads: 1 (default)
        # Total: 1 × 2 = 2 requests
      
      # Multiple concurrent threads
      - name: concurrent_api_call
        action: api_call
        url: "https://api.example.com/posts"
        method: GET
        threads: 10  # 10 concurrent requests
        # Total: 10 × 2 = 20 requests
      
      # Threads + Step Iterations
      - name: high_load_api_call
        action: api_call
        url: "https://api.example.com/data"
        method: GET
        threads: 5      # 5 concurrent threads
        iterations: 3   # Repeat 3 times
        # Total: 5 × 3 × 2 = 30 requests
```

#### **2. Agent Execute with Threads**

```yaml
workflows:
  validation_test:
    steps:
      - name: concurrent_validation
        action: agent_execute
        agent: validation-server
        threads: 5  # 5 concurrent executions
        code: |
          import requests
          import time
          
          # This code runs 5 times concurrently
          thread_id = context.get('thread_id', 0)
          print(f"Thread {thread_id} executing...")
          
          response = requests.get('https://api.example.com/validate')
          result = {
              'thread_id': thread_id,
              'success': response.status_code == 200,
              'data': response.json()
          }
```

**Key Features:**
- Each thread gets a unique `thread_id` in the context
- All threads execute simultaneously
- Results are tracked individually

#### **3. Complete Example with All Features**

```yaml
workflows:
  comprehensive_load:
    iterations: 2  # Workflow runs 2 times
    steps:
      # Step 1: Light load
      - name: light_load
        action: api_call
        url: "https://api.example.com/endpoint-a"
        threads: 5
        # Total: 5 × 2 = 10 requests
      
      # Step 2: Medium load with iterations
      - name: medium_load
        action: api_call
        url: "https://api.example.com/endpoint-b"
        threads: 10
        iterations: 3
        # Total: 10 × 3 × 2 = 60 requests
      
      # Step 3: Heavy load
      - name: heavy_load
        action: api_call
        url: "https://api.example.com/endpoint-c"
        threads: 20
        # Total: 20 × 2 = 40 requests
```

**Grand Total**: 10 + 60 + 40 = **110 requests**

### **Execution Flow**

Understanding how threads, iterations, and parallel groups interact:

```
┌─────────────────────────────────────────────────────────────┐
│ EXECUTION HIERARCHY                                          │
│                                                              │
│ 1. Parallel Groups (Concurrent)                             │
│    ├─ Workflow A (parallel with B)                         │
│    │   └─ Workflow Iterations (Sequential)                 │
│    │       └─ Step Iterations (Sequential)                 │
│    │           └─ Threads (Concurrent) ← All at once       │
│    │                                                        │
│    └─ Workflow B (parallel with A)                         │
│        └─ Workflow Iterations (Sequential)                 │
│            └─ Step Iterations (Sequential)                 │
│                └─ Threads (Concurrent) ← All at once       │
└─────────────────────────────────────────────────────────────┘
```

**Example with 5 threads, 2 iterations, 2 workflows in parallel group:**

```yaml
workflows:
  workflow_A:
    group: "parallel_group"
    iterations: 2
    steps:
      - name: api_test_A
        action: api_call
        url: "https://api.example.com/a"
        threads: 5
        iterations: 2

  workflow_B:
    group: "parallel_group"
    iterations: 2
    steps:
      - name: api_test_B
        action: api_call
        url: "https://api.example.com/b"
        threads: 5
        iterations: 2
```

**Execution Timeline:**

```
T0: Both workflows start simultaneously
    ↓
T1: Workflow A: 5 concurrent requests | Workflow B: 5 concurrent requests
    (Step Iteration 1, Workflow Iteration 1)
    ↓
T2: Workflow A: 5 concurrent requests | Workflow B: 5 concurrent requests
    (Step Iteration 2, Workflow Iteration 1)
    ↓
T3: Workflow A: 5 concurrent requests | Workflow B: 5 concurrent requests
    (Step Iteration 1, Workflow Iteration 2)
    ↓
T4: Workflow A: 5 concurrent requests | Workflow B: 5 concurrent requests
    (Step Iteration 2, Workflow Iteration 2)
    ↓
T5: Both workflows complete
```

**Total Requests per Workflow**: 5 threads × 2 step iterations × 2 workflow iterations = **20 requests**
**Grand Total**: 20 + 20 = **40 requests**
**Peak Concurrency**: 10 (5 from A + 5 from B running simultaneously)

### **Report Display**

The HTML report shows thread information for each step:

```
Step: concurrent_api_call
  Agent: local
  Threads: 10
  Iterations: 3
  Total Requests: 30  (10 threads × 3 iterations)
  Success Rate: 100%
  Avg Response Time: 234ms
```

### **Best Practices**

1. **Start Small**: Begin with low thread counts (1-5) and increase gradually
2. **Monitor Resources**: Watch CPU, memory, and network on both client and server
3. **Realistic Load**: Use thread counts that simulate real-world usage
4. **Combine Wisely**: Use threads for concurrency, iterations for sustained load

**Load Profiles:**
- **Light**: 1-10 threads
- **Medium**: 10-50 threads
- **Heavy**: 50-200 threads
- **Stress**: 200+ threads

### **Comparison with k6 and JMeter**

| Action | Thread Parameter | Default |
|--------|------------------|---------|
| `api_call` | `threads` | 1 |
| `agent_execute` | `threads` | 1 |
| `k6_test` | `options.vus` | 1 |
| `jmeter_test` | `thread_group_config.threads` | 1 |

**All actions now have consistent thread support!**

For detailed execution flow diagrams, see: `EXECUTION_FLOW_EXPLAINED.md`

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
          print(f"I am running on {platform.node()}")
          result = {"host": platform.node(), "status": "online"}
```

### **Detailed Explanation**

This demo showcases 5 key capabilities of QPT in a single file:

1.  **Parallel Loading**: 
    *   The workflows `parallel_load_phase_us` and `parallel_load_phase_eu` share the same group ID `global_load_attack`. 
    *   This instructs the QPT engine to execute them **concurrently**, simulating a distributed load from multiple regions (US & EU) simultaneously.

2.  **Declarative Mode (JMeter)**:
    *   The `jmeter_declarative_load` step uses `action: jmeter_test` without referring to an external `.jmx` file.
    *   QPT automatically constructs a JMeter test plan on the fly based on the `jmeter_config` block (scenarios, threads, duration).

3.  **File-Based Mode (k6)**:
    *   The `k6_file_based_load` step explicitly points to `examples/scripts/my_k6_test.js`.
    *   This file is automatically uploaded to the `k6-server` agent before execution.

4.  **Smart Resolution**:
    *   **Method Matching**: `custom_validation` has no code attached. QPT looks into `performance_scripts.py`, finds `def custom_validation(context):`, and transmits that code to the agent.
    *   **File Matching**: `remote_cleanup` also has no code. QPT looks into `agent_scripts/`, finds `remote_cleanup.py`, and executes it on the remote agent.

5.  **Inline Execution**:
    *   The `inline_check` step defines Python code directly in the YAML using the `code: |` block. This is perfect for quick assertions, environmental checks, or debugging.

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
