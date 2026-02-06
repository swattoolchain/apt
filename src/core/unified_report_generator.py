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
    
    def generate_unified_html_report(self, filename: str = "unified_performance_report.html", template: str = "detailed") -> Path:
        """
        Generate unified HTML report with all test results.
        
        Args:
            filename: Name of the HTML file
            template: Report template to use ('detailed' or 'compact')
            
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
        
        # Generate HTML based on template
        if template == "compact":
            html_content = self._render_compact_tabulator_template(normalized_results, summary, grouped_results)
        else:
            html_content = self._render_compact_template(normalized_results, summary, grouped_results)
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Unified HTML report generated: {report_path} (template: {template})")
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
                load_profile = result.get('load_profile', {})
                request_details = result.get('request_details', [])
                
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
                    'load_profile': load_profile,
                    'request_details': request_details,
                    'details': jmeter_summary
                })
            else:
                normalized.append({
                    'test_name': result['test_name'],
                    'tool': 'JMeter',
                    'type': 'API',
                    'status': result['status'],
                    'metrics': {},
                    'load_profile': {},
                    'request_details': [],
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
    <title>QPT - Performance Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Modern Professional Styling */
        body {
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
            background: #fafafa;
            color: #1a202c;
            -webkit-font-smoothing: antialiased;
        }

        header {
            background: #0f172a; /* Dark Navy Blue */
            color: white;
            padding: 16px 32px;
            border-bottom: 4px solid #1e293b;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        header h1 {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: white;
            margin: 0;
        }
        
        .subtitle {
            font-size: 13px;
            color: #718096;
            font-weight: 500;
            opacity: 1;
        }

        .metric-compact {
            background: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .metric-compact.success {
            background: #e8f5e9; /* Very light green */
            border-color: #c3e6cb;
            color: #155724;
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
            font-size: 26px;
            font-weight: bold;
            color: #1a202c;
        }
        
        .metric-unit-compact {
            font-size: 13px;
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
            font-size: 14px;
            font-weight: 600;
            color: #2d3748;
        }
        
        .tool-badge {
            display: inline-block;
            padding: 2px 8px;
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
            padding: 3px 8px;
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
            font-size: 15px;
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
            font-size: 12px;
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
    /* Dashboard Cards */
        .summary-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .dashboard-card {
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .card-label {
            font-size: 11px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .card-value {
            font-size: 26px;
            font-weight: 700;
            color: #2d3748;
        }

        /* Progress Bar */
        .progress-container {
            width: 100%;
            background-color: #edf2f7;
            border-radius: 4px;
            height: 8px;
            margin-top: 12px;
            overflow: hidden;
        }

        .progress-bar {
            height: 100%;
            background-color: #48bb78;
            border-radius: 4px;
            transition: width 0.5s ease-in-out;
        }
        
        /* Modern Accordion / Tree View */
        details {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
            background: white;
            margin-bottom: 12px;
        }

        details > summary {
            padding: 16px 20px;
            cursor: pointer;
            list-style: none;
            display: flex;
            align-items: center;
            background: #fff;
            font-weight: 600;
            color: #2d3748;
            transition: background 0.2s;
            position: relative;
        }
        
        details > summary:hover {
            background: #f8f9fa;
        }
        
        /* Custom Chevron using SVG or logic would be standard, 
           but CSS borders are robust for single-file text templates */
        details > summary::before {
            content: '▶';
            display: inline-block;
            font-size: 12px;
            margin-right: 12px;
            transition: transform 0.2s;
            color: #718096;
        }

        details[open] > summary::before {
            transform: rotate(90deg);
        }

        details > summary::-webkit-details-marker {
            display: none;
        }

        .workflow-content {
            padding: 20px;
            border-top: 1px solid #e2e8f0;
            background: #fff;
        }
        
        /* Nested Tree Style (Indent with Line) */
        details.sub-details {
            margin-top: 16px;
            margin-left: 12px;
            border-left: 2px solid #cbd5e0;
            border-radius: 4px;
            background: #fcfcfc;
        }
        
        details.sub-details > summary {
            background: #f7fafc;
            padding: 10px 16px;
            font-size: 13px;
        }
        
        details.sub-details .panel {
            padding: 12px;
        }

    </style>
</head>
<body>
    <div class="container">
        <header>
            <div style="display: flex; align-items: center;">
                <img src="https://qa.hub.quvia.ai/assets/images/neuron_logo.svg" alt="Neuron Logo" style="height: 32px; margin-right: 16px;">
                <h1>QPT - Performance Report</h1>
            </div>
            <div class="subtitle">{{ timestamp }}</div>
        </header>
        
        <div class="content">
            <!-- Dashboard Summary -->
            <div class="summary-dashboard">
                <div class="dashboard-card">
                    <div>
                        <div class="card-label">Total Tests</div>
                        <div class="card-value">{{ summary.total_tests }}</div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <div>
                        <div class="card-label">Success Rate</div>
                        <div class="card-value">{{ "%.0f"|format(summary.success_rate * 100) }}%</div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {{ summary.success_rate * 100 }}%"></div>
                        </div>
                    </div>
                </div>
                
                {% if summary.ui_tests > 0 %}
                <div class="dashboard-card">
                    <div>
                        <div class="card-label">UI Tests</div>
                        <div class="card-value">{{ summary.ui_tests }}</div>
                    </div>
                </div>
                {% endif %}
                
                {% if summary.api_tests > 0 %}
                <div class="dashboard-card">
                    <div>
                        <div class="card-label">API Tests</div>
                        <div class="card-value">{{ summary.api_tests }}</div>
                    </div>
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
                            <strong style="font-size: 14px; color: #2d3748;">Detailed k6 Metrics</strong>
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
                        
                        <!-- Load Profile (Threads & Loops) -->
                        {% if result.load_profile and result.load_profile.total_threads %}
                        <div style="margin-top: 12px; padding: 10px; background: #edf2f7; border-radius: 6px; border-left: 3px solid #f59e0b;">
                            <div style="font-size: 12px; font-weight: 600; color: #2d3748; margin-bottom: 8px;">⚙️ Load Profile</div>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: #718096; text-transform: uppercase;">Threads (Users)</div>
                                    <div style="font-size: 18px; font-weight: 700; color: #f59e0b;">{{ result.load_profile.total_threads }}</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: #718096; text-transform: uppercase;">Loop Count</div>
                                    <div style="font-size: 18px; font-weight: 700; color: #f59e0b;">{{ result.load_profile.total_loops }}</div>
                                </div>
                                <div style="text-align: center;">
                                    <div style="font-size: 10px; color: #718096; text-transform: uppercase;">Expected Reqs</div>
                                    <div style="font-size: 18px; font-weight: 700; color: #f59e0b;">{{ result.load_profile.expected_requests }}</div>
                                </div>
                            </div>
                        </div>
                        {% endif %}
                        
                        <!-- Expand Button -->
                        <button class="expand-btn" onclick="toggleDetails('jmeter-{{ result.test_name }}-{{ loop.index }}')">📊 View Detailed Metrics</button>
                        
                        <!-- Detailed Metrics Section -->
                        <div id="jmeter-{{ result.test_name }}-{{ loop.index }}" class="details-section">
                            <strong style="font-size: 14px; color: #2d3748;">Detailed JMeter Metrics</strong>
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
                            
                            <!-- Per-Request Details -->
                            {% if result.request_details and result.request_details|length > 0 %}
                            <div style="margin-top: 16px;">
                                <strong style="font-size: 14px; color: #2d3748;">📋 Request-by-Request Breakdown</strong>
                                <table class="details-table" style="margin-top: 8px;">
                                    <thead>
                                        <tr>
                                            <th>Request Name</th>
                                            <th>Total Reqs</th>
                                            <th>Success</th>
                                            <th>Errors</th>
                                            <th>Avg (ms)</th>
                                            <th>P95 (ms)</th>
                                            <th>Success %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for req in result.request_details %}
                                        <tr>
                                            <td><strong>{{ req.name }}</strong></td>
                                            <td>{{ req.total_requests }}</td>
                                            <td style="color: #22543d;">{{ req.success_count }}</td>
                                            <td style="color: #742a2a;">{{ req.error_count }}</td>
                                            <td>{{ "%.0f"|format(req.avg_response_time) }}</td>
                                            <td>{{ "%.0f"|format(req.p95) }}</td>
                                            <td>{{ "%.1f"|format(req.success_rate * 100) }}%</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                            {% endif %}
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
                
                <!-- Group By Controls -->
                <div class="controls" style="margin-bottom: 20px; display: flex; align-items: center; justify-content: flex-end; padding: 10px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                    <label style="font-size: 13px; font-weight: 500; color: #4a5568; margin-right: 12px;">Group Workflows By:</label>
                    <select id="groupBySelect" onchange="groupWorkflows()" style="padding: 6px 12px; border: 1px solid #cbd5e0; border-radius: 4px; font-size: 13px; color: #2d3748; background: white;">
                        <option value="none">None (List)</option>
                        <option value="tags">Tags</option>
                        <option value="agent">Agent</option>
                    </select>
                </div>

                <div id="workflows-container">
                {% for workflow in workflows %}
                {% set agent_set = [] %}
                {% for s in workflow.step_breakdown.values() %}{% if s.agent and s.agent not in agent_set %}{% set _ = agent_set.append(s.agent) %}{% endif %}{% endfor %}
                {% set primary_agent = agent_set[0] if agent_set else 'Local' %}
                
                <details class="workflow-details" 
                         data-tags="{{ workflow.tags|join(',') }}" 
                         data-agent="{{ primary_agent }}">
                    <summary>
                        <span>{{ workflow.name }}</span>
                        <div>
                            <span style="font-size: 13px; color: #718096; margin-right: 12px; font-weight: normal;">Avg: {{ "%.2f"|format(workflow.workflow_summary.avg_duration) }}s</span>
                            <span class="status-badge success">(x {{ workflow.total_workflows }})</span>
                        </div>
                    </summary>
                    
                    <div class="workflow-content">
                        <!-- Workflow Summary -->
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                            <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                                <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Avg Duration</div>
                                <div style="font-size: 17px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.avg_duration) }}s</div>
                            </div>
                            <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                                <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Min Duration</div>
                                <div style="font-size: 17px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.min_duration) }}s</div>
                            </div>
                            <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                                <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Max Duration</div>
                                <div style="font-size: 17px; font-weight: 600; color: #2d3748;">{{ "%.2f"|format(workflow.workflow_summary.max_duration) }}s</div>
                            </div>
                            <div style="background: #f7fafc; padding: 12px; border-radius: 6px;">
                                <div style="font-size: 11px; color: #718096; margin-bottom: 4px;">Total Steps</div>
                                <div style="font-size: 17px; font-weight: 600; color: #2d3748;">{{ workflow.step_breakdown|length }}</div>
                            </div>
                        </div>
                        
                        <!-- Step Breakdown Table -->
                        <h4 style="margin: 0 0 12px 0; color: #2d3748; font-size: 14px;">📋 Step-by-Step Breakdown</h4>
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 16px;">
                            <thead>
                                <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">
                                    <th style="padding: 10px; text-align: left; font-weight: 600; color: #4a5568;">Step</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Threads</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Loops</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Total Req</th>
                                    <th style="padding: 10px; text-align: right; font-weight: 600; color: #4a5568;">Avg Time</th>
                                    <th style="padding: 10px; text-align: right; font-weight: 600; color: #4a5568;">Success</th>
                                    <th style="padding: 10px; text-align: center; font-weight: 600; color: #4a5568;">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for step_name, step_data in workflow.step_breakdown.items() %}
                                <tr style="border-bottom: 1px solid #e2e8f0; {% if step_data.iteration_config.total_iterations > 1 %}background: #fffbeb;{% endif %}">
                                    <td style="padding: 8px; font-weight: 500; color: #2d3748;">
                                        {{ step_name }}<br/>
                                        <span class="tool-badge" style="background: #e2e8f0; color: #4a5568; font-weight: normal; font-size: 10px; padding: 1px 4px;">{{ step_data.agent }}</span>
                                    </td>
                                    <td style="padding: 8px; text-align: center; font-family: monospace; color: #4a5568;">
                                        {{ step_data.iteration_config.threads|default(1) }}
                                    </td>
                                    <td style="padding: 8px; text-align: center; font-family: monospace; color: #4a5568;">
                                        {{ step_data.iteration_config.display }}
                                    </td>
                                    <td style="padding: 8px; text-align: center; font-family: monospace; font-weight: 600; color: #2d3748;">
                                        {{ step_data.iteration_config.total_requests|default(step_data.iteration_config.total_iterations) }}
                                    </td>
                                    <td style="padding: 8px; text-align: right; color: #2d3748;">
                                        {{ "%.3f"|format(step_data.timing.avg_duration) }}s
                                    </td>
                                    <td style="padding: 8px; text-align: right;">
                                        <span style="color: {% if step_data.success.success_rate >= 0.95 %}#10b981{% else %}#ef4444{% endif %}; font-weight: 600;">
                                            {{ step_data.success.success_percentage }}
                                        </span>
                                    </td>
                                    <td style="padding: 8px; text-align: center;">
                                        {% if step_data.iteration_config.total_iterations > 1 %}
                                        <button class="expand-btn" onclick="toggleDetails(this)" style="font-size: 10px; padding: 2px 6px;">📋 Stats</button>
                                        {% else %}
                                        <span style="color: #cbd5e0; font-size: 10px;">—</span>
                                        {% endif %}
                                    </td>
                                </tr>
                                <!-- Detailed Metrics for High-Iteration Steps -->
                                {% if step_data.iteration_config.total_iterations > 1 %}
                                <tr>
                                    <td colspan="7" style="padding: 0;">
                                            <div id="workflow-{{ step_name }}-{{ loop.index }}" class="details-section">
                                                <div style="padding: 12px; background: #fffbeb;">
                                                    <strong style="font-size: 12px; color: #2d3748;">Detailed Metrics: {{ step_name }}</strong>
                                                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 10px;">
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">Total Iterations</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ step_data.iteration_config.total_iterations }}</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #d1fae5;">
                                                            <div style="font-size: 10px; color: #718096;">Min Time</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #059669;">{{ "%.3f"|format(step_data.timing.min_duration) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fecaca;">
                                                            <div style="font-size: 10px; color: #718096;">Max Time</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #dc2626;">{{ "%.3f"|format(step_data.timing.max_duration) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">Avg Time</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.avg_duration) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">Median</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.median_duration) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">P95</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.p95) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">P99</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.p99) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">Std Dev</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #2d3748;">{{ "%.3f"|format(step_data.timing.std_dev) }}s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #dbeafe;">
                                                            <div style="font-size: 10px; color: #718096;">Throughput</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: #1e40af;">{{ "%.2f"|format(step_data.throughput.requests_per_second) }} req/s</div>
                                                        </div>
                                                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #fee2e2;">
                                                            <div style="font-size: 10px; color: #718096;">Success Rate</div>
                                                            <div style="font-size: 14px; font-weight: 600; color: {% if step_data.success.success_rate >= 0.95 %}#059669{% else %}#dc2626{% endif %};">{{ step_data.success.success_percentage }}</div>
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
                                                    
                                                    <!-- Individual Request Breakdown -->
                                                    {% set iteration_results = [] %}
                                                    {% for wf_exec in workflow.workflow_executions %}
                                                        {% for step in wf_exec.steps %}
                                                            {% if step.name == step_name %}
                                                                {% for result in step.iteration_results %}
                                                                    {% set _ = iteration_results.append(result) %}
                                                                {% endfor %}
                                                            {% endif %}
                                                        {% endfor %}
                                                    {% endfor %}
                                                    
                                                    {% if iteration_results|length > 0 %}
                                                    <details style="margin-top: 12px;">
                                                        <summary style="cursor: pointer; font-size: 11px; font-weight: 600; color: #2d3748; padding: 8px; background: white; border-radius: 4px; border: 1px solid #e2e8f0;">
                                                            📋 View Individual Request Results ({{ iteration_results|length }} requests)
                                                        </summary>
                                                        <div style="margin-top: 8px; max-height: 300px; overflow-y: auto; background: white; border-radius: 4px; border: 1px solid #e2e8f0;">
                                                            <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                                                <thead style="position: sticky; top: 0; background: #f7fafc; z-index: 1;">
                                                                    <tr style="border-bottom: 2px solid #e2e8f0;">
                                                                        <th style="padding: 6px 8px; text-align: left; font-weight: 600; color: #4a5568;">#</th>
                                                                        <th style="padding: 6px 8px; text-align: right; font-weight: 600; color: #4a5568;">Duration</th>
                                                                        <th style="padding: 6px 8px; text-align: center; font-weight: 600; color: #4a5568;">Status</th>
                                                                        <th style="padding: 6px 8px; text-align: left; font-weight: 600; color: #4a5568;">Details</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {% for result in iteration_results %}
                                                                    <tr style="border-bottom: 1px solid #f0f0f0; {% if not result.success %}background: #fef2f2;{% endif %}">
                                                                        <td style="padding: 4px 8px; color: #718096;">{{ loop.index }}</td>
                                                                        <td style="padding: 4px 8px; text-align: right; font-family: monospace; color: #2d3748;">
                                                                            {{ "%.3f"|format(result.duration) }}s
                                                                        </td>
                                                                        <td style="padding: 4px 8px; text-align: center;">
                                                                            {% if result.success %}
                                                                            <span style="color: #059669; font-weight: 600;">✓</span>
                                                                            {% else %}
                                                                            <span style="color: #dc2626; font-weight: 600;">✗</span>
                                                                            {% endif %}
                                                                        </td>
                                                                        <td style="padding: 4px 8px; color: #718096; font-size: 10px;">
                                                                            {% if result.data %}
                                                                                {% if result.data.status_code %}
                                                                                    HTTP {{ result.data.status_code }}
                                                                                {% elif result.data.status %}
                                                                                    {{ result.data.status }}
                                                                                {% else %}
                                                                                    —
                                                                                {% endif %}
                                                                            {% else %}
                                                                                —
                                                                            {% endif %}
                                                                        </td>
                                                                    </tr>
                                                                    {% endfor %}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </details>
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
                        {% if workflow.workflow_executions and workflow.total_workflows > 1 %}
                        <details class="sub-details">
                            <summary>🔄 View Individual Workflow Executions (x{{ workflow.total_workflows }})</summary>
                            <div style="padding: 10px;">
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
                                                    <th style="padding: 8px; text-align: left; font-weight: 600; color: #4a5568;">Agent</th>
                                                    <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Iterations</th>
                                                    <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Duration</th>
                                                    <th style="padding: 8px; text-align: right; font-weight: 600; color: #4a5568;">Success Rate</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for step in wf_exec.steps %}
                                                <tr style="border-bottom: 1px solid #f7fafc;">
                                                    <td style="padding: 8px; color: #2d3748;">{{ step.name }}</td>
                                                    <td style="padding: 8px; color: #4a5568;">
                                                        <span class="tool-badge" style="background: #e2e8f0; color: #4a5568; font-weight: normal;">{{ step.agent }}</span>
                                                    </td>
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
                            </div>
                        </details>
                        {% endif %}
                    </div>
                </details>
                {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
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
        
        function toggleDetails(btn) {
            const tr = btn.closest('tr');
            const nextTr = tr.nextElementSibling;
            
            if (nextTr) {
                const detailsSection = nextTr.querySelector('.details-section');
                if (detailsSection) {
                    detailsSection.classList.toggle('show');
                    
                    // Toggle Button Text
                    if (detailsSection.classList.contains('show')) {
                        btn.innerHTML = '📉 Hide Details';
                        btn.style.background = '#4a5568';
                    } else {
                        btn.innerHTML = '📊 View Details';
                        btn.style.background = '#667eea';
                    }
                }
            }
        }

        function toggleAccordion(id) {
            const panel = document.getElementById(id);
            if (panel.style.display === "block") {
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
            }
        }
        
        function groupWorkflows() {
            const container = document.getElementById('workflows-container');
            const mode = document.getElementById('groupBySelect').value;
            
            // 1. Flatten: Find all workflow details, whether directly in container or in subgroups
            const allDetails = Array.from(document.querySelectorAll('.workflow-details'));
            
            // Clear current view
            container.innerHTML = '';
            
            if (mode === 'none') {
                allDetails.forEach(d => container.appendChild(d));
                return;
            }
            
            // 2. Grouping
            const groups = {};
            
            allDetails.forEach(d => {
                let keys = [];
                let rawValue = d.dataset[mode];
                
                if (mode === 'tags') {
                    if (!rawValue || rawValue.trim() === '') {
                        keys.push('No Tags');
                    } else {
                        // Split tags by comma, trim, and normalize case
                        keys = rawValue.toLowerCase().split(',').map(t => t.trim()).filter(t => t !== '');
                        if (keys.length === 0) keys.push('No Tags');
                    }
                } else {
                    // Standard single-value grouping (Agent, etc.)
                    let key = rawValue;
                    if (!key || key.trim() === '') key = 'Unspecified';
                    keys.push(key);
                }
                
                // Add workflow to each identified group
                keys.forEach(k => {
                    // Format key
                    let groupKey = k.charAt(0).toUpperCase() + k.slice(1);
                    
                    if (!groups[groupKey]) groups[groupKey] = [];
                    
                    // IMPORTANT: If a workflow belongs to multiple groups, we must clone it
                    // for subsequent groups so it can appear in multiple places.
                    // However, 'd' is a live DOM element.
                    // We'll store the element reference. In the render loop, we'll clone if needed.
                    groups[groupKey].push(d);
                });
            });
            
            // 3. Render Groups
            Object.keys(groups).sort().forEach(groupName => {
                const groupDetails = document.createElement('details');
                groupDetails.open = true; // Default to open
                groupDetails.style.marginBottom = '20px';
                groupDetails.style.border = '1px solid #e2e8f0';
                groupDetails.style.borderRadius = '8px';
                groupDetails.style.background = '#f8fafc';
                
                const summary = document.createElement('summary');
                summary.innerHTML = `<span style="font-size:14px; font-weight:600; color:#2d3748;">${groupName}</span> <span style="font-size:12px;color:#718096;font-weight:normal; margin-left:8px;">(${groups[groupName].length} workflows)</span>`;
                summary.style.padding = '12px 16px';
                summary.style.cursor = 'pointer';
                summary.style.borderBottom = '1px solid #e2e8f0';
                summary.style.listStyle = 'none';
                
                groupDetails.appendChild(summary);
                
                const contentDiv = document.createElement('div');
                contentDiv.style.padding = '16px';
                
                groups[groupName].forEach(d => {
                    // Clone the node to allow it to exist in multiple groups
                    contentDiv.appendChild(d.cloneNode(true)); 
                });
                
                groupDetails.appendChild(contentDiv);
                
                container.appendChild(groupDetails);
            });
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
    
    def _render_compact_tabulator_template(self, normalized_results: List[Dict], summary: Dict, grouped: Dict) -> str:
        """Render compact Tabulator.js template from external file."""
        
        # Load the compact template file
        template_path = Path(__file__).parent / "compact_report_template.html"
        
        if not template_path.exists():
            logger.warning(f"Compact template not found at {template_path}, falling back to detailed template")
            return self._render_compact_template(normalized_results, summary, grouped)
        
        with open(template_path, 'r') as f:
            template_str = f.read()
        
        # Prepare data for template
        workflows_json = json.dumps(self.results.get('workflows', []))
        
        # Calculate metadata
        total_workflows = len(self.results.get('workflows', []))
        total_duration = sum(wf.get('workflow_summary', {}).get('total_duration', 0) 
                           for wf in self.results.get('workflows', []))
        
        # Calculate success rate
        total_steps = 0
        successful_steps = 0
        for wf in self.results.get('workflows', []):
            for step_name, step_data in wf.get('step_breakdown', {}).items():
                total_steps += 1
                if step_data.get('success', {}).get('success_rate', 0) >= 0.95:
                    successful_steps += 1
        
        success_rate = successful_steps / total_steps if total_steps > 0 else 0
        
        # Calculate total requests
        total_requests = sum(
            step_data.get('iteration_config', {}).get('total_requests', 0)
            for wf in self.results.get('workflows', [])
            for step_data in wf.get('step_breakdown', {}).values()
        )
        
        metadata = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_duration': total_duration,
            'success_rate': success_rate,
            'total_requests': total_requests
        }
        
        test_info = {
            'test_suite_name': 'QPT Performance Test',
            'description': 'Unified Performance Testing Report'
        }
        
        # Render template
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_str)
        
        html = template.render(
            workflows=self.results.get('workflows', []),
            workflows_json=workflows_json,
            k6=self.results.get('k6', []),
            jmeter=self.results.get('jmeter', []),
            metadata=metadata,
            test_info=test_info
        )
        
        return html
