"""
Auto-generate OpenAPI specifications from API endpoints.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
import re


class OpenAPISpecGenerator:
    """Generate OpenAPI specifications from API endpoints."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Auto-Generated API",
                "version": "1.0.0",
                "description": "Auto-generated from API endpoints"
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "API Server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
    
    def discover_endpoints(self, common_paths: List[str] = None) -> Dict[str, Any]:
        """Discover API endpoints by trying common paths."""
        if common_paths is None:
            common_paths = [
                "/", "/api", "/api/v1", "/api/v2",
                "/users", "/posts", "/items", "/products",
                "/health", "/status", "/docs", "/swagger"
            ]
        
        discovered_paths = {}
        
        for path in common_paths:
            try:
                response = requests.get(urljoin(self.base_url, path), timeout=5)
                discovered_paths[path] = {
                    "status": response.status_code,
                    "content_type": response.headers.get('content-type', ''),
                    "methods": self._detect_methods(path)
                }
            except Exception as e:
                print(f"Error testing {path}: {e}")
        
        return discovered_paths
    
    def _detect_methods(self, path: str) -> List[str]:
        """Detect which HTTP methods are supported for a path."""
        methods = []
        test_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in test_methods:
            try:
                response = requests.request(method, urljoin(self.base_url, path), timeout=3)
                if response.status_code not in [404, 405, 501]:
                    methods.append(method.lower())
            except:
                pass
        
        return methods
    
    def generate_spec_from_discovery(self, discovered_paths: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI spec from discovered endpoints."""
        for path, info in discovered_paths.items():
            if info['methods']:
                self.spec['paths'][path] = {}
                
                for method in info['methods']:
                    self.spec['paths'][path][method] = {
                        "summary": f"{method.upper()} {path}",
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "description": "Response data"
                                        }
                                    }
                                }
                            }
                        }
                    }
        
        return self.spec
    
    def save_spec(self, filename: str = "auto_generated_api.yaml"):
        """Save the generated specification to a file."""
        import yaml
        
        with open(filename, 'w') as f:
            yaml.dump(self.spec, f, default_flow_style=False, sort_keys=False)
        
        return filename


def generate_spec_from_url(base_url: str, output_file: str = "auto_generated_api.yaml") -> str:
    """Convenience function to generate OpenAPI spec from URL."""
    generator = OpenAPISpecGenerator(base_url)
    discovered = generator.discover_endpoints()
    spec = generator.generate_spec_from_discovery(discovered)
    return generator.save_spec(output_file) 