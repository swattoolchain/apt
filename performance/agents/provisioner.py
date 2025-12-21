"""
Agent Provisioner - Generate agent packages for deployment

Creates Docker, cron, or systemd packages for remote agent deployment.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from enum import Enum
import shutil


class DeploymentMethod(Enum):
    """Deployment method for agent"""
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker-compose"
    CRON = "cron"
    SYSTEMD = "systemd"
    SHELL = "shell"


class AgentProvisioner:
    """Creates agent packages for deployment"""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize provisioner.
        
        Args:
            output_dir: Base directory for agent packages (default: .apt/agents)
        """
        self.output_dir = output_dir or Path.home() / ".apt" / "agents"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_agent(
        self,
        name: str,
        deployment_method: DeploymentMethod,
        config: Dict
    ) -> Path:
        """
        Generate agent package based on deployment method.
        
        Args:
            name: Agent name
            deployment_method: Deployment method
            config: Agent configuration
        
        Returns:
            Path to agent package directory
        """
        package_dir = self.output_dir / name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        if deployment_method == DeploymentMethod.DOCKER:
            self._create_docker_agent(package_dir, name, config)
        elif deployment_method == DeploymentMethod.CRON:
            self._create_cron_agent(package_dir, name, config)
        elif deployment_method == DeploymentMethod.SYSTEMD:
            self._create_systemd_agent(package_dir, name, config)
        elif deployment_method == DeploymentMethod.SHELL:
            self._create_shell_agent(package_dir, name, config)
        
        print(f"✅ Agent package created: {package_dir}")
        return package_dir
    
    def _create_docker_agent(self, package_dir: Path, name: str, config: Dict):
        """Generate Docker agent package"""
        
        # Dockerfile
        dockerfile = f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent_server.py .
COPY config.json .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\
  CMD python -c "import requests; requests.get('http://localhost:9090/health', timeout=3)"

EXPOSE 9090

CMD ["python", "agent_server.py"]
"""
        (package_dir / "Dockerfile").write_text(dockerfile)
        
        # docker-compose.yml
        compose = f"""version: '3.8'

services:
  {name}:
    build: .
    container_name: {name}
    restart: unless-stopped
    ports:
      - "9090:9090"
    environment:
      - AGENT_NAME={name}
      - AGENT_MODE={config.get('mode', 'emit')}
      - EMIT_TARGET={config.get('emit_target', '')}
    volumes:
      - agent-data:/app/data
    networks:
      - apt-network

volumes:
  agent-data:

networks:
  apt-network:
    driver: bridge
"""
        (package_dir / "docker-compose.yml").write_text(compose)
        
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0
pydantic==2.5.0
influxdb-client==1.38.0
requests==2.31.0
"""
        (package_dir / "requirements.txt").write_text(requirements)
        
        # config.json
        config_json = {
            "name": name,
            "mode": config.get('mode', 'emit'),
            "emit_target": config.get('emit_target', ''),
            "auth_token": config.get('auth_token', '')
        }
        (package_dir / "config.json").write_text(json.dumps(config_json, indent=2))
        
        # Copy agent_server.py from framework
        self._copy_agent_server(package_dir)
        
        # README
        readme = f"""# Agent: {name}

## Deployment Method: Docker

### Build and Run

```bash
# Build image
docker-compose build

# Start agent
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop agent
docker-compose down
```

### Verify

```bash
curl http://localhost:9090/health
```
"""
        (package_dir / "README.md").write_text(readme)
    
    def _create_cron_agent(self, package_dir: Path, name: str, config: Dict):
        """Generate cron agent package"""
        
        # run_agent.sh
        script = f"""#!/bin/bash
# APT Agent: {name}
# Mode: {config.get('mode', 'serve')}

AGENT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
LOG_FILE="$AGENT_DIR/agent.log"

# Source virtual environment if exists
if [ -d "$AGENT_DIR/venv" ]; then
    source "$AGENT_DIR/venv/bin/activate"
fi

# Execute agent
python3 "$AGENT_DIR/agent_server.py" \\
    >> "$LOG_FILE" 2>&1

# Cleanup old logs (keep last 7 days)
find "$AGENT_DIR" -name "*.log" -mtime +7 -delete
"""
        script_path = package_dir / "run_agent.sh"
        script_path.write_text(script)
        script_path.chmod(0o755)
        
        # Crontab entry
        schedule = config.get('schedule', '*/5 * * * *')
        cron_entry = f"{schedule} {script_path.absolute()}\n"
        (package_dir / "crontab.txt").write_text(cron_entry)
        
        # config.json
        config_json = {
            "name": name,
            "mode": config.get('mode', 'serve'),
            "emit_target": config.get('emit_target', ''),
            "auth_token": config.get('auth_token', '')
        }
        (package_dir / "config.json").write_text(json.dumps(config_json, indent=2))
        
        # Copy agent_server.py
        self._copy_agent_server(package_dir)
        
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0
pydantic==2.5.0
"""
        (package_dir / "requirements.txt").write_text(requirements)
        
        # README
        readme = f"""# Agent: {name}

## Deployment Method: Cron

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install crontab
crontab -l > /tmp/current_cron
cat crontab.txt >> /tmp/current_cron
crontab /tmp/current_cron
rm /tmp/current_cron

# Verify
crontab -l | grep {name}
```

### Manual Run

```bash
./run_agent.sh
```
"""
        (package_dir / "README.md").write_text(readme)
    
    def _create_systemd_agent(self, package_dir: Path, name: str, config: Dict):
        """Generate systemd agent package"""
        
        # Systemd service file
        service = f"""[Unit]
Description=APT Remote Agent - {name}
After=network.target

[Service]
Type=simple
User=apt-agent
WorkingDirectory={package_dir.absolute()}
Environment="AGENT_PORT=9090"
Environment="AGENT_CONFIG_FILE={package_dir.absolute()}/config.json"
ExecStart={package_dir.absolute()}/venv/bin/python {package_dir.absolute()}/agent_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        (package_dir / f"{name}.service").write_text(service)
        
        # config.json
        config_json = {
            "name": name,
            "mode": config.get('mode', 'emit'),
            "emit_target": config.get('emit_target', ''),
            "auth_token": config.get('auth_token', '')
        }
        (package_dir / "config.json").write_text(json.dumps(config_json, indent=2))
        
        # Copy agent_server.py
        self._copy_agent_server(package_dir)
        
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0
pydantic==2.5.0
"""
        (package_dir / "requirements.txt").write_text(requirements)
        
        # install.sh
        install_script = f"""#!/bin/bash
# Install APT Agent as systemd service

set -e

echo "Installing APT Agent: {name}"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create service user
if ! id "apt-agent" &>/dev/null; then
    sudo useradd -r -s /bin/false apt-agent
fi

# Set permissions
sudo chown -R apt-agent:apt-agent .

# Install service
sudo cp {name}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable {name}
sudo systemctl start {name}

echo "✅ Agent installed and started"
echo "Check status: sudo systemctl status {name}"
"""
        install_path = package_dir / "install.sh"
        install_path.write_text(install_script)
        install_path.chmod(0o755)
        
        # README
        readme = f"""# Agent: {name}

## Deployment Method: Systemd

### Install

```bash
sudo ./install.sh
```

### Manage

```bash
# Status
sudo systemctl status {name}

# Logs
sudo journalctl -u {name} -f

# Restart
sudo systemctl restart {name}

# Stop
sudo systemctl stop {name}
```
"""
        (package_dir / "README.md").write_text(readme)
    
    def _create_shell_agent(self, package_dir: Path, name: str, config: Dict):
        """Generate standalone shell script agent"""
        
        # Simple shell wrapper
        script = f"""#!/bin/bash
# APT Agent: {name}

cd "$(dirname "$0")"

# Setup venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run agent
python agent_server.py
"""
        script_path = package_dir / "start_agent.sh"
        script_path.write_text(script)
        script_path.chmod(0o755)
        
        # config.json
        config_json = {
            "name": name,
            "mode": config.get('mode', 'serve'),
            "auth_token": config.get('auth_token', '')
        }
        (package_dir / "config.json").write_text(json.dumps(config_json, indent=2))
        
        # Copy agent_server.py
        self._copy_agent_server(package_dir)
        
        # requirements.txt
        requirements = """fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0
pydantic==2.5.0
"""
        (package_dir / "requirements.txt").write_text(requirements)
    
    def _copy_agent_server(self, package_dir: Path):
        """Copy agent_server.py from framework"""
        # Get path to agent_server.py in the framework
        framework_root = Path(__file__).parent.parent.parent
        agent_server_src = framework_root / "performance" / "agents" / "agent_server.py"
        
        if agent_server_src.exists():
            shutil.copy(agent_server_src, package_dir / "agent_server.py")
        else:
            # Fallback: create a note
            (package_dir / "COPY_AGENT_SERVER.txt").write_text(
                f"Copy agent_server.py from:\n{agent_server_src}\n"
                "Or from: performance/agents/agent_server.py"
            )
