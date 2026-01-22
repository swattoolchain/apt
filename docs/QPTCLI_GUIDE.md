# QPT CLI (qpt.py) - Complete Guide

## Overview

`qpt.py` is the command-line interface for the QPT Framework. It provides convenient commands for agent management, deployment, and test execution.

## Installation

```bash
# Make executable
chmod +x qpt.py

# Install dependencies
pip install click aiohttp

# Optional: Add to PATH
ln -s $(pwd)/qpt.py /usr/local/bin/qpt
```

---

## Commands

### 1. Agent Management

#### Create Agent Package

```bash
# Create Docker agent in serve mode
qpt agent create \
  --name my-agent \
  --type docker \
  --mode serve \
  --auth-token "your-secret-token"

# Create systemd agent in emit mode
qpt agent create \
  --name metrics-agent \
  --type systemd \
  --mode emit \
  --emit-target "http://influxdb:8086"
```

**Options**:
- `--name`: Agent identifier
- `--type`: `docker`, `systemd`, `cron`, or `shell`
- `--mode`: `serve` (for testing) or `emit` (for monitoring)
- `--auth-token`: Authentication token (auto-generated if not provided)
- `--emit-target`: InfluxDB URL (for emit mode)
- `--schedule`: Cron schedule (for cron type, default: `*/5 * * * *`)

**Output**: Creates agent package in `~/.qpt/agents/<name>/`

---

#### Deploy Agent

```bash
# Deploy to remote server
qpt agent deploy \
  --name my-agent \
  --target user@vm1.example.com \
  --type docker \
  --ssh-key ~/.ssh/id_rsa \
  --remote-dir /opt/qpt-agent
```

**Options**:
- `--name`: Agent name (must exist in `~/.qpt/agents/`)
- `--target`: SSH target (`user@host`)
- `--type`: Deployment type
- `--ssh-key`: Path to SSH private key (optional)
- `--remote-dir`: Remote installation directory (default: `/opt/qpt-agent`)

---

#### Check Agent Status

```bash
# Check agent health
qpt agent status \
  --endpoint "http://vm1:9090" \
  --auth-token "your-token"
```

**Output**:
```
✅ Agent: my-agent
   Status: healthy
   Mode: serve
   Uptime: 3600.5s
   Metrics: 1234
```

---

#### View Agent Logs

```bash
# Fetch logs from remote agent
qpt agent logs \
  --name my-agent \
  --target user@vm1.example.com \
  --type docker \
  --tail 100
```

---

#### Remove Agent

```bash
# Remove agent from remote server
qpt agent remove \
  --name my-agent \
  --target user@vm1.example.com \
  --type docker \
  --cleanup  # Remove all files
```

---

### 2. Test Execution

#### Run Test

```bash
# Run test file (uses pytest)
qpt run examples/01_simple_api_test.yml
```

Equivalent to:
```bash
pytest examples/01_simple_api_test.yml
```

---

### 3. Version Info

```bash
qpt version
```

---

## Complete Workflow Example

### Setup Distributed Testing with 2 VMs

**Step 1: Create Agent Packages**

```bash
# Create agent for VM1 (US East)
qpt agent create \
  --name us-east-agent \
  --type docker \
  --mode serve \
  --auth-token "us-east-secret-token-123"

# Create agent for VM2 (EU West)
qpt agent create \
  --name eu-west-agent \
  --type docker \
  --mode serve \
  --auth-token "eu-west-secret-token-456"
```

**Step 2: Deploy to VMs**

```bash
# Deploy to VM1
qpt agent deploy \
  --name us-east-agent \
  --target ubuntu@vm1-us-east.example.com \
  --type docker \
  --ssh-key ~/.ssh/aws-key.pem

# Deploy to VM2
qpt agent deploy \
  --name eu-west-agent \
  --target ubuntu@vm2-eu-west.example.com \
  --type docker \
  --ssh-key ~/.ssh/aws-key.pem
```

**Step 3: Verify Agents**

```bash
# Check VM1 agent
qpt agent status \
  --endpoint "http://vm1-us-east.example.com:9090" \
  --auth-token "us-east-secret-token-123"

# Check VM2 agent
qpt agent status \
  --endpoint "http://vm2-eu-west.example.com:9090" \
  --auth-token "eu-west-secret-token-456"
```

**Step 4: Create Test YAML**

```yaml
# distributed_test.yml
agents:
  us-east:
    endpoint: "http://vm1-us-east.example.com:9090"
    auth_token: "us-east-secret-token-123"
  
  eu-west:
    endpoint: "http://vm2-eu-west.example.com:9090"
    auth_token: "eu-west-secret-token-456"

workflows:
  distributed_test:
    steps:
      - name: test_us
        agent: us-east
        action: api_call
        url: "https://api.example.com"
      
      - name: test_eu
        agent: eu-west
        action: api_call
        url: "https://api.example.com"
```

**Step 5: Run Test**

```bash
# Run distributed test
qpt run distributed_test.yml

# Or use pytest directly
pytest distributed_test.yml -v
```

---

## Integration with Latest Features

### Async Agents with Job Queue

The CLI creates agents that support the new async features:

```bash
# Create async-capable agent
qpt agent create \
  --name async-agent \
  --type docker \
  --mode serve
```

**Agent config automatically includes**:
- `max_concurrent_jobs: 2` (for 2 CPU VMs)
- `max_queued_jobs: 10`
- Job priority scheduling
- Async polling pattern

---

### Browser Context Testing

Deploy agents for browser testing:

```bash
# Create browser agent
qpt agent create \
  --name browser-agent \
  --type docker \
  --mode serve

# Deploy to VM with Playwright
qpt agent deploy \
  --name browser-agent \
  --target ubuntu@browser-vm.example.com \
  --type docker
```

**Test with browser contexts**:
```yaml
workflows:
  browser_test:
    concurrency: 15  # 15 concurrent browser contexts
    steps:
      - name: ui_test
        agent: browser-agent
        code: |
          # Browser context code (see examples/09_async_distributed_browsers.yml)
```

---

## Advanced Usage

### Custom Agent Configuration

After creating agent package, customize config:

```bash
# Create agent
qpt agent create --name custom-agent --type docker --mode serve

# Edit config
nano ~/.qpt/agents/custom-agent/config.json
```

**Edit config.json**:
```json
{
  "agent_id": "custom-agent",
  "max_concurrent_jobs": 4,  // Increase for 8 CPU VM
  "max_queued_jobs": 20,     // Increase queue size
  "job_timeout": 3600,       // 1 hour timeout
  "allowed_modules": [
    "requests",
    "playwright.sync_api"
  ]
}
```

Then deploy:
```bash
qpt agent deploy --name custom-agent --target user@host --type docker
```

---

### Multiple Environments

```bash
# Development agents
qpt agent create --name dev-agent-1 --type docker --mode serve
qpt agent create --name dev-agent-2 --type docker --mode serve

# Production monitoring agents
qpt agent create --name prod-monitor-1 --type systemd --mode emit --emit-target "http://influxdb:8086"
qpt agent create --name prod-monitor-2 --type systemd --mode emit --emit-target "http://influxdb:8086"
```

---

## Troubleshooting

### Agent Not Responding

```bash
# Check logs
qpt agent logs \
  --name my-agent \
  --target user@host \
  --type docker \
  --tail 200

# Check status
qpt agent status \
  --endpoint "http://host:9090" \
  --auth-token "token"
```

### Deployment Failed

```bash
# Remove and redeploy
qpt agent remove \
  --name my-agent \
  --target user@host \
  --type docker \
  --cleanup

qpt agent deploy \
  --name my-agent \
  --target user@host \
  --type docker
```

---

## Limitations & Future Enhancements

**Current (Phase 1)**:
- ✅ Agent creation and deployment
- ✅ Health checks
- ✅ Log fetching
- ✅ Basic test execution

**Planned (Phase 2)**:
- 🔄 Testbed automation (multi-VM setup)
- 🔄 Agent auto-discovery
- 🔄 Load balancing configuration
- 🔄 Integrated monitoring dashboard

---

## Quick Reference

```bash
# Create agent
qpt agent create --name NAME --type TYPE --mode MODE

# Deploy agent
qpt agent deploy --name NAME --target USER@HOST --type TYPE

# Check status
qpt agent status --endpoint URL --auth-token TOKEN

# View logs
qpt agent logs --name NAME --target USER@HOST --type TYPE

# Remove agent
qpt agent remove --name NAME --target USER@HOST --type TYPE

# Run test
qpt run TEST_FILE.yml
```

---

## See Also

- [Agent Deployment Guide](AGENT_DEPLOYMENT.md)
- [Agent Usage Guide](AGENT_USAGE.md)
- [Examples](../examples/)
- [Getting Started](../GETTING_STARTED.md)
