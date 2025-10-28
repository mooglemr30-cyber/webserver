#!/usr/bin/env python3
"""
Flask error handling integration and custom error pages.
Provides comprehensive error handling for Flask applications with user-friendly responses.
"""

import json
import traceback
from flask import Flask, request, jsonify, render_template_string, g
from werkzeug.exceptions import HTTPException
from typing import Dict, Any, Optional
import logging

from error_handling import (
    ErrorHandler, ErrorCategory, ErrorSeverity, get_error_handler,
    handle_errors, CircuitBreakerOpenError
)

logger = logging.getLogger(__name__)

class FlaskErrorHandler:
    """Flask-specific error handling integration."""
    
    def __init__(self, app: Flask, error_handler: ErrorHandler):
        self.app = app
        self.error_handler = error_handler
        self._register_error_handlers()
    
    def _register_error_handlers(self):
        """Register Flask error handlers."""
        
        # HTTP error handlers
        self.app.register_error_handler(400, self._handle_bad_request)
        self.app.register_error_handler(401, self._handle_unauthorized)
        self.app.register_error_handler(403, self._handle_forbidden)
        self.app.register_error_handler(404, self._handle_not_found)
        self.app.register_error_handler(405, self._handle_method_not_allowed)
        self.app.register_error_handler(413, self._handle_payload_too_large)
        self.app.register_error_handler(429, self._handle_rate_limit_exceeded)
        self.app.register_error_handler(500, self._handle_internal_server_error)
        self.app.register_error_handler(502, self._handle_bad_gateway)
        self.app.register_error_handler(503, self._handle_service_unavailable)
        self.app.register_error_handler(504, self._handle_gateway_timeout)
        
        # Custom exception handlers
        self.app.register_error_handler(CircuitBreakerOpenError, self._handle_circuit_breaker_open)
        self.app.register_error_handler(Exception, self._handle_generic_exception)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Get request context for error handling."""
        return {
            'request_id': getattr(g, 'request_id', None),
            'user_id': getattr(g, 'user_id', None),
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'client_ip': getattr(g, 'client_ip', request.remote_addr)
        }
    
    def _handle_bad_request(self, error: HTTPException):
        """Handle 400 Bad Request errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Invalid request. Please check your input."
        )
        
        return self._create_error_response(error_details, 400)
    
    def _handle_unauthorized(self, error: HTTPException):
        """Handle 401 Unauthorized errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Authentication required. Please log in."
        )
        
        return self._create_error_response(error_details, 401)
    
    def _handle_forbidden(self, error: HTTPException):
        """Handle 403 Forbidden errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Access denied. You don't have permission for this action."
        )
        
        return self._create_error_response(error_details, 403)
    
    def _handle_not_found(self, error: HTTPException):
        """Handle 404 Not Found errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="The requested resource was not found."
        )
        
        return self._create_error_response(error_details, 404)
    
    def _handle_method_not_allowed(self, error: HTTPException):
        """Handle 405 Method Not Allowed errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message=f"Method {request.method} not allowed for this endpoint."
        )
        
        return self._create_error_response(error_details, 405)
    
    def _handle_payload_too_large(self, error: HTTPException):
        """Handle 413 Payload Too Large errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="File or request size is too large. Please reduce the size and try again."
        )
        
        return self._create_error_response(error_details, 413)
    
    def _handle_rate_limit_exceeded(self, error: HTTPException):
        """Handle 429 Rate Limit Exceeded errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Rate limit exceeded. Please wait before making more requests."
        )
        
        return self._create_error_response(error_details, 429)
    
    def _handle_internal_server_error(self, error: HTTPException):
        """Handle 500 Internal Server Error."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="An internal server error occurred. Please try again later."
        )
        
        return self._create_error_response(error_details, 500)
    
    def _handle_bad_gateway(self, error: HTTPException):
        """Handle 502 Bad Gateway errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="External service error. Please try again later."
        )
        
        return self._create_error_response(error_details, 502)
    
    def _handle_service_unavailable(self, error: HTTPException):
        """Handle 503 Service Unavailable errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Service temporarily unavailable. Please try again later."
        )
        
        return self._create_error_response(error_details, 503)
    
    def _handle_gateway_timeout(self, error: HTTPException):
        """Handle 504 Gateway Timeout errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Request timeout. Please try again."
        )
        
        return self._create_error_response(error_details, 504)
    
    def _handle_circuit_breaker_open(self, error: CircuitBreakerOpenError):
        """Handle circuit breaker open errors."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="Service temporarily unavailable due to high failure rate. Please try again later."
        )
        
        return self._create_error_response(error_details, 503)
    
    def _handle_generic_exception(self, error: Exception):
        """Handle generic exceptions."""
        context = self._get_request_context()
        
        error_details = self.error_handler.handle_error(
            error=error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            request_id=context['request_id'],
            user_id=context['user_id'],
            endpoint=context['endpoint'],
            custom_message="An unexpected error occurred. Please try again later."
        )
        
        return self._create_error_response(error_details, 500)
    
    def _create_error_response(self, error_details, status_code: int):
        """Create standardized error response."""
        if request.is_json or request.content_type == 'application/json':
            # JSON response for API requests
            response_data = {
                'success': False,
                'error': error_details.user_message,
                'error_id': error_details.error_id,
                'category': error_details.category.value,
                'suggestions': error_details.recovery_suggestions,
                'timestamp': error_details.timestamp.isoformat()
            }
            
            # Add debug info in development
            if self.app.debug:
                response_data['debug'] = {
                    'error_type': error_details.error_type,
                    'technical_details': error_details.technical_details,
                    'stack_trace': error_details.stack_trace
                }
            
            response = jsonify(response_data)
            response.status_code = status_code
            return response
        
        else:
            # HTML response for web requests
            return self._render_error_page(error_details, status_code)
    
    def _render_error_page(self, error_details, status_code: int):
        """Render HTML error page."""
        template = self._get_error_page_template()
        
        html = render_template_string(
            template,
            error_title=self._get_error_title(status_code),
            error_message=error_details.user_message,
            error_id=error_details.error_id,
            suggestions=error_details.recovery_suggestions,
            status_code=status_code,
            show_debug=self.app.debug,
            debug_info={
                'error_type': error_details.error_type,
                'technical_details': error_details.technical_details,
                'stack_trace': error_details.stack_trace
            } if self.app.debug else None
        )
        
        return html, status_code
    
    def _get_error_title(self, status_code: int) -> str:
        """Get error title for status code."""
        titles = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            413: "Payload Too Large",
            429: "Rate Limit Exceeded",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout"
        }
        return titles.get(status_code, "Error")
    
    def _get_error_page_template(self) -> str:
        """Get HTML template for error pages."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ error_title }} - Enhanced Web Server</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
            line-height: 1.6;
        }
        
        .error-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            padding: 3rem;
            max-width: 600px;
            width: 90%;
            text-align: center;
        }
        
        .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            color: #dc3545;
        }
        
        .error-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: #2c3e50;
        }
        
        .error-message {
            font-size: 1.1rem;
            margin-bottom: 2rem;
            color: #666;
        }
        
        .error-id {
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background: #f8f9fa;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            margin-bottom: 2rem;
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        .suggestions {
            text-align: left;
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .suggestions h3 {
            margin-bottom: 1rem;
            color: #2c3e50;
        }
        
        .suggestions ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .suggestions li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }
        
        .suggestions li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #007acc;
            font-weight: bold;
        }
        
        .btn {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #007acc;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s ease;
            margin: 0.5rem;
        }
        
        .btn:hover {
            background: #005c99;
        }
        
        .debug-section {
            text-align: left;
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 2rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.8rem;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .debug-section h3 {
            color: #e74c3c;
            margin-bottom: 1rem;
        }
        
        .debug-section pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        @media (max-width: 768px) {
            .error-container {
                padding: 2rem;
                margin: 1rem;
            }
            
            .error-title {
                font-size: 1.5rem;
            }
            
            .error-icon {
                font-size: 3rem;
            }
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1 class="error-title">{{ error_title }}</h1>
        <p class="error-message">{{ error_message }}</p>
        
        <div class="error-id">
            Error ID: {{ error_id }}
        </div>
        
        {% if suggestions %}
        <div class="suggestions">
            <h3>What you can try:</h3>
            <ul>
                {% for suggestion in suggestions %}
                <li>{{ suggestion }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <div>
            <a href="/" class="btn">Go Home</a>
            <a href="javascript:history.back()" class="btn">Go Back</a>
        </div>
        
        {% if show_debug and debug_info %}
        <div class="debug-section">
            <h3>Debug Information (Development Mode)</h3>
            <p><strong>Error Type:</strong> {{ debug_info.error_type }}</p>
            {% if debug_info.technical_details %}
            <p><strong>Technical Details:</strong></p>
            <pre>{{ debug_info.technical_details | tojson(indent=2) }}</pre>
            {% endif %}
            {% if debug_info.stack_trace %}
            <p><strong>Stack Trace:</strong></p>
            <pre>{{ debug_info.stack_trace }}</pre>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
        """

def setup_flask_error_handling(app: Flask) -> FlaskErrorHandler:
    """Setup Flask error handling."""
    error_handler = get_error_handler()
    if not error_handler:
        from error_handling import initialize_error_handling
        error_handler = initialize_error_handling()
    
    flask_error_handler = FlaskErrorHandler(app, error_handler)
    
    # Add error handling middleware
    @app.before_request
    def before_request_error_handling():
        """Setup error handling context for each request."""
        # This can be extended to set up request-specific error handling
        pass
    
    @app.teardown_request
    def teardown_request_error_handling(exception):
        """Clean up error handling context after each request."""
        if exception:
            # Log unhandled exceptions
            logger.error(f"Unhandled exception in request: {exception}")
    
    return flask_error_handler