"""
AI-Powered API Auto-Tester

A smart automation tool that uses AI to generate and execute comprehensive test cases
for APIs based on OpenAPI (Swagger) specifications.
"""

__version__ = "1.0.0"
__author__ = "AI-Powered API Auto-Tester Team"

from .core.parser import OpenAPIParser
from .core.generator import TestCaseGenerator
from .core.executor import TestExecutor
from .core.validator import ResponseValidator
from .core.reporter import TestReporter

__all__ = [
    "OpenAPIParser",
    "TestCaseGenerator", 
    "TestExecutor",
    "ResponseValidator",
    "TestReporter"
] 