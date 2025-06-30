"""
OpenAPI specification parser module.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from pydantic import HttpUrl

from ..models.schemas import (
    APISpec, Endpoint, Parameter, HTTPMethod, 
    ParameterType, ParameterLocation
)


class OpenAPIParser:
    """Parser for OpenAPI (Swagger) specifications."""
    
    def __init__(self):
        self.spec_data: Dict[str, Any] = {}
        self.base_url: Optional[str] = None
        
    def parse_file(self, file_path: str) -> APISpec:
        """Parse an OpenAPI specification file."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")
            
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            if file_path_obj.suffix.lower() in ['.yaml', '.yml']:
                self.spec_data = yaml.safe_load(f)
            elif file_path_obj.suffix.lower() == '.json':
                self.spec_data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path_obj.suffix}")
                
        return self._parse_spec()
    
    def parse_string(self, spec_content: str, format: str = 'yaml') -> APISpec:
        """Parse an OpenAPI specification from string content."""
        if format.lower() == 'yaml':
            self.spec_data = yaml.safe_load(spec_content)
        elif format.lower() == 'json':
            self.spec_data = json.loads(spec_content)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        return self._parse_spec()
    
    def _parse_spec(self) -> APISpec:
        """Parse the OpenAPI specification into internal models."""
        # Extract basic info
        info = self.spec_data.get('info', {})
        title = info.get('title', 'Unknown API')
        version = info.get('version', '1.0.0')
        description = info.get('description')
        
        # Extract base URL
        servers = self.spec_data.get('servers', [])
        self.base_url = servers[0].get('url') if servers else None
        
        # Extract endpoints
        endpoints = self._extract_endpoints()
        
        # Extract schemas
        schemas = self.spec_data.get('components', {}).get('schemas', {})
        
        return APISpec(
            title=title,
            version=version,
            description=description,
            base_url=HttpUrl(self.base_url) if self.base_url else None,
            endpoints=endpoints,
            schemas=schemas,
            info=info
        )
    
    def _extract_endpoints(self) -> List[Endpoint]:
        """Extract all endpoints from the OpenAPI specification."""
        endpoints = []
        paths = self.spec_data.get('paths', {})
        
        for path, path_data in paths.items():
            for method, method_data in path_data.items():
                if method.lower() in [m.value for m in HTTPMethod]:
                    endpoint = self._parse_endpoint(path, method, method_data)
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_endpoint(self, path: str, method: str, method_data: Dict[str, Any]) -> Endpoint:
        """Parse a single endpoint from the OpenAPI specification."""
        # Extract basic info
        summary = method_data.get('summary')
        description = method_data.get('description')
        operation_id = method_data.get('operationId')
        tags = method_data.get('tags', [])
        
        # Extract parameters
        parameters = self._parse_parameters(method_data.get('parameters', []))
        
        # Extract request body
        request_body = self._parse_request_body(method_data.get('requestBody'))
        
        # Extract responses
        responses = method_data.get('responses', {})
        
        return Endpoint(
            path=path,
            method=HTTPMethod(method.lower()),
            summary=summary,
            description=description,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            tags=tags,
            operation_id=operation_id
        )
    
    def _parse_parameters(self, parameters_data: List[Dict[str, Any]]) -> List[Parameter]:
        """Parse parameters from the OpenAPI specification."""
        parameters = []
        
        for param_data in parameters_data:
            name = param_data.get('name')
            if name is None:
                continue  # Skip parameters without names
            location = param_data.get('in', 'query')
            required = param_data.get('required', False)
            description = param_data.get('description')
            
            # Extract type information
            schema = param_data.get('schema', {})
            param_type = self._extract_parameter_type(schema)
            
            # Extract default and example values
            default = param_data.get('default')
            example = param_data.get('example')
            
            parameter = Parameter(
                name=name,
                type=param_type,
                location=ParameterLocation(location),
                required=required,
                description=description,
                default=default,
                param_schema=schema,
                example=example
            )
            parameters.append(parameter)
        
        return parameters
    
    def _parse_request_body(self, request_body_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Parse request body from the OpenAPI specification."""
        if not request_body_data:
            return None
            
        content = request_body_data.get('content', {})
        required = request_body_data.get('required', False)
        
        return {
            'content': content,
            'required': required
        }
    
    def _extract_parameter_type(self, schema: Dict[str, Any]) -> ParameterType:
        """Extract parameter type from schema."""
        if not schema:
            return ParameterType.STRING
            
        param_type = schema.get('type', 'string')
        
        # Map OpenAPI types to our enum
        type_mapping = {
            'string': ParameterType.STRING,
            'integer': ParameterType.INTEGER,
            'number': ParameterType.NUMBER,
            'boolean': ParameterType.BOOLEAN,
            'array': ParameterType.ARRAY,
            'object': ParameterType.OBJECT
        }
        
        return type_mapping.get(param_type, ParameterType.STRING)
    
    def get_endpoint_by_path_and_method(self, path: str, method: str) -> Optional[Endpoint]:
        """Get a specific endpoint by path and method."""
        for endpoint in self._extract_endpoints():
            if endpoint.path == path and endpoint.method.value == method.lower():
                return endpoint
        return None
    
    def get_endpoints_by_tag(self, tag: str) -> List[Endpoint]:
        """Get all endpoints with a specific tag."""
        return [ep for ep in self._extract_endpoints() if tag in ep.tags] 