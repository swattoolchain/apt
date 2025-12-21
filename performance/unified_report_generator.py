"""
Unified Report Generator - Improved Compact Version with Tabs

Generates a single comprehensive report with:
- Compact summary tiles
- Tabbed sections for UI/API/k6/JMeter
- Only shows sections with data
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from jinja2 import Environment, BaseLoader
import logging

logger = logging.getLogger(__name__)


class UnifiedReportGenerator:
    """Generate unified reports combining all testing tools."""
    
    def __init__(self, unified_results: Dict, output_dir: Path):
        """
        Initialize unified report generator.
        
        Args:
            unified_results: Results from UnifiedTestRunner
            output_dir: Directory to save reports
        """
        self.results = unified_results
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_unified_html_report(self, filename: str = "unified_performance_report.html") -> Path:
        """
        Generate unified HTML report with all test results.
        
        Args:
            filename: Name of the HTML file
            
        Returns:
            Path to generated report
        """
        report_path = self.output_dir / filename
        
        # Normalize all results to standard format
        normalized_results = self._normalize_results()
        
        # Calculate summary statistics
        summary = self._calculate_summary(normalized_results)
        
        # Group results by tool
        grouped_results = self._group_by_tool(normalized_results)
        
        # Generate HTML
        html_content = self._render_compact_template(normalized_results, summary, grouped_results)
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Unified HTML report generated: {report_path}")
        return report_path
    
    def _normalize_results(self) -> List[Dict]:
        """Normalize all results to standard format."""
        normalized = []
        
        # Normalize Playwright results
        for result in self.results.get('playwright', []):
            normalized.append({
                'test_name': result['test_name'],
                'tool': 'Playwright',
                'type': 'UI',
                'status': result['status'],
                'metrics': {
                    'avg_response_time': result.get('duration', 0),
                    'min_response_time': result.get('duration', 0),
                    'max_response_time': result.get('duration', 0),
                    'p50': result.get('duration', 0),
                    'p95': result.get('duration', 0),
                    'p99': result.get('duration', 0),
                    'total_requests': 1,
                    'success_rate': 1.0 if result['status'] == 'success' else 0.0,
                    'throughput': 0
                },
                'details': result.get('metrics', {})
            })
        
        # Normalize k6 results
        for result in self.results.get('k6', []):
            if result['status'] == 'success' and 'metrics' in result:
                k6_metrics = result.get('metrics', {})
                http_duration = k6_metrics.get('http_req_duration', {})
                http_reqs = k6_metrics.get('http_reqs', {})
                http_failed = k6_metrics.get('http_req_failed', {})
                
                normalized.append({
                    'test_name': result['test_name'],
                    'tool': 'k6',
                    'type': 'API',
                    'status': result['status'],
                    'metrics': {
                        'avg_response_time': http_duration.get('avg', 0) / 1000,  # ms to s
                        'min_response_time': http_duration.get('min', 0) / 1000,
                        'max_response_time': http_duration.get('max', 0) / 1000,
                        'p50': http_duration.get('p(50)', 0) / 1000,
                        'p95': http_duration.get('p(95)', 0) / 1000,
                        'p99': http_duration.get('p(99)', 0) / 1000,
                        'total_requests': http_reqs.get('count', 0),
                        'success_rate': 1.0 - http_failed.get('rate', 0),
                        'throughput': http_reqs.get('rate', 0)
                    },
                    'details': k6_metrics
                })
            else:
                normalized.append({
                    'test_name': result['test_name'],
                    'tool': 'k6',
                    'type': 'API',
                    'status': result['status'],
                    'metrics': {},
                    'error': result.get('error', 'Unknown error')
                })
        
        # Normalize JMeter results
        for result in self.results.get('jmeter', []):
            if result['status'] == 'success' and 'summary' in result:
                jmeter_summary = result.get('summary', {})
                
                normalized.append({
                    'test_name': result['test_name'],
                    'tool': 'JMeter',
                    'type': 'API',
                    'status': result['status'],
                    'metrics': {
                        'avg_response_time': jmeter_summary.get('avg_response_time', 0) / 1000,
                        'min_response_time': jmeter_summary.get('min_response_time', 0) / 1000,
                        'max_response_time': jmeter_summary.get('max_response_time', 0) / 1000,
                        'p50': jmeter_summary.get('avg_response_time', 0) / 1000,
                        'p95': jmeter_summary.get('max_response_time', 0) * 0.95 / 1000,
                        'p99': jmeter_summary.get('max_response_time', 0) * 0.99 / 1000,
                        'total_requests': jmeter_summary.get('total_samples', 0),
                        'success_rate': jmeter_summary.get('success_rate', 0),
                        'throughput': jmeter_summary.get('total_samples', 0) / max(jmeter_summary.get('avg_response_time', 1), 1) * 1000
                    },
                    'details': jmeter_summary
                })
            else:
                normalized.append({
                    'test_name': result['test_name'],
                    'tool': 'JMeter',
                    'type': 'API',
                    'status': result['status'],
                    'metrics': {},
                    'error': result.get('error', 'Unknown error')
                })
        
        return normalized
    
    def _calculate_summary(self, normalized_results: List[Dict]) -> Dict:
        """Calculate overall summary statistics."""
        total_tests = len(normalized_results)
        successful_tests = len([r for r in normalized_results if r['status'] == 'success'])
        
        ui_tests = [r for r in normalized_results if r['type'] == 'UI']
        api_tests = [r for r in normalized_results if r['type'] == 'API']
        
        all_avg_times = [r['metrics'].get('avg_response_time', 0) 
                        for r in normalized_results if r['status'] == 'success' and r['metrics']]
        
        # Include workflows in test count
        workflows = self.results.get('workflows', [])
        total_workflow_executions = sum(wf.get('total_workflows', 0) for wf in workflows)
        
        # Adjust totals to include workflows
        adjusted_total = total_tests + total_workflow_executions
        adjusted_successful = successful_tests + total_workflow_executions
        
        return {
            'total_tests': adjusted_total if adjusted_total > 0 else total_tests,
            'successful_tests': adjusted_successful if adjusted_total > 0 else successful_tests,
            'failed_tests': (adjusted_total - adjusted_successful) if adjusted_total > 0 else (total_tests - successful_tests),
            'success_rate': adjusted_successful / adjusted_total if adjusted_total > 0 else (successful_tests / total_tests if total_tests > 0 else 0),
            'ui_tests': len(ui_tests),
            'api_tests': len(api_tests),
            'avg_response_time': sum(all_avg_times) / len(all_avg_times) if all_avg_times else 0,
            'tools_used': list(set(r['tool'] for r in normalized_results))
        }
    
    def _group_by_tool(self, normalized_results: List[Dict]) -> Dict:
        """Group results by tool."""
        grouped = {
            'playwright': [],
            'k6': [],
            'jmeter': []
        }
        
        for result in normalized_results:
            tool_key = result['tool'].lower()
            if tool_key in grouped:
                grouped[tool_key].append(result)
        
        return grouped
    
    def _render_compact_template(self, normalized_results: List[Dict], summary: Dict, grouped: Dict) -> str:
        """Render compact HTML template with tabs."""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APT - Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
            padding: 20px 40px;
        }
        
        header h1 {
            font-size: 24px;
            margin-bottom: 4px;
        }
        
        .subtitle {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .content {
            padding: 24px 40px;
        }
        
        /* Compact Summary */
        .summary-compact {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }
        
        .metric-compact {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 8px;
            padding: 12px 16px;
            text-align: center;
        }
        
        .metric-compact.success {
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
        }
        
        .metric-label-compact {
            font-size: 11px;
            color: #4a5568;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        
        .metric-value-compact {
            font-size: 28px;
            font-weight: bold;
            color: #1a202c;
        }
        
        .metric-unit-compact {
            font-size: 14px;
            color: #4a5568;
            margin-left: 2px;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            gap: 4px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 24px;
        }
        
        .tab {
            padding: 12px 24px;
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #718096;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        
        .tab:hover {
            color: #667eea;
            background: #f7fafc;
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
        
        /* Test Cards */
        .test-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
            align-items: start;
        }
        
        .test-card {
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 3px solid #667eea;
        }
        
        .test-card.api {
            border-left-color: #48bb78;
        }
        
        .test-card.failed {
            border-left-color: #f56565;
            background: #fff5f5;
        }
        
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .test-name {
            font-size: 15px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .tool-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
            background: #edf2f7;
            color: #4a5568;
        }
        
        .tool-badge.playwright {
            background: #bee3f8;
            color: #2c5282;
        }
        
        .tool-badge.k6 {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .tool-badge.jmeter {
            background: #feebc8;
            color: #7c2d12;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .status-badge.success {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-badge.failed, .status-badge.error {
            background: #fed7d7;
            color: #742a2a;
        }
        
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 12px;
        }
        
        .metric-item {
            text-align: center;
            padding: 8px;
            background: #f7fafc;
            border-radius: 6px;
        }
        
        .metric-item-label {
            font-size: 10px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        
        .metric-item-value {
            font-size: 16px;
            font-weight: 600;
            color: #2d3748;
            margin-top: 2px;
        }
        
        .error-box {
            margin-top: 12px;
            padding: 10px;
            background: #fed7d7;
            border-radius: 6px;
            color: #742a2a;
            font-size: 12px;
        }
        
        .expand-btn {
            margin-top: 12px;
            padding: 6px 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .expand-btn:hover {
            background: #5568d3;
        }
        
        .details-section {
            display: none;
            margin-top: 12px;
            padding: 12px;
            background: #f7fafc;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }
        
        .details-section.show {
            display: block;
        }
        
        .details-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 8px;
        }
        
        .details-table th {
            background: #edf2f7;
            padding: 6px 8px;
            text-align: left;
            font-weight: 600;
            color: #2d3748;
            border-bottom: 1px solid #cbd5e0;
        }
        
        .details-table td {
            padding: 6px 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .details-table tr:hover {
            background: #edf2f7;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #a0aec0;
        }
        
        footer {
            background: #f7fafc;
            padding: 20px;
            text-align: center;
            color: #718096;
            font-size: 13px;
            border-top: 1px solid #e2e8f0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 APT - Report</h1>
            <div class="subtitle">{{ timestamp }}</div>
        </header>
        
        <div class="content">
            <!-- Compact Summary -->
            <div class="summary-compact">
                <div class="metric-compact">
                    <div class="metric-label-compact">Tests</div>
                    <div class="metric-value-compact">{{ summary.total_tests }}</div>
                </div>
                
                <div class="metric-compact success">
                    <div class="metric-label-compact">Success</div>
                    <div class="metric-value-compact">{{ "%.0f"|format(summary.success_rate * 100) }}<span class="metric-unit-compact">%</span></div>
                </div>
                
                {% if summary.ui_tests > 0 %}
                <div class="metric-compact">
                    <div class="metric-label-compact">UI Tests</div>
                    <div class="metric-value-compact">{{ summary.ui_tests }}</div>
                </div>
                {% endif %}
                
                {% if summary.api_tests > 0 %}
                <div class="metric-compact">
                    <div class="metric-label-compact">API Tests</div>
                    <div class="metric-value-compact">{{ summary.api_tests }}</div>
                </div>
                {% endif %}
                

            </div>
            
            <!-- Tabs -->
            <div class="tabs">
                {% if grouped.playwright|length > 0 %}
                <button class="tab active" onclick="showTab('playwright')">Playwright ({{ grouped.playwright|length }})</button>
                {% endif %}
                {% if grouped.k6|length > 0 %}
                <button class="tab {% if grouped.playwright|length == 0 %}active{% endif %}" onclick="showTab('k6')">k6 ({{ grouped.k6|length }})</button>
                {% endif %}
                {% if grouped.jmeter|length > 0 %}
                <button class="tab {% if grouped.playwright|length == 0 and grouped.k6|length == 0 %}active{% endif %}" onclick="showTab('jmeter')">JMeter ({{ grouped.jmeter|length }})</button>
                {% endif %}
                {% if workflows|length > 0 %}
                <button class="tab {% if grouped.playwright|length == 0 and grouped.k6|length == 0 and grouped.jmeter|length == 0 %}active{% endif %}" onclick="showTab('workflows')">Workflows ({{ workflows|length }})</button>
                {% endif %}
            </div>
            
            <!-- Tab Content: Playwright -->
            {% if grouped.playwright|length > 0 %}
            <div id="playwright-tab" class="tab-content active">
                <div class="test-grid">
                    {% for result in grouped.playwright %}
                    <div class="test-card {% if result.status != 'success' %}failed{% endif %}">
                        <div class="test-header">
                            <div class="test-name">{{ result.test_name }}</div>
                            <span class="tool-badge playwright">Playwright</span>
                        </div>
                        <div>
                            <span class="status-badge {{ result.status }}">{{ result.status|upper }}</span>
                        </div>
                        {% if result.metrics %}
                        <div class="metrics-row">
                            <div class="metric-item">
                                <div class="metric-item-label">Duration</div>
                                <div class="metric-item-value">{{ "%.2f"|format(result.metrics.avg_response_time) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">P95</div>
                                <div class="metric-item-value">{{ "%.2f"|format(result.metrics.p95) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">Success</div>
                                <div class="metric-item-value">{{ "%.0f"|format(result.metrics.success_rate * 100) }}%</div>
                            </div>
                        </div>
                        {% endif %}
                        {% if result.error %}
                        <div class="error-box"><strong>Error:</strong> {{ result.error }}</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Tab Content: k6 -->
            {% if grouped.k6|length > 0 %}
            <div id="k6-tab" class="tab-content {% if grouped.playwright|length == 0 %}active{% endif %}">
                <div class="test-grid">
                    {% for result in grouped.k6 %}
                    <div class="test-card api {% if result.status != 'success' %}failed{% endif %}">
                        <div class="test-header">
                            <div class="test-name">{{ result.test_name }}</div>
                            <span class="tool-badge k6">k6</span>
                        </div>
                        <div>
                            <span class="status-badge {{ result.status }}">{{ result.status|upper }}</span>
                        </div>
                        {% if result.metrics %}
                        <div class="metrics-row">
                            <div class="metric-item">
                                <div class="metric-item-label">Avg</div>
                                <div class="metric-item-value">{{ "%.3f"|format(result.metrics.avg_response_time) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">P95</div>
                                <div class="metric-item-value">{{ "%.3f"|format(result.metrics.p95) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">RPS</div>
                                <div class="metric-item-value">{{ "%.1f"|format(result.metrics.throughput) }}</div>
                            </div>
                        </div>
                        <div class="metrics-row" style="grid-template-columns: repeat(2, 1fr); margin-top: 8px;">
                            <div class="metric-item">
                                <div class="metric-item-label">Requests</div>
                                <div class="metric-item-value">{{ result.metrics.total_requests }}</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">Success</div>
                                <div class="metric-item-value">{{ "%.1f"|format(result.metrics.success_rate * 100) }}%</div>
                            </div>
                        </div>
                        
                        <!-- Expand Button -->
                        <button class="expand-btn" onclick="toggleDetails('k6-{{ result.test_name }}-{{ loop.index }}')">📊 View Detailed Metrics</button>
                        
                        <!-- Detailed Metrics Section -->
                        <div id="k6-{{ result.test_name }}-{{ loop.index }}" class="details-section">
                            <strong style="font-size: 12px; color: #2d3748;">Detailed k6 Metrics</strong>
                            <table class="details-table">
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th>Value</th>
                                        <th>Unit</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>Response Time (Avg)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.avg_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (Min)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.min_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (Max)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.max_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (P50)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.p50) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (P95)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.p95) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (P99)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.p99) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Total Requests</strong></td>
                                        <td>{{ result.metrics.total_requests }}</td>
                                        <td>requests</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Throughput</strong></td>
                                        <td>{{ "%.2f"|format(result.metrics.throughput) }}</td>
                                        <td>req/s</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Success Rate</strong></td>
                                        <td>{{ "%.2f"|format(result.metrics.success_rate * 100) }}</td>
                                        <td>%</td>
                                    </tr>
                                    {% if result.details %}
                                    {% for key, value in result.details.items() %}
                                    {% if value is mapping and 'avg' in value %}
                                    <tr>
                                        <td><strong>{{ key }}</strong></td>
                                        <td colspan="2">
                                            avg: {{ "%.2f"|format(value.avg) }} | 
                                            min: {{ "%.2f"|format(value.min) }} | 
                                            max: {{ "%.2f"|format(value.max) }}
                                        </td>
                                    </tr>
                                    {% endif %}
                                    {% endfor %}
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                        {% endif %}
                        {% if result.error %}
                        <div class="error-box"><strong>Error:</strong> {{ result.error }}</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Tab Content: JMeter -->
            {% if grouped.jmeter|length > 0 %}
            <div id="jmeter-tab" class="tab-content {% if grouped.playwright|length == 0 and grouped.k6|length == 0 %}active{% endif %}">
                <div class="test-grid">
                    {% for result in grouped.jmeter %}
                    <div class="test-card api {% if result.status != 'success' %}failed{% endif %}">
                        <div class="test-header">
                            <div class="test-name">{{ result.test_name }}</div>
                            <span class="tool-badge jmeter">JMeter</span>
                        </div>
                        <div>
                            <span class="status-badge {{ result.status }}">{{ result.status|upper }}</span>
                        </div>
                        {% if result.metrics %}
                        <div class="metrics-row">
                            <div class="metric-item">
                                <div class="metric-item-label">Avg</div>
                                <div class="metric-item-value">{{ "%.3f"|format(result.metrics.avg_response_time) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">Min</div>
                                <div class="metric-item-value">{{ "%.3f"|format(result.metrics.min_response_time) }}s</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">Max</div>
                                <div class="metric-item-value">{{ "%.3f"|format(result.metrics.max_response_time) }}s</div>
                            </div>
                        </div>
                        <div class="metrics-row" style="grid-template-columns: repeat(2, 1fr); margin-top: 8px;">
                            <div class="metric-item">
                                <div class="metric-item-label">Samples</div>
                                <div class="metric-item-value">{{ result.metrics.total_requests }}</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-item-label">Success</div>
                                <div class="metric-item-value">{{ "%.1f"|format(result.metrics.success_rate * 100) }}%</div>
                            </div>
                        </div>
                        
                        <!-- Expand Button -->
                        <button class="expand-btn" onclick="toggleDetails('jmeter-{{ result.test_name }}-{{ loop.index }}')">📊 View Detailed Metrics</button>
                        
                        <!-- Detailed Metrics Section -->
                        <div id="jmeter-{{ result.test_name }}-{{ loop.index }}" class="details-section">
                            <strong style="font-size: 12px; color: #2d3748;">Detailed JMeter Metrics</strong>
                            <table class="details-table">
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th>Value</th>
                                        <th>Unit</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>Response Time (Avg)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.avg_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (Min)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.min_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Response Time (Max)</strong></td>
                                        <td>{{ "%.3f"|format(result.metrics.max_response_time) }}</td>
                                        <td>seconds</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Total Samples</strong></td>
                                        <td>{{ result.metrics.total_requests }}</td>
                                        <td>requests</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Throughput</strong></td>
                                        <td>{{ "%.2f"|format(result.metrics.throughput) }}</td>
                                        <td>req/s</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Success Rate</strong></td>
                                        <td>{{ "%.2f"|format(result.metrics.success_rate * 100) }}</td>
                                        <td>%</td>
                                    </tr>
                                    {% if result.details %}
                                    {% for key, value in result.details.items() %}
                                    <tr>
                                        <td><strong>{{ key }}</strong></td>
                                        <td colspan="2">{{ value }}</td>
                                    </tr>
                                    {% endfor %}
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                        {% endif %}
                        {% if result.error %}
                        <div class="error-box"><strong>Error:</strong> {{ result.error }}</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- Tab Content: Workflows -->
            {% if workflows|length > 0 %}
            <div id="workflows-tab" class="tab-content {% if grouped.playwright|length == 0 and grouped.k6|length == 0 and grouped.jmeter|length == 0 %}active{% endif %}">
                {% for workflow in workflows %}
                <div style="background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h3 style="margin: 0; color: #2d3748;">{{ workflow.name }}</h3>
                        <span class="status-badge success">{{ workflow.total_workflows }} workflows</span>
                    </div>
                    
                    <!-- Workflow Summary -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                        <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Avg Duration</div>
                            <div style="font-size: 18px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.avg_duration) }}s</div>
                        </div>
                        <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Min Duration</div>
                            <div style="font-size: 18px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.min_duration) }}s</div>
                        </div>
                        <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Max Duration</div>
                            <div style="font-size: 18px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.max_duration) }}s</div>
                        </div>
                        <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                            <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Total Steps</div>
                            <div style="font-size: 18px; font-weight: 600; color: #2d3748;">{{ workflow.step_breakdown|length }}</div>
                        </div>
                    </div>
                    
                    <!-- Step Breakdown Table -->
                    <h4 style="margin: 0 0 12px 0; color: #2d3748; font-size: 14px;">📋 Step-by-Step Breakdown</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 16px;">
                        <thead>
                            <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">
                                <th style="padding: 10px; text-align: left; font-weight: 600; color: #4a5568;">Step</th>
                                <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Iterations</th>
                                <th style="padding: 10px; text-align: right; font-weight: 600; color: #4a5568;">Avg Time</th>
                                <th style="padding: 10px; text-align: right; font-weight: 600; color: #4a5568;">Success</th>
                                <th style="padding: 10px; text-align: right; font-weight: 600; color: #4a5568;">Total Time</th>
                                <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for step_name, step_data in workflow.step_breakdown.items() %}
                            <tr style="border-bottom: 1px solid #e2e8f0; {% if step_data.iteration_config.iterations_per_workflow > 1 %}background: #fffbeb;{% endif %}">
                                <td style="padding: 10px; font-weight: 500; color: #2d3748;">
                                    {{ step_name }}
                                    {% if step_data.iteration_config.iterations_per_workflow > 1 %}
                                    <span style="background: #fbbf24; color: #78350f; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 6px;">HIGH ITERATION</span>
                                    {% endif %}
                                </td>
                                <td style="padding: 10px; text-align: center; font-family: monospace; color: #4a5568;">
                                    {{ step_data.iteration_config.display }}
                                </td>
                                <td style="padding: 10px; text-align: right; color: #2d3748;">
                                    {{ "%.3f"|format(step_data.timing.avg_duration) }}s
                                </td>
                                <td style="padding: 10px; text-align: right;">
                                    <span style="color: {% if step_data.success.success_rate >= 0.95 %}#10b981{% else %}#ef4444{% endif %}; font-weight: 600;">
                                        {{ step_data.success.success_percentage }}
                                    </span>
                                </td>
                                <td style="padding: 10px; text-align: right; color: #4a5568;">
                                    {{ "%.2f"|format(step_data.timing.total_time) }}s
                                </td>
                                <td style="padding: 10px; text-align: center;">
                                    {% if step_data.iteration_config.iterations_per_workflow > 1 %}
                                    <button class="expand-btn" onclick="toggleDetails('workflow-{{ step_name }}-{{ loop.index }}')" style="font-size: 11px; padding: 4px 8px;">📊 Details</button>
                                    {% else %}
                                    <span style="color: #cbd5e0; font-size: 11px;">—</span>
                                    {% endif %}
                                </td>
                            </tr>
                            <!-- Detailed Metrics for High-Iteration Steps -->
                            {% if step_data.iteration_config.iterations_per_workflow > 1 %}
                            <tr>
                                <td colspan="6" style="padding: 0;">
                                    <div id="workflow-{{ step_name }}-{{ loop.index }}" class="details-section">
                                        <div style="padding: 16px; background: #fffbeb;">
                                            <strong style="font-size: 12px; color: #2d3748;">Detailed Metrics: {{ step_name }}</strong>
                                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px;">
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">Total Iterations</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ step_data.iteration_config.total_iterations }}</div>
                                                </div>
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">P95</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.p95) }}s</div>
                                                </div>
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">P99</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.p99) }}s</div>
                                                </div>
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">Throughput</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(step_data.throughput.iterations_per_second) }} req/s</div>
                                                </div>
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">Std Dev</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.std_dev) }}s</div>
                                                </div>
                                                <div style="background: white; padding: 10px; border-radius: 4px;">
                                                    <div style="font-size: 10px; color: #718096;">Median</div>
                                                    <div style="font-size: 16px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.median_duration) }}s</div>
                                                </div>
                                            </div>
                                            
                                            <!-- Performance Degradation Warning -->
                                            {% if step_data.degradation and step_data.degradation.degradation_detected %}
                                            <div style="margin-top: 12px; padding: 10px; background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 4px;">
                                                <div style="font-size: 11px; font-weight: 600; color: #991b1b; margin-bottom: 4px;">⚠️ Performance Degradation Detected</div>
                                                <div style="font-size: 11px; color: #7f1d1d;">
                                                    Performance degrades by {{ "%.1f"|format(step_data.degradation.degradation_percentage) }}% from iteration 1 to {{ step_data.iteration_config.iterations_per_workflow }}.
                                                    First avg: {{ "%.3f"|format(step_data.degradation.first_iteration_avg) }}s, 
                                                    Last avg: {{ "%.3f"|format(step_data.degradation.last_iteration_avg) }}s
                                                </div>
                                            </div>
                                            {% endif %}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                            {% endif %}
                            {% endfor %}
                        </tbody>
                    </table>
                    
                    <!-- Per-Workflow Results (Accordion) -->
                    {% if workflow.workflow_executions %}
                    <h4 style="margin: 20px 0 12px 0; color: #2d3748; font-size: 14px;">🔄 Individual Workflow Executions</h4>
                    {% for wf_exec in workflow.workflow_executions %}
                    <div style="border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px; overflow: hidden;">
                        <button class="accordion" onclick="toggleAccordion('wf-{{ loop.index }}-exec-{{ loop.index }}')">
                                <span>Workflow #{{ loop.index }} - {{ "%.2f"|format(wf_exec.total_duration|default(wf_exec.duration)) }}s</span>
                                <span class="badge {{ 'badge-success' if wf_exec.success else 'badge-danger' }}">{{ 'PASS' if wf_exec.success else 'FAIL' }}</span>
                            </button>
                            <div id="wf-{{ loop.index }}-exec-{{ loop.index }}" class="panel">
                            <div style="padding: 16px; background: white;">
                                <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                                    <thead>
                                        <tr style="background: #f7fafc; border-bottom: 1px solid #e2e8f0;">
                                            <th style="padding: 8px; text-align: left; font-weight: 600; color: #4a5568;">Step</th>
                                            <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Iterations</th>
                                            <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Duration</th>
                                            <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Success Rate</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for step in wf_exec.steps %}
                                        <tr style="border-bottom: 1px solid #f7fafc;">
                                            <td style="padding: 8px; color: #2d3748;">{{ step.name }}</td>
                                            <td style="padding: 8px; text-align: right; color: #4a5568;">{{ step.iterations }}</td>
                                            <td style="padding: 8px; text-align: right; color: #2d3748;">{{ "%.3f"|format(step.total_duration) }}s</td>
                                            <td style="padding: 8px; text-align: right;">
                                                <span style="color: {% if step.success_rate >= 0.95 %}#10b981{% else %}#ef4444{% endif %}; font-weight: 600;">
                                                    {{ "%.1f"|format(step.success_rate * 100) }}%
                                                </span>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        
        <footer>
            <p>APT - Allied Performance Testing | Powered by Playwright + k6 + JMeter</p>
            <p style="margin-top: 4px; font-size: 11px;">{{ timestamp }}</p>
        </footer>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function toggleDetails(id) {
            const details = document.getElementById(id);
            details.classList.toggle('show');
        }
    </script>
</body>
</html>
        """
        
        # Render template
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        
        html = template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            results=normalized_results,
            summary=summary,
            grouped=grouped,
            workflows=self.results.get('workflows', [])
        )
        
        return html
