"""
Load generation script
Language: Python
"""
import requests
import time
import concurrent.futures

def generate_load(target_url, requests_per_second, duration):
    """Generate HTTP load"""
    total_requests = requests_per_second * duration
    interval = 1.0 / requests_per_second
    
    results = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_duration": 0,
        "min_duration": float('inf'),
        "max_duration": 0,
        "durations": []
    }
    
    start_time = time.time()
    
    def make_request():
        req_start = time.time()
        try:
            response = requests.get(target_url, timeout=10)
            req_duration = time.time() - req_start
            return {
                "success": response.status_code == 200,
                "duration": req_duration,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - req_start,
                "error": str(e)
            }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(int(total_requests)):
            futures.append(executor.submit(make_request))
            time.sleep(interval)
            
            if time.time() - start_time >= duration:
                break
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results["total_requests"] += 1
            
            if result["success"]:
                results["successful_requests"] += 1
            else:
                results["failed_requests"] += 1
            
            duration_val = result["duration"]
            results["total_duration"] += duration_val
            results["durations"].append(duration_val)
            results["min_duration"] = min(results["min_duration"], duration_val)
            results["max_duration"] = max(results["max_duration"], duration_val)
    
    # Calculate statistics
    if results["durations"]:
        sorted_durations = sorted(results["durations"])
        results["avg_duration"] = results["total_duration"] / len(results["durations"])
        results["p50_duration"] = sorted_durations[len(sorted_durations) // 2]
        results["p95_duration"] = sorted_durations[int(len(sorted_durations) * 0.95)]
        results["p99_duration"] = sorted_durations[int(len(sorted_durations) * 0.99)]
    
    results["success_rate"] = results["successful_requests"] / results["total_requests"] if results["total_requests"] > 0 else 0
    
    return results

# Execute with context parameters
target_url = context.get("target_url", "https://api.example.com")
rps = context.get("requests_per_second", 100)
duration = context.get("duration", 60)

result = generate_load(target_url, rps, duration)
