#!/usr/bin/env python3
"""
Command-line interface for AI-Powered API Auto-Tester.
"""

import click
import time
import yaml
import json
from pathlib import Path

from api_tester import OpenAPIParser, TestCaseGenerator, TestExecutor, ResponseValidator, TestReporter
from api_tester.models.schemas import TestReport


@click.group()
def cli():
    """AI-Powered API Auto-Tester CLI"""
    pass


@cli.command()
@click.option('--spec', '-s', required=True, help='Path to OpenAPI specification file (JSON/YAML)')
@click.option('--base-url', '-u', help='Base URL for API requests')
@click.option('--model', '-m', default='gpt-3.5-turbo', help='OpenAI model to use')
@click.option('--output', '-o', default='html', help='Report format (html, json, markdown)')
def test(spec, base_url, model, output):
    """Run API tests using OpenAPI specification."""
    
    try:
        # Load the complete OpenAPI spec for validation
        spec_path = Path(spec)
        with open(spec_path, 'r', encoding='utf-8') as f:
            if spec_path.suffix.lower() in ['.yaml', '.yml']:
                complete_api_spec = yaml.safe_load(f)
            elif spec_path.suffix.lower() == '.json':
                complete_api_spec = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {spec_path.suffix}")
        
        # Parse OpenAPI spec
        click.echo("🔍 Parsing OpenAPI specification...")
        parser = OpenAPIParser()
        api_spec = parser.parse_file(spec)
        click.echo(f"✅ Found {len(api_spec.endpoints)} endpoints")
        
        # Set base URL
        if base_url:
            api_spec.base_url = base_url
        elif api_spec.base_url:
            base_url = str(api_spec.base_url)
        else:
            base_url = click.prompt("Enter base URL for API requests")
        
        # Initialize components
        generator = TestCaseGenerator(model=model)
        executor = TestExecutor(base_url=base_url)
        executor.set_api_key("special-key", header_name="api_key")
        validator = ResponseValidator()
        reporter = TestReporter()
        
        all_test_cases = []
        all_test_results = []
        
        # Generate and execute tests for each endpoint
        for endpoint in api_spec.endpoints:
            click.echo(f"\n🧠 Generating test cases for {endpoint.method.value.upper()} {endpoint.path}...")
            
            # Generate test cases
            test_cases = generator.generate_test_cases(endpoint)
            all_test_cases.extend(test_cases)
            click.echo(f"✅ Generated {len(test_cases)} test cases")
            
            # Execute test cases
            click.echo("🚀 Executing test cases...")
            test_results = executor.execute_test_cases(test_cases)
            
            # Validate responses
            click.echo("🔍 Validating responses...")
            for result in test_results:
                # Pass the complete OpenAPI spec for proper schema resolution
                validated_result = validator.validate_response(result, complete_api_spec)
                all_test_results.append(validated_result)
            
            # Show progress
            passed = len([r for r in test_results if r.status.value == 'passed'])
            failed = len([r for r in test_results if r.status.value == 'failed'])
            errors = len([r for r in test_results if r.status.value == 'error'])
            click.echo(f"📊 Results: {passed} passed, {failed} failed, {errors} errors")
        
        # Generate report
        click.echo("\n📝 Generating test report...")
        start_time = time.time()
        test_report = TestReport(
            api_spec=api_spec,
            test_results=all_test_results,
            execution_time=time.time() - start_time
        )
        
        report_path = reporter.generate_report(test_report, output)
        click.echo(f"✅ Report generated: {report_path}")
        
        # Show summary
        click.echo(f"\n📊 Final Summary:")
        click.echo(f"   Total Tests: {test_report.total_tests}")
        click.echo(f"   Passed: {test_report.passed_tests}")
        click.echo(f"   Failed: {test_report.failed_tests}")
        click.echo(f"   Errors: {test_report.error_tests}")
        click.echo(f"   Success Rate: {test_report.success_rate:.1f}%")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--spec', '-s', required=True, help='Path to OpenAPI specification file')
@click.option('--output', '-o', default='test_cases.json', help='Output file for test cases')
def generate(spec, output):
    """Generate test cases without executing them."""
    
    try:
        # Parse OpenAPI spec
        click.echo("🔍 Parsing OpenAPI specification...")
        parser = OpenAPIParser()
        api_spec = parser.parse_file(spec)
        
        # Generate test cases
        generator = TestCaseGenerator()
        all_test_cases = []
        
        for endpoint in api_spec.endpoints:
            click.echo(f"🧠 Generating test cases for {endpoint.method.value.upper()} {endpoint.path}...")
            test_cases = generator.generate_test_cases(endpoint)
            all_test_cases.extend([tc.model_dump() for tc in test_cases])
        
        # Save to file
        import json
        with open(output, 'w') as f:
            json.dump(all_test_cases, f, indent=2, default=str)
        
        click.echo(f"✅ Generated {len(all_test_cases)} test cases: {output}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--url', '-u', required=True, help='Base URL of the API to discover')
@click.option('--output', '-o', default='auto_generated_api.yaml', help='Output file for generated spec')
def discover(url, output):
    """Auto-generate OpenAPI specification from API URL."""
    
    try:
        from api_tester.core.spec_generator import generate_spec_from_url
        
        click.echo(f"🔍 Discovering API endpoints at {url}...")
        spec_file = generate_spec_from_url(url, output)
        click.echo(f"✅ Generated OpenAPI spec: {spec_file}")
        click.echo(f"📝 You can now test the API with: python cli.py test --spec {spec_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli() 