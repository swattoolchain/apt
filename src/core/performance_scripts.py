"""
Performance Scripts - Reusable test methods
Convention: Methods here can be called by step name without explicit code_file parameter
"""
import requests
import time
from playwright.sync_api import sync_playwright


def ui_test_us_east(context):
    """
    UI performance test for US East region
    Automatically called when step name is 'ui_test_us_east'
    """
    url = context.get("url", "https://example.com")
    viewport_width = context.get("viewport_width", 1920)
    viewport_height = context.get("viewport_height", 1080)
    region = context.get("region", "us-east")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
        
        start = time.time()
        page.goto(url, wait_until="networkidle")
        load_time = time.time() - start
        
        # Get metrics
        metrics = page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    ttfb: timing.responseStart - timing.navigationStart,
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    loadComplete: timing.loadEventEnd - timing.navigationStart
                };
            }
        """)
        
        browser.close()
        
        return {
            "total_load_time": load_time,
            "ttfb_ms": metrics["ttfb"],
            "dom_content_loaded_ms": metrics["domContentLoaded"],
            "load_complete_ms": metrics["loadComplete"],
            "url": url,
            "region": region,
            "success": True
        }


def ui_test_eu_west(context):
    """
    UI performance test for EU West region
    Automatically called when step name is 'ui_test_eu_west'
    """
    url = context.get("url", "https://example.com")
    viewport_width = context.get("viewport_width", 1920)
    viewport_height = context.get("viewport_height", 1080)
    region = context.get("region", "eu-west")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
        
        start = time.time()
        page.goto(url, wait_until="networkidle")
        load_time = time.time() - start
        
        # Get metrics
        metrics = page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    ttfb: timing.responseStart - timing.navigationStart,
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    loadComplete: timing.loadEventEnd - timing.navigationStart
                };
            }
        """)
        
        browser.close()
        
        return {
            "total_load_time": load_time,
            "ttfb_ms": metrics["ttfb"],
            "dom_content_loaded_ms": metrics["domContentLoaded"],
            "load_complete_ms": metrics["loadComplete"],
            "url": url,
            "region": region,
            "success": True
        }


def api_health_check(context):
    """
    Simple API health check
    Automatically called when step name is 'api_health_check'
    """
    url = context.get("url", "http://localhost:8080/health")
    timeout = context.get("timeout", 5)
    
    start = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        duration = time.time() - start
        
        return {
            "duration": duration,
            "status_code": response.status_code,
            "healthy": response.status_code == 200,
            "url": url,
            "success": True
        }
    except Exception as e:
        return {
            "duration": time.time() - start,
            "status_code": 0,
            "healthy": False,
            "error": str(e),
            "url": url,
            "success": False
        }


def database_connectivity_check(context):
    """
    Check database connectivity
    Automatically called when step name is 'database_connectivity_check'
    """
    import psycopg2
    
    db_host = context.get("db_host", "localhost")
    db_name = context.get("db_name", "postgres")
    db_user = context.get("db_user", "postgres")
    
    start = time.time()
    try:
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            connect_timeout=5
        )
        duration = time.time() - start
        conn.close()
        
        return {
            "duration": duration,
            "connected": True,
            "db_host": db_host,
            "db_name": db_name,
            "success": True
        }
    except Exception as e:
        return {
            "duration": time.time() - start,
            "connected": False,
            "error": str(e),
            "db_host": db_host,
            "success": False
        }
