"""
Test report generator for API testing results.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from jinja2 import Template
from ..models.schemas import TestReport, TestResult, TestStatus, APISpec


class TestReporter:
    """Generates comprehensive test reports."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, test_report: TestReport, format: str = "html") -> str:
        """Generate a test report in the specified format."""
        if format.lower() == "html":
            return self._generate_html_report(test_report)
        elif format.lower() == "json":
            return self._generate_json_report(test_report)
        elif format.lower() == "markdown":
            return self._generate_markdown_report(test_report)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def _generate_html_report(self, test_report: TestReport) -> str:
        """Generate an HTML test report."""
        template = self._get_html_template()
        
        # Prepare data for template
        template_data = self._prepare_template_data(test_report)
        
        # Render template
        html_content = template.render(**template_data)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(filepath)
    
    def _generate_json_report(self, test_report: TestReport) -> str:
        """Generate a JSON test report."""
        # Convert test report to dict
        report_dict = test_report.model_dump()
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        return str(filepath)
    
    def _generate_markdown_report(self, test_report: TestReport) -> str:
        """Generate a Markdown test report."""
        content = []
        
        # Header
        content.append(f"# API Test Report")
        content.append(f"")
        content.append(f"**Generated:** {test_report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**API:** {test_report.api_spec.title} v{test_report.api_spec.version}")
        content.append(f"**Execution Time:** {test_report.execution_time:.2f} seconds")
        content.append(f"")
        
        # Summary
        content.append(f"## Summary")
        content.append(f"")
        content.append(f"- **Total Tests:** {test_report.total_tests}")
        content.append(f"- **Passed:** {test_report.passed_tests}")
        content.append(f"- **Failed:** {test_report.failed_tests}")
        content.append(f"- **Errors:** {test_report.error_tests}")
        content.append(f"- **Success Rate:** {test_report.success_rate:.1f}%")
        content.append(f"")
        
        # Test Results
        content.append(f"## Test Results")
        content.append(f"")
        
        for result in test_report.test_results:
            status_emoji = "✅" if result.status == TestStatus.PASSED else "❌" if result.status == TestStatus.FAILED else "⚠️"
            content.append(f"### {status_emoji} {result.test_case.name}")
            content.append(f"")
            content.append(f"- **Endpoint:** {result.test_case.endpoint.method.value.upper()} {result.test_case.endpoint.path}")
            content.append(f"- **Status:** {result.status.value}")
            content.append(f"- **Response Status:** {result.response_status or 'N/A'}")
            content.append(f"- **Execution Time:** {result.execution_time:.3f}s")
            content.append(f"- **Test Type:** {result.test_case.test_type}")
            content.append(f"")
            
            if result.error_message:
                content.append(f"**Error:** {result.error_message}")
                content.append(f"")
            
            if result.validation_errors:
                content.append(f"**Validation Errors:**")
                for error in result.validation_errors:
                    content.append(f"- {error}")
                content.append(f"")
            
            if result.response_body:
                content.append(f"**Response Body:**")
                content.append(f"```json")
                content.append(json.dumps(result.response_body, indent=2))
                content.append(f"```")
                content.append(f"")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return str(filepath)
    
    def _prepare_template_data(self, test_report: TestReport) -> Dict[str, Any]:
        """Prepare data for HTML template."""
        return {
            'report': test_report,
            'api_spec': test_report.api_spec,
            'test_results': test_report.test_results,
            'summary': {
                'total_tests': test_report.total_tests,
                'passed_tests': test_report.passed_tests,
                'failed_tests': test_report.failed_tests,
                'error_tests': test_report.error_tests,
                'success_rate': test_report.success_rate,
                'execution_time': test_report.execution_time
            },
            'timestamp': test_report.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status_emoji': {
                TestStatus.PASSED: '✅',
                TestStatus.FAILED: '❌',
                TestStatus.ERROR: '⚠️',
                TestStatus.SKIPPED: '⏭️'
            }
        }
    
    def _get_html_template(self) -> Template:
        """Get the HTML template for reports."""
        template_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Test Report - {{ api_spec.title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .summary-card .number {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .error { color: #ffc107; }
        .total { color: #007bff; }
        .results {
            padding: 30px;
        }
        .test-result {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .test-header {
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .test-header.passed { background-color: #d4edda; }
        .test-header.failed { background-color: #f8d7da; }
        .test-header.error { background-color: #fff3cd; }
        .test-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        .test-status {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .test-details {
            padding: 20px;
        }
        .detail-row {
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 15px;
            margin-bottom: 10px;
            align-items: center;
        }
        .detail-label {
            font-weight: bold;
            color: #666;
        }
        .detail-value {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 5px 10px;
            border-radius: 4px;
            word-break: break-all;
        }
        .validation-errors {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
        }
        .validation-errors h4 {
            margin: 0 0 10px 0;
            color: #721c24;
        }
        .validation-errors ul {
            margin: 0;
            padding-left: 20px;
        }
        .response-body {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin-top: 15px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>API Test Report</h1>
            <p>{{ api_spec.title }} v{{ api_spec.version }}</p>
            <p>Generated on {{ timestamp }}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number total">{{ summary.total_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Passed</h3>
                <div class="number passed">{{ summary.passed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Failed</h3>
                <div class="number failed">{{ summary.failed_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Errors</h3>
                <div class="number error">{{ summary.error_tests }}</div>
            </div>
            <div class="summary-card">
                <h3>Success Rate</h3>
                <div class="number passed">{{ "%.1f"|format(summary.success_rate) }}%</div>
            </div>
            <div class="summary-card">
                <h3>Execution Time</h3>
                <div class="number total">{{ "%.2f"|format(summary.execution_time) }}s</div>
            </div>
        </div>
        
        <div class="results">
            <h2>Test Results</h2>
            {% for result in test_results %}
            <div class="test-result">
                <div class="test-header {{ result.status.value }}">
                    <div class="test-name">{{ result.test_case.name }}</div>
                    <div class="test-status">
                        <span>{{ status_emoji[result.status] }}</span>
                        <span>{{ result.status.value.upper() }}</span>
                    </div>
                </div>
                <div class="test-details">
                    <div class="detail-row">
                        <div class="detail-label">Endpoint:</div>
                        <div class="detail-value">{{ result.test_case.endpoint.method.value.upper() }} {{ result.test_case.endpoint.path }}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Response Status:</div>
                        <div class="detail-value">{{ result.response_status or 'N/A' }}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Execution Time:</div>
                        <div class="detail-value">{{ "%.3f"|format(result.execution_time) }}s</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Test Type:</div>
                        <div class="detail-value">{{ result.test_case.test_type }}</div>
                    </div>
                    {% if result.error_message %}
                    <div class="detail-row">
                        <div class="detail-label">Error:</div>
                        <div class="detail-value">{{ result.error_message }}</div>
                    </div>
                    {% endif %}
                    
                    {% if result.validation_errors %}
                    <div class="validation-errors">
                        <h4>Validation Errors:</h4>
                        <ul>
                            {% for error in result.validation_errors %}
                            <li>{{ error }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    
                    {% if result.response_body %}
                    <div class="detail-row">
                        <div class="detail-label">Response Body:</div>
                        <div class="response-body">{{ result.response_body | tojson(indent=2) }}</div>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>Generated by AI-Powered API Auto-Tester</p>
        </div>
    </div>
</body>
</html>
"""
        return Template(template_content)
    
    def get_report_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Get a summary of test results."""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in test_results if r.status == TestStatus.ERROR])
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        } 