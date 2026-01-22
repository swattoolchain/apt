"""
Performance Comparison and Baseline Tracking

Track performance metrics over time and compare against baselines.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceComparison:
    """Track and compare performance metrics over time."""
    
    def __init__(self, baseline_file: str = "performance_baseline.json"):
        """
        Initialize performance comparison tracker.
        
        Args:
            baseline_file: Path to baseline JSON file
        """
        self.baseline_file = Path(baseline_file)
        self.baseline = self._load_baseline()
    
    def _load_baseline(self) -> Dict:
        """Load baseline metrics from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading baseline: {e}")
                return {}
        return {}
    
    def save_baseline(self, test_name: str, metrics: Dict[str, float], metadata: Optional[Dict] = None):
        """
        Save current metrics as baseline.
        
        Args:
            test_name: Name of the test
            metrics: Dictionary of metric_name: value
            metadata: Optional metadata (git commit, environment, etc.)
        """
        self.baseline[test_name] = {
            'metrics': metrics,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baseline, f, indent=2)
        
        logger.info(f"Baseline saved for '{test_name}' with {len(metrics)} metrics")
    
    def compare(
        self, 
        test_name: str, 
        current_metrics: Dict[str, float],
        regression_threshold: float = 10.0
    ) -> Dict[str, Any]:
        """
        Compare current metrics with baseline.
        
        Args:
            test_name: Name of the test
            current_metrics: Current metric values
            regression_threshold: Percentage threshold for regression (default: 10%)
            
        Returns:
            Dictionary with comparison results
        """
        if test_name not in self.baseline:
            return {
                'status': 'no_baseline',
                'message': f'No baseline found for {test_name}',
                'test_name': test_name
            }
        
        baseline_data = self.baseline[test_name]
        baseline_metrics = baseline_data['metrics']
        
        comparison = {
            'test_name': test_name,
            'baseline_date': baseline_data['timestamp'],
            'baseline_metadata': baseline_data.get('metadata', {}),
            'current_date': datetime.now().isoformat(),
            'changes': {},
            'regressions': [],
            'improvements': [],
            'summary': {}
        }
        
        total_metrics = 0
        regression_count = 0
        improvement_count = 0
        
        for key, current_value in current_metrics.items():
            if key in baseline_metrics and isinstance(current_value, (int, float)):
                baseline_value = baseline_metrics[key]
                
                if baseline_value > 0:
                    change = current_value - baseline_value
                    change_pct = (change / baseline_value) * 100
                    
                    change_info = {
                        'baseline': baseline_value,
                        'current': current_value,
                        'change': change,
                        'change_pct': change_pct,
                        'is_regression': change_pct > regression_threshold,
                        'is_improvement': change_pct < -regression_threshold
                    }
                    
                    comparison['changes'][key] = change_info
                    total_metrics += 1
                    
                    if change_info['is_regression']:
                        regression_count += 1
                        comparison['regressions'].append({
                            'metric': key,
                            'change_pct': change_pct,
                            'baseline': baseline_value,
                            'current': current_value
                        })
                    elif change_info['is_improvement']:
                        improvement_count += 1
                        comparison['improvements'].append({
                            'metric': key,
                            'change_pct': change_pct,
                            'baseline': baseline_value,
                            'current': current_value
                        })
        
        comparison['summary'] = {
            'total_metrics': total_metrics,
            'regressions': regression_count,
            'improvements': improvement_count,
            'stable': total_metrics - regression_count - improvement_count,
            'has_regressions': regression_count > 0
        }
        
        return comparison
    
    def get_trend(self, test_name: str, metric_name: str, history_file: str = "performance_history.json") -> Dict:
        """
        Get historical trend for a specific metric.
        
        Args:
            test_name: Name of the test
            metric_name: Name of the metric
            history_file: Path to history file
            
        Returns:
            Dictionary with trend data
        """
        history_path = Path(history_file)
        
        if not history_path.exists():
            return {'status': 'no_history', 'message': 'No history file found'}
        
        try:
            with open(history_path) as f:
                history = json.load(f)
            
            if test_name not in history:
                return {'status': 'no_data', 'message': f'No history for {test_name}'}
            
            test_history = history[test_name]
            metric_values = []
            
            for entry in test_history:
                if metric_name in entry.get('metrics', {}):
                    metric_values.append({
                        'timestamp': entry['timestamp'],
                        'value': entry['metrics'][metric_name]
                    })
            
            if not metric_values:
                return {'status': 'no_data', 'message': f'No data for metric {metric_name}'}
            
            # Calculate trend statistics
            values = [v['value'] for v in metric_values]
            
            return {
                'test_name': test_name,
                'metric_name': metric_name,
                'data_points': len(values),
                'current': values[-1] if values else None,
                'average': sum(values) / len(values) if values else None,
                'min': min(values) if values else None,
                'max': max(values) if values else None,
                'history': metric_values
            }
            
        except Exception as e:
            logger.error(f"Error getting trend: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def append_to_history(
        self, 
        test_name: str, 
        metrics: Dict[str, float],
        metadata: Optional[Dict] = None,
        history_file: str = "performance_history.json"
    ):
        """
        Append current metrics to history for trend analysis.
        
        Args:
            test_name: Name of the test
            metrics: Current metrics
            metadata: Optional metadata
            history_file: Path to history file
        """
        history_path = Path(history_file)
        
        # Load existing history
        if history_path.exists():
            with open(history_path) as f:
                history = json.load(f)
        else:
            history = {}
        
        # Initialize test history if needed
        if test_name not in history:
            history[test_name] = []
        
        # Append current data
        history[test_name].append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'metadata': metadata or {}
        })
        
        # Keep only last 100 entries per test
        history[test_name] = history[test_name][-100:]
        
        # Save history
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Appended metrics to history for '{test_name}'")
