"""
Health check script for production API
Language: Python
"""
import requests
import time
import json

def check_health():
    """Check API health endpoint"""
    start = time.time()
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        duration = time.time() - start
        
        return {
            "duration": duration,
            "status_code": response.status_code,
            "healthy": response.status_code == 200,
            "response_time_ms": duration * 1000,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "duration": time.time() - start,
            "status_code": 0,
            "healthy": False,
            "error": str(e),
            "timestamp": time.time()
        }

# Execute and set result
result = check_health()
