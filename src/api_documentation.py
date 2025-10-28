#!/usr/bin/env python3
"""
API documentation and OpenAPI/Swagger integration.
Provides comprehensive API documentation with interactive testing.
"""

import json
import inspect
from typing import Dict, List, Any, Optional, Union, get_type_hints
from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class APIDocumentationManager:
    """Manage API documentation and OpenAPI specifications."""
    
    def __init__(self, app_name: str = "Enhanced Web Server", version: str = "2.0.0"):
        self.app_name = app_name
        self.version = version
        self.endpoints = {}
        self.schemas = {}
        self.tags = {}
        
        # OpenAPI specification structure
        self.openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": app_name,
                "version": version,
                "description": "Comprehensive web server with security, file management, and command execution",
                "contact": {
                    "name": "API Support",
                    "url": "https://github.com/your-repo",
                    "email": "support@example.com"
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "csrf_token": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-CSRF-Token",
                        "description": "CSRF protection token"
                    },
                    "session_auth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-Session-ID",
                        "description": "Session-based authentication"
                    },
                    "bearer_token": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "responses": {
                    "NotFound": {
                        "description": "Resource not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "ValidationError": {
                        "description": "Validation error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "RateLimitExceeded": {
                        "description": "Rate limit exceeded",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RateLimitResponse"}
                            }
                        }
                    },
                    "Unauthorized": {
                        "description": "Authentication required",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "security": [
                {"csrf_token": []},
                {"session_auth": []}
            ],
            "tags": []
        }
        
        # Define common schemas
        self._define_common_schemas()
    
    def _define_common_schemas(self):
        """Define common API schemas."""
        self.openapi_spec["components"]["schemas"] = {
            "SuccessResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string", "example": "Operation completed successfully"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "data": {"type": "object", "description": "Response data"}
                },
                "required": ["success", "timestamp"]
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error": {"type": "string", "example": "An error occurred"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "details": {"type": "object", "description": "Error details"}
                },
                "required": ["success", "error", "timestamp"]
            },
            "RateLimitResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error": {"type": "string", "example": "Rate limit exceeded"},
                    "retry_after": {"type": "integer", "example": 60},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["success", "error", "retry_after", "timestamp"]
            },
            "DataStoreItem": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "example": "user_preferences"},
                    "value": {"type": "object", "description": "Stored data value"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "updated_at": {"type": "string", "format": "date-time"}
                },
                "required": ["key", "value"]
            },
            "FileMetadata": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "example": "document.pdf"},
                    "original_name": {"type": "string", "example": "my_document.pdf"},
                    "mime_type": {"type": "string", "example": "application/pdf"},
                    "size": {"type": "integer", "example": 1048576},
                    "uploaded_at": {"type": "string", "format": "date-time"},
                    "checksum": {"type": "string", "example": "abc123def456"}
                },
                "required": ["filename", "original_name", "size"]
            },
            "ProgramMetadata": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "example": "script.py"},
                    "original_name": {"type": "string", "example": "my_script.py"},
                    "program_type": {"type": "string", "example": "python"},
                    "size": {"type": "integer", "example": 2048},
                    "uploaded_at": {"type": "string", "format": "date-time"},
                    "execution_count": {"type": "integer", "example": 5},
                    "last_executed": {"type": "string", "format": "date-time"},
                    "description": {"type": "string", "example": "Data processing script"}
                },
                "required": ["filename", "original_name", "program_type", "size"]
            },
            "CommandRequest": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "example": "ls -la"},
                    "sudo_password": {"type": "string", "example": "password123"},
                    "interactive": {"type": "boolean", "example": True}
                },
                "required": ["command"]
            },
            "CommandResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "command": {"type": "string", "example": "ls -la"},
                    "stdout": {"type": "string", "example": "file1.txt\nfile2.txt"},
                    "stderr": {"type": "string", "example": ""},
                    "return_code": {"type": "integer", "example": 0},
                    "waiting_for_input": {"type": "boolean", "example": False},
                    "session_id": {"type": "string", "example": "abc-123-def"},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["success", "command", "timestamp"]
            },
            "TunnelStatus": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "example": "ngrok"},
                    "status": {"type": "string", "example": "running"},
                    "public_url": {"type": "string", "example": "https://abc123.ngrok.io"},
                    "started_at": {"type": "string", "format": "date-time"}
                },
                "required": ["service", "status"]
            },
            "HealthStatus": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "healthy"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string", "example": "2.0.0"},
                    "services": {"type": "object", "description": "Service health status"},
                    "security": {"type": "object", "description": "Security feature status"}
                },
                "required": ["status", "timestamp"]
            }
        }
    
    def add_tag(self, name: str, description: str):
        """Add API tag for grouping endpoints."""
        tag = {
            "name": name,
            "description": description
        }
        
        if tag not in self.openapi_spec["tags"]:
            self.openapi_spec["tags"].append(tag)
        
        self.tags[name] = description
    
    def document_endpoint(self, path: str, method: str, summary: str, 
                         description: str = "", tags: List[str] = None,
                         parameters: List[Dict] = None, request_body: Dict = None,
                         responses: Dict = None, security: List[Dict] = None):
        """Document an API endpoint."""
        
        if path not in self.openapi_spec["paths"]:
            self.openapi_spec["paths"][path] = {}
        
        # Build endpoint documentation
        endpoint_doc = {
            "summary": summary,
            "description": description or summary,
            "tags": tags or [],
            "operationId": f"{method}_{path.replace('/', '_').replace('<', '').replace('>', '').replace(':', '_')}",
        }
        
        if parameters:
            endpoint_doc["parameters"] = parameters
        
        if request_body:
            endpoint_doc["requestBody"] = request_body
        
        if responses:
            endpoint_doc["responses"] = responses
        else:
            # Default responses
            endpoint_doc["responses"] = {
                "200": {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/ValidationError"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "404": {"$ref": "#/components/responses/NotFound"},
                "429": {"$ref": "#/components/responses/RateLimitExceeded"}
            }
        
        if security:
            endpoint_doc["security"] = security
        
        self.openapi_spec["paths"][path][method.lower()] = endpoint_doc
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get the complete OpenAPI specification."""
        return self.openapi_spec
    
    def generate_swagger_ui_html(self) -> str:
        """Generate Swagger UI HTML page."""
        spec_json = json.dumps(self.openapi_spec, indent=2)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - {self.app_name}</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
        .swagger-ui .topbar {{
            background-color: #2d2d2d;
        }}
        .swagger-ui .topbar .download-url-wrapper .select-label {{
            color: #007acc;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                spec: {spec_json},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                docExpansion: "list",
                filter: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                onComplete: function() {{
                    console.log('Swagger UI loaded');
                }}
            }});
        }};
    </script>
</body>
</html>
        """
    
    def export_postman_collection(self) -> Dict[str, Any]:
        """Export API documentation as Postman collection."""
        collection = {
            "info": {
                "name": self.app_name,
                "description": f"API collection for {self.app_name}",
                "version": self.version,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [],
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "http://localhost:8000",
                    "type": "string"
                }
            ]
        }
        
        # Group items by tags
        tag_groups = {}
        
        for path, methods in self.openapi_spec["paths"].items():
            for method, endpoint in methods.items():
                tags = endpoint.get("tags", ["General"])
                
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    
                    # Convert OpenAPI to Postman format
                    item = {
                        "name": endpoint.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json",
                                    "type": "text"
                                }
                            ],
                            "url": {
                                "raw": "{{baseUrl}}" + path,
                                "host": ["{{baseUrl}}"],
                                "path": path.split("/")[1:]  # Remove empty first element
                            },
                            "description": endpoint.get("description", "")
                        }
                    }
                    
                    # Add request body if present
                    if "requestBody" in endpoint:
                        item["request"]["body"] = {
                            "mode": "raw",
                            "raw": json.dumps({
                                "example": "Request body schema defined in OpenAPI spec"
                            }, indent=2),
                            "options": {
                                "raw": {
                                    "language": "json"
                                }
                            }
                        }
                    
                    tag_groups[tag].append(item)
        
        # Add grouped items to collection
        for tag, items in tag_groups.items():
            collection["item"].append({
                "name": tag,
                "item": items,
                "description": self.tags.get(tag, f"API endpoints for {tag}")
            })
        
        return collection

def api_doc(path: str, method: str, summary: str, description: str = "",
           tags: List[str] = None, request_schema: str = None,
           response_schema: str = None, security_required: bool = True):
    """Decorator to automatically document API endpoints."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Document the endpoint
            parameters = []
            
            # Extract path parameters
            import re
            path_params = re.findall(r'<([^>]+)>', path)
            for param in path_params:
                param_name = param.split(':')[-1]  # Remove type hint if present
                parameters.append({
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": f"Path parameter: {param_name}"
                })
            
            # Build request body schema
            request_body = None
            if request_schema and method.lower() in ['post', 'put', 'patch']:
                request_body = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{request_schema}"}
                        }
                    }
                }
            
            # Build response schema
            responses = {
                "200": {
                    "description": "Successful operation",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"#/components/schemas/{response_schema or 'SuccessResponse'}"
                            }
                        }
                    }
                }
            }
            
            # Security requirements
            security = []
            if security_required:
                security.append({"csrf_token": [], "session_auth": []})
            
            # Document the endpoint
            if hasattr(wrapper, '_api_doc_manager'):
                wrapper._api_doc_manager.document_endpoint(
                    path=path,
                    method=method,
                    summary=summary,
                    description=description,
                    tags=tags or ["General"],
                    parameters=parameters if parameters else None,
                    request_body=request_body,
                    responses=responses,
                    security=security if security else None
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Global API documentation manager
api_doc_manager = APIDocumentationManager()

def initialize_api_documentation(app_name: str = "Enhanced Web Server", version: str = "2.0.0"):
    """Initialize API documentation."""
    global api_doc_manager
    api_doc_manager = APIDocumentationManager(app_name, version)
    
    # Add common tags
    api_doc_manager.add_tag("Data Storage", "Key-value data storage operations")
    api_doc_manager.add_tag("File Management", "File upload, download, and management")
    api_doc_manager.add_tag("Program Management", "Program upload and execution")
    api_doc_manager.add_tag("Command Execution", "System command execution")
    api_doc_manager.add_tag("Tunnel Management", "Public tunnel management (ngrok, localtunnel, cloudflared)")
    api_doc_manager.add_tag("System", "Health checks and system information")
    api_doc_manager.add_tag("Configuration", "Configuration and settings management")
    api_doc_manager.add_tag("Security", "Authentication and security operations")
    
    return api_doc_manager

def get_api_documentation() -> APIDocumentationManager:
    """Get the global API documentation manager."""
    return api_doc_manager