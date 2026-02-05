# QPT Distributed Testing: Simple Guide

This guide explains how tests run across different machines using the **Quvia Performance Toolkit (QPT)**.

---

## 🏃 How the Test Runs (Step-by-Step)

When you run a command like `python3 qptcli.py run my_test.yml`, here is what happens:

1.  **Reading the Instructions**: QPT reads your YAML file to see what tools (JMeter, k6, etc.) and what agents (remote VMs) are needed.
2.  **Health Check (The "Are you awake?" Phase)**:
    *   QPT pings every remote agent to see if it is online.
    *   **Self-Healing**: If an agent is down, QPT uses the `deploy_info` in your YAML to automatically log into that VM via SSH, set up everything it needs, and start the agent service for you.
3.  **Sending the Work**: QPT looks at each step in your test. If a step is assigned to a remote agent, QPT "bundles" the code or the script file and sends it to that agent over the network.
4.  **Reporting**: Once all agents finish their work, QPT gathers all the numbers and creates one single HTML report.

---

## ❓ Common Questions

### 1. Do steps run in Sequential or Parallel?
*   **Sequential (Default)**: Steps run one after another.
*   **Parallel Groups (New)**: You can group steps to run simultaneously across multiple agents.
    ```yaml
    - group: "attack_phase"
      parallel: true
      steps:
        - name: us_load (runs on agent-1)
        - name: eu_load (runs on agent-2)
    ```
*   **Load Testing**: Inside a `k6_test` or `jmeter_test` step, the traffic is always parallel.

### 2. How does the local VM know the Agent is done?
It works like a phone call:
1.  The local VM (Your machine) sends a "POST" request to the Agent with the code.
2.  The Local VM **stays on the line** (waits for the response).
3.  The Agent runs the test.
4.  When the Agent finishes, it sends back the results as the response to that same "POST" request.
5.  Only after receiving this response does the Local VM move to the next step.

---

## 🧪 How to Add New Tests

### Path 1: Just YAML (No coding)
Best for standard load tests.
```yaml
- name: api_stress
  action: k6_test        # Use k6
  agent: k6-server       # Run on this remote VM
  k6_config:
    vus: 10              # 10 Parallel users
    duration: "30s"      # Run for 30 seconds
    scenarios: [ {url: "http://api.com", method: "GET"} ]
```

### Path 2: Auto-Discovery (Naming convention)
Best for custom logic.
1. Create a file in `examples/agent_scripts/` called `my_check.py`.
2. Inside it, write your Python code.
3. In your YAML, just name the step `my_check`. QPT will automatically find the file and send it to the agent.

---

## � Quick Links
*   **Run a test**: `python3 qptcli.py run <file.yml>`
*   **Check Agent**: `python3 qptcli.py agent status --endpoint <url>`
*   **The Code**: View `performance_scripts.py` for reusable methods.
