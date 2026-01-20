# APT Framework Examples

This directory contains comprehensive examples demonstrating all features of the APT Framework.

## 📚 Examples Overview

### **Basic Examples**

#### [01_simple_api_test.yml](01_simple_api_test.yml)
- **Level**: Beginner
- **Features**: Basic API testing
- **Use Case**: Simple REST API performance test
- **Tools**: API calls
- **Duration**: < 1 minute

#### [02_hybrid_multi_tool.yml](02_hybrid_multi_tool.yml)
- **Level**: Beginner
- **Features**: Multiple testing tools
- **Use Case**: Combined API + k6 + JMeter testing
- **Tools**: API, k6, JMeter
- **Duration**: 2-3 minutes

---

### **Distributed Testing**

#### [03_multi_region_test.yml](03_multi_region_test.yml)
- **Level**: Intermediate
- **Features**: Multi-region testing
- **Use Case**: Test from multiple geographic locations
- **Tools**: Remote agents, API calls
- **Duration**: 2-3 minutes

#### [09_async_distributed_browsers.yml](09_async_distributed_browsers.yml) ⭐ **NEW**
- **Level**: Advanced
- **Features**: Async agents, browser contexts, job queue
- **Use Case**: Long-running browser tests (30+ minutes)
- **Tools**: Playwright, async agents
- **Duration**: 30 minutes
- **Key Features**:
  - Browser contexts (isolated, efficient)
  - Async job queue
  - Priority scheduling
  - No AWS timeout issues

#### [10_weighted_load_distribution.yml](10_weighted_load_distribution.yml) ⭐ **NEW**
- **Level**: Advanced
- **Features**: Weighted load distribution, job queue
- **Use Case**: Distribute load based on agent capacity
- **Tools**: k6, async agents
- **Duration**: 30 minutes
- **Key Features**:
  - Weighted distribution (50%/25%/25%)
  - Priority-based scheduling
  - Concurrent job management

---

### **Production Monitoring**

#### [04_production_monitoring.yml](04_production_monitoring.yml)
- **Level**: Intermediate
- **Features**: Continuous monitoring
- **Use Case**: Production health checks and metrics
- **Tools**: Remote agents, custom scripts
- **Duration**: Continuous

---

### **Advanced Features**

#### [05_selective_iterations.yml](05_selective_iterations.yml)
- **Level**: Intermediate
- **Features**: Selective iteration aggregation
- **Use Case**: Aggregate only specific iterations
- **Tools**: Custom aggregators
- **Duration**: 5 minutes

#### [06_external_agent_code.yml](06_external_agent_code.yml)
- **Level**: Intermediate
- **Features**: External code files
- **Use Case**: Reusable test scripts
- **Tools**: Remote agents, external Python files
- **Duration**: 2-3 minutes
- **Scripts**: Uses `src/test_scripts/`

#### [07_complete_showcase.yml](07_complete_showcase.yml)
- **Level**: Advanced
- **Features**: All framework features
- **Use Case**: Comprehensive demonstration
- **Tools**: All tools combined
- **Duration**: 5-10 minutes

#### [08_advanced_agents.yml](08_advanced_agents.yml)
- **Level**: Advanced
- **Features**: Multi-agent coordination
- **Use Case**: Complex distributed testing
- **Tools**: Multiple specialized agents, k6
- **Duration**: 5 minutes
- **Key Features**:
  - Multiple specialized agents
  - Coordinated workflows
  - Priority scheduling
  - Custom validation

---

### **Legacy Examples**

#### [agent_test.yml](agent_test.yml)
- **Level**: Beginner
- **Features**: Basic agent testing
- **Use Case**: Test remote agent connectivity
- **Tools**: Remote agents
- **Duration**: 1 minute

#### [unified_performance_test.yml](unified_performance_test.yml)
- **Level**: Intermediate
- **Features**: Unified testing approach
- **Use Case**: Combined performance testing
- **Tools**: Multiple tools
- **Duration**: 3-5 minutes

---

## 🚀 Quick Start

### **Run an Example**

```bash
# Using pytest (recommended)
pytest examples/01_simple_api_test.yml -v

# Using CLI
./aptcli.py run examples/01_simple_api_test.yml
```

---

## 🎯 Latest Features (v2.0)

### **1. Async Agents with Job Queue**

**Example**: [09_async_distributed_browsers.yml](09_async_distributed_browsers.yml)

```yaml
agents:
  us-east-agent:
    endpoint: "http://vm1:9090"
    timeout: 1800  # 30 minutes

workflows:
  browser_test:
    concurrency: 15  # 15 concurrent browser contexts
    steps:
      - name: us_east_browsers
        agent: us-east-agent
        priority: high  # Priority scheduling
        code: |
          # Browser context code (isolated, efficient)
```

**Benefits**:
- ✅ No AWS ELB/NAT timeout issues
- ✅ Handles 30+ minute tests
- ✅ Job queue with priority
- ✅ Browser contexts (3x more efficient)

---

### **2. Browser Contexts**

**Instead of**:
```yaml
# Old: Multiple browser instances (heavy)
concurrency: 5  # 5 separate browsers = 5GB RAM
```

**Use**:
```yaml
# New: Browser contexts (efficient)
concurrency: 15  # 15 contexts = 6GB RAM (3x more efficient!)
```

**Benefits**:
- ✅ 70% less RAM
- ✅ 65% less CPU
- ✅ Same isolation
- ✅ 4x more capacity

---

### **3. Weighted Load Distribution**

**Example**: [10_weighted_load_distribution.yml](10_weighted_load_distribution.yml)

```yaml
workflows:
  weighted_load_test:
    steps:
      # Large agent: 500 VUs (50%)
      - name: large_agent_load
        agent: large-agent
        priority: urgent
        k6_config:
          options:
            vus: 500
      
      # Medium agent: 250 VUs (25%)
      - name: medium_agent_load
        agent: medium-agent
        k6_config:
          options:
            vus: 250
```

**Benefits**:
- ✅ Distribute based on capacity
- ✅ Priority scheduling
- ✅ Optimal resource usage

---

### **4. New Directory Structure**

**Old paths**:
```yaml
code_file: "agent_scripts/collect_metrics.py"  # ❌ Old
```

**New paths**:
```yaml
code_file: "src/test_scripts/collect_metrics.py"  # ✅ New
```

**All examples updated!**

---

## 📖 Feature Matrix

| Example | Agents | k6 | JMeter | Playwright | Async | Priority | Browser Contexts |
|---------|--------|----|----|-----------|-------|----------|-----------------|
| 01 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 02 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 03 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 04 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 05 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 06 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 07 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| 08 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **09** ⭐ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **10** ⭐ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 🎓 Learning Path

### **Beginner**
1. Start with [01_simple_api_test.yml](01_simple_api_test.yml)
2. Try [02_hybrid_multi_tool.yml](02_hybrid_multi_tool.yml)
3. Explore [agent_test.yml](agent_test.yml)

### **Intermediate**
1. Learn multi-region: [03_multi_region_test.yml](03_multi_region_test.yml)
2. Try external code: [06_external_agent_code.yml](06_external_agent_code.yml)
3. Explore monitoring: [04_production_monitoring.yml](04_production_monitoring.yml)

### **Advanced**
1. Master async agents: [09_async_distributed_browsers.yml](09_async_distributed_browsers.yml)
2. Learn load distribution: [10_weighted_load_distribution.yml](10_weighted_load_distribution.yml)
3. Study coordination: [08_advanced_agents.yml](08_advanced_agents.yml)

---

## 📚 See Also

- [Getting Started](../GETTING_STARTED.md)
- [Repository Structure](../STRUCTURE.md)
- [APTCLI Guide](../docs/APTCLI_GUIDE.md)
- [Agent Deployment](../docs/AGENT_DEPLOYMENT.md)
