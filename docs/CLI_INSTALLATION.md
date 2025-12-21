# APT CLI Installation

## Installing aptcli

The `aptcli` command-line tool provides convenient commands for managing agents and running tests.

### Method 1: Direct Execution (Development)

```bash
# Make executable
chmod +x aptcli.py

# Run directly
./aptcli.py --help

# Or with python
python3 aptcli.py --help
```

### Method 2: System-wide Installation (Recommended)

```bash
# Create symlink in /usr/local/bin
sudo ln -s $(pwd)/aptcli.py /usr/local/bin/aptcli

# Now you can run from anywhere
aptcli --help
```

### Method 3: Add to PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/neuron-perf-test"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc

# Run
aptcli.py --help
```

## Available Commands

### Agent Management (Phase 2 - Placeholders)

```bash
# Create agent package
aptcli agent create --name <name> --type <docker|cron|systemd> --mode <emit|serve>

# Deploy agent
aptcli agent deploy --name <name> --target ssh://user@host --ssh-key ~/.ssh/key.pem

# Check agent status
aptcli agent status [--name <name>]

# View agent logs
aptcli agent logs --name <name> --tail 100

# Remove agent
aptcli agent remove --name <name> --cleanup
```

### Testbed Management (Phase 2 - Placeholders)

```bash
# Setup entire testbed
aptcli testbed setup --config testbed.yml
```

### Test Execution

```bash
# Run a test file (currently wraps pytest)
aptcli run examples/agent_test.yml
```

### Utility

```bash
# Show version
aptcli version

# Show help
aptcli --help
aptcli agent --help
```

## Current Status

**Phase 1 (Current):**
- ✅ CLI structure created
- ✅ Command placeholders implemented
- ✅ `aptcli run` works (wraps pytest)
- ⚠️  Agent management commands show Phase 2 notice

**Phase 2 (Planned):**
- Agent provisioning automation
- SSH-based deployment
- Health monitoring CLI
- Testbed orchestration

## Usage Examples

### Running Tests

```bash
# Run YAML test
aptcli run examples/agent_test.yml

# This is equivalent to:
pytest examples/agent_test.yml
```

### Checking Agent Status (Manual - Phase 1)

```bash
# For now, check manually
curl http://agent-host:9090/health

# Phase 2 will support:
# aptcli agent status --name my-agent
```

### Deploying Agents (Manual - Phase 1)

Follow the deployment guide:
```bash
# See docs/AGENT_DEPLOYMENT.md for manual deployment
# Docker, cron, or systemd methods

# Phase 2 will support:
# aptcli agent create --name my-agent --type docker --mode emit
# aptcli agent deploy --name my-agent --target ssh://user@host
```

## Troubleshooting

### Command not found

```bash
# Check if executable
ls -l aptcli.py

# Make executable if needed
chmod +x aptcli.py

# Check PATH
echo $PATH

# Run with full path
/path/to/neuron-perf-test/aptcli.py --help
```

### Import errors

```bash
# Ensure you're in the project directory or have it in PYTHONPATH
export PYTHONPATH=/path/to/neuron-perf-test:$PYTHONPATH
```

## Next Steps

1. Install aptcli using one of the methods above
2. Deploy agents manually (see [AGENT_DEPLOYMENT.md](AGENT_DEPLOYMENT.md))
3. Configure agents in your test YAML
4. Run tests with `aptcli run test.yml` or `pytest test.yml`
