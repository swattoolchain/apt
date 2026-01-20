"""
Base Performance Testing Module

Provides base classes and data structures for performance testing.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import time
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Class to store performance metrics for a single test run."""
    
    test_name: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    iteration: int = 0
    user_id: int = 0
    
    # Metrics dictionary for flexible metric storage
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    # Artifacts
    screenshots: List[Dict[str, str]] = field(default_factory=list)
    trace_path: Optional[str] = None
    video_path: Optional[str] = None
    
    # Network requests
    network_requests: List[Dict] = field(default_factory=list)
    
    # Browser-specific metrics
    browser_metrics: Dict = field(default_factory=dict)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finalize(self) -> 'PerformanceMetrics':
        """Calculate final metrics and return self."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Performance test error in {self.test_name}: {error}")
    
    def add_screenshot(self, step: str, path: str) -> None:
        """Add a screenshot reference."""
        self.screenshots.append({
            "step": step,
            "path": path,
            "timestamp": time.time()
        })
    
    def add_network_request(self, request_data: Dict) -> None:
        """Add network request data."""
        self.network_requests.append(request_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_successful(self) -> bool:
        """Check if the test was successful (no errors)."""
        return len(self.errors) == 0


@dataclass
class PerformanceConfig:
    """Configuration for performance tests."""
    
    # Test execution settings
    concurrent_users: int = 5
    iterations: int = 3
    ramp_up_time: int = 0  # seconds to ramp up users
    
    # Browser settings (for UI tests)
    headless: bool = False
    browser_name: str = "chromium"
    viewport: Optional[Dict[str, int]] = None
    timeout: int = 60000  # milliseconds
    
    # Artifact settings
    screenshots: bool = True
    traces: bool = True
    videos: bool = False
    
    # Performance optimization settings
    lightweight_mode: bool = False  # Skip heavy metrics for high concurrency
    trace_on_failure_only: bool = False  # Only save traces for failed tests
    
    # API settings
    api_timeout: int = 30  # seconds
    
    # Output settings
    output_dir: str = "performance_results"
    generate_html: bool = True
    generate_json: bool = True
    open_browser: bool = False
    
    # Performance thresholds
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "page_load_time": 5.0,
        "api_response_time": 2.0,
        "error_rate": 0.05
    })
    
    def __post_init__(self):
        """Initialize default viewport if not provided."""
        if self.viewport is None:
            self.viewport = {"width": 1920, "height": 1080}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceConfig':
        """Create from dictionary."""
        return cls(**data)


class BasePerformanceTester:
    """Abstract base class for performance testing."""
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize the performance tester.
        
        Args:
            config: Performance test configuration
        """
        self.config = config
        self.results: List[PerformanceMetrics] = []
        self._setup_directories()
    
    def _setup_directories(self) -> None:
        """Create necessary directories for results."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_dir = Path(self.config.output_dir) / f"test_run_{self.timestamp}"
        self.screenshots_dir = self.test_dir / "screenshots"
        self.traces_dir = self.test_dir / "traces"
        self.videos_dir = self.test_dir / "videos"
        
        for directory in [self.test_dir, self.screenshots_dir, self.traces_dir, self.videos_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Performance test output directory: {self.test_dir}")
    
    def add_result(self, metrics: PerformanceMetrics) -> None:
        """Add a performance metrics result."""
        self.results.append(metrics)
    
    def get_results(self) -> List[PerformanceMetrics]:
        """Get all performance results."""
        return self.results
    
    def save_results_json(self, filename: str = "results.json") -> Path:
        """
        Save results to JSON file.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Path to the saved file
        """
        output_path = self.test_dir / filename
        
        data = {
            "timestamp": self.timestamp,
            "config": self.config.to_dict(),
            "results": [r.to_dict() for r in self.results],
            "summary": self._generate_summary()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return output_path
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics from results."""
        if not self.results:
            return {}
        
        durations = [r.duration for r in self.results if r.duration > 0]
        successful = [r for r in self.results if r.is_successful()]
        failed = [r for r in self.results if not r.is_successful()]
        
        summary = {
            "total_tests": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) if self.results else 0,
        }
        
        if durations:
            import numpy as np
            summary.update({
                "avg_duration": float(np.mean(durations)),
                "min_duration": float(min(durations)),
                "max_duration": float(max(durations)),
                "median_duration": float(np.median(durations)),
                "p95_duration": float(np.percentile(durations, 95)),
                "p99_duration": float(np.percentile(durations, 99)),
                "std_dev": float(np.std(durations))
            })
        
        return summary
    
    def check_thresholds(self) -> Dict[str, bool]:
        """
        Check if performance metrics meet configured thresholds.
        
        Returns:
            Dictionary of threshold checks
        """
        summary = self._generate_summary()
        checks = {}
        
        if "avg_duration" in summary:
            checks["page_load_time"] = summary["avg_duration"] <= self.config.thresholds.get("page_load_time", float('inf'))
        
        if "success_rate" in summary:
            error_rate = 1 - summary["success_rate"]
            checks["error_rate"] = error_rate <= self.config.thresholds.get("error_rate", 1.0)
        
        return checks
