"""
AI-powered test case generator using OpenAI GPT.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from ..models.schemas import Endpoint, TestCase, Parameter, ParameterType

load_dotenv()


class TestCaseGenerator:
    """AI-powered test case generator using OpenAI GPT."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_test_cases(self, endpoint: Endpoint, num_cases: int = 5) -> List[TestCase]:
        """Generate test cases for a given endpoint using AI."""
        test_cases = []
        
        # Generate different types of test cases
        test_types = [
            ("valid", 2),      # 2 valid test cases
            ("invalid", 2),    # 2 invalid test cases  
            ("boundary", 1)    # 1 boundary test case
        ]
        
        for test_type, count in test_types:
            for i in range(count):
                test_case = self._generate_single_test_case(endpoint, test_type, i + 1)
                test_cases.append(test_case)
                
        return test_cases
    
    def _generate_single_test_case(self, endpoint: Endpoint, test_type: str, case_number: int) -> TestCase:
        """Generate a single test case for an endpoint."""
        
        # Build the prompt for GPT
        prompt = self._build_prompt(endpoint, test_type)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert API tester. Generate realistic test inputs based on the provided endpoint specification."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from OpenAI API")
            test_data = self._parse_ai_response(content, endpoint)
            
            # Create test case
            test_case = TestCase(
                endpoint=endpoint,
                name=f"{test_type.capitalize()} Test Case {case_number}",
                description=f"AI-generated {test_type} test case for {endpoint.method.value.upper()} {endpoint.path}",
                input_data=test_data,
                expected_status=self._get_expected_status(test_type),
                test_type=test_type,
                tags=[test_type, "ai-generated"]
            )
            
            return test_case
            
        except Exception as e:
            # Fallback to basic test case if AI generation fails
            return self._create_fallback_test_case(endpoint, test_type, case_number, str(e))
    
    def _build_prompt(self, endpoint: Endpoint, test_type: str) -> str:
        """Build the prompt for GPT based on endpoint and test type."""
        
        prompt = f"""
Generate a JSON test input for the following API endpoint:

**Endpoint Details:**
- Method: {endpoint.method.value.upper()}
- Path: {endpoint.path}
- Summary: {endpoint.summary or 'No summary provided'}
- Description: {endpoint.description or 'No description provided'}

**Parameters:**
"""
        
        # Add parameter details
        for param in endpoint.parameters:
            prompt += f"- {param.name} ({param.type.value}, {param.location.value}"
            if param.required:
                prompt += ", required"
            prompt += f"): {param.description or 'No description'}\n"
        
        # Add request body info if available
        if endpoint.request_body:
            prompt += f"\n**Request Body:** {json.dumps(endpoint.request_body, indent=2)}\n"
        
        # Add test type specific instructions
        if test_type == "valid":
            prompt += """
**Requirements for VALID test case:**
- Use realistic, valid data that should work with the API
- Include all required parameters
- Use appropriate data types for each parameter
- Follow any format requirements (email, date, etc.)
"""
        elif test_type == "invalid":
            prompt += """
**Requirements for INVALID test case:**
- Use invalid data that should cause the API to return an error
- Examples: missing required fields, wrong data types, invalid formats
- The API should return a 4xx status code
"""
        elif test_type == "boundary":
            prompt += """
**Requirements for BOUNDARY test case:**
- Use edge case values (min/max values, empty strings, null values)
- Test limits of the API's validation
- Examples: maximum string length, minimum integer values, empty arrays
"""
        
        prompt += """
**Response Format:**
Return ONLY a valid JSON object with the test data. The JSON should contain:
- query_params: for query parameters
- path_params: for path parameters  
- headers: for header parameters
- body: for request body (if applicable)

Example format:
{
  "query_params": {"param1": "value1"},
  "path_params": {"id": 123},
  "headers": {"Authorization": "Bearer token"},
  "body": {"field1": "value1"}
}
"""
        
        return prompt
    
    def _parse_ai_response(self, content: str, endpoint: Endpoint) -> Dict[str, Any]:
        """Parse the AI response and extract test data."""
        try:
            # Try to extract JSON from the response
            # Sometimes GPT wraps JSON in markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()
            
            # Parse JSON
            test_data = json.loads(json_str)
            
            # Ensure all required keys exist
            required_keys = ["query_params", "path_params", "headers", "body"]
            for key in required_keys:
                if key not in test_data:
                    test_data[key] = {}
            
            return test_data
            
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, return empty test data
            return {
                "query_params": {},
                "path_params": {},
                "headers": {},
                "body": {}
            }
    
    def _get_expected_status(self, test_type: str) -> int:
        """Get expected HTTP status code based on test type."""
        if test_type == "valid":
            return 200
        elif test_type == "invalid":
            return 400
        elif test_type == "boundary":
            return 200  # Could be 200 or 400 depending on the boundary
        else:
            return 200
    
    def _create_fallback_test_case(self, endpoint: Endpoint, test_type: str, case_number: int, error: str) -> TestCase:
        """Create a fallback test case when AI generation fails."""
        
        # Generate basic test data based on parameters
        test_data = {
            "query_params": {},
            "path_params": {},
            "headers": {},
            "body": {}
        }
        
        # Add some basic test data based on parameter types
        for param in endpoint.parameters:
            if param.location.value == "query":
                test_data["query_params"][param.name] = self._generate_basic_value(param, test_type)
            elif param.location.value == "path":
                test_data["path_params"][param.name] = self._generate_basic_value(param, test_type)
            elif param.location.value == "header":
                test_data["headers"][param.name] = self._generate_basic_value(param, test_type)
        
        return TestCase(
            endpoint=endpoint,
            name=f"{test_type.capitalize()} Test Case {case_number} (Fallback)",
            description=f"Fallback {test_type} test case for {endpoint.method.value.upper()} {endpoint.path}. AI generation failed: {error}",
            input_data=test_data,
            expected_status=self._get_expected_status(test_type),
            test_type=test_type,
            tags=[test_type, "fallback"]
        )
    
    def _generate_basic_value(self, param: Parameter, test_type: str) -> Any:
        """Generate a basic test value for a parameter."""
        
        if test_type == "valid":
            if param.type == ParameterType.STRING:
                return "test_value"
            elif param.type == ParameterType.INTEGER:
                return 123
            elif param.type == ParameterType.NUMBER:
                return 123.45
            elif param.type == ParameterType.BOOLEAN:
                return True
            elif param.type == ParameterType.ARRAY:
                return ["item1", "item2"]
            elif param.type == ParameterType.OBJECT:
                return {"key": "value"}
        elif test_type == "invalid":
            if param.type == ParameterType.STRING:
                return 123  # Wrong type
            elif param.type == ParameterType.INTEGER:
                return "not_a_number"  # Wrong type
            elif param.type == ParameterType.NUMBER:
                return "not_a_number"  # Wrong type
            elif param.type == ParameterType.BOOLEAN:
                return "not_a_boolean"  # Wrong type
            else:
                return None  # Missing value
        elif test_type == "boundary":
            if param.type == ParameterType.STRING:
                return ""  # Empty string
            elif param.type == ParameterType.INTEGER:
                return 0  # Zero value
            elif param.type == ParameterType.NUMBER:
                return 0.0  # Zero value
            elif param.type == ParameterType.BOOLEAN:
                return False  # False value
            else:
                return None  # Null value
        
        return None 