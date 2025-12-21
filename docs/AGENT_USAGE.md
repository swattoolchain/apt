# Agent Usage Guide

This guide shows how to use remote agents in your APT performance tests.

## Quick Start

### 1. Deploy an Agent

Follow the [Agent Deployment Guide](AGENT_DEPLOYMENT.md) to deploy an agent using Docker, cron, or systemd.

### 2. Configure Agent in YAML

```yaml
# Define agents in your test file
agents:
  us-east-server:
    endpoint: "http://agent-us-east.company.com:9090"
    auth_token: "${US_EAST_TOKEN}"  # From environment variable
    timeout: 300
    health_check_interval: 60
  
  eu-west-server:
    endpoint: "http://agent-eu-west.company.com:9090"
    auth_token: "${EU_WEST_TOKEN}"
    timeout: 300

# Use agents in workflows
workflows:
  multi_region_test:
    iterations: 10
    steps:
      - name: test_from_us_east
        action: agent_execute
        agent: us-east-server
        code: |
          import requests
          import time
          
          start = time.time()
          response = requests.get("https://api.company.com/health")
          duration = time.time() - start
          
          result = {
            "duration": duration,
            "status_code": response.status_code,
            "region": "us-east"
          }
      
      - name: test_from_eu_west
        action: agent_execute
        agent: eu-west-server
        code: |
          import requests
          import time
          
          start = time.time()
          response = requests.get("https://api.company.com/health")
          duration = time.time() - start
          
          result = {
            "duration": duration,
            "status_code": response.status_code,
            "region": "eu-west"
          }
```

### 3. Run Test

```bash
export US_EAST_TOKEN="your-token-1"
export EU_WEST_TOKEN="your-token-2"

pytest your_test.yml
```

## Step Actions

### agent_execute

Execute code on a remote agent and collect metrics.

**Required Fields:**
- `action`: `agent_execute`
- `agent`: Agent ID (defined in `agents` section)
- `code`: Python code to execute

**Optional Fields:**
- `context`: Variables to pass to execution
- `tags`: Tags for metrics
- `timeout`: Execution timeout (overrides agent default)

**Example:**

```yaml
- name: database_query_test
  action: agent_execute
  agent: db-server-agent
  context:
    query: "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '1 day'"
  code: |
    import psycopg2
    import time
    
    conn = psycopg2.connect("dbname=prod user=readonly")
    cursor = conn.cursor()
    
    start = time.time()
    cursor.execute(context['query'])
    rows = cursor.fetchall()
    duration = time.time() - start
    
    result = {
      "duration": duration,
      "row_count": len(rows),
      "query": context['query']
    }
```

### agent_query

Query metrics from an agent (serve mode only).

**Required Fields:**
- `action`: `agent_query`
- `agent`: Agent ID

**Optional Fields:**
- `metric`: Metric name to filter
- `timerange`: Time range (e.g., `last_1h`, `last_24h`)
- `filters`: Additional filters
- `limit`: Maximum results

**Example:**

```yaml
- name: get_recent_metrics
  action: agent_query
  agent: monitoring-agent
  metric: "cpu_usage"
  timerange: "last_1h"
  filters:
    host: "web-server-1"
  limit: 100
```

## Use Cases

### Use Case 1: Multi-Region Latency Testing

Test API latency from multiple geographic locations:

```yaml
agents:
  us-east:
    endpoint: "http://us-east-agent.company.com:9090"
    auth_token: "${US_EAST_TOKEN}"
  
  eu-west:
    endpoint: "http://eu-west-agent.company.com:9090"
    auth_token: "${EU_WEST_TOKEN}"
  
  ap-south:
    endpoint: "http://ap-south-agent.company.com:9090"
    auth_token: "${AP_SOUTH_TOKEN}"

workflows:
  global_latency_test:
    iterations: 100
    steps:
      - name: us_east_latency
        action: agent_execute
        agent: us-east
        code: |
          import requests, time
          start = time.time()
          r = requests.get("https://api.company.com/health")
          result = {"duration": time.time() - start, "region": "us-east"}
      
      - name: eu_west_latency
        action: agent_execute
        agent: eu-west
        code: |
          import requests, time
          start = time.time()
          r = requests.get("https://api.company.com/health")
          result = {"duration": time.time() - start, "region": "eu-west"}
      
      - name: ap_south_latency
        action: agent_execute
        agent: ap-south
        code: |
          import requests, time
          start = time.time()
          r = requests.get("https://api.company.com/health")
          result = {"duration": time.time() - start, "region": "ap-south"}
```

### Use Case 2: Database Performance from App Server

Measure database query performance from the application server's perspective:

```yaml
agents:
  app-server:
    endpoint: "http://app-server-1.internal:9090"
    auth_token: "${APP_SERVER_TOKEN}"

workflows:
  db_performance_test:
    iterations: 50
    steps:
      - name: simple_query
        action: agent_execute
        agent: app-server
        code: |
          import psycopg2, time
          conn = psycopg2.connect("dbname=prod")
          cursor = conn.cursor()
          start = time.time()
          cursor.execute("SELECT * FROM users LIMIT 100")
          rows = cursor.fetchall()
          result = {"duration": time.time() - start, "rows": len(rows)}
      
      - name: complex_join
        action: agent_execute
        agent: app-server
        code: |
          import psycopg2, time
          conn = psycopg2.connect("dbname=prod")
          cursor = conn.cursor()
          start = time.time()
          cursor.execute("""
            SELECT u.*, o.* FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE o.created_at > NOW() - INTERVAL '7 days'
          """)
          rows = cursor.fetchall()
          result = {"duration": time.time() - start, "rows": len(rows)}
```

### Use Case 3: Hybrid Local + Remote Testing

Combine local execution with remote agents:

```yaml
agents:
  production-monitor:
    endpoint: "https://prod-agent.company.com:9090"
    auth_token: "${PROD_TOKEN}"

workflows:
  hybrid_test:
    steps:
      # Local execution (existing functionality)
      - name: local_api_call
        action: api_call
        url: "https://api.company.com/test"
        method: GET
      
      # Remote execution on production agent
      - name: production_check
        action: agent_execute
        agent: production-monitor
        code: |
          import requests, time
          start = time.time()
          r = requests.get("http://localhost:8080/internal/health")
          result = {
            "duration": time.time() - start,
            "status": r.status_code,
            "environment": "production"
          }
      
      # Local k6 test
      - name: load_test
        action: k6_test
        scenarios:
          - name: "API Load"
            url: "https://api.company.com/users"
        options:
          vus: 10
          duration: "30s"
```

## Agent Configuration Reference

### Agent Definition

```yaml
agents:
  agent-id:
    endpoint: string          # Required: Agent URL
    auth_token: string        # Optional: Authentication token
    timeout: int              # Optional: Default execution timeout (seconds)
    health_check_interval: int # Optional: Health check interval (seconds)
```

### Environment Variables

Use environment variables for sensitive data:

```yaml
agents:
  my-agent:
    endpoint: "${AGENT_ENDPOINT}"
    auth_token: "${AGENT_TOKEN}"
```

```bash
export AGENT_ENDPOINT="http://agent.company.com:9090"
export AGENT_TOKEN="secret-token"
```

## Security Best Practices

### 1. Always Use Authentication

```yaml
agents:
  secure-agent:
    endpoint: "https://agent.company.com:9090"
    auth_token: "${SECURE_TOKEN}"  # Never hardcode tokens
```

### 2. Use HTTPS in Production

Deploy agents behind TLS-enabled reverse proxy (nginx, Caddy, etc.).

### 3. Restrict Code Execution

Agents run in a sandboxed environment with limited imports. Only whitelisted modules are available:
- `time`
- `json`
- `requests`
- `datetime`
- `math`

### 4. Set Execution Timeouts

```yaml
- name: risky_operation
  action: agent_execute
  agent: my-agent
  timeout: 60  # Limit to 60 seconds
  code: |
    # Your code here
```

## Monitoring Agent Health

### Check Status Programmatically

```python
from performance.agents import AgentRegistry, AgentHealthMonitor

# Create registry
registry = AgentRegistry()

# Register agents from YAML config
# (This happens automatically in UnifiedYAMLTestRunner)

# Start health monitoring
monitor = AgentHealthMonitor(registry)
await monitor.start()

# Get status
status = monitor.get_status('my-agent')
print(f"Agent status: {status['status']}")
print(f"Uptime: {status['uptime_percentage']:.2f}%")

# Get all statuses
all_statuses = monitor.get_all_statuses()
```

### CLI Status Check

```bash
# Check all agents
aptcli agent status

# Check specific agent
aptcli agent status --name my-agent
```

### Health Check Endpoint

```bash
curl http://agent-host:9090/health

# Response:
# {
#   "status": "healthy",
#   "agent_name": "my-agent",
#   "mode": "emit",
#   "uptime_seconds": 3600.5,
#   "metrics_count": 150,
#   "timestamp": "2024-01-01T12:00:00"
# }
```

## Troubleshooting

### Agent Connection Failed

**Check agent is running:**
```bash
curl http://agent-host:9090/health
```

**Verify network connectivity:**
```bash
telnet agent-host 9090
```

**Check authentication:**
```bash
curl -H "Authorization: Bearer your-token" http://agent-host:9090/health
```

### Code Execution Errors

**Check agent logs:**
```bash
# Docker
docker logs apt-agent

# Systemd
sudo journalctl -u apt-agent -n 100
```

**Common issues:**
- Import errors: Module not in whitelist
- Timeout: Increase timeout in step definition
- Syntax errors: Validate Python code locally first

### Metrics Not Appearing

**For emit mode:**
- Verify `emit_target` in agent config.json
- Check InfluxDB connectivity from agent
- Review agent logs for emission errors

**For serve mode:**
- Query metrics endpoint: `GET /metrics`
- Check metrics_count in health response
- Verify agent has processed requests

## Next Steps

1. Deploy your first agent (see [AGENT_DEPLOYMENT.md](AGENT_DEPLOYMENT.md))
2. Configure agents in your test YAML
3. Run tests with `agent_execute` steps
4. Monitor agent health and metrics

For advanced scenarios, see the [Agent System Design](../brain/agent_system_design.md).
