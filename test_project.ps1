#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test script for AI-Powered API Auto-Tester

.DESCRIPTION
    This script tests all components of the API Auto-Tester project:
    1. Dependencies installation
    2. Individual component testing
    3. CLI functionality
    4. Report generation
#>

param(
    [string]$OpenAIApiKey = "",
    [switch]$SkipInstall = $false
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-Status {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $Color
}

function Test-Command {
    param(
        [string]$Command,
        [string]$Description
    )
    Write-Status "Testing: $Description" $Blue
    try {
        $result = Invoke-Expression $Command 2>&1
        $output = $result -join "`n"
        
        # Check for success patterns in output
        $successPatterns = @(
            "✅ Generated",
            "✅ Found",
            "✅ Created",
            "✅ Report generated",
            "Generated.*test cases",
            "Found.*endpoints",
            "Report generated"
        )
        
        $isSuccess = $false
        foreach ($pattern in $successPatterns) {
            if ($output -match $pattern) {
                $isSuccess = $true
                break
            }
        }
        
        # Also check exit code
        if ($LASTEXITCODE -eq 0 -or $isSuccess) {
            Write-Status "✅ PASSED: $Description" $Green
            return $true
        } else {
            Write-Status "❌ FAILED: $Description" $Red
            Write-Host $output -ForegroundColor $Red
            return $false
        }
    } catch {
        Write-Status "❌ FAILED: $Description" $Red
        Write-Host $_.Exception.Message -ForegroundColor $Red
        return $false
    }
}

function Test-PythonImport {
    param(
        [string]$Module,
        [string]$Description
    )
    $command = "python -c `"import $Module; print('Import successful')`""
    Test-Command $command $Description
}

# Main test execution
Write-Status "🚀 Starting AI-Powered API Auto-Tester Test Suite" $Blue
Write-Status "==================================================" $Blue

# Step 1: Check Python installation
Write-Status "Step 1: Checking Python installation..." $Yellow
if (-not (Test-Command "python --version" "Python installation")) {
    Write-Status "❌ Python not found. Please install Python first." $Red
    exit 1
}

# Step 2: Install dependencies (if not skipped)
if (-not $SkipInstall) {
    Write-Status "Step 2: Installing dependencies..." $Yellow
    $dependencies = @(
        "openai",
        "requests", 
        "pyyaml",
        "jsonschema",
        "streamlit",
        "jinja2",
        "python-dotenv",
        "click",
        "rich",
        "pydantic",
        "typing-extensions"
    )
    
    foreach ($dep in $dependencies) {
        Test-Command "python -m pip install $dep" "Installing $dep"
    }
}

# Step 3: Check environment file
Write-Status "Step 3: Checking environment configuration..." $Yellow
if (-not (Test-Path ".env")) {
    Write-Status "⚠️  .env file not found. Creating template..." $Yellow
    @"
# OpenAI Configuration
OPENAI_API_KEY=$OpenAIApiKey
OPENAI_MODEL=gpt-3.5-turbo

# API Testing Configuration
DEFAULT_TIMEOUT=30
MAX_RETRIES=3
DEFAULT_HEADERS={"Content-Type": "application/json"}

# Report Configuration
REPORT_FORMAT=html
REPORT_OUTPUT_DIR=reports
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Status "✅ Created .env file" $Green
} else {
    Write-Status "✅ .env file exists" $Green
}

# Step 4: Test individual imports
Write-Status "Step 4: Testing module imports..." $Yellow
$imports = @(
    @{Module="openai"; Description="OpenAI module"},
    @{Module="requests"; Description="Requests module"},
    @{Module="yaml"; Description="PyYAML module"},
    @{Module="jsonschema"; Description="JSONSchema module"},
    @{Module="jinja2"; Description="Jinja2 module"},
    @{Module="dotenv"; Description="Python-dotenv module"},
    @{Module="click"; Description="Click module"},
    @{Module="pydantic"; Description="Pydantic module"}
)

foreach ($import in $imports) {
    Test-PythonImport $import.Module $import.Description
}

# Step 5: Test API Tester components
Write-Status "Step 5: Testing API Tester components..." $Yellow

# Test OpenAPI Parser
$parserTest = @"
from api_tester import OpenAPIParser
parser = OpenAPIParser()
spec = parser.parse_file('examples/sample_openapi.yaml')
print(f'Found {len(spec.endpoints)} endpoints')
for endpoint in spec.endpoints:
    print(f'  - {endpoint.method.value.upper()} {endpoint.path}')
"@
$parserTest | Out-File -FilePath "temp_parser_test.py" -Encoding UTF8
Test-Command "python temp_parser_test.py" "OpenAPI Parser"

# Test Test Case Generator (if API key is provided)
if ($OpenAIApiKey -ne "") {
    $generatorTest = @"
from api_tester import OpenAPIParser, TestCaseGenerator
parser = OpenAPIParser()
spec = parser.parse_file('examples/sample_openapi.yaml')
generator = TestCaseGenerator()
test_cases = generator.generate_test_cases(spec.endpoints[0])
print(f'Generated {len(test_cases)} test cases for {spec.endpoints[0].method.value.upper()} {spec.endpoints[0].path}')
"@
    $generatorTest | Out-File -FilePath "temp_generator_test.py" -Encoding UTF8
    Test-Command "python temp_generator_test.py" "Test Case Generator"
} else {
    Write-Status "⚠️  Skipping AI test case generation (no API key provided)" $Yellow
}

# Step 6: Test CLI commands
Write-Status "Step 6: Testing CLI commands..." $Yellow

# Test generate command
Test-Command "python cli.py generate --spec examples/sample_openapi.yaml --output test_cases.json" "CLI Generate Command"

# Check if test cases were generated
if (Test-Path "test_cases.json") {
    $testCases = Get-Content "test_cases.json" | ConvertFrom-Json
    Write-Status "✅ Generated $($testCases.Count) test cases" $Green
} else {
    Write-Status "❌ Test cases file not found" $Red
}

# Test full test command (if API key is provided)
if ($OpenAIApiKey -ne "") {
    Test-Command "python cli.py test --spec examples/sample_openapi.yaml --output html" "CLI Full Test Command"
    
    # Check if reports were generated
    if (Test-Path "reports") {
        $reports = Get-ChildItem "reports" -Filter "*.html"
        Write-Status "✅ Generated $($reports.Count) HTML report(s)" $Green
    }
} else {
    Write-Status "⚠️  Skipping full test execution (no API key provided)" $Yellow
}

# Step 7: Test different report formats
Write-Status "Step 7: Testing report formats..." $Yellow
if ($OpenAIApiKey -ne "") {
    Test-Command "python cli.py test --spec examples/sample_openapi.yaml --output json" "JSON Report Generation"
    Test-Command "python cli.py test --spec examples/sample_openapi.yaml --output markdown" "Markdown Report Generation"
}

# Step 8: Cleanup
Write-Status "Step 8: Cleaning up temporary files..." $Yellow
if (Test-Path "temp_parser_test.py") { Remove-Item "temp_parser_test.py" }
if (Test-Path "temp_generator_test.py") { Remove-Item "temp_generator_test.py" }

# Step 9: Final summary
Write-Status "==================================================" $Blue
Write-Status "🎉 Test Suite Completed!" $Green
Write-Status "==================================================" $Blue

# Check generated files
Write-Status "Generated files:" $Yellow
if (Test-Path "test_cases.json") {
    Write-Status "  ✅ test_cases.json" $Green
}
if (Test-Path "reports") {
    $reportFiles = Get-ChildItem "reports" -Recurse
    foreach ($file in $reportFiles) {
        Write-Status "  ✅ $($file.Name)" $Green
    }
}

Write-Status "Test completed successfully!" $Green 