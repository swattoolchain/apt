"""
Distributed UI Performance Test
Measures page load performance from different geographic locations
Language: Python
"""
from playwright.sync_api import sync_playwright
import time

def measure_ui_performance(url, viewport_width=1920, viewport_height=1080):
    """
    Measure comprehensive UI performance metrics using Playwright
    
    Args:
        url: URL to test
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
    
    Returns:
        Dictionary with performance metrics
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
        
        # Start timing
        start_time = time.time()
        
        # Navigate to page
        page.goto(url, wait_until="networkidle")
        
        # Total load time
        total_load_time = time.time() - start_time
        
        # Get Web Vitals and Navigation Timing
        web_vitals = page.evaluate("""
            () => {
                const vitals = {};
                
                // First Contentful Paint
                const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
                vitals.fcp = fcpEntry ? fcpEntry.startTime : null;
                
                // Navigation Timing
                const timing = performance.timing;
                vitals.domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
                vitals.loadComplete = timing.loadEventEnd - timing.navigationStart;
                vitals.ttfb = timing.responseStart - timing.navigationStart;
                vitals.domInteractive = timing.domInteractive - timing.navigationStart;
                
                return vitals;
            }
        """)
        
        # Get resource counts
        resource_timing = page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                return {
                    total: resources.length,
                    scripts: resources.filter(r => r.initiatorType === 'script').length,
                    stylesheets: resources.filter(r => r.initiatorType === 'link').length,
                    images: resources.filter(r => r.initiatorType === 'img').length,
                    xhr: resources.filter(r => r.initiatorType === 'xmlhttprequest').length,
                    fetch: resources.filter(r => r.initiatorType === 'fetch').length
                };
            }
        """)
        
        # Get page size
        page_size = page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                const totalSize = resources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
                return {
                    total_bytes: totalSize,
                    total_mb: (totalSize / 1024 / 1024).toFixed(2)
                };
            }
        """)
        
        browser.close()
        
        return {
            "total_load_time_sec": round(total_load_time, 3),
            "fcp_ms": web_vitals.get("fcp"),
            "ttfb_ms": web_vitals.get("ttfb"),
            "dom_interactive_ms": web_vitals.get("domInteractive"),
            "dom_content_loaded_ms": web_vitals.get("domContentLoaded"),
            "load_complete_ms": web_vitals.get("loadComplete"),
            "resource_counts": resource_timing,
            "page_size": page_size,
            "url": url,
            "viewport": f"{viewport_width}x{viewport_height}",
            "success": True
        }

# Get parameters from context (passed from YAML)
url = context.get("url", "https://example.com")
viewport_width = context.get("viewport_width", 1920)
viewport_height = context.get("viewport_height", 1080)
region = context.get("region", "unknown")

# Run test
try:
    metrics = measure_ui_performance(url, viewport_width, viewport_height)
    metrics["region"] = region
    metrics["timestamp"] = time.time()
    result = metrics
except Exception as e:
    result = {
        "success": False,
        "error": str(e),
        "region": region,
        "url": url,
        "timestamp": time.time()
    }
