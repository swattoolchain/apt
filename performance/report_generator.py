"""
Performance Report Generator

Generates comprehensive HTML reports with visualizations for performance test results.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from jinja2 import Environment, BaseLoader
import logging

from .base_performance_tester import PerformanceMetrics, PerformanceConfig
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class PerformanceReportGenerator:
    """Generates HTML performance reports."""
    
    def __init__(self, metrics_collector: MetricsCollector, config: PerformanceConfig, output_dir: Path):
        """
        Initialize report generator.
        
        Args:
            metrics_collector: MetricsCollector with test results
            config: Performance test configuration
            output_dir: Directory to save reports
        """
        self.collector = metrics_collector
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_html_report(self, filename: str = "performance_report.html") -> Path:
        """
        Generate comprehensive HTML report.
        
        Args:
            filename: Name of the HTML file
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / filename
        
        # Get statistics
        summary = self.collector.get_summary_statistics()
        test_stats = self.collector.get_all_test_statistics()
        percentile_data = self.collector.get_percentile_data()
        
        # Generate HTML
        html_content = self._render_html_template(summary, test_stats, percentile_data)
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {report_path}")
        return report_path
    
    def _render_html_template(
        self, 
        summary: Dict[str, Any], 
        test_stats: List[Dict[str, Any]],
        percentile_data: Dict[str, Dict[int, float]]
    ) -> str:
        """Render HTML template with data."""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report - {{ timestamp }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        
        header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        header .subtitle {
            opacity: 0.9;
            font-size: 16px;
        }
        
        .content {
            padding: 30px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        
        .metric-card.success {
            border-left-color: #10b981;
        }
        
        .metric-card.warning {
            border-left-color: #f59e0b;
        }
        
        .metric-card.error {
            border-left-color: #ef4444;
        }
        
        .metric-label {
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #1f2937;
        }
        
        .metric-unit {
            font-size: 16px;
            color: #6b7280;
            margin-left: 4px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1f2937;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 12px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-error {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            transition: width 0.3s ease;
        }
        
        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f9fafb;
            border-radius: 8px;
        }
        
        .percentile-bar {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }
        
        .percentile-label {
            width: 80px;
            font-weight: 600;
            color: #6b7280;
        }
        
        .percentile-value {
            flex: 1;
            margin: 0 15px;
        }
        
        .percentile-number {
            width: 100px;
            text-align: right;
            font-weight: 600;
        }
        
        footer {
            background: #f3f4f6;
            padding: 20px 30px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }
        
        .config-section {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .config-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .config-item:last-child {
            border-bottom: none;
        }
        
        .config-label {
            font-weight: 600;
            color: #374151;
        }
        
        .config-value {
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Performance Test Report</h1>
            <div class="subtitle">Generated on {{ timestamp }}</div>
        </header>
        
        <div class="content">
            <!-- Summary Section -->
            <div class="section">
                <h2 class="section-title">Executive Summary</h2>
                <div class="summary-grid">
                    <div class="metric-card">
                        <div class="metric-label">Total Tests</div>
                        <div class="metric-value">{{ summary.total_tests }}</div>
                    </div>
                    
                    <div class="metric-card success">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">{{ "%.1f"|format(summary.success_rate * 100) }}<span class="metric-unit">%</span></div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {{ summary.success_rate * 100 }}%"></div>
                        </div>
                    </div>
                    
                    {% if summary.avg_duration is defined %}
                    <div class="metric-card">
                        <div class="metric-label">Avg Duration</div>
                        <div class="metric-value">{{ "%.3f"|format(summary.avg_duration) }}<span class="metric-unit">s</span></div>
                    </div>
                    
                    <div class="metric-card warning">
                        <div class="metric-label">P95 Duration</div>
                        <div class="metric-value">{{ "%.3f"|format(summary.p95_duration) }}<span class="metric-unit">s</span></div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Test Results Section -->
            <div class="section">
                <h2 class="section-title">Test Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>Runs</th>
                            <th>Success Rate</th>
                            <th>Avg Duration</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>P95</th>
                            <th>Std Dev</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for test in test_stats %}
                        <tr>
                            <td><strong>{{ test.test_name }}</strong></td>
                            <td>{{ test.total_runs }}</td>
                            <td>
                                {% if test.success_rate >= 0.95 %}
                                <span class="badge badge-success">{{ "%.1f"|format(test.success_rate * 100) }}%</span>
                                {% else %}
                                <span class="badge badge-error">{{ "%.1f"|format(test.success_rate * 100) }}%</span>
                                {% endif %}
                            </td>
                            <td>{{ "%.3f"|format(test.avg_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.min_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.max_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.p95_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.std_dev) }}s</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Percentile Analysis -->
            {% if percentile_data %}
            <div class="section">
                <h2 class="section-title">Percentile Analysis</h2>
                {% for test_name, percentiles in percentile_data.items() %}
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #374151;">{{ test_name }}</h3>
                    {% for p, value in percentiles.items() %}
                    <div class="percentile-bar">
                        <div class="percentile-label">P{{ p }}</div>
                        <div class="percentile-value">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {{ (value / percentiles[99] * 100) if 99 in percentiles else 50 }}%"></div>
                            </div>
                        </div>
                        <div class="percentile-number">{{ "%.3f"|format(value) }}s</div>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Configuration Section -->
            <div class="section">
                <h2 class="section-title">Test Configuration</h2>
                <div class="config-section">
                    <div class="config-item">
                        <span class="config-label">Concurrent Users:</span>
                        <span class="config-value">{{ config.concurrent_users }}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Iterations:</span>
                        <span class="config-value">{{ config.iterations }}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Browser:</span>
                        <span class="config-value">{{ config.browser_name }} (headless: {{ config.headless }})</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Screenshots:</span>
                        <span class="config-value">{{ "Enabled" if config.screenshots else "Disabled" }}</span>
                    </div>
                    <div class="config-item">
                        <span class="config-label">Traces:</span>
                        <span class="config-value">{{ "Enabled" if config.traces else "Disabled" }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Performance Test Report | Generated by APT - Allied Performance Testing</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # Render template
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        
        html = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            test_stats=test_stats,
            percentile_data=percentile_data,
            config=self.config
        )
        
        return html
    
    def generate_json_report(self, filename: str = "performance_report.json") -> Path:
        """
        Generate JSON report with all data.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / filename
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config.to_dict(),
            "summary": self.collector.get_summary_statistics(),
            "test_statistics": self.collector.get_all_test_statistics(),
            "percentile_data": self.collector.get_percentile_data(),
            "all_results": [m.to_dict() for m in self.collector.all_metrics]
        }
        
        with open(report_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"JSON report generated: {report_path}")
        return report_path
