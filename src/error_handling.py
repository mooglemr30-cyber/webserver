#!/usr/bin/env python3
"""
Enhanced error handling system with retry mechanisms, circuit breakers, and graceful degradation.
Provides comprehensive error management, user-friendly error responses, and system resilience.
"""

import time
import json
import traceback
import functools
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import requests
import sqlite3

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"

@dataclass
class ErrorDetails:
    """Detailed error information."""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_details: Dict[str, Any]
    stack_trace: Optional[str]
    request_id: Optional[str]
    user_id: Optional[str]
    endpoint: Optional[str]
    recovery_suggestions: List[str]
    retry_count: int = 0
    resolved: bool = False

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5      # Number of failures before opening
    timeout: int = 60              # Seconds before trying half-open
    recovery_threshold: int = 3     # Successful calls to close circuit
    monitored_exceptions: tuple = (Exception,)

class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker for {func.__name__} is half-open")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is open for {func.__name__}"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.config.monitored_exceptions as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return (
            datetime.now() - self.last_failure_time
        ).total_seconds() >= self.config.timeout
    
    def _on_success(self):
        """Handle successful call."""
        with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.recovery_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker closed after recovery")
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
                logger.warning("Circuit breaker opened from half-open state")
            elif (self.state == CircuitBreakerState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                self.state = CircuitBreakerState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass

class RetryConfig:
    """Configuration for retry mechanism."""
    
    def __init__(self, 
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True,
                 retryable_exceptions: tuple = (Exception,)):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

def retry_with_backoff(config: RetryConfig):
    """Decorator for retry mechanism with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt failed
                        logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}: {e}")
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to avoid thundering herd
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            # Should never reach here
            raise last_exception
        
        return wrapper
    return decorator

class ErrorHandler:
    """Main error handling system."""
    
    def __init__(self, db_path: str = "data/errors.db"):
        self.db_path = db_path
        self.circuit_breakers = {}
        self.error_counts = defaultdict(int)
        self.recent_errors = deque(maxlen=1000)
        self._init_database()
    
    def _init_database(self):
        """Initialize error tracking database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS errors (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        category TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        user_message TEXT,
                        technical_details TEXT,
                        stack_trace TEXT,
                        request_id TEXT,
                        user_id TEXT,
                        endpoint TEXT,
                        recovery_suggestions TEXT,
                        retry_count INTEGER DEFAULT 0,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_category ON errors(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_severity ON errors(severity)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_errors_resolved ON errors(resolved)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing error database: {e}")
    
    def register_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Register a circuit breaker."""
        circuit_breaker = CircuitBreaker(config)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get registered circuit breaker."""
        return self.circuit_breakers.get(name)
    
    def handle_error(self, 
                    error: Exception,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    request_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    endpoint: Optional[str] = None,
                    custom_message: Optional[str] = None) -> ErrorDetails:
        """Handle and log error with comprehensive details."""
        
        error_id = f"err_{int(time.time() * 1000)}_{hash(str(error)) % 10000}"
        
        # Determine user-friendly message
        user_message = custom_message or self._get_user_friendly_message(error, category)
        
        # Get recovery suggestions
        recovery_suggestions = self._get_recovery_suggestions(error, category)
        
        # Create error details
        error_details = ErrorDetails(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            category=category,
            severity=severity,
            user_message=user_message,
            technical_details=self._extract_technical_details(error),
            stack_trace=traceback.format_exc(),
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint,
            recovery_suggestions=recovery_suggestions
        )
        
        # Store error
        self._store_error(error_details)
        
        # Update error tracking
        self.error_counts[category.value] += 1
        self.recent_errors.append(error_details)
        
        # Log error
        self._log_error(error_details)
        
        return error_details
    
    def _get_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message."""
        error_messages = {
            ErrorCategory.VALIDATION: "Please check your input and try again.",
            ErrorCategory.AUTHENTICATION: "Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.NOT_FOUND: "The requested resource was not found.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment and try again.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.NETWORK: "Network connection failed. Please check your connection.",
            ErrorCategory.DATABASE: "Database error occurred. Please try again later.",
            ErrorCategory.FILE_SYSTEM: "File operation failed. Please check file permissions.",
            ErrorCategory.EXTERNAL_SERVICE: "External service is temporarily unavailable.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        
        return error_messages.get(category, "An error occurred. Please try again.")
    
    def _get_recovery_suggestions(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Get recovery suggestions for the error."""
        suggestions = {
            ErrorCategory.VALIDATION: [
                "Check input format and required fields",
                "Ensure data types are correct",
                "Verify field length limits"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Verify username and password",
                "Check if account is locked",
                "Try logging out and back in"
            ],
            ErrorCategory.AUTHORIZATION: [
                "Contact administrator for access",
                "Check user permissions",
                "Verify user role assignments"
            ],
            ErrorCategory.NOT_FOUND: [
                "Check the URL or resource path",
                "Verify the resource exists",
                "Try refreshing the page"
            ],
            ErrorCategory.RATE_LIMIT: [
                "Wait before making more requests",
                "Reduce request frequency",
                "Contact support for rate limit increase"
            ],
            ErrorCategory.SYSTEM: [
                "Try again in a few minutes",
                "Contact system administrator",
                "Check system status page"
            ],
            ErrorCategory.NETWORK: [
                "Check internet connection",
                "Try again later",
                "Contact network administrator"
            ],
            ErrorCategory.DATABASE: [
                "Try again later",
                "Contact system administrator",
                "Check database connectivity"
            ],
            ErrorCategory.FILE_SYSTEM: [
                "Check file permissions",
                "Verify disk space availability",
                "Try with a different file"
            ],
            ErrorCategory.EXTERNAL_SERVICE: [
                "Try again later",
                "Check service status",
                "Contact service provider"
            ]
        }
        
        return suggestions.get(category, ["Try again later", "Contact support if problem persists"])
    
    def _extract_technical_details(self, error: Exception) -> Dict[str, Any]:
        """Extract technical details from error."""
        details = {
            "error_class": type(error).__name__,
            "error_module": type(error).__module__,
        }
        
        # Add specific details based on error type
        if hasattr(error, 'status_code'):
            details['status_code'] = error.status_code
        
        if hasattr(error, 'response') and hasattr(error.response, 'text'):
            details['response_text'] = error.response.text[:1000]  # Limit length
        
        if hasattr(error, 'errno'):
            details['errno'] = error.errno
        
        if hasattr(error, 'filename'):
            details['filename'] = error.filename
        
        return details
    
    def _store_error(self, error_details: ErrorDetails):
        """Store error details in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO errors (
                        id, timestamp, error_type, message, category, severity,
                        user_message, technical_details, stack_trace, request_id,
                        user_id, endpoint, recovery_suggestions, retry_count, resolved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_details.error_id,
                    error_details.timestamp.isoformat(),
                    error_details.error_type,
                    error_details.message,
                    error_details.category.value,
                    error_details.severity.value,
                    error_details.user_message,
                    json.dumps(error_details.technical_details),
                    error_details.stack_trace,
                    error_details.request_id,
                    error_details.user_id,
                    error_details.endpoint,
                    json.dumps(error_details.recovery_suggestions),
                    error_details.retry_count,
                    error_details.resolved
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing error details: {e}")
    
    def _log_error(self, error_details: ErrorDetails):
        """Log error with appropriate level."""
        log_message = f"Error {error_details.error_id}: {error_details.message}"
        
        extra_data = {
            'error_id': error_details.error_id,
            'category': error_details.category.value,
            'severity': error_details.severity.value,
            'request_id': error_details.request_id,
            'user_id': error_details.user_id,
            'endpoint': error_details.endpoint
        }
        
        if error_details.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra=extra_data)
        elif error_details.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra=extra_data)
        elif error_details.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra=extra_data)
        else:
            logger.info(log_message, extra=extra_data)
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified period."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total errors
                cursor.execute("""
                    SELECT COUNT(*) FROM errors 
                    WHERE timestamp >= ?
                """, (since.isoformat(),))
                total_errors = cursor.fetchone()[0]
                
                # Errors by category
                cursor.execute("""
                    SELECT category, COUNT(*) FROM errors 
                    WHERE timestamp >= ? 
                    GROUP BY category
                """, (since.isoformat(),))
                by_category = dict(cursor.fetchall())
                
                # Errors by severity
                cursor.execute("""
                    SELECT severity, COUNT(*) FROM errors 
                    WHERE timestamp >= ? 
                    GROUP BY severity
                """, (since.isoformat(),))
                by_severity = dict(cursor.fetchall())
                
                # Most common errors
                cursor.execute("""
                    SELECT error_type, COUNT(*) as count FROM errors 
                    WHERE timestamp >= ? 
                    GROUP BY error_type 
                    ORDER BY count DESC 
                    LIMIT 10
                """, (since.isoformat(),))
                common_errors = cursor.fetchall()
                
                # Unresolved errors
                cursor.execute("""
                    SELECT COUNT(*) FROM errors 
                    WHERE timestamp >= ? AND resolved = FALSE
                """, (since.isoformat(),))
                unresolved_errors = cursor.fetchone()[0]
                
                return {
                    "total_errors": total_errors,
                    "unresolved_errors": unresolved_errors,
                    "by_category": by_category,
                    "by_severity": by_severity,
                    "common_errors": [{"type": err[0], "count": err[1]} for err in common_errors],
                    "period_hours": hours,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting error statistics: {e}")
            return {}
    
    def mark_error_resolved(self, error_id: str) -> bool:
        """Mark an error as resolved."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE errors SET resolved = TRUE 
                    WHERE id = ?
                """, (error_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marking error as resolved: {e}")
            return False

class GracefulDegradation:
    """Handle graceful degradation of services."""
    
    def __init__(self):
        self.degraded_services = set()
        self.fallback_handlers = {}
    
    def register_fallback(self, service_name: str, fallback_handler: Callable):
        """Register fallback handler for a service."""
        self.fallback_handlers[service_name] = fallback_handler
    
    def degrade_service(self, service_name: str):
        """Mark service as degraded."""
        self.degraded_services.add(service_name)
        logger.warning(f"Service {service_name} degraded")
    
    def restore_service(self, service_name: str):
        """Restore service from degraded state."""
        self.degraded_services.discard(service_name)
        logger.info(f"Service {service_name} restored")
    
    def is_degraded(self, service_name: str) -> bool:
        """Check if service is degraded."""
        return service_name in self.degraded_services
    
    def handle_with_fallback(self, service_name: str, primary_func: Callable, *args, **kwargs):
        """Execute function with fallback if service is degraded."""
        if not self.is_degraded(service_name):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary service {service_name} failed, using fallback: {e}")
                self.degrade_service(service_name)
        
        # Use fallback
        fallback_handler = self.fallback_handlers.get(service_name)
        if fallback_handler:
            return fallback_handler(*args, **kwargs)
        else:
            raise Exception(f"No fallback handler registered for {service_name}")

# Global error handler instance
error_handler = None
graceful_degradation = None

def initialize_error_handling(db_path: str = "data/errors.db") -> ErrorHandler:
    """Initialize error handling system."""
    global error_handler, graceful_degradation
    error_handler = ErrorHandler(db_path)
    graceful_degradation = GracefulDegradation()
    return error_handler

def get_error_handler() -> Optional[ErrorHandler]:
    """Get global error handler."""
    return error_handler

def get_graceful_degradation() -> Optional[GracefulDegradation]:
    """Get graceful degradation handler."""
    return graceful_degradation

# Decorator for automatic error handling
def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 custom_message: Optional[str] = None):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler:
                    error_details = error_handler.handle_error(
                        error=e,
                        category=category,
                        severity=severity,
                        custom_message=custom_message
                    )
                    # Return error response
                    return {
                        'success': False,
                        'error': error_details.user_message,
                        'error_id': error_details.error_id,
                        'suggestions': error_details.recovery_suggestions
                    }
                else:
                    # Fallback if error handler not initialized
                    logger.error(f"Error in {func.__name__}: {e}")
                    raise e
        
        return wrapper
    return decorator