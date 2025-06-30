"""
HTTP request executor for API testing.
"""

import time
import json
from typing import Dict, List, Any, Optional
import requests
from urllib.parse import urljoin, urlencode

from ..models.schemas import TestCase, TestResult, TestStatus, Endpoint


class TestExecutor:
    """Executes test cases by sending HTTP requests to API endpoints."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Auto-Tester/1.0'
        })
    
    def execute_test_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case and return the result."""
        start_time = time.time()
        
        try:
            # Build the request
            url, headers, data = self._build_request(test_case)
            
            # Send the request
            response = self._send_request(test_case.endpoint.method.value, url, headers, data)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Determine test status
            status = self._determine_test_status(test_case, response)
            
            # Create test result
            test_result = TestResult(
                test_case=test_case,
                status=status,
                response_status=response.status_code,
                response_body=self._parse_response_body(response),
                response_headers=dict(response.headers),
                execution_time=execution_time,
                error_message=None
            )
            
            return test_result
            
        except Exception as e:
            # Handle any exceptions during execution
            execution_time = time.time() - start_time
            
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                response_status=None,
                response_body=None,
                response_headers=None,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    def execute_test_cases(self, test_cases: List[TestCase]) -> List[TestResult]:
        """Execute multiple test cases and return results."""
        results = []
        
        for test_case in test_cases:
            result = self.execute_test_case(test_case)
            results.append(result)
            
            # Add a small delay between requests to be respectful
            time.sleep(0.1)
        
        return results
    
    def _build_request(self, test_case: TestCase) -> tuple[str, Dict[str, str], Optional[Any]]:
        """Build the HTTP request from a test case."""
        endpoint = test_case.endpoint
        input_data = test_case.input_data
        
        # Build URL
        url = self._build_url(endpoint.path, input_data.get('path_params', {}))
        
        # Build headers
        headers = self._build_headers(input_data.get('headers', {}))
        
        # Build request data
        data = self._build_request_data(endpoint, input_data.get('body', {}))
        
        return url, headers, data
    
    def _build_url(self, path: str, path_params: Dict[str, Any]) -> str:
        """Build the complete URL with path parameters."""
        # Replace path parameters in the URL
        url_path = path
        for param_name, param_value in path_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in url_path:
                url_path = url_path.replace(placeholder, str(param_value))
        
        # Join with base URL
        if self.base_url:
            return urljoin(self.base_url, url_path)
        else:
            return url_path
    
    def _build_headers(self, custom_headers: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers."""
        headers = {}
        
        # Add custom headers
        for key, value in custom_headers.items():
            headers[key] = str(value)
        
        return headers
    
    def _build_request_data(self, endpoint: Endpoint, body_data: Dict[str, Any]) -> Optional[Any]:
        """Build request data based on endpoint method and body data."""
        method = endpoint.method.value.lower()
        
        # GET requests typically don't have a body
        if method == 'get':
            return None
        
        # For other methods, return the body data
        if body_data:
            return body_data
        
        return None
    
    def _send_request(self, method: str, url: str, headers: Dict[str, str], data: Optional[Any]) -> requests.Response:
        """Send the HTTP request with retry logic."""
        method = method.lower()
        
        for attempt in range(self.max_retries):
            try:
                if method == 'get':
                    response = self.session.get(url, headers=headers, timeout=self.timeout)
                elif method == 'post':
                    response = self.session.post(url, headers=headers, json=data, timeout=self.timeout)
                elif method == 'put':
                    response = self.session.put(url, headers=headers, json=data, timeout=self.timeout)
                elif method == 'delete':
                    response = self.session.delete(url, headers=headers, timeout=self.timeout)
                elif method == 'patch':
                    response = self.session.patch(url, headers=headers, json=data, timeout=self.timeout)
                elif method == 'head':
                    response = self.session.head(url, headers=headers, timeout=self.timeout)
                elif method == 'options':
                    response = self.session.options(url, headers=headers, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(1)  # Wait before retry
        
        raise Exception("Max retries exceeded")
    
    def _parse_response_body(self, response: requests.Response) -> Any:
        """Parse the response body based on content type."""
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        else:
            return response.text
    
    def _determine_test_status(self, test_case: TestCase, response: requests.Response) -> TestStatus:
        """Determine if the test passed, failed, or had an error."""
        expected_status = test_case.expected_status
        actual_status = response.status_code
        
        # Check if status code matches expected
        if actual_status == expected_status:
            return TestStatus.PASSED
        else:
            return TestStatus.FAILED
    
    def set_base_url(self, base_url: str):
        """Set the base URL for API requests."""
        self.base_url = base_url
    
    def set_auth_token(self, token: str, auth_type: str = "Bearer"):
        """Set authentication token for requests."""
        if auth_type.lower() == "bearer":
            self.session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            self.session.headers.update({'Authorization': token})
    
    def set_api_key(self, api_key: str, header_name: str = "api_key"):
        """Set API key for requests."""
        self.session.headers.update({header_name: api_key})
    
    def set_custom_headers(self, headers: Dict[str, str]):
        """Set custom headers for all requests."""
        self.session.headers.update(headers)
    
    def clear_session(self):
        """Clear the session and reset to default state."""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'API-Auto-Tester/1.0'
        })

    def print_headers(self):
        """Print the current headers for debugging."""
        print(self.session.headers)
