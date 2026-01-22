#!/bin/bash
# Quick setup script for first distributed test

set -e

echo "🚀 APT Framework - First Distributed Test Setup"
echo "================================================"
echo ""

# Get VM details
read -p "VM1 IP address: " VM1_IP
read -p "VM2 IP address: " VM2_IP
read -p "VM SSH user (default: ubuntu): " SSH_USER
SSH_USER=${SSH_USER:-ubuntu}
read -sp "Auth token (will be generated if empty): " AUTH_TOKEN
echo ""

# Generate token if not provided
if [ -z "$AUTH_TOKEN" ]; then
    AUTH_TOKEN=$(openssl rand -hex 16)
    echo "Generated auth token: $AUTH_TOKEN"
fi

# Ask deployment method
echo ""
echo "Deployment method:"
echo "1) Docker (recommended)"
echo "2) Direct VM"
read -p "Choose (1 or 2): " DEPLOY_METHOD

# Create deployment directory
DEPLOY_DIR="agent_deployment_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

echo ""
echo "📦 Creating deployment files..."

# Copy agent server
cp ../performance/agents/agent_server.py ./

if [ "$DEPLOY_METHOD" == "1" ]; then
    echo "🐳 Creating Docker deployment files..."
    
    # Create Dockerfile
    cat > Dockerfile <<'EOF'
FROM python:3.9-slim

RUN apt-get update && apt-get install -y curl wget && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/grafana/k6/releases/download/v0.48.0/k6-v0.48.0-linux-amd64.tar.gz && \
    tar -xzf k6-v0.48.0-linux-amd64.tar.gz && \
    mv k6-v0.48.0-linux-amd64/k6 /usr/local/bin/ && \
    rm -rf k6-v0.48.0-linux-amd64*

RUN pip install --no-cache-dir fastapi uvicorn requests playwright
RUN playwright install chromium && playwright install-deps chromium

WORKDIR /app
COPY agent_server.py /app/
COPY config.json /app/

EXPOSE 9090

CMD ["python", "-m", "uvicorn", "agent_server:app", "--host", "0.0.0.0", "--port", "9090"]
EOF

    # Create config for VM1
    cat > config_vm1.json <<EOF
{
  "agent_id": "vm1-agent",
  "mode": "serve",
  "port": 9090,
  "auth_token": "$AUTH_TOKEN",
  "allowed_modules": ["requests", "json", "time", "datetime", "random", "playwright.sync_api", "subprocess"]
}
EOF

    # Create config for VM2
    cat > config_vm2.json <<EOF
{
  "agent_id": "vm2-agent",
  "mode": "serve",
  "port": 9090,
  "auth_token": "$AUTH_TOKEN",
  "allowed_modules": ["requests", "json", "time", "datetime", "random", "playwright.sync_api", "subprocess"]
}
EOF

    # Create deployment script
    cat > deploy.sh <<'DEPLOY_EOF'
#!/bin/bash
# Deploy agent with Docker

echo "Building Docker image..."
docker build -t apt-agent .

echo "Stopping old container if exists..."
docker stop apt-agent 2>/dev/null || true
docker rm apt-agent 2>/dev/null || true

echo "Starting agent container..."
docker run -d \
  --name apt-agent \
  -p 9090:9090 \
  --restart unless-stopped \
  apt-agent

echo "Waiting for agent to start..."
sleep 5

echo "Checking agent health..."
curl -s http://localhost:9090/health || echo "Health check failed"

echo "Agent deployed! Logs:"
docker logs apt-agent
DEPLOY_EOF

    chmod +x deploy.sh

    # Package for VM1
    tar -czf agent-vm1.tar.gz Dockerfile agent_server.py config_vm1.json deploy.sh
    
    # Package for VM2
    cp config_vm2.json config.json
    tar -czf agent-vm2.tar.gz Dockerfile agent_server.py config.json deploy.sh
    mv config_vm1.json config.json

    echo "✅ Docker deployment files created"
    
else
    echo "📦 Creating direct VM deployment files..."
    
    # Create config for VM1
    cat > config_vm1.json <<EOF
{
  "agent_id": "vm1-agent",
  "mode": "serve",
  "port": 9090,
  "auth_token": "$AUTH_TOKEN",
  "allowed_modules": ["requests", "json", "time", "datetime", "random", "playwright.sync_api", "subprocess"]
}
EOF

    # Create config for VM2
    cat > config_vm2.json <<EOF
{
  "agent_id": "vm2-agent",
  "mode": "serve",
  "port": 9090,
  "auth_token": "$AUTH_TOKEN",
  "allowed_modules": ["requests", "json", "time", "datetime", "random", "playwright.sync_api", "subprocess"]
}
EOF

    # Create setup script
    cat > setup.sh <<'SETUP_EOF'
#!/bin/bash
# Setup agent on VM

echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip wget

echo "Installing k6..."
wget https://github.com/grafana/k6/releases/download/v0.48.0/k6-v0.48.0-linux-amd64.tar.gz
tar -xzf k6-v0.48.0-linux-amd64.tar.gz
sudo mv k6-v0.48.0-linux-amd64/k6 /usr/local/bin/
rm -rf k6-v0.48.0-linux-amd64*

echo "Installing Python packages..."
pip3 install fastapi uvicorn requests playwright
playwright install chromium
playwright install-deps chromium

echo "Starting agent..."
nohup python3 -m uvicorn agent_server:app --host 0.0.0.0 --port 9090 > agent.log 2>&1 &

echo "Waiting for agent to start..."
sleep 5

echo "Checking agent health..."
curl -s http://localhost:9090/health || echo "Health check failed"

echo "Agent started! Check logs: tail -f agent.log"
SETUP_EOF

    chmod +x setup.sh

    # Package for VM1
    tar -czf agent-vm1.tar.gz agent_server.py config_vm1.json setup.sh
    
    # Package for VM2
    tar -czf agent-vm2.tar.gz agent_server.py config_vm2.json setup.sh

    echo "✅ Direct VM deployment files created"
fi

echo ""
echo "📤 Deploying to VMs..."

# Deploy to VM1
echo "Deploying to VM1 ($VM1_IP)..."
scp agent-vm1.tar.gz $SSH_USER@$VM1_IP:/tmp/
ssh $SSH_USER@$VM1_IP "mkdir -p ~/apt-agent && cd ~/apt-agent && tar -xzf /tmp/agent-vm1.tar.gz && mv config_vm1.json config.json && ./$([ "$DEPLOY_METHOD" == "1" ] && echo "deploy.sh" || echo "setup.sh")"

# Deploy to VM2
echo "Deploying to VM2 ($VM2_IP)..."
scp agent-vm2.tar.gz $SSH_USER@$VM2_IP:/tmp/
ssh $SSH_USER@$VM2_IP "mkdir -p ~/apt-agent && cd ~/apt-agent && tar -xzf /tmp/agent-vm2.tar.gz && mv config_vm2.json config.json && ./$([ "$DEPLOY_METHOD" == "1" ] && echo "deploy.sh" || echo "setup.sh")"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 Creating test file..."

# Create test YAML
cat > ../my_first_distributed_test.yml <<EOF
test_info:
  test_suite_name: "My First Distributed Test"
  test_suite_type: "unified"
  description: "Testing from 2 VMs"
  version: "1.0"

agents:
  vm1:
    endpoint: "http://$VM1_IP:9090"
    auth_token: "$AUTH_TOKEN"
    timeout: 300
  vm2:
    endpoint: "http://$VM2_IP:9090"
    auth_token: "$AUTH_TOKEN"
    timeout: 300

workflows:
  distributed_test:
    iterations: 1
    steps:
      - name: api_test_vm1
        action: api_call
        agent: vm1
        url: "https://httpbin.org/get"
        method: GET
      
      - name: api_test_vm2
        action: api_call
        agent: vm2
        url: "https://httpbin.org/get"
        method: GET

reporting:
  output_dir: "performance_results/my_first_distributed_test"
  formats: ["html", "json"]
EOF

echo "✅ Test file created: my_first_distributed_test.yml"
echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify agents are healthy:"
echo "   curl http://$VM1_IP:9090/health"
echo "   curl http://$VM2_IP:9090/health"
echo ""
echo "2. Run your first distributed test:"
echo "   cd .."
echo "   pytest my_first_distributed_test.yml -v"
echo ""
echo "3. View the unified report:"
echo "   open performance_results/my_first_distributed_test/unified_performance_report.html"
echo ""
echo "Auth token: $AUTH_TOKEN"
echo "Save this token - you'll need it for future tests!"
