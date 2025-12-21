"""
Metrics collection script
Language: Python
"""
import time
import psutil
import json

def collect_metrics(metric_type, duration):
    """Collect system and application metrics"""
    metrics = {
        "metric_type": metric_type,
        "timestamp": time.time(),
        "duration": duration,
        "system": {},
        "network": {},
        "disk": {}
    }
    
    # Collect system metrics
    metrics["system"]["cpu_percent"] = psutil.cpu_percent(interval=1)
    metrics["system"]["memory_percent"] = psutil.virtual_memory().percent
    metrics["system"]["memory_available_mb"] = psutil.virtual_memory().available / (1024 * 1024)
    
    # Collect network metrics
    net_io = psutil.net_io_counters()
    metrics["network"]["bytes_sent"] = net_io.bytes_sent
    metrics["network"]["bytes_recv"] = net_io.bytes_recv
    metrics["network"]["packets_sent"] = net_io.packets_sent
    metrics["network"]["packets_recv"] = net_io.packets_recv
    
    # Collect disk metrics
    disk_io = psutil.disk_io_counters()
    metrics["disk"]["read_bytes"] = disk_io.read_bytes
    metrics["disk"]["write_bytes"] = disk_io.write_bytes
    metrics["disk"]["read_count"] = disk_io.read_count
    metrics["disk"]["write_count"] = disk_io.write_count
    
    # Collect over duration
    if duration > 1:
        time.sleep(duration)
        
        # Collect again for delta
        net_io_after = psutil.net_io_counters()
        disk_io_after = psutil.disk_io_counters()
        
        metrics["network"]["bytes_sent_per_sec"] = (net_io_after.bytes_sent - net_io.bytes_sent) / duration
        metrics["network"]["bytes_recv_per_sec"] = (net_io_after.bytes_recv - net_io.bytes_recv) / duration
        metrics["disk"]["read_bytes_per_sec"] = (disk_io_after.read_bytes - disk_io.read_bytes) / duration
        metrics["disk"]["write_bytes_per_sec"] = (disk_io_after.write_bytes - disk_io.write_bytes) / duration
    
    return metrics

# Execute with context
metric_type = context.get("metric_type", "baseline")
duration = context.get("duration", 60)

result = collect_metrics(metric_type, duration)
