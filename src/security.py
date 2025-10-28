#!/usr/bin/env python3
"""
Security module for the web server.
Provides rate limiting, input validation, CSRF protection, and more.
"""

import time
import hashlib
import secrets
import re
import os
import mimetypes
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import request, jsonify, session, abort
import logging

# Configure security logging
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('data/security.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class RateLimiter:
    """Advanced rate limiting with different tiers."""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}
        
        # Rate limit configurations
        self.limits = {
            'api': {'requests': 100, 'window': 60},      # 100 requests per minute for API
            'upload': {'requests': 10, 'window': 60},    # 10 uploads per minute
            'command': {'requests': 20, 'window': 60},   # 20 commands per minute
            'auth': {'requests': 5, 'window': 300},      # 5 auth attempts per 5 minutes
            'tunnel': {'requests': 5, 'window': 300},    # 5 tunnel operations per 5 minutes
        }
    
    def is_allowed(self, client_ip, endpoint_type='api'):
        """Check if request is allowed based on rate limits."""
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                security_logger.warning(f"Blocked IP {client_ip} attempted access")
                return False
            else:
                del self.blocked_ips[client_ip]
        
        # Get rate limit configuration
        config = self.limits.get(endpoint_type, self.limits['api'])
        window = config['window']
        max_requests = config['requests']
        
        # Clean old requests
        request_times = self.requests[f"{client_ip}:{endpoint_type}"]
        while request_times and current_time - request_times[0] > window:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= max_requests:
            # Block IP for escalating periods
            block_duration = min(300 * (2 ** len([k for k in self.blocked_ips.keys() if k == client_ip])), 3600)
            self.blocked_ips[client_ip] = current_time + block_duration
            security_logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint_type}, blocked for {block_duration}s")
            return False
        
        # Add current request
        request_times.append(current_time)
        return True
    
    def get_remaining_requests(self, client_ip, endpoint_type='api'):
        """Get remaining requests for the current window."""
        current_time = time.time()
        config = self.limits.get(endpoint_type, self.limits['api'])
        window = config['window']
        max_requests = config['requests']
        
        request_times = self.requests[f"{client_ip}:{endpoint_type}"]
        # Count valid requests in current window
        valid_requests = sum(1 for t in request_times if current_time - t <= window)
        return max(0, max_requests - valid_requests)

class InputValidator:
    """Comprehensive input validation and sanitization."""
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def is_safe_sql(query):
        """Check if SQL query is safe (basic check)."""
        if not query:
            return False
        
        # Basic SQL injection patterns
        dangerous_patterns = [
            r';.*drop\s+table',
            r';.*delete\s+from',
            r';.*update\s+.*set',
            r';.*insert\s+into',
            r'union\s+select',
            r'--',
            r'/\*.*\*/',
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower):
                return False
        
        return True
    
    @staticmethod
    def contains_xss(content):
        """Check if content contains XSS patterns."""
        if not content:
            return False
        
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe.*?>',
            r'<object.*?>',
            r'<embed.*?>',
        ]
        
        content_lower = content.lower()
        for pattern in xss_patterns:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    @staticmethod
    def sanitize_string(input_string, max_length=1000, allow_html=False):
        """Sanitize string input."""
        if not isinstance(input_string, str):
            return str(input_string)[:max_length]
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_string)
        
        if not allow_html:
            # Escape HTML characters
            sanitized = sanitized.replace('&', '&amp;')
            sanitized = sanitized.replace('<', '&lt;')
            sanitized = sanitized.replace('>', '&gt;')
            sanitized = sanitized.replace('"', '&quot;')
            sanitized = sanitized.replace("'", '&#x27;')
        
        return sanitized[:max_length]
    
    @staticmethod
    def validate_filename(filename):
        """Validate and sanitize filenames."""
        if not filename:
            return False, "Filename cannot be empty"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'\.\.', r'[\x00-\x1f]', r'[<>:"|?*]',
            r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
            r'^\.',  # Hidden files
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False, f"Invalid filename: contains forbidden pattern"
        
        # Check length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        return True, filename
    
    @staticmethod
    def validate_command(command):
        """Validate command execution requests."""
        if not command or not isinstance(command, str):
            return False, "Invalid command"
        
        # Remove excessive whitespace
        command = ' '.join(command.split())
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'rm\s+-rf\s*/',        # Dangerous rm commands
            r'dd\s+if=',            # dd commands
            r'mkfs\.',              # Filesystem creation
            r'fdisk',               # Disk partitioning
            r'format',              # Drive formatting
            r'del\s+/[qsf]',        # Windows dangerous delete
            r':\(\)\{.*\};:',       # Fork bomb
            r'>\s*/dev/',           # Writing to devices
            r'curl.*\|\s*sh',       # Piped shell execution
            r'wget.*\|\s*sh',       # Piped shell execution
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command blocked: potentially dangerous pattern detected"
        
        # Check command length
        if len(command) > 1000:
            return False, "Command too long (max 1000 characters)"
        
        return True, command
    
    @staticmethod
    def validate_file_upload(file_data, filename, allowed_types=None):
        """Validate file uploads for security."""
        if not file_data:
            return False, "No file data provided"
        
        # Check file size (100MB max)
        if len(file_data) > 100 * 1024 * 1024:
            return False, "File too large (max 100MB)"
        
        # Validate filename
        valid, result = InputValidator.validate_filename(filename)
        if not valid:
            return False, result
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Blocked MIME types (executables, scripts, etc.)
        blocked_types = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'application/x-shockwave-flash',
            'application/java-archive',
            'application/x-java-archive',
        ]
        
        if mime_type in blocked_types:
            return False, f"File type not allowed: {mime_type}"
        
        # Check for executable file extensions
        dangerous_extensions = [
            '.exe', '.com', '.scr', '.bat', '.cmd', '.pif',
            '.vbs', '.vbe', '.js', '.jse', '.ws', '.wsf',
            '.msi', '.msp', '.jar', '.app', '.deb', '.rpm'
        ]
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in dangerous_extensions:
            return False, f"File extension not allowed: {file_ext}"
        
        # Basic content scanning for known malicious patterns
        file_content = file_data[:1024].decode('utf-8', errors='ignore').lower()
        malicious_patterns = [
            'eval(', 'exec(', 'system(', 'shell_exec(',
            '<script', 'javascript:', 'vbscript:',
            'powershell', 'cmd.exe', '/bin/sh'
        ]
        
        for pattern in malicious_patterns:
            if pattern in file_content:
                security_logger.warning(f"Potentially malicious file upload blocked: {filename}")
                return False, "File content appears to be malicious"
        
        return True, "File validated successfully"

class CSRFProtection:
    """CSRF protection implementation."""
    
    @staticmethod
    def generate_token():
        """Generate a CSRF token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(provided_token, session_token):
        """Validate CSRF token."""
        if not provided_token or not session_token:
            return False
        return secrets.compare_digest(provided_token, session_token)

class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers():
        """Get recommended security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

class AuthenticationManager:
    """Simple authentication manager."""
    
    def __init__(self):
        self.sessions = {}
        self.users = self._load_users()
        self.failed_attempts = defaultdict(list)
    
    def _load_users(self):
        """Load user credentials from file."""
        users_file = 'data/users.json'
        if os.path.exists(users_file):
            import json
            try:
                with open(users_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default admin user (change this!)
        default_users = {
            'admin': {
                'password_hash': self._hash_password('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }
        }
        
        # Save default users
        os.makedirs('data', exist_ok=True)
        with open(users_file, 'w') as f:
            import json
            json.dump(default_users, f, indent=2)
        
        return default_users
    
    def _hash_password(self, password):
        """Hash a password securely."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def create_user(self, username, password, role='user'):
        """Create a new user."""
        if username in self.users:
            return False  # User already exists
        
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        # Save users to file
        users_file = 'data/users.json'
        os.makedirs('data', exist_ok=True)
        with open(users_file, 'w') as f:
            import json
            json.dump(self.users, f, indent=2)
        
        return True
    
    def verify_password(self, username, password):
        """Verify user password."""
        if username not in self.users:
            return False
        
        stored_hash = self.users[username]['password_hash']
        return self._verify_password_hash(password, stored_hash)
    
    def _verify_password_hash(self, password, password_hash):
        """Verify a password against its hash."""
        try:
            salt, hash_hex = password_hash.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hash_hex
        except:
            return False
    
    def authenticate(self, username, password, client_ip):
        """Authenticate a user."""
        current_time = time.time()
        
        # Check for too many failed attempts
        recent_attempts = [t for t in self.failed_attempts[client_ip] if current_time - t < 300]
        if len(recent_attempts) >= 5:
            security_logger.warning(f"Too many failed login attempts from {client_ip}")
            return False, "Too many failed attempts. Try again later."
        
        # Validate credentials
        if username not in self.users:
            self.failed_attempts[client_ip].append(current_time)
            return False, "Invalid credentials"
        
        user = self.users[username]
        if not self.verify_password(password, user['password_hash']):
            self.failed_attempts[client_ip].append(current_time)
            return False, "Invalid credentials"
        
        # Clear failed attempts on successful login
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'username': username,
            'role': user['role'],
            'created_at': current_time,
            'last_activity': current_time,
            'client_ip': client_ip
        }
        
        security_logger.info(f"User {username} logged in from {client_ip}")
        return True, session_id
    
    def validate_session(self, session_id, client_ip):
        """Validate a session."""
        if not session_id or session_id not in self.sessions:
            return False, None
        
        session_data = self.sessions[session_id]
        current_time = time.time()
        
        # Check session timeout (24 hours)
        if current_time - session_data['created_at'] > 86400:
            del self.sessions[session_id]
            return False, None
        
        # Check inactivity timeout (2 hours)
        if current_time - session_data['last_activity'] > 7200:
            del self.sessions[session_id]
            return False, None
        
        # Validate IP (optional, can be disabled for mobile users)
        if session_data['client_ip'] != client_ip:
            security_logger.warning(f"Session IP mismatch for user {session_data['username']}")
            # Don't immediately invalidate - log for monitoring
        
        # Update last activity
        session_data['last_activity'] = current_time
        return True, session_data
    
    def logout(self, session_id):
        """Logout and invalidate session."""
        if session_id in self.sessions:
            username = self.sessions[session_id]['username']
            del self.sessions[session_id]
            security_logger.info(f"User {username} logged out")
            return True
        return False

# Global instances
rate_limiter = RateLimiter()
auth_manager = AuthenticationManager()

def require_rate_limit(endpoint_type='api'):
    """Decorator for rate limiting endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if not rate_limiter.is_allowed(client_ip, endpoint_type):
                security_logger.warning(f"Rate limit exceeded for {client_ip} on {f.__name__}")
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': 60
                }), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_auth(role=None):
    """Decorator requiring authentication."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_id = request.headers.get('X-Session-ID') or request.cookies.get('session_id')
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            valid, session_data = auth_manager.validate_session(session_id, client_ip)
            if not valid:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            
            if role and session_data['role'] != role:
                return jsonify({
                    'success': False,
                    'error': 'Insufficient permissions'
                }), 403
            
            # Add user info to request context
            request.user = session_data
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_csrf():
    """Decorator for CSRF protection."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE']:
                provided_token = request.headers.get('X-CSRF-Token')
                session_token = session.get('csrf_token')
                
                if not CSRFProtection.validate_token(provided_token, session_token):
                    security_logger.warning(f"CSRF token validation failed for {request.remote_addr}")
                    return jsonify({
                        'success': False,
                        'error': 'CSRF token validation failed'
                    }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def apply_security_headers():
    """Apply security headers to response."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Apply security headers
            for header, value in SecurityHeaders.get_security_headers().items():
                response.headers[header] = value
            
            return response
        return decorated_function
    return decorator