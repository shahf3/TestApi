"""
Pydantic models for API Auto-Tester data structures.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class HTTPMethod(str, Enum):
    """HTTP methods supported by the API."""
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"


class ParameterType(str, Enum):
    """Parameter types in OpenAPI specification."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ParameterLocation(str, Enum):
    """Parameter locations in HTTP requests."""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class Parameter(BaseModel):
    """Represents an API parameter."""
    name: str
    type: ParameterType
    location: ParameterLocation
    required: bool = False
    description: Optional[str] = None
    default: Optional[Any] = None
    param_schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None


class Endpoint(BaseModel):
    """Represents an API endpoint."""
    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Parameter] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = {}
    tags: List[str] = []
    operation_id: Optional[str] = None


class APISpec(BaseModel):
    """Represents a complete OpenAPI specification."""
    title: str
    version: str
    description: Optional[str] = None
    base_url: Optional[HttpUrl] = None
    endpoints: List[Endpoint] = []
    schemas: Dict[str, Any] = {}
    info: Dict[str, Any] = {}


class TestCase(BaseModel):
    """Represents a test case for an API endpoint."""
    endpoint: Endpoint
    name: str
    description: str
    input_data: Dict[str, Any] = {}
    expected_status: int = 200
    expected_schema: Optional[Dict[str, Any]] = None
    test_type: str = "valid"  # valid, invalid, boundary, edge_case
    tags: List[str] = []


class TestResult(BaseModel):
    """Represents the result of a test case execution."""
    test_case: TestCase
    status: TestStatus
    response_status: Optional[int] = None
    response_body: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)


class TestReport(BaseModel):
    """Represents a comprehensive test report."""
    api_spec: APISpec
    test_results: List[TestResult]
    summary: Dict[str, Any] = {}
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

    @property
    def total_tests(self) -> int:
        """Total number of tests executed."""
        return len(self.test_results)

    @property
    def passed_tests(self) -> int:
        """Number of tests that passed."""
        return len([r for r in self.test_results if r.status == TestStatus.PASSED])

    @property
    def failed_tests(self) -> int:
        """Number of tests that failed."""
        return len([r for r in self.test_results if r.status == TestStatus.FAILED])

    @property
    def error_tests(self) -> int:
        """Number of tests that encountered errors."""
        return len([r for r in self.test_results if r.status == TestStatus.ERROR])

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100 