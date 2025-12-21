# aptcli - CLI Reference

Quick reference for the APT Framework command-line interface.

## Installation

See [CLI_INSTALLATION.md](CLI_INSTALLATION.md) for installation instructions.

## Commands

### Agent Management

#### create
Create a new agent package (Phase 2).

```bash
aptcli agent create --name <name> --type <type> --mode <mode> [--emit-target <url>]
```

**Options:**
- `--name`: Agent name (required)
- `--type`: Deployment type: `docker`, `cron`, `systemd` (required)
- `--mode`: Agent mode: `emit`, `serve` (required)
- `--emit-target`: InfluxDB URL for emit mode

**Example:**
```bash
aptcli agent create --name us-east --type docker --mode emit --emit-target influxdb://metrics.company.com:8086/agents
```

#### deploy
Deploy agent to remote server (Phase 2).

```bash
aptcli agent deploy --name <name> --target <ssh-target> [--ssh-key <path>]
```

**Options:**
- `--name`: Agent name (required)
- `--target`: SSH target in format `user@host` (required)
- `--ssh-key`: Path to SSH private key

**Example:**
```bash
aptcli agent deploy --name us-east --target ubuntu@ec2-us-east.amazonaws.com --ssh-key ~/.ssh/aws-key.pem
```

#### status
Check agent health status (Phase 2).

```bash
aptcli agent status [--name <name>]
```

**Options:**
- `--name`: Specific agent name (optional, shows all if omitted)

**Example:**
```bash
aptcli agent status --name us-east
```

#### logs
View agent logs (Phase 2).

```bash
aptcli agent logs --name <name> [--tail <lines>]
```

**Options:**
- `--name`: Agent name (required)
- `--tail`: Number of lines to show (default: 100)

**Example:**
```bash
aptcli agent logs --name us-east --tail 50
```

#### remove
Remove an agent (Phase 2).

```bash
aptcli agent remove --name <name> [--cleanup]
```

**Options:**
- `--name`: Agent name (required)
- `--cleanup`: Remove all agent files (flag)

**Example:**
```bash
aptcli agent remove --name us-east --cleanup
```

### Testbed Management

#### setup
Setup testbed infrastructure (Phase 2).

```bash
aptcli testbed setup --config <file>
```

**Options:**
- `--config`: Testbed configuration file (required)

**Example:**
```bash
aptcli testbed setup --config testbed.yml
```

### Test Execution

#### run
Run a test file.

```bash
aptcli run <test-file>
```

**Arguments:**
- `test-file`: Path to test file (required)

**Example:**
```bash
aptcli run examples/agent_test.yml
```

### Utility

#### version
Show version information.

```bash
aptcli version
```

#### help
Show help for any command.

```bash
aptcli --help
aptcli agent --help
aptcli agent create --help
```

## Phase Status

| Command | Status | Notes |
|---------|--------|-------|
| `aptcli run` | ✅ Available | Wraps pytest |
| `aptcli version` | ✅ Available | Shows version info |
| `aptcli agent create` | ⏳ Phase 2 | Shows placeholder message |
| `aptcli agent deploy` | ⏳ Phase 2 | Shows placeholder message |
| `aptcli agent status` | ⏳ Phase 2 | Shows placeholder message |
| `aptcli agent logs` | ⏳ Phase 2 | Shows placeholder message |
| `aptcli agent remove` | ⏳ Phase 2 | Shows placeholder message |
| `aptcli testbed setup` | ⏳ Phase 2 | Shows placeholder message |

## Manual Alternatives (Phase 1)

While Phase 2 commands are being developed, use these manual alternatives:

### Agent Creation
See [AGENT_DEPLOYMENT.md](AGENT_DEPLOYMENT.md) for Docker/cron/systemd deployment.

### Agent Status
```bash
curl http://agent-host:9090/health
```

### Agent Logs
```bash
# Docker
docker logs apt-agent --tail 100

# Systemd
sudo journalctl -u apt-agent -n 100

# Cron
cat /opt/apt-agent/agent.log
```

### Test Execution
```bash
pytest examples/agent_test.yml
```

## Examples

### Complete Workflow (Phase 2 - Future)

```bash
# 1. Create agent package
aptcli agent create --name prod-monitor --type docker --mode emit

# 2. Deploy to production server
aptcli agent deploy --name prod-monitor --target admin@prod-server.com

# 3. Verify deployment
aptcli agent status --name prod-monitor

# 4. Run tests using the agent
aptcli run tests/production_test.yml

# 5. Check agent logs if needed
aptcli agent logs --name prod-monitor --tail 50
```

### Current Workflow (Phase 1)

```bash
# 1. Deploy agent manually (see AGENT_DEPLOYMENT.md)
ssh admin@prod-server.com
# ... follow deployment guide ...

# 2. Verify deployment
curl http://prod-server.com:9090/health

# 3. Configure agent in test YAML
# agents:
#   prod-monitor:
#     endpoint: "http://prod-server.com:9090"
#     auth_token: "${PROD_TOKEN}"

# 4. Run tests
aptcli run tests/production_test.yml
# or
pytest tests/production_test.yml
```

## See Also

- [AGENT_DEPLOYMENT.md](AGENT_DEPLOYMENT.md) - Manual agent deployment
- [AGENT_USAGE.md](AGENT_USAGE.md) - Agent usage in tests
- [CLI_INSTALLATION.md](CLI_INSTALLATION.md) - CLI installation
