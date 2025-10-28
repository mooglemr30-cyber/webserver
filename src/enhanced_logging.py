#!/usr/bin/env python3
"""
Enhanced logging system for the web server.
Provides structured logging, performance monitoring, and audit trails.
"""

import logging
import logging.handlers
import os
import time
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from functools import wraps
from collections import defaultdict, deque
import uuid

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)

class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'recent_times': deque(maxlen=100),
            'errors': 0,
        })
        self.lock = threading.Lock()
    
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record request performance metrics."""
        with self.lock:
            metric = self.metrics[endpoint]
            metric['count'] += 1
            metric['total_time'] += duration
            metric['min_time'] = min(metric['min_time'], duration)
            metric['max_time'] = max(metric['max_time'], duration)
            metric['recent_times'].append(duration)
            
            if status_code >= 400:
                metric['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self.lock:
            result = {}
            for endpoint, metric in self.metrics.items():
                if metric['count'] > 0:
                    avg_time = metric['total_time'] / metric['count']
                    recent_avg = sum(metric['recent_times']) / len(metric['recent_times']) if metric['recent_times'] else 0
                    error_rate = (metric['errors'] / metric['count']) * 100
                    
                    result[endpoint] = {
                        'total_requests': metric['count'],
                        'average_time': round(avg_time, 3),
                        'min_time': round(metric['min_time'], 3),
                        'max_time': round(metric['max_time'], 3),
                        'recent_average_time': round(recent_avg, 3),
                        'error_rate': round(error_rate, 2),
                        'total_errors': metric['errors'],
                    }
            return result
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        metrics = self.get_metrics()
        
        total_requests = sum(m['total_requests'] for m in metrics.values())
        total_errors = sum(m['total_errors'] for m in metrics.values())
        overall_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Determine health status
        health = 'healthy'
        if overall_error_rate > 10:
            health = 'critical'
        elif overall_error_rate > 5:
            health = 'warning'
        
        # Check for slow endpoints
        slow_endpoints = [
            endpoint for endpoint, metric in metrics.items()
            if metric['recent_average_time'] > 2.0
        ]
        
        return {
            'status': health,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': round(overall_error_rate, 2),
            'slow_endpoints': slow_endpoints,
            'uptime_start': self.start_time if hasattr(self, 'start_time') else None,
        }

class AuditLogger:
    """Audit logging for security and compliance."""
    
    def __init__(self, log_file: str = 'data/audit.log'):
        self.log_file = log_file
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create audit log handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, details: Dict[str, Any], 
                  user_id: Optional[str] = None, client_ip: Optional[str] = None):
        """Log an audit event."""
        audit_entry = {
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        if user_id:
            audit_entry['user_id'] = user_id
        if client_ip:
            audit_entry['client_ip'] = client_ip
        
        self.logger.info('', extra=audit_entry)
    
    def log_auth_event(self, event: str, username: str, client_ip: str, success: bool, details: Optional[Dict] = None):
        """Log authentication events."""
        self.log_event('authentication', {
            'action': event,
            'username': username,
            'success': success,
            'details': details or {}
        }, client_ip=client_ip)
    
    def log_file_event(self, event: str, filename: str, user_id: str, client_ip: str, details: Optional[Dict] = None):
        """Log file operation events."""
        self.log_event('file_operation', {
            'action': event,
            'filename': filename,
            'details': details or {}
        }, user_id=user_id, client_ip=client_ip)
    
    def log_command_event(self, command: str, user_id: str, client_ip: str, 
                         success: bool, output_length: Optional[int] = None):
        """Log command execution events."""
        self.log_event('command_execution', {
            'command': command[:100] + '...' if len(command) > 100 else command,
            'success': success,
            'output_length': output_length
        }, user_id=user_id, client_ip=client_ip)
    
    def log_security_event(self, event: str, details: Dict[str, Any], client_ip: str, severity: str = 'medium'):
        """Log security-related events."""
        self.log_event('security', {
            'action': event,
            'severity': severity,
            'details': details
        }, client_ip=client_ip)

class LoggingManager:
    """Central logging management."""
    
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.performance_monitor = PerformanceMonitor()
        self.audit_logger = AuditLogger()
        self.loggers = {}
        
        # Setup main application logger
        self.setup_application_logging()
        
        # Track startup time
        self.performance_monitor.start_time = datetime.now(timezone.utc).isoformat()
    
    def setup_application_logging(self):
        """Setup application logging configuration."""
        log_level = getattr(logging, self.config.get('logging.level', 'INFO') if self.config else 'INFO')
        log_to_file = self.config.get('logging.log_to_file', True) if self.config else True
        log_to_console = self.config.get('logging.log_to_console', True) if self.config else True
        
        # Create logs directory
        os.makedirs('data/logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Add file handler
        if log_to_file:
            file_handler = logging.handlers.RotatingFileHandler(
                'data/logs/application.log',
                maxBytes=self.config.get('logging.max_file_size', 10*1024*1024) if self.config else 10*1024*1024,
                backupCount=self.config.get('logging.backup_count', 5) if self.config else 5
            )
            file_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(file_handler)
        
        # Setup specific loggers
        self.setup_logger('security', 'data/logs/security.log')
        self.setup_logger('performance', 'data/logs/performance.log')
        self.setup_logger('api', 'data/logs/api.log')
    
    def setup_logger(self, name: str, log_file: str) -> logging.Logger:
        """Setup a specific logger."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        self.loggers[name] = logger
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger by name."""
        return self.loggers.get(name, logging.getLogger(name))

def log_performance(endpoint_name: Optional[str] = None):
    """Decorator to log endpoint performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            request_id = str(uuid.uuid4())
            
            # Get endpoint name
            name = endpoint_name or f"{func.__module__}.{func.__name__}"
            
            # Get logger
            logger = logging.getLogger('performance')
            
            try:
                # Log request start
                logger.info(f"Request started: {name}", extra={
                    'request_id': request_id,
                    'endpoint': name,
                })
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Determine status code
                status_code = 200
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                elif isinstance(result, tuple) and len(result) > 1:
                    status_code = result[1]
                
                # Record metrics
                logging_manager.performance_monitor.record_request(name, duration, status_code)
                
                # Log completion
                logger.info(f"Request completed: {name}", extra={
                    'request_id': request_id,
                    'endpoint': name,
                    'duration': round(duration, 3),
                    'status_code': status_code,
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error metrics
                logging_manager.performance_monitor.record_request(name, duration, 500)
                
                # Log error
                logger.error(f"Request failed: {name}", extra={
                    'request_id': request_id,
                    'endpoint': name,
                    'duration': round(duration, 3),
                    'error': str(e),
                }, exc_info=True)
                
                raise
        
        return wrapper
    return decorator

def log_audit_event(event_type: str, details: Optional[Dict] = None):
    """Decorator to automatically log audit events."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request info if available
            from flask import request, g
            
            client_ip = getattr(request, 'environ', {}).get('REMOTE_ADDR', 'unknown')
            user_id = getattr(g, 'user_id', None) if hasattr(g, 'user_id') else None
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful event
                audit_details = details.copy() if details else {}
                audit_details.update({
                    'function': func.__name__,
                    'success': True,
                })
                
                logging_manager.audit_logger.log_event(
                    event_type, audit_details, user_id, client_ip
                )
                
                return result
                
            except Exception as e:
                # Log failed event
                audit_details = details.copy() if details else {}
                audit_details.update({
                    'function': func.__name__,
                    'success': False,
                    'error': str(e),
                })
                
                logging_manager.audit_logger.log_event(
                    event_type, audit_details, user_id, client_ip
                )
                
                raise
        
        return wrapper
    return decorator

class LogAnalyzer:
    """Analyze log files for insights and alerts."""
    
    def __init__(self, log_dir: str = 'data/logs'):
        self.log_dir = log_dir
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns in logs."""
        patterns = defaultdict(int)
        total_errors = 0
        
        # This would analyze log files for error patterns
        # Implementation depends on log format and requirements
        
        return {
            'total_errors': total_errors,
            'error_patterns': dict(patterns),
            'analysis_period_hours': hours,
        }
    
    def get_security_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security alerts from logs."""
        alerts = []
        
        # This would analyze security logs for suspicious activity
        # Implementation depends on security requirements
        
        return alerts
    
    def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report."""
        metrics = logging_manager.performance_monitor.get_metrics()
        health = logging_manager.performance_monitor.get_health_status()
        
        return {
            'health_status': health,
            'endpoint_metrics': metrics,
            'report_period_hours': hours,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }

# Global logging manager instance
logging_manager = LoggingManager()

# Convenience functions
def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging_manager.get_logger(name)
    return logging.getLogger()

def log_security_event(event: str, details: Dict[str, Any], client_ip: str, severity: str = 'medium'):
    """Log a security event."""
    logging_manager.audit_logger.log_security_event(event, details, client_ip, severity)

def log_auth_event(event: str, username: str, client_ip: str, success: bool, details: Optional[Dict] = None):
    """Log an authentication event."""
    logging_manager.audit_logger.log_auth_event(event, username, client_ip, success, details)

def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    return logging_manager.performance_monitor.get_metrics()

def get_health_status() -> Dict[str, Any]:
    """Get application health status."""
    return logging_manager.performance_monitor.get_health_status()