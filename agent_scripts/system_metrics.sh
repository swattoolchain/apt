#!/bin/bash
# System metrics collection
# Language: Shell

# Collect CPU, memory, disk usage
cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
memory_usage=$(vm_stat | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')

# Output as JSON-like result
echo "result = {
    'cpu_usage': $cpu_usage,
    'memory_usage': $memory_usage,
    'disk_usage': $disk_usage,
    'timestamp': $(date +%s)
}"
