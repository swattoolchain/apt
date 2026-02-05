# Global Agent Pool Configuration Guide

## 📋 Overview

The **Global Agent Pool** allows you to centralize agent definitions in a single configuration file (`config/agents.yml`). This eliminates the need to duplicate agent connection details across multiple test files.

## 🎯 Benefits

1. **Single Source of Truth**: Define each agent once, use everywhere
2. **Easier Maintenance**: Update agent endpoints/tokens in one place
3. **Cleaner Test Files**: Tests only reference agent names
4. **Environment Management**: Easy to swap between dev/staging/prod agents
5. **Team Collaboration**: Shared agent pool across all team members

---

## 📁 File Structure

```
neuron-perf-test/
├── config/
│   └── agents.yml          # ← Global agent pool
├── examples/
│   ├── 15_comprehensive_demo.yml    # Old style (agents defined in test)
│   └── 16_global_agents_demo.yml    # New style (uses global pool)
└── src/
    └── core/
        └── unified_yaml_loader.py   # Loads global + test agents
```

---

## 🔧 Configuration

### **Global Agent Pool** (`config/agents.yml`)

```yaml
agents:
  # JMeter Agent - US East Region
  jmeter-server:
    endpoint: "http://172.31.128.182:5007"
    auth_token: "default_token"
    timeout: 300
    deploy_info:
      type: "shell"
      target: "ubuntu@172.31.128.182"
      ssh_key: "~/pems/world-cloud.pem"
      remote_dir: "/home/ubuntu/jmeter-agent"
    metadata:
      region: "us-east-1"
      capabilities: ["jmeter", "python", "agent_execute"]
      description: "Primary JMeter agent for load testing"
  
  # k6 Agent - EU West Region
  k6-server:
    endpoint: "http://172.31.128.185:5007"
    auth_token: "rtkbC6b35jrChrvWyJtdUL0mhyMWEfcS5rYhDMBHkgQ"
    timeout: 300
    deploy_info:
      type: "shell"
      target: "ubuntu@172.31.128.185"
      ssh_key: "~/pems/world-cloud.pem"
      remote_dir: "/home/ubuntu/k6-agent"
    metadata:
      region: "eu-west-1"
      capabilities: ["k6", "python", "agent_execute"]
      description: "Primary k6 agent for distributed load testing"
```

### **Test File** (Using Global Pool)

```yaml
test_info:
  test_suite_name: "My Performance Test"
  version: "1.0"
  test_suite_type: "unified"

# ✅ NO AGENTS SECTION NEEDED!
# Agents are loaded from config/agents.yml

workflows:
  my_workflow:
    steps:
      - name: my_step
        action: agent_execute
        agent: jmeter-server  # ← References global agent
        code: |
          print("Running on jmeter-server from global pool!")
          result = {"status": "success"}
```

---

## 🔄 Override Priority

QPT uses the following priority when loading agents:

```
1. Test-Level Agents (Highest Priority)
   ↓
2. Global Agent Pool
   ↓
3. Local Execution (No Agent)
```

### **Example: Test-Level Override**

```yaml
# config/agents.yml
agents:
  jmeter-server:
    endpoint: "http://prod-server:5007"
    auth_token: "prod_token"

---

# test.yml
test_info:
  test_suite_name: "Dev Test"

agents:
  jmeter-server:  # ← Overrides global definition
    endpoint: "http://localhost:5007"
    auth_token: "dev_token"

workflows:
  my_workflow:
    steps:
      - name: test_step
        agent: jmeter-server  # Uses localhost (test-level override)
```

**Result**: The test uses `http://localhost:5007` instead of the global `http://prod-server:5007`.

---

## 🚀 Usage Examples

### **1. Simple Test (Global Agents Only)**

```yaml
# examples/simple_global_test.yml
test_info:
  test_suite_name: "Simple Global Agent Test"
  test_suite_type: "unified"

workflows:
  health_check:
    steps:
      - name: check_jmeter
        agent: jmeter-server
        code: |
          import platform
          result = {"host": platform.node()}
      
      - name: check_k6
        agent: k6-server
        code: |
          import platform
          result = {"host": platform.node()}
```

**Run:**
```bash
python3 qptcli.py run examples/simple_global_test.yml
```

**Output:**
```
✅ Loaded global agent pool from config/agents.yml
   Available agents: jmeter-server, k6-server
Registered agent: jmeter-server at http://172.31.128.182:5007 (from global pool)
Registered agent: k6-server at http://172.31.128.185:5007 (from global pool)
```

### **2. Mixed Mode (Global + Test-Specific)**

```yaml
# examples/mixed_agents_test.yml
test_info:
  test_suite_name: "Mixed Agent Test"
  test_suite_type: "unified"

agents:
  # Test-specific agent (not in global pool)
  local-docker:
    endpoint: "http://localhost:5007"
    auth_token: "local_token"

workflows:
  distributed_test:
    steps:
      - name: global_agent_step
        agent: jmeter-server  # From global pool
        code: |
          result = {"source": "global"}
      
      - name: test_agent_step
        agent: local-docker  # From test definition
        code: |
          result = {"source": "test-specific"}
```

**Output:**
```
✅ Loaded global agent pool from config/agents.yml
Registered agent: jmeter-server at http://172.31.128.182:5007 (from global pool)
Registered agent: k6-server at http://172.31.128.185:5007 (from global pool)
Registered agent: local-docker at http://localhost:5007 (from test-specific)
```

---

## 🌍 Environment-Specific Configurations

### **Development Setup**

```yaml
# config/agents.yml (dev)
agents:
  jmeter-server:
    endpoint: "http://localhost:5007"
    auth_token: "dev_token"
  
  k6-server:
    endpoint: "http://localhost:5008"
    auth_token: "dev_token"
```

### **Production Setup**

```yaml
# config/agents.yml (prod)
agents:
  jmeter-server:
    endpoint: "http://172.31.128.182:5007"
    auth_token: "${JMETER_AUTH_TOKEN}"  # From environment variable
  
  k6-server:
    endpoint: "http://172.31.128.185:5007"
    auth_token: "${K6_AUTH_TOKEN}"
```

**Switching Environments:**
```bash
# Development
cp config/agents.dev.yml config/agents.yml

# Production
cp config/agents.prod.yml config/agents.yml
```

---

## 📊 Metadata Fields

The `metadata` section is optional but recommended for documentation:

```yaml
agents:
  my-agent:
    endpoint: "http://example.com:5007"
    auth_token: "token"
    metadata:
      region: "us-east-1"              # Geographic region
      capabilities: ["jmeter", "k6"]   # Supported tools
      description: "Primary load agent" # Human-readable description
      owner: "performance-team"        # Team responsible
      cost_center: "engineering"       # For billing/tracking
```

**Note**: Metadata is not used by QPT internally - it's purely for documentation and team coordination.

---

## 🔍 Troubleshooting

### **Agent Not Found**

```
ERROR: Agent 'my-agent' not found in global pool or test definition
```

**Solution:**
1. Check `config/agents.yml` for the agent name
2. Verify spelling (case-sensitive)
3. Ensure the file exists and is valid YAML

### **Global Pool Not Loading**

```
WARNING: Failed to load global agent pool: [Errno 2] No such file or directory
```

**Solution:**
```bash
# Create the config directory
mkdir -p config

# Copy the example
cp config/agents.example.yml config/agents.yml

# Edit with your agents
vim config/agents.yml
```

### **Test-Level Override Not Working**

If your test-level agent definition isn't overriding the global one, check:

1. **Indentation**: YAML is whitespace-sensitive
2. **Agent Name**: Must match exactly (case-sensitive)
3. **Syntax**: Ensure valid YAML structure

---

## 📝 Best Practices

### **1. Use Global Pool for Shared Agents**

```yaml
# ✅ Good: Shared agents in global pool
# config/agents.yml
agents:
  prod-jmeter:
    endpoint: "http://prod-server:5007"
```

### **2. Use Test-Level for Temporary/Experimental Agents**

```yaml
# ✅ Good: Experimental agent in test file
# test.yml
agents:
  experimental-agent:
    endpoint: "http://temp-server:5007"
```

### **3. Document Your Agents**

```yaml
# ✅ Good: Well-documented agent
agents:
  jmeter-us-east:
    endpoint: "http://172.31.128.182:5007"
    auth_token: "token"
    metadata:
      region: "us-east-1"
      description: "Primary JMeter agent for US region load testing"
      owner: "performance-team"
      last_updated: "2026-02-05"
```

### **4. Use Environment Variables for Secrets**

```yaml
# ✅ Good: Secrets from environment
agents:
  prod-agent:
    endpoint: "${AGENT_ENDPOINT}"
    auth_token: "${AGENT_AUTH_TOKEN}"
```

```bash
# Set in environment
export AGENT_ENDPOINT="http://prod-server:5007"
export AGENT_AUTH_TOKEN="super_secret_token"
```

---

## 🔗 Related Documentation

- [QPT Framework Guide](QPT_FRAMEWORK_GUIDE.md)
- [Distributed Testing Guide](DISTRIBUTED_TESTING_GUIDE.md)
- [Agent Deployment Guide](../README.md#agent-deployment)

---

## 📞 Support

For questions or issues with the global agent pool:
1. Check this documentation
2. Review example files in `examples/`
3. Contact the performance team
