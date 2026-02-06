# QPT Multi-Agent Test - Quick Start

## Current Setup

- **JMeter Agent**: ubuntu@172.31.128.182 (VM1)
- **k6 Agent**: ubuntu@172.31.128.185 (VM2)
- **Auth Tokens**: Stored in `examples/multi_agent_hybrid_test.yml`

## To Run the Test

### 1. Open Security Group Port 9090 (Recommended)

If you can modify AWS security groups:

```bash
# Add inbound rule for port 9090 from your VPN CIDR
# Then update test file to use direct IPs:
# endpoint: "http://172.31.128.182:9090"
# endpoint: "http://172.31.128.185:9090"
```

### 2. OR Use SSH Tunnels (Current Setup)

```bash
# Start agents and tunnels
./restart_agents.sh

# Run test
pytest examples/multi_agent_hybrid_test.yml -v -s

# View report
open performance_results/multi_agent_test/unified_performance_report.html
```

## Manual Agent Management

### Check Agent Status

```bash
# Via SSH
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.182 "curl -s http://localhost:9090/health"
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.185 "curl -s http://localhost:9090/health"

# Via Tunnel (if active)
curl http://localhost:9091/health
curl http://localhost:9092/health
```

### Restart Agents

```bash
# JMeter Agent
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.182 "cd jmeter-agent && pkill -f agent_server && ./start_agent.sh"

# k6 Agent
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.185 "cd k6-agent && pkill -f agent_server && ./start_agent.sh"
```

### View Agent Logs

```bash
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.182 "tail -50 jmeter-agent/agent.log"
ssh -i ~/pems/world-cloud.pem ubuntu@172.31.128.185 "tail -50 k6-agent/agent.log"
```

## Test File Location

`examples/multi_agent_hybrid_test.yml`

## Results Location

`performance_results/multi_agent_test/`
- `unified_results.json` - Raw data
- `unified_performance_report.html` - Visual report

## Next Steps

1. **Fix Network Access**: Choose Option 1 or 2 above
2. **Run Full Test**: Execute the test with both agents
3. **Review Results**: Check the unified report
4. **Scale Up**: Add more agents or increase load parameters

## Framework Documentation

See `docs/QPT_FRAMEWORK_GUIDE.md` for complete framework reference.
