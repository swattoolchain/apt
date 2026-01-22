# APT CLI Installation

## Installing qpt

The `qpt` command-line tool provides convenient commands for managing agents and running tests.

### Method 1: Direct Execution (Development)

```bash
# Make executable
chmod +x qpt.py

# Run directly
./qpt.py --help

# Or with python
python3 qpt.py --help
```

### Method 2: System-wide Installation (Recommended)

```bash
# Create symlink in /usr/local/bin
sudo ln -s $(pwd)/qpt.py /usr/local/bin/qpt

# Now you can run from anywhere
qpt --help
```

### Method 3: Add to PATH

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/neuron-perf-test"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc

# Run
qpt.py --help
```

## Available Commands

### Agent Management (Phase 2 - Placeholders)

```bash
# Create agent package
qpt agent create --name <name> --type <docker|cron|systemd> --mode <emit|serve>

# Deploy agent
qpt agent deploy --name <name> --target ssh://user@host --ssh-key ~/.ssh/key.pem

# Check agent status
qpt agent status [--name <name>]

# View agent logs
qpt agent logs --name <name> --tail 100

# Remove agent
qpt agent remove --name <name> --cleanup
```

### Testbed Management (Phase 2 - Placeholders)

```bash
# Setup entire testbed
qpt testbed setup --config testbed.yml
```

### Test Execution

```bash
# Run a test file (currently wraps pytest)
qpt run examples/agent_test.yml
```

### Utility

```bash
# Show version
qpt version

# Show help
qpt --help
qpt agent --help
```

## Current Status

**Phase 1 (Current):**
- ✅ CLI structure created
- ✅ Command placeholders implemented
- ✅ `qpt run` works (wraps pytest)
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
qpt run examples/agent_test.yml

# This is equivalent to:
pytest examples/agent_test.yml
```

### Checking Agent Status (Manual - Phase 1)

```bash
# For now, check manually
curl http://agent-host:9090/health

# Phase 2 will support:
# qpt agent status --name my-agent
```

### Deploying Agents (Manual - Phase 1)

Follow the deployment guide:
```bash
# See docs/AGENT_DEPLOYMENT.md for manual deployment
# Docker, cron, or systemd methods

# Phase 2 will support:
# qpt agent create --name my-agent --type docker --mode emit
# qpt agent deploy --name my-agent --target ssh://user@host
```

## Troubleshooting

### Command not found

```bash
# Check if executable
ls -l qpt.py

# Make executable if needed
chmod +x qpt.py

# Check PATH
echo $PATH

# Run with full path
/path/to/neuron-perf-test/qpt.py --help
```

### Import errors

```bash
# Ensure you're in the project directory or have it in PYTHONPATH
export PYTHONPATH=/path/to/neuron-perf-test:$PYTHONPATH
```

## Next Steps

1. Install qpt using one of the methods above
2. Deploy agents manually (see [AGENT_DEPLOYMENT.md](AGENT_DEPLOYMENT.md))
3. Configure agents in your test YAML
4. Run tests with `qpt run test.yml` or `pytest test.yml`
