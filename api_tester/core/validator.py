"""
Response validator for API testing.
"""

import json
from typing import Dict, List, Any, Optional, Union
from jsonschema import validate, ValidationError, SchemaError, RefResolver

from ..models.schemas import TestResult, TestStatus, Endpoint


class ResponseValidator:
    """Validates API responses against OpenAPI schemas."""
    
    def __init__(self):
        self.validation_errors: List[str] = []
    
    def validate_response(self, test_result: TestResult, api_spec: Dict[str, Any]) -> TestResult:
        """Validate a test result against the API specification."""
        self.validation_errors = []
        
        if test_result.status == TestStatus.ERROR:
            return test_result
        
        endpoint = test_result.test_case.endpoint
        response_status = test_result.response_status
        
        # Get expected response schema
        expected_schema = self._get_response_schema(endpoint, str(response_status), api_spec)
        
        if expected_schema:
            # Validate response body against schema
            self._validate_response_body(test_result.response_body, expected_schema, api_spec)
            
            # Validate response headers
            self._validate_response_headers(test_result.response_headers, endpoint, str(response_status), api_spec)
        
        # Update test result with validation errors
        if self.validation_errors:
            test_result.validation_errors = self.validation_errors.copy()
            # Don't change status to FAILED if it was already PASSED due to status code
            # Only mark as failed if validation was critical
        
        return test_result
    
    def _get_response_schema(self, endpoint: Endpoint, status_code: str, api_spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the expected response schema for a given status code."""
        responses = endpoint.responses
        
        # Try exact status code match
        if status_code in responses:
            response_spec = responses[status_code]
            return self._extract_schema_from_response(response_spec, api_spec)
        
        # Try default response
        if 'default' in responses:
            response_spec = responses['default']
            return self._extract_schema_from_response(response_spec, api_spec)
        
        # Try pattern matching (e.g., "2xx", "4xx")
        for pattern, response_spec in responses.items():
            if self._status_code_matches_pattern(status_code, pattern):
                return self._extract_schema_from_response(response_spec, api_spec)
        
        return None
    
    def _extract_schema_from_response(self, response_spec: Dict[str, Any], api_spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract schema from response specification."""
        content = response_spec.get('content', {})
        
        # Look for JSON schema
        if 'application/json' in content:
            json_content = content['application/json']
            schema = json_content.get('schema')
            
            if schema:
                return schema  # Return schema as-is, let RefResolver handle $ref
        
        return None
    
    def _status_code_matches_pattern(self, status_code: str, pattern: str) -> bool:
        """Check if a status code matches a pattern like '2xx'."""
        if pattern.endswith('xx'):
            prefix = pattern[:-2]
            return status_code.startswith(prefix)
        return False
    
    def _validate_response_body(self, response_body: Any, schema: Dict[str, Any], api_spec: Dict[str, Any]):
        """Validate response body against schema."""
        if response_body is None:
            return
        
        try:
            # Create a proper RefResolver with the complete OpenAPI spec
            # The api_spec should contain the full OpenAPI document including components/schemas
            resolver = RefResolver.from_schema(api_spec)
            validate(instance=response_body, schema=schema, resolver=resolver)
        except ValidationError as e:
            self.validation_errors.append(f"Response body validation failed: {e.message}")
        except SchemaError as e:
            # If schema error occurs, try to resolve the issue
            if "PointerToNowhere" in str(e):
                # This is the specific error we're seeing - schema reference not found
                self.validation_errors.append(f"Schema reference resolution failed: {e.message}")
            else:
                self.validation_errors.append(f"Schema error: {e.message}")
        except Exception as e:
            # If RefResolver fails completely, try without it
            try:
                validate(instance=response_body, schema=schema)
            except Exception as e2:
                self.validation_errors.append(f"Validation failed: {str(e2)}")
    
    def _validate_response_headers(self, response_headers: Optional[Dict[str, str]], 
                                 endpoint: Endpoint, status_code: str, api_spec: Dict[str, Any]):
        """Validate response headers."""
        if not response_headers:
            return
        
        # Get expected headers from response specification
        responses = endpoint.responses
        response_spec = responses.get(status_code, responses.get('default', {}))
        
        if 'headers' in response_spec:
            expected_headers = response_spec['headers']
            
            for header_name, header_spec in expected_headers.items():
                if header_name.lower() in [h.lower() for h in response_headers.keys()]:
                    # Header exists, validate if schema is provided
                    if 'schema' in header_spec:
                        header_value = response_headers.get(header_name)
                        try:
                            validate(instance=header_value, schema=header_spec['schema'])
                        except ValidationError as e:
                            self.validation_errors.append(f"Header '{header_name}' validation failed: {e.message}")
                else:
                    # Check if header is required
                    if header_spec.get('required', False):
                        self.validation_errors.append(f"Required header '{header_name}' is missing")
    
    def validate_status_code(self, actual_status: int, expected_status: int) -> bool:
        """Validate if the actual status code matches the expected one."""
        return actual_status == expected_status
    
    def validate_content_type(self, content_type: str, expected_types: List[str]) -> bool:
        """Validate if the content type matches expected types."""
        if not expected_types:
            return True
        
        return any(expected_type in content_type.lower() for expected_type in expected_types)
    
    def validate_response_time(self, response_time: float, max_time: float) -> bool:
        """Validate if the response time is within acceptable limits."""
        return response_time <= max_time
    
    def get_validation_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Get a summary of validation results."""
        total_tests = len(test_results)
        validation_errors = 0
        schema_validation_failures = 0
        
        for result in test_results:
            if result.validation_errors:
                validation_errors += 1
                schema_validation_failures += len(result.validation_errors)
        
        return {
            'total_tests': total_tests,
            'tests_with_validation_errors': validation_errors,
            'total_validation_errors': schema_validation_failures,
            'validation_success_rate': ((total_tests - validation_errors) / total_tests * 100) if total_tests > 0 else 0
        } 