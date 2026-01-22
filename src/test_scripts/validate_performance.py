"""
Performance validation script
Language: Python
"""
import json

def validate_performance(threshold_p95, threshold_error_rate):
    """Validate performance against thresholds"""
    # This would typically query collected metrics
    # For demo, using mock data
    
    validation_results = {
        "passed": True,
        "violations": [],
        "metrics": {
            "p95_latency": 450,  # Mock value
            "error_rate": 0.005,  # Mock value
            "throughput": 1000    # Mock value
        },
        "thresholds": {
            "p95_latency": threshold_p95,
            "error_rate": threshold_error_rate
        }
    }
    
    # Check P95 latency
    if validation_results["metrics"]["p95_latency"] > threshold_p95:
        validation_results["passed"] = False
        validation_results["violations"].append({
            "metric": "p95_latency",
            "value": validation_results["metrics"]["p95_latency"],
            "threshold": threshold_p95,
            "message": f"P95 latency {validation_results['metrics']['p95_latency']}ms exceeds threshold {threshold_p95}ms"
        })
    
    # Check error rate
    if validation_results["metrics"]["error_rate"] > threshold_error_rate:
        validation_results["passed"] = False
        validation_results["violations"].append({
            "metric": "error_rate",
            "value": validation_results["metrics"]["error_rate"],
            "threshold": threshold_error_rate,
            "message": f"Error rate {validation_results['metrics']['error_rate']} exceeds threshold {threshold_error_rate}"
        })
    
    return validation_results

# Execute with context
threshold_p95 = context.get("threshold_p95", 500)
threshold_error_rate = context.get("threshold_error_rate", 0.01)

result = validate_performance(threshold_p95, threshold_error_rate)
