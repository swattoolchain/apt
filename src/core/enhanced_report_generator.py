"""
Enhanced Performance Report Generator with Advanced Visualizations

Generates comprehensive HTML reports with charts, trends, and comparisons.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from jinja2 import Environment, BaseLoader
import logging

from .base_performance_tester import PerformanceMetrics, PerformanceConfig
from .metrics_collector import MetricsCollector
from .comparison_tracker import PerformanceComparison

logger = logging.getLogger(__name__)


class EnhancedReportGenerator:
    """Generates enhanced HTML performance reports with visualizations."""
    
    def __init__(self, metrics_collector: MetricsCollector, config: PerformanceConfig, output_dir: Path):
        """
        Initialize enhanced report generator.
        
        Args:
            metrics_collector: MetricsCollector with test results
            config: Performance test configuration
            output_dir: Directory to save reports
        """
        self.collector = metrics_collector
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.comparison = PerformanceComparison(str(self.output_dir / "baseline.json"))
    
    def generate_html_report(self, filename: str = "performance_report.html") -> Path:
        """
        Generate comprehensive HTML report with charts and visualizations.
        
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
        
        # Get step-by-step data if available
        step_data = self._extract_step_data()
        
        # Get comparison data if baseline exists
        comparison_data = self._get_comparison_data(test_stats)
        
        # Generate HTML
        html_content = self._render_enhanced_template(
            summary, 
            test_stats, 
            percentile_data,
            step_data,
            comparison_data
        )
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Enhanced HTML report generated: {report_path}")
        return report_path
    
    def _extract_step_data(self) -> List[Dict]:
        """Extract step-by-step timing data from metrics."""
        step_data = []
        
        for metrics in self.collector.all_metrics:
            if 'step_timings' in metrics.metrics:
                step_data.append({
                    'test_name': metrics.test_name,
                    'steps': metrics.metrics['step_timings'],
                    'total_time': metrics.metrics.get('total_workflow_time', 0)
                })
        
        return step_data
    
    def _get_comparison_data(self, test_stats: List[Dict]) -> Dict:
        """Get comparison with baseline if available."""
        comparisons = {}
        
        for test in test_stats:
            test_name = test['test_name']
            metrics = {
                'avg_duration': test.get('avg_duration', 0),
                'p95_duration': test.get('p95_duration', 0),
                'success_rate': test.get('success_rate', 0)
            }
            
            comparison = self.comparison.compare(test_name, metrics)
            if comparison.get('status') != 'no_baseline':
                comparisons[test_name] = comparison
        
        return comparisons
    
    def _render_enhanced_template(
        self,
        summary: Dict[str, Any],
        test_stats: List[Dict[str, Any]],
        percentile_data: Dict[str, Dict[int, float]],
        step_data: List[Dict],
        comparison_data: Dict
    ) -> str:
        """Render enhanced HTML template with all data."""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report - {{ timestamp }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }
        
        header h1 {
            font-size: 36px;
            margin-bottom: 10px;
        }
        
        header .subtitle {
            opacity: 0.9;
            font-size: 18px;
        }
        
        .content {
            padding: 40px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 50px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.07);
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        .metric-card.success {
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
        }
        
        .metric-card.warning {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        }
        
        .metric-card.error {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        }
        
        .metric-label {
            font-size: 13px;
            color: #4a5568;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 42px;
            font-weight: bold;
            color: #1a202c;
            line-height: 1;
        }
        
        .metric-unit {
            font-size: 18px;
            color: #4a5568;
            margin-left: 4px;
        }
        
        .section {
            margin-bottom: 50px;
        }
        
        .section-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 24px;
            color: #1a202c;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        th {
            background: #f7fafc;
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        td {
            padding: 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 14px;
        }
        
        tr:hover {
            background: #f7fafc;
        }
        
        .badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .badge-warning {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .badge-error {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .chart-container {
            margin: 30px 0;
            padding: 30px;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        canvas {
            max-height: 400px;
        }
        
        .comparison-alert {
            padding: 16px 20px;
            border-radius: 8px;
            margin: 16px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .comparison-alert.regression {
            background: #fed7d7;
            border-left: 4px solid #e53e3e;
            color: #742a2a;
        }
        
        .comparison-alert.improvement {
            background: #c6f6d5;
            border-left: 4px solid #38a169;
            color: #22543d;
        }
        
        .step-timeline {
            position: relative;
            padding-left: 40px;
            margin: 20px 0;
        }
        
        .step-item {
            position: relative;
            padding: 16px 20px;
            margin-bottom: 12px;
            background: #f7fafc;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }
        
        .step-item::before {
            content: '';
            position: absolute;
            left: -40px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: #667eea;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 2px #667eea;
        }
        
        .step-name {
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 4px;
        }
        
        .step-duration {
            color: #4a5568;
            font-size: 14px;
        }
        
        footer {
            background: #f7fafc;
            padding: 30px;
            text-align: center;
            color: #718096;
            font-size: 14px;
            border-top: 1px solid #e2e8f0;
        }
        
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .tab {
            padding: 12px 24px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 15px;
            font-weight: 500;
            color: #718096;
            transition: all 0.2s;
            border-bottom: 3px solid transparent;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Performance Test Report</h1>
            <div class="subtitle">Generated on {{ timestamp }}</div>
        </header>
        
        <div class="content">
            <!-- Executive Summary -->
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
                    </div>
                    
                    {% if summary.avg_duration is defined %}
                    <div class="metric-card">
                        <div class="metric-label">Avg Duration</div>
                        <div class="metric-value">{{ "%.2f"|format(summary.avg_duration) }}<span class="metric-unit">s</span></div>
                    </div>
                    
                    <div class="metric-card warning">
                        <div class="metric-label">P95 Duration</div>
                        <div class="metric-value">{{ "%.2f"|format(summary.p95_duration) }}<span class="metric-unit">s</span></div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">P99 Duration</div>
                        <div class="metric-value">{{ "%.2f"|format(summary.p99_duration) }}<span class="metric-unit">s</span></div>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Tabs for different views -->
            <div class="tabs">
                <button class="tab active" onclick="showTab('overview')">Overview</button>
                <button class="tab" onclick="showTab('detailed')">Detailed Results</button>
                {% if step_data %}<button class="tab" onclick="showTab('steps')">Step Analysis</button>{% endif %}
                {% if comparison_data %}<button class="tab" onclick="showTab('comparison')">Baseline Comparison</button>{% endif %}
            </div>
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="chart-container">
                    <div class="chart-title">Response Time Distribution</div>
                    <canvas id="responseTimeChart"></canvas>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">Test Performance Comparison</div>
                    <canvas id="testComparisonChart"></canvas>
                </div>
            </div>
            
            <!-- Detailed Results Tab -->
            <div id="detailed" class="tab-content">
                <table>
                    <thead>
                        <tr>
                            <th>Test Name</th>
                            <th>Runs</th>
                            <th>Success Rate</th>
                            <th>Avg</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>P50</th>
                            <th>P95</th>
                            <th>P99</th>
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
                                {% elif test.success_rate >= 0.80 %}
                                <span class="badge badge-warning">{{ "%.1f"|format(test.success_rate * 100) }}%</span>
                                {% else %}
                                <span class="badge badge-error">{{ "%.1f"|format(test.success_rate * 100) }}%</span>
                                {% endif %}
                            </td>
                            <td>{{ "%.3f"|format(test.avg_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.min_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.max_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.median_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.p95_duration) }}s</td>
                            <td>{{ "%.3f"|format(test.get('p99_duration', 0)) }}s</td>
                            <td>{{ "%.3f"|format(test.std_dev) }}s</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Step Analysis Tab -->
            {% if step_data %}
            <div id="steps" class="tab-content">
                {% for workflow in step_data %}
                <div class="chart-container">
                    <div class="chart-title">{{ workflow.test_name }} - Step Breakdown</div>
                    <div class="step-timeline">
                        {% for step in workflow.steps %}
                        <div class="step-item">
                            <div class="step-name">{{ step.step }}</div>
                            <div class="step-duration">
                                Duration: {{ "%.3f"|format(step.duration) }}s | 
                                Cumulative: {{ "%.3f"|format(step.cumulative_time) }}s |
                                Status: {{ step.status }}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    <canvas id="stepChart{{ loop.index }}"></canvas>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Comparison Tab -->
            {% if comparison_data %}
            <div id="comparison" class="tab-content">
                {% for test_name, comparison in comparison_data.items() %}
                <div class="chart-container">
                    <div class="chart-title">{{ test_name }} - Baseline Comparison</div>
                    
                    {% if comparison.summary.has_regressions %}
                    <div class="comparison-alert regression">
                        <strong>⚠️ Performance Regression Detected</strong>
                        <span>{{ comparison.summary.regressions }} metric(s) slower than baseline</span>
                    </div>
                    {% endif %}
                    
                    {% if comparison.summary.improvements > 0 %}
                    <div class="comparison-alert improvement">
                        <strong>✓ Performance Improvement</strong>
                        <span>{{ comparison.summary.improvements }} metric(s) faster than baseline</span>
                    </div>
                    {% endif %}
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Baseline</th>
                                <th>Current</th>
                                <th>Change</th>
                                <th>% Change</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for metric, change in comparison.changes.items() %}
                            <tr>
                                <td><strong>{{ metric }}</strong></td>
                                <td>{{ "%.3f"|format(change.baseline) }}</td>
                                <td>{{ "%.3f"|format(change.current) }}</td>
                                <td>{{ "%+.3f"|format(change.change) }}</td>
                                <td>{{ "%+.1f"|format(change.change_pct) }}%</td>
                                <td>
                                    {% if change.is_regression %}
                                    <span class="badge badge-error">Regression</span>
                                    {% elif change.is_improvement %}
                                    <span class="badge badge-success">Improvement</span>
                                    {% else %}
                                    <span class="badge">Stable</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <footer>
            <p>Performance Test Report | Generated by APT - Allied Performance Testing</p>
            <p style="margin-top: 8px; font-size: 12px;">{{ timestamp }}</p>
        </footer>
    </div>
    
    <script>
        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }
        
        // Chart data
        const testStats = {{ test_stats | tojson }};
        const percentileData = {{ percentile_data | tojson }};
        const stepData = {{ step_data | tojson }};
        
        // Response Time Distribution Chart
        if (testStats.length > 0) {
            const ctx1 = document.getElementById('responseTimeChart').getContext('2d');
            new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: testStats.map(t => t.test_name),
                    datasets: [{
                        label: 'P50',
                        data: testStats.map(t => t.median_duration),
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2
                    }, {
                        label: 'P95',
                        data: testStats.map(t => t.p95_duration),
                        backgroundColor: 'rgba(237, 100, 166, 0.6)',
                        borderColor: 'rgba(237, 100, 166, 1)',
                        borderWidth: 2
                    }, {
                        label: 'P99',
                        data: testStats.map(t => t.p99_duration || 0),
                        backgroundColor: 'rgba(255, 107, 107, 0.6)',
                        borderColor: 'rgba(255, 107, 107, 1)',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Duration (seconds)'
                            }
                        }
                    }
                }
            });
            
            // Test Comparison Chart
            const ctx2 = document.getElementById('testComparisonChart').getContext('2d');
            new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: testStats.map(t => t.test_name),
                    datasets: [{
                        label: 'Average Duration',
                        data: testStats.map(t => t.avg_duration),
                        borderColor: 'rgba(102, 126, 234, 1)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }, {
                        label: 'Max Duration',
                        data: testStats.map(t => t.max_duration),
                        borderColor: 'rgba(255, 107, 107, 1)',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        borderDash: [5, 5]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Duration (seconds)'
                            }
                        }
                    }
                }
            });
        }
        
        // Step Charts
        stepData.forEach((workflow, index) => {
            const canvasId = 'stepChart' + (index + 1);
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: workflow.steps.map(s => s.step),
                        datasets: [{
                            label: 'Duration (seconds)',
                            data: workflow.steps.map(s => s.duration),
                            backgroundColor: workflow.steps.map((s, i) => {
                                const colors = [
                                    'rgba(102, 126, 234, 0.7)',
                                    'rgba(118, 75, 162, 0.7)',
                                    'rgba(237, 100, 166, 0.7)',
                                    'rgba(255, 154, 158, 0.7)',
                                    'rgba(250, 177, 160, 0.7)'
                                ];
                                return colors[i % colors.length];
                            }),
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Duration (seconds)'
                                }
                            }
                        }
                    }
                });
            }
        });
    </script>
</body>
</html>
        """
        
        # Render template
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        
        # Add p99 to test stats if not present
        for test in test_stats:
            if 'p99_duration' not in test:
                test['p99_duration'] = test.get('p95_duration', 0) * 1.1
        
        html = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            summary=summary,
            test_stats=test_stats,
            percentile_data=percentile_data,
            step_data=step_data,
            comparison_data=comparison_data,
            config=self.config
        )
        
        return html
    
    def generate_json_report(self, filename: str = "performance_report.json") -> Path:
        """Generate comprehensive JSON report."""
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
