# Remote Agent Deployment Guide

This guide explains how to manually deploy APT remote agents using Docker, cron, or systemd.

## Prerequisites

- Python 3.9+
- FastAPI and dependencies
- Network connectivity to APT framework
- (Optional) Docker for containerized deployment

## Deployment Methods

### Method 1: Docker Deployment (Recommended)

#### 1. Create Agent Directory

```bash
mkdir -p /opt/apt-agent
cd /opt/apt-agent
```

#### 2. Create config.json

```json
{
  "name": "my-agent",
  "mode": "emit",
  "emit_target": "influxdb://metrics.company.com:8086/agents",
  "auth_token": "your-secret-token-here"
}
```

**Configuration Options:**
- `name`: Unique agent identifier
- `mode`: `"emit"` (push metrics) or `"serve"` (store locally)
- `emit_target`: InfluxDB URL for emit mode
- `auth_token`: Authentication token (optional but recommended)

#### 3. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    aiohttp==3.9.0 \
    pydantic==2.5.0

# Copy agent server
COPY agent_server.py .
COPY config.json .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:9090/health', timeout=3)"

EXPOSE 9090

CMD ["python", "agent_server.py"]
```

#### 4. Copy agent_server.py

#### 4. Copy agent_server.py

Copy the `agent_server.py` file from the APT framework:

```bash
cp /path/to/neuron-perf-test/performance/agents/agent_server.py .
```

#### 5. Build and Run

```bash
# Build image
docker build -t apt-agent:latest .

# Run container
docker run -d \
  --name apt-agent \
  --restart unless-stopped \
  -p 9090:9090 \
  -v $(pwd)/config.json:/app/config.json:ro \
  apt-agent:latest
```
```

#### 6. Verify Deployment

```bash
# Check health
curl http://localhost:9090/health

# Expected response:
# {
#   "status": "healthy",
#   "agent_name": "my-agent",
#   "mode": "emit",
#   "uptime_seconds": 123.45,
#   "metrics_count": 0,
#   "timestamp": "2024-01-01T00:00:00"
# }
```

---

### Method 2: Cron-based Deployment

For periodic execution (e.g., scheduled monitoring).

#### 1. Setup Directory

```bash
mkdir -p /opt/apt-agent
cd /opt/apt-agent
```

#### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn aiohttp pydantic
```

#### 3. Create config.json

```json
{
  "name": "cron-agent",
  "mode": "serve",
  "auth_token": "your-token"
}
```

#### 4. Copy agent_server.py

```bash
cp /path/to/apt/performance/agents/agent_server.py .
```

#### 5. Create run_agent.sh

```bash
#!/bin/bash
# APT Agent Runner

AGENT_DIR="/opt/apt-agent"
LOG_FILE="$AGENT_DIR/agent.log"

cd "$AGENT_DIR"
source venv/bin/activate

# Run agent (will exit after handling requests)
python agent_server.py >> "$LOG_FILE" 2>&1

# Cleanup old logs (keep last 7 days)
find "$AGENT_DIR" -name "*.log" -mtime +7 -delete
```

```bash
chmod +x run_agent.sh
```

#### 6. Install Crontab

```bash
# Run every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/apt-agent/run_agent.sh") | crontab -
```

---

### Method 3: Systemd Service (Long-running)

For always-on agents.

#### 1. Setup Directory

```bash
sudo mkdir -p /opt/apt-agent
cd /opt/apt-agent
```

#### 2. Install Dependencies

```bash
sudo python3 -m venv venv
sudo venv/bin/pip install fastapi uvicorn aiohttp pydantic
```

#### 3. Create config.json

```bash
sudo tee config.json > /dev/null <<EOF
{
  "name": "systemd-agent",
  "mode": "emit",
  "emit_target": "influxdb://metrics.company.com:8086/agents",
  "auth_token": "your-token"
}
EOF
```

#### 4. Copy agent_server.py

```bash
sudo cp /path/to/apt/performance/agents/agent_server.py .
```

#### 5. Create Systemd Service

```bash
sudo tee /etc/systemd/system/apt-agent.service > /dev/null <<EOF
[Unit]
Description=APT Remote Agent
After=network.target

[Service]
Type=simple
User=apt-agent
WorkingDirectory=/opt/apt-agent
Environment="AGENT_PORT=9090"
ExecStart=/opt/apt-agent/venv/bin/python /opt/apt-agent/agent_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### 6. Create Service User

```bash
sudo useradd -r -s /bin/false apt-agent
sudo chown -R apt-agent:apt-agent /opt/apt-agent
```

#### 7. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable apt-agent
sudo systemctl start apt-agent
```

#### 8. Check Status

```bash
sudo systemctl status apt-agent
sudo journalctl -u apt-agent -f  # Follow logs
```

---

## Security Best Practices

### 1. Use Authentication Tokens

Always set `auth_token` in config.json:

```json
{
  "auth_token": "$(openssl rand -hex 32)"
}
```

Store the token securely and configure it in your test definitions.

### 2. Use TLS/HTTPS

For production, run agent behind nginx with TLS:

```nginx
server {
    listen 443 ssl;
    server_name agent.company.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:9090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Firewall Configuration

Only allow connections from APT framework:

```bash
# UFW example
sudo ufw allow from 10.0.0.0/8 to any port 9090
sudo ufw enable
```

### 4. Resource Limits

Set execution limits in config.json or Docker:

```bash
# Docker resource limits
docker run -d \
  --memory="512m" \
  --cpus="1.0" \
  --name apt-agent \
  apt-agent:latest
```

---

## Testing Your Agent

### 1. Health Check

```bash
curl http://agent-host:9090/health
```

### 2. Execute Test Code

```bash
curl -X POST http://agent-host:9090/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "code": "import time; result = {\"duration\": 1.5, \"status\": \"success\"}",
    "context": {},
    "timeout": 30
  }'
```

### 3. Query Metrics (Serve Mode)

```bash
curl "http://agent-host:9090/metrics?limit=10" \
  -H "Authorization: Bearer your-token"
```

---

## Troubleshooting

### Agent Not Starting

**Check logs:**
```bash
# Docker
docker logs apt-agent

# Systemd
sudo journalctl -u apt-agent -n 50

# Cron
cat /opt/apt-agent/agent.log
```

### Connection Refused

**Verify port binding:**
```bash
netstat -tlnp | grep 9090
```

**Check firewall:**
```bash
sudo ufw status
```

### Authentication Errors

**Verify token:**
```bash
# Check config.json
cat /opt/apt-agent/config.json

# Test with correct token
curl -H "Authorization: Bearer correct-token" http://localhost:9090/health
```

---

## Next Steps

1. Deploy agent using one of the methods above
2. Configure agent in your test YAML (see AGENT_USAGE.md)
3. Run tests with agent-based steps
4. Monitor agent health via APT framework

For usage examples, see: `docs/AGENT_USAGE.md`
