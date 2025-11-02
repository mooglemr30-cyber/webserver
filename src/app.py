#!/usr/bin/env python3
"""
Flask web server for localhost data storage and command execution.
"""

from flask import Flask, request, jsonify, render_template, send_file, g
from pydantic import BaseModel, ValidationError, Field
from typing import Optional
from flask_cors import CORS
import json
import os
import subprocess
import sys
import threading
import time
import requests
import zipfile
from datetime import datetime

# Handle both direct execution and module import
if __name__ == '__main__':
    from data_store import DataStore
    from file_store import FileStore
    from program_store import ProgramStore
else:
    from .data_store import DataStore
    from .file_store import FileStore
    from .program_store import ProgramStore

from werkzeug.utils import secure_filename
import io
import pexpect
import uuid
import threading
import logging
import signal
import psutil
import socket
from collections import deque
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Handle both direct execution and module import
if __name__ == '__main__':
    from performance import CacheManager
    from auth_system import AuthenticationManager, create_auth_decorators
    from privileged_execution import get_privileged_system, MIN_TIMEOUT, MAX_TIMEOUT
    from tunnel_manager import PersistentTunnelManager
else:
    from .performance import CacheManager
    from .auth_system import AuthenticationManager, create_auth_decorators
    from .privileged_execution import get_privileged_system, MIN_TIMEOUT, MAX_TIMEOUT
    from .tunnel_manager import PersistentTunnelManager

# Monitoring temporarily disabled - causing blocking issues
# from monitoring import initialize_monitoring, get_monitoring_manager

# Initialize Flask App
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)  # Enable CORS for all routes

from path_config import PATHS  # centralized paths
from document_scanner import DocumentScanner

# Initialize authentication manager using centralized path
_users_file = os.path.join(PATHS['data'], 'users.json')
auth_manager = AuthenticationManager(
    secret_key=app.config['SECRET_KEY'],
    users_file=_users_file
)

# Create authentication decorators
login_required, role_required, admin_required = create_auth_decorators(auth_manager)

# Initialize data store, file store, and program store
data_store = DataStore()
file_store = FileStore()
program_store = ProgramStore()

# Log key paths once at startup (stdout) for diagnostics
print(json.dumps({'event': 'path-config', 'paths': {k: v for k, v in PATHS.items()}}, ensure_ascii=False))
cache = CacheManager(use_redis=False)

# Initialize persistent tunnel manager for mobile access
persistent_tunnel = PersistentTunnelManager()
scanner = DocumentScanner()
_scan_lock = threading.Lock()
_last_scan_report = None

# Global variables to store tunnel info
tunnel_info = {
    'ngrok': {
        'public_url': None,
        'process': None,
        'status': 'stopped'
    },
    'localtunnel': {
        'public_url': None,
        'process': None,
        'status': 'stopped'
    },
    'cloudflared': {
        'public_url': None,
        'process': None,
        'status': 'stopped'
    }
}

# Interactive command sessions storage
interactive_sessions = {}
session_lock = threading.Lock()

# Persistent terminal sessions storage
terminal_sessions = {}
terminal_session_lock = threading.Lock()

# Voice chat rooms storage
voice_chat_rooms = {}
voice_chat_lock = threading.Lock()

# ---------------------------
# Request ID + Metrics
# ---------------------------

REQUEST_COUNTER = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_latency_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

def _endpoint_label():
    # Use rule or path as a stable-ish label
    try:
        return request.url_rule.rule if request.url_rule else request.path
    except Exception:
        return request.path

@app.before_request
def _request_context_start():
    # Request ID
    g.request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
    # Timer
    g._start_time = time.perf_counter()
    # Monitoring init disabled for now - causing blocking issues
    # Will be re-enabled after debugging
    pass

@app.after_request
def _request_context_finish(resp):
    # Echo request id
    try:
        resp.headers['X-Request-ID'] = getattr(g, 'request_id', '')
    except Exception:
        pass
    # Metrics
    try:
        elapsed = max(0.0, time.perf_counter() - getattr(g, '_start_time', time.perf_counter()))
        endpoint = _endpoint_label()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(elapsed)
        REQUEST_COUNTER.labels(request.method, endpoint, str(resp.status_code)).inc()
    except Exception:
        pass
    return resp

@app.get('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# ---------------------------
# Structured response + logging (v1)
# ---------------------------

logger = logging.getLogger("request")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# In-memory recent request history (for dashboard)
REQUEST_HISTORY = deque(maxlen=200)

# Initialize monitoring lazily on first request to avoid Flask reloader double-start
_monitoring_initialized = False

def api_ok(data=None, **extra):
    return jsonify({
        'success': True,
        'data': data or {},
        'request_id': getattr(g, 'request_id', ''),
        'timestamp': datetime.now().isoformat(),
        **extra
    })

def api_error(message, status=400, **extra):
    return jsonify({
        'success': False,
        'error': message,
        'request_id': getattr(g, 'request_id', ''),
        'timestamp': datetime.now().isoformat(),
        **extra
    }), status

@app.after_request
def _structured_log(resp):
    try:
        log = {
            'request_id': getattr(g, 'request_id', ''),
            'method': request.method,
            'path': request.path,
            'status': resp.status_code,
            'latency_ms': int(1000 * max(0.0, time.perf_counter() - getattr(g, '_start_time', time.perf_counter()))),
            'timestamp': datetime.now().isoformat()
        }
        logger.info(json.dumps(log))
        # Also keep a short in-memory history for dashboard
        REQUEST_HISTORY.append(log)
        # Monitoring storage disabled for now - causing blocking issues
    except Exception:
        pass
    return resp

# ---------------------------
# API v1: health and programs list
# ---------------------------

@app.get('/api/v1/health')
def v1_health():
    return api_ok({'status': 'healthy'})

# ---------------------------
# AI Document Scan Endpoints
# ---------------------------

@app.post('/api/ai/scan')
def ai_scan():
    """Trigger a document scan of agent storage.
    Optional JSON body: {"max_files": 100}
    """
    global _last_scan_report
    try:
        payload = request.get_json(silent=True) or {}
        max_files = payload.get('max_files')
        with _scan_lock:
            if max_files:
                scanner.max_files = int(max_files)
            report = scanner.scan()
            _last_scan_report = report
        return api_ok({'scan_report': report, 'summary': report.get('summary')})
    except Exception as e:
        return api_error(f'Scan failed: {e}', 500)

@app.get('/api/ai/scan/status')
def ai_scan_status():
    try:
        return api_ok({'last_report': _last_scan_report, 'configured_base': PATHS.get('agent_storage')})
    except Exception as e:
        return api_error(f'Status failed: {e}', 500)

@app.post('/api/ai/scan/full')
def ai_scan_full():
    """Perform a full multi-root scan: AIAGENTSTORAGE + project base + data dir.
    Optional JSON body: {"max_files": 500}
    """
    global _last_scan_report
    try:
        payload = request.get_json(silent=True) or {}
        max_files = payload.get('max_files')
        with _scan_lock:
            if max_files:
                scanner.max_files = int(max_files)
            roots = [PATHS.get('agent_storage'), PATHS.get('base'), PATHS.get('data')]
            report = scanner.scan_multi(roots)
            _last_scan_report = report
        return api_ok({'scan_report': report, 'summary': report.get('summary')})
    except Exception as e:
        return api_error(f'Full scan failed: {e}', 500)

# ---------------------------
# Authentication Endpoints
# ---------------------------

@app.post('/api/auth/register')
def auth_register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return api_error('Missing required fields: username, email, password', 400)
        
        success, message, user = auth_manager.register_user(username, email, password)
        
        if not success:
            return api_error(message, 400)
        
        return api_ok({
            'message': message,
            'user': user.to_dict()
        })
    
    except Exception as e:
        return api_error(f'Registration failed: {str(e)}', 500)


@app.post('/api/auth/login')
def auth_login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return api_error('Missing username or password', 400)
        
        success, message, user = auth_manager.authenticate_user(username, password)
        
        if not success:
            return api_error(message, 401)
        
        # Generate token
        token = auth_manager.generate_token(user)
        
        return api_ok({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict(),
            'expires_in': 24 * 3600  # 24 hours in seconds
        })
    
    except Exception as e:
        return api_error(f'Login failed: {str(e)}', 500)


@app.post('/api/auth/logout')
@login_required
def auth_logout():
    """Logout user (revoke token)"""
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            auth_manager.revoke_token(token)
        
        return api_ok({'message': 'Logged out successfully'})
    
    except Exception as e:
        return api_error(f'Logout failed: {str(e)}', 500)


@app.get('/api/auth/me')
@login_required
def auth_me():
    """Get current user information"""
    try:
        user = g.current_user
        return api_ok({
            'user': user.to_dict()
        })
    
    except Exception as e:
        return api_error(f'Failed to get user info: {str(e)}', 500)


@app.get('/api/auth/users')
@admin_required
def auth_list_users():
    """List all users (admin only)"""
    try:
        users = auth_manager.list_users(include_inactive=True)
        return api_ok({
            'users': [u.to_dict() for u in users],
            'total': len(users)
        })
    
    except Exception as e:
        return api_error(f'Failed to list users: {str(e)}', 500)


@app.put('/api/auth/users/<user_id>')
@admin_required
def auth_update_user(user_id: str):
    """Update user (admin only)"""
    try:
        data = request.get_json()
        
        success, message = auth_manager.update_user(user_id, **data)
        
        if not success:
            return api_error(message, 404)
        
        user = auth_manager.get_user(user_id)
        return api_ok({
            'message': message,
            'user': user.to_dict()
        })
    
    except Exception as e:
        return api_error(f'Failed to update user: {str(e)}', 500)


@app.delete('/api/auth/users/<user_id>')
@admin_required
def auth_delete_user(user_id: str):
    """Delete user (admin only)"""
    try:
        success, message = auth_manager.delete_user(user_id)
        
        if not success:
            return api_error(message, 404)
        
        return api_ok({'message': message})
    
    except Exception as e:
        return api_error(f'Failed to delete user: {str(e)}', 500)


@app.post('/api/auth/change-password')
@login_required
def auth_change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return api_error('Missing old_password or new_password', 400)
        
        # Verify old password
        user = g.current_user
        if not auth_manager.verify_password(old_password, user.password_hash):
            return api_error('Invalid old password', 401)
        
        # Update password
        success, message = auth_manager.update_user(g.user_id, password=new_password)
        
        if not success:
            return api_error(message, 500)
        
        return api_ok({'message': 'Password changed successfully'})
    
    except Exception as e:
        return api_error(f'Failed to change password: {str(e)}', 500)


class ListQuery(BaseModel):
    page: Optional[int] = Field(default=None, ge=1)
    limit: Optional[int] = Field(default=None, ge=1, le=1000)

@app.get('/api/v1/programs/list')
def v1_list_programs():
    try:
        # Validate query
        try:
            q = ListQuery(page=request.args.get('page'), limit=request.args.get('limit'))
        except ValidationError as ve:
            return api_error('Invalid query parameters', 400, details=ve.errors())

        page = int(q.page) if q.page else None
        limit = int(q.limit) if q.limit else None
        cache_key = f"v1:programs:list:page={page or 'all'}:limit={limit or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return api_ok(cached)

        programs = program_store.get_program_list()
        storage_info = program_store.get_storage_info()
        total = len(programs)
        if page and limit:
            start = max(0, (page - 1) * limit)
            end = start + limit
            items = programs[start:end]
        else:
            items = programs
            start = 0
            end = total

        data = {
            'programs': items,
            'storage': storage_info,
            'pagination': {
                'page': page or 1,
                'limit': limit or total,
                'total': total,
                'has_next': bool(page and limit and (end < total)),
            }
        }
        cache.set(cache_key, data, ttl=2)
        return api_ok(data)
    except Exception as e:
        return api_error(str(e), 500)

# ---------------------------
# Dashboard API and Page
# ---------------------------

@app.get('/api/v1/dashboard')
def api_dashboard():
        try:
                storage = program_store.get_storage_info()
                programs = program_store.get_program_list()

                # Sort recent by upload_time if present
                def _ts(p):
                        return p.get('upload_time') or p.get('created_at') or ''
                recent_programs = sorted(programs, key=_ts, reverse=True)[:10]

                # Recent requests from in-memory (monitoring disabled temporarily)
                recent_requests = list(REQUEST_HISTORY)[-50:]
                endpoint_breakdown = []
                system = {}
                history = {}

                data = {
                        'storage': storage,
                        'totals': {
                                'programs': storage.get('total_programs', len(programs)),
                                'projects': storage.get('total_projects', 0),
                                'files': storage.get('total_files', 0),
                                'size_bytes': storage.get('total_size', 0),
                        },
                        'recent_programs': recent_programs,
                        'recent_requests': recent_requests,
                        'endpoint_breakdown': endpoint_breakdown,
                        'system_metrics': system,
                        'system_history': history,
                        'server_time': datetime.now().isoformat(),
                }
                return api_ok(data)
        except Exception as e:
                return api_error(str(e), 500)

@app.get("/dashboard")
def dashboard():
    """Serves the dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/v1/dashboard', methods=['GET'])
def dashboard_api():
    """API endpoint for dashboard data."""
    try:
        import psutil
        import os
        
        # Get program storage info
        storage_info = program_store.get_storage_info()
        
        # Get recent programs (last 10)
        all_programs = program_store.get_program_list()
        recent_programs = sorted(
            all_programs,
            key=lambda x: x.get('upload_time', ''),
            reverse=True
        )[:10]
        
        # System metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids()),
            'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
        }
        
        # Get monitoring data if available
        endpoint_breakdown = []
        recent_requests = []
        try:
            # Try to get monitoring data from the monitoring module if it's initialized
            from monitoring import get_monitoring_manager
            
            monitor = get_monitoring_manager()
            if monitor and monitor.storage:
                # Get endpoint breakdown from the database
                endpoint_breakdown = monitor.storage.get_endpoint_breakdown(hours=1, limit=10)
                
                # Get recent requests from the database
                recent_requests = monitor.storage.get_recent_requests(limit=20)
        except Exception as e:
            # Monitoring not available or not initialized
            pass
        
        dashboard_data = {
            'success': True,
            'data': {
                'server_time': datetime.now().isoformat(),
                'totals': {
                    'programs': storage_info.get('total_programs', 0),
                    'projects': storage_info.get('total_projects', 0),
                    'files': storage_info.get('total_files', 0),
                    'size_bytes': storage_info.get('total_size', 0)
                },
                'storage': storage_info,
                'recent_programs': recent_programs,
                'system_metrics': system_metrics,
                'endpoint_breakdown': endpoint_breakdown,
                'recent_requests': recent_requests
            }
        }
        
        return jsonify(dashboard_data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# API route to get all data from the store
@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Get all stored data."""
    try:
        data = data_store.get_all()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data', methods=['POST'])
def store_data():
    """Store new data - accepts string or JSON, stores as JSON."""
    try:
        request_data = request.get_json()
        if not request_data or 'key' not in request_data:
            return jsonify({
                'success': False,
                'error': 'Key is required'
            }), 400
        
        key = request_data['key']
        raw_value = request_data.get('value', '')
        
        # Try to parse as JSON if it's a string, otherwise use as-is
        if isinstance(raw_value, str):
            try:
                # Try parsing as JSON
                value = json.loads(raw_value)
            except json.JSONDecodeError:
                # If not valid JSON, store as a string value
                value = raw_value
        else:
            value = raw_value
        
        data_store.set(key, value)
        
        return jsonify({
            'success': True,
            'message': f'Data stored for key: {key}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/<key>', methods=['GET'])
def get_data(key):
    """Get data by key - returns as formatted string."""
    try:
        value = data_store.get(key)
        if value is None:
            return jsonify({
                'success': False,
                'error': f'Key "{key}" not found'
            }), 404
        
        # Convert value to string representation
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)
        
        return jsonify({
            'success': True,
            'key': key,
            'value': value,  # Original value for programmatic use
            'value_string': value_str,  # String representation for display
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/<key>', methods=['DELETE'])
def delete_data(key):
    """Delete data by key."""
    try:
        success = data_store.delete(key)
        if not success:
            return jsonify({
                'success': False,
                'error': f'Key "{key}" not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': f'Data deleted for key: {key}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def execute_interactive_command(command, sudo_password=None):
    """Execute a command that may require interactive input."""
    try:
        # Create new session
        session_id = str(uuid.uuid4())
        
        # Prepare command
        full_command = f"sudo {command}" if sudo_password else command
        
        # Set environment to disable colors
        env = {
            'TERM': 'dumb',
            'NO_COLOR': '1',
            'FORCE_COLOR': '0',
            'COLORTERM': '',
            'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        }
        
        # Start the command with pexpect
        child = pexpect.spawn(full_command, timeout=60, encoding='utf-8', env=env)
        
        # Store session
        with session_lock:
            interactive_sessions[session_id] = {
                'child': child,
                'command': full_command,
                'sudo_password': sudo_password,
                'password_sent': False,
                'output_buffer': ''
            }
        
        # Handle initial password prompt for sudo
        if sudo_password:
            try:
                index = child.expect(['.*password.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
                if index == 0:  # Password prompt
                    child.sendline(sudo_password)
                    interactive_sessions[session_id]['password_sent'] = True
                elif index == 1:  # Command finished immediately
                    output = child.before
                    if hasattr(child, 'after') and child.after:
                        output += str(child.after)
                    exit_code = child.exitstatus if child.exitstatus is not None else 0
                    
                    # Clean up session
                    with session_lock:
                        if session_id in interactive_sessions:
                            del interactive_sessions[session_id]
                    
                    return jsonify({
                        'success': True,
                        'command': full_command,
                        'stdout': clean_output(output),
                        'stderr': '',
                        'return_code': exit_code,
                        'completed': True,
                        'timestamp': datetime.now().isoformat()
                    })
            except pexpect.TIMEOUT:
                pass  # Continue to check for other prompts
        
        # Check if command is waiting for input
        try:
            index = child.expect([r'.*[yY]/[nN].*', r'.*\(y/n\).*', r'.*\[Y/n\].*', r'.*\[y/N\].*', 
                                 r'.*Enter.*', r'.*Continue.*', r'.*Press.*', r'.*confirm.*',
                                 pexpect.EOF, pexpect.TIMEOUT], timeout=2)
            
            if index < 8:  # One of the interactive prompts
                output = child.before
                if output:
                    interactive_sessions[session_id]['output_buffer'] = clean_output(output)
                
                return jsonify({
                    'success': True,
                    'command': full_command,
                    'stdout': interactive_sessions[session_id]['output_buffer'],
                    'waiting_for_input': True,
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            elif index == 8:  # EOF - command completed
                output = child.before
                if hasattr(child, 'after') and child.after:
                    output += str(child.after)
                exit_code = child.exitstatus if child.exitstatus is not None else 0
                
                # Clean up session
                with session_lock:
                    if session_id in interactive_sessions:
                        del interactive_sessions[session_id]
                
                return jsonify({
                    'success': True,
                    'command': full_command,
                    'stdout': clean_output(output),
                    'stderr': '',
                    'return_code': exit_code,
                    'completed': True,
                    'timestamp': datetime.now().isoformat()
                })
        
        except pexpect.TIMEOUT:
            # Command might still be running, treat as interactive
            output = child.before if hasattr(child, 'before') else ''
            if output:
                interactive_sessions[session_id]['output_buffer'] = clean_output(output)
            
            return jsonify({
                'success': True,
                'command': full_command,
                'stdout': interactive_sessions[session_id]['output_buffer'],
                'waiting_for_input': True,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            # Clean up session on error
            with session_lock:
                if session_id in interactive_sessions:
                    try:
                        interactive_sessions[session_id]['child'].close(force=True)
                    except:
                        pass
                    del interactive_sessions[session_id]
            
            return jsonify({
                'success': False,
                'error': f'Interactive command failed: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start interactive command: {str(e)}'
        }), 500

def clean_output(output):
    """Clean command output by removing ANSI codes and password prompts."""
    if not output:
        return ""
    
    import re
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    output = ansi_escape.sub('', output)
    
    lines = output.split('\n')
    # Only remove password prompt lines, preserve all other content including empty lines
    filtered_lines = []
    for line in lines:
        # Only skip password prompts, keep everything else including empty lines
        if not any(keyword in line.lower() for keyword in ['password for', '[sudo]', 'sorry, try again']):
            filtered_lines.append(line.rstrip())  # Only strip trailing whitespace
    
    # Remove leading/trailing empty lines but preserve internal structure
    while filtered_lines and not filtered_lines[0].strip():
        filtered_lines.pop(0)
    while filtered_lines and not filtered_lines[-1].strip():
        filtered_lines.pop()
        
    return '\n'.join(filtered_lines)

# Persistent Terminal Session Endpoints
@app.route('/api/terminal/create', methods=['POST'])
def create_terminal_session():
    """Create a new persistent terminal session with bash."""
    try:
        session_id = str(uuid.uuid4())
        
        # Start a bash shell in the user's home directory or current directory
        initial_dir = os.path.expanduser('~')
        if os.path.exists('/home/tom/Documents/webserver'):
            initial_dir = '/home/tom/Documents/webserver'
        
        # Spawn bash shell with proper environment
        env = dict(os.environ)
        env.update({
            'PS1': '$ ',  # Simple prompt
            'TERM': 'xterm-256color',
            'COLUMNS': '120',
            'LINES': '30'
        })
        
        child = pexpect.spawn(
            '/bin/bash',
            ['--norc', '--noprofile'],
            cwd=initial_dir,
            env=env,
            encoding='utf-8',
            dimensions=(30, 120)
        )
        
        # Wait for initial prompt
        child.expect(['\\$', '#', '>', pexpect.TIMEOUT], timeout=2)
        
        # Store session
        with terminal_session_lock:
            terminal_sessions[session_id] = {
                'child': child,
                'cwd': initial_dir,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'cwd': initial_dir,
            'message': 'Terminal session created',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create terminal session: {str(e)}'
        }), 500

@app.route('/api/terminal/execute/<session_id>', methods=['POST'])
def execute_in_terminal_session(session_id):
    """Execute a command in a persistent terminal session."""
    try:
        request_data = request.get_json()
        if not request_data or 'command' not in request_data:
            return jsonify({
                'success': False,
                'error': 'Command is required'
            }), 400
        
        command = request_data['command']
        
        with terminal_session_lock:
            if session_id not in terminal_sessions:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired session. Please create a new session.'
                }), 404
            
            session = terminal_sessions[session_id]
            child = session['child']
            
            # Update last activity
            session['last_activity'] = datetime.now().isoformat()
        
        # Send command
        child.sendline(command)
        
        # Wait for prompt to return
        try:
            child.expect(['\\$', '#', '>', pexpect.TIMEOUT], timeout=30)
            output = child.before
            
            # Clean output - remove ANSI codes
            if output:
                import re
                # Remove ANSI escape sequences
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                output = ansi_escape.sub('', output)
                
                # Remove the command echo
                lines = output.split('\n')
                if lines and command in lines[0]:
                    lines = lines[1:]
                output = '\n'.join(lines).strip()
            
            # Try to get current working directory
            child.sendline('pwd')
            child.expect(['\\$', '#', '>', pexpect.TIMEOUT], timeout=2)
            pwd_output = child.before
            
            # Extract directory - clean ANSI codes first
            cwd = session['cwd']
            if pwd_output:
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                pwd_output = ansi_escape.sub('', pwd_output)
                
                # Remove carriage returns and clean up
                pwd_output = pwd_output.replace('\r', '')
                pwd_lines = [line.strip() for line in pwd_output.split('\n') if line.strip()]
                
                # The directory should be in the lines after 'pwd' command
                for line in pwd_lines:
                    if line != 'pwd' and line.startswith('/'):
                        cwd = line
                        session['cwd'] = cwd
                        break
            
            return jsonify({
                'success': True,
                'output': output,
                'cwd': cwd,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except pexpect.TIMEOUT:
            # Command still running or hanging
            return jsonify({
                'success': False,
                'error': 'Command timed out after 30 seconds',
                'output': child.before if hasattr(child, 'before') else '',
                'cwd': session['cwd']
            }), 408
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Command execution failed: {str(e)}'
        }), 500

@app.route('/api/terminal/close/<session_id>', methods=['POST'])
def close_terminal_session(session_id):
    """Close a terminal session."""
    try:
        with terminal_session_lock:
            if session_id not in terminal_sessions:
                return jsonify({
                    'success': False,
                    'error': 'Invalid session'
                }), 404
            
            session = terminal_sessions[session_id]
            try:
                session['child'].sendline('exit')
                session['child'].close(force=True)
            except:
                pass
            
            del terminal_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': 'Terminal session closed',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/terminal/list', methods=['GET'])
def list_terminal_sessions():
    """List all active terminal sessions."""
    try:
        with terminal_session_lock:
            sessions = []
            for sid, session in terminal_sessions.items():
                sessions.append({
                    'session_id': sid,
                    'cwd': session['cwd'],
                    'created_at': session['created_at'],
                    'last_activity': session['last_activity']
                })
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Programs Terminal - Persistent session in programs directory
programs_terminal_session = None

@app.route('/api/programs-terminal/init', methods=['POST'])
def init_programs_terminal():
    """Initialize a persistent terminal session in the programs directory."""
    global programs_terminal_session
    
    try:
        import pexpect
        import uuid
        
        # Get programs directory path
        programs_dir = os.path.abspath(program_store.programs_dir)
        
        # Close existing session if any
        if programs_terminal_session and programs_terminal_session.get('process'):
            try:
                programs_terminal_session['process'].terminate(force=True)
            except:
                pass
        
        # Create new bash session
        session_id = str(uuid.uuid4())
        bash_process = pexpect.spawn(
            'bash',
            ['--norc', '--noprofile'],
            encoding='utf-8',
            timeout=30,
            cwd=programs_dir,
            env={**os.environ, 'TERM': 'dumb'}  # Use dumb terminal to avoid control sequences
        )
        
        # Disable readline features that add control sequences
        bash_process.sendline('set +o emacs')
        bash_process.sendline('set +o vi')
        bash_process.sendline('stty -echo')  # Disable echo
        
        # Set simple prompt
        bash_process.sendline('export PS1="\\n"')
        
        # Wait a moment for initialization
        time.sleep(0.2)
        
        # Clear any initial output
        try:
            bash_process.read_nonblocking(size=10000, timeout=0.1)
        except:
            pass
        
        # Store session
        programs_terminal_session = {
            'session_id': session_id,
            'process': bash_process,
            'cwd': programs_dir,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'working_dir': programs_dir,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to initialize programs terminal: {str(e)}'
        }), 500

@app.route('/api/programs-terminal/execute', methods=['POST'])
def execute_programs_terminal():
    """Execute a command in the programs terminal session."""
    global programs_terminal_session
    
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({
                'success': False,
                'error': 'No command provided'
            }), 400
        
        if not programs_terminal_session or programs_terminal_session.get('session_id') != session_id:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired session. Please refresh the page.'
            }), 400
        
        bash = programs_terminal_session['process']
        
        # Send command and newline
        bash.sendline(command)
        
        # Wait for command to complete (look for new prompt which is just a newline)
        time.sleep(0.5)  # Give command time to execute
        
        # Read all available output
        try:
            output = bash.read_nonblocking(size=100000, timeout=30)
            # Clean up output - remove the command echo and extra newlines
            lines = output.split('\n')
            # Remove first line (command echo) and last line (empty prompt)
            if len(lines) > 0 and command in lines[0]:
                lines = lines[1:]
            if len(lines) > 0 and not lines[-1].strip():
                lines = lines[:-1]
            output = '\n'.join(lines)
        except pexpect.TIMEOUT:
            output = ""
        except pexpect.EOF:
            return jsonify({
                'success': False,
                'error': 'Terminal session ended unexpectedly'
            }), 500
        
        # Update last activity
        programs_terminal_session['last_activity'] = datetime.now().isoformat()
        
        # Get current working directory
        bash.sendline('pwd')
        time.sleep(0.1)
        try:
            pwd_output = bash.read_nonblocking(size=1000, timeout=1)
            lines = pwd_output.split('\n')
            # Find the line with the path (should be second line after pwd command)
            current_dir = programs_terminal_session['cwd']
            for line in lines:
                line = line.strip()
                if line and line.startswith('/'):
                    current_dir = line
                    break
            programs_terminal_session['cwd'] = current_dir
        except:
            current_dir = programs_terminal_session['cwd']
        
        return jsonify({
            'success': True,
            'output': output,
            'working_dir': current_dir,
            'timestamp': datetime.now().isoformat()
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution failed: {str(e)}'
        }), 500

@app.route('/api/programs-terminal/close', methods=['POST'])
def close_programs_terminal():
    """Close the persistent terminal session in the programs directory."""
    global programs_terminal_session

    try:
        if programs_terminal_session and programs_terminal_session.get('process'):
            try:
                programs_terminal_session['process'].sendline('exit')
                programs_terminal_session['process'].close(force=True)
            except:
                pass

            programs_terminal_session = None

        return jsonify({
            'success': True,
            'message': 'Programs terminal session closed',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# AI Agent Execution Endpoints
@app.route('/api/ai-agent/execute', methods=['POST'])
def ai_agent_execute():
    """Execute a command as an AI agent."""
    try:
        data = request.get_json()
        command = data.get('command')
        agent_id = data.get('agent_id', 'unknown')
        timeout = data.get('timeout', 300)
        working_dir = data.get('working_dir')

        if not command:
            return api_error('Missing command field', 400)

        # For now, just log and echo the command back
        print(f"Executing as AI agent ({agent_id}): {command}")

        return api_ok({
            'message': 'Command executed',
            'command': command,
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return api_error(f'Execution failed: {str(e)}', 500)

# ---------------------------
# API v2: health and programs list
# ---------------------------

@app.get('/api/v2/health')
def v2_health():
    return api_ok({'status': 'healthy'})

@app.get('/api/v2/programs/list')
def v2_list_programs():
    try:
        # Validate query
        try:
            q = ListQuery(page=request.args.get('page'), limit=request.args.get('limit'))
        except ValidationError as ve:
            return api_error('Invalid query parameters', 400, details=ve.errors())

        page = int(q.page) if q.page else None
        limit = int(q.limit) if q.limit else None
        cache_key = f"v2:programs:list:page={page or 'all'}:limit={limit or 'all'}"
        cached = cache.get(cache_key)
        if cached:
            return api_ok(cached)

        programs = program_store.get_program_list()
        storage_info = program_store.get_storage_info()
        total = len(programs)
        if page and limit:
            start = max(0, (page - 1) * limit)
            end = start + limit
            items = programs[start:end]
        else:
            items = programs
            start = 0
            end = total

        data = {
            'programs': items,
            'storage': storage_info,
            'pagination': {
                'page': page or 1,
                'limit': limit or total,
                'total': total,
                'has_next': bool(page and limit and (end < total)),
            }
        }
        cache.set(cache_key, data, ttl=2)
        return api_ok(data)
    except Exception as e:
        return api_error(str(e), 500)

# ---------------------------
# Dashboard API and Page
# ---------------------------

@app.get('/api/v2/dashboard')
def v2_dashboard():
        try:
                storage = program_store.get_storage_info()
                programs = program_store.get_program_list()

                # Sort recent by upload_time if present
                def _ts(p):
                        return p.get('upload_time') or p.get('created_at') or ''
                recent_programs = sorted(programs, key=_ts, reverse=True)[:10]

                # Recent requests from in-memory (monitoring disabled temporarily)
                recent_requests = list(REQUEST_HISTORY)[-50:]
                endpoint_breakdown = []
                system = {}
                history = {}

                data = {
                        'storage': storage,
                        'totals': {
                                'programs': storage.get('total_programs', len(programs)),
                                'projects': storage.get('total_projects', 0),
                                'files': storage.get('total_files', 0),
                                'size_bytes': storage.get('total_size', 0),
                        },
                        'recent_programs': recent_programs,
                        'recent_requests': recent_requests,
                        'endpoint_breakdown': endpoint_breakdown,
                        'system_metrics': system,
                        'system_history': history,
                        'server_time': datetime.now().isoformat(),
                }
                return api_ok(data)
        except Exception as e:
                return api_error(str(e), 500)

@app.route('/api/v2/dashboard', methods=['GET'])
def dashboard_v2_api():
    """API endpoint for dashboard data."""
    try:
        import psutil
        import os

        # Get program storage info
        storage_info = program_store.get_storage_info()

        # Get recent programs (last 10)
        all_programs = program_store.get_program_list()
        recent_programs = sorted(
            all_programs,
            key=lambda x: x.get('upload_time', ''),
            reverse=True
        )[:10]

        # System metrics
        system_metrics = {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'process_count': len(psutil.pids()),
            'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
        }

        # Get monitoring data if available
        endpoint_breakdown = []
        recent_requests = []
        try:
            # Try to get monitoring data from the monitoring module if it's initialized
            from monitoring import get_monitoring_manager

            monitor = get_monitoring_manager()
            if monitor and monitor.storage:
                # Get endpoint breakdown from the database
                endpoint_breakdown = monitor.storage.get_endpoint_breakdown(hours=1, limit=10)

                # Get recent requests from the database
                recent_requests = monitor.storage.get_recent_requests(limit=20)
        except Exception as e:
            # Monitoring not available or not initialized
            pass

        dashboard_data = {
            'success': True,
            'data': {
                'server_time': datetime.now().isoformat(),
                'totals': {
                    'programs': storage_info.get('total_programs', 0),
                    'projects': storage_info.get('total_projects', 0),
                    'files': storage_info.get('total_files', 0),
                    'size_bytes': storage_info.get('total_size', 0)
                },
                'storage': storage_info,
                'recent_programs': recent_programs,
                'system_metrics': system_metrics,
                'endpoint_breakdown': endpoint_breakdown,
                'recent_requests': recent_requests
            }
        }

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/programs/upload', methods=['POST'])
def v2_upload_program():
    """
    Upload a single program file with validation.
    
    Form data:
        file: File - The program file to upload
        description: str - Optional description of the program
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'hint': 'Include a file in the request with key "file"'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'hint': 'Select a valid file to upload'
            }), 400
        
        description = request.form.get('description', '')
        
        # Read file content
        content = file.read()
        
        # Validate size before processing
        if len(content) == 0:
            return jsonify({
                'success': False,
                'error': 'File is empty',
                'hint': 'Upload a file with content'
            }), 400
        
        # Store the program
        program_info = program_store.store_program(file.filename, content, description)
        
        return jsonify({
            'success': True,
            'message': 'Program uploaded successfully',
            'program': program_info
        })
    
    except ValueError as e:
        # Validation errors
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'validation_error'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'server_error'
        }), 500

@app.route('/api/v2/programs/upload-multiple', methods=['POST'])
def v2_upload_multiple_programs():
    """
    Upload multiple files as a project with validation.
    
    Form data:
        files[]: List[File] - Multiple files to upload
        project_name: str - Optional project name
        description: str - Optional project description
        relative_paths[]: List[str] - Optional relative paths for files
    """
    try:
        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided',
                'hint': 'Include files in the request with key "files[]"'
            }), 400
        
        files = request.files.getlist('files[]')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files selected',
                'hint': 'Select at least one valid file to upload'
            }), 400
        
        project_name = request.form.get('project_name', '')
        description = request.form.get('description', '')
        
        # Get relative paths from form data (supports both formats)
        relative_paths = request.form.getlist('relative_paths[]')
        
        # Prepare files data
        files_data = []
        for i, file in enumerate(files):
            if file.filename:
                content = file.read()
                
                # Try multiple ways to get the relative path:
                # 1. From relative_paths[] array (if frontend uses this)
                # 2. From path_<filename> field (current frontend implementation)
                # 3. Fall back to just the filename
                if i < len(relative_paths):
                    relative_path = relative_paths[i]
                else:
                    # Check for path_<filename> in form data (folder upload format)
                    path_key = f'path_{file.filename}'
                    relative_path = request.form.get(path_key, file.filename)
                
                files_data.append({
                    'filename': file.filename,
                    'content': content,
                    'relative_path': relative_path
                })
        
        if not files_data:
            return jsonify({
                'success': False,
                'error': 'No valid files to upload',
                'hint': 'Ensure files contain valid data'
            }), 400
        
        # Store the project
        project_info = program_store.store_multiple_files(files_data, project_name, description)
        
        return jsonify({
            'success': True,
            'message': 'Project uploaded successfully',
            'project': project_info
        })
    
    except ValueError as e:
        # Validation errors
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'validation_error'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'server_error'
        }), 500


@app.route('/api/v2/programs/project/<project_id>/files', methods=['GET'])
def v2_get_project_files(project_id):
    """Get list of files in a project."""
    try:
        files = program_store.list_project_files(project_id)
        
        if not files:
            program_info = program_store.get_program_info(project_id)
            if not program_info:
                return jsonify({
                    'success': False,
                    'error': f'Project {project_id} not found'
                }), 404
            
            if program_info.get('type') != 'project':
                return jsonify({
                    'success': False,
                    'error': f'{project_id} is not a project'
                }), 400
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'files': files,
            'count': len(files)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/programs/execute/<filename>', methods=['POST'])
def v2_execute_program(filename):
    """
    Execute an uploaded program with enhanced options.
    
    Request JSON body:
        args: List[str] - Command line arguments
        use_sudo: bool - Execute with sudo privileges
        sudo_password: str - Password for sudo (if use_sudo=True)
        specific_file: str - Specific file to execute in project
        interactive: bool - Use interactive mode
        timeout: int - Execution timeout in seconds (default: 30, max: 300)
        env: Dict[str, str] - Additional environment variables
    """
    try:
        args = request.json.get('args', []) if request.json else []
        use_sudo = request.json.get('use_sudo', False) if request.json else False
        sudo_password = request.json.get('sudo_password', '') if request.json else ''
        specific_file = request.json.get('specific_file', None) if request.json else None
        interactive = request.json.get('interactive', False) if request.json else False
        timeout = request.json.get('timeout', 30) if request.json else 30
        env_vars = request.json.get('env', {}) if request.json else {}
        exec_start = time.perf_counter()
        
        # Validate timeout using constants from privileged_execution module
        timeout = max(MIN_TIMEOUT, min(timeout, MAX_TIMEOUT))
        
        # Validate environment variables
        if env_vars and not isinstance(env_vars, dict):
            return jsonify({
                'success': False,
                'error': 'Environment variables must be a dictionary'
            }), 400
        
        # Get program info and path
        program_info = program_store.get_program_info(filename)
        if not program_info:
            return jsonify({
                'success': False,
                'error': f'Program {filename} not found'
            }), 404
        
        # Handle project execution
        if program_info.get('type') == 'project':
            project_files = program_store.list_project_files(filename)
            
            # If specific_file is provided, use that instead of main_file
            if specific_file:
                # Find the specific file in the project
                project_dir = program_store.get_program_path(filename)
                program_path = os.path.join(project_dir, specific_file)
                
                if not os.path.exists(program_path):
                    return jsonify({
                        'success': False,
                        'error': f'File {specific_file} not found in project'
                    }), 404
                
                # Get file info to determine type
                file_info = next((f for f in project_files if f.get('relative_path') == specific_file), None)
                if not file_info:
                    return jsonify({
                        'success': False,
                        'error': f'File {specific_file} not found in project metadata'
                    }), 404
                program_type = file_info['program_type']
            else:
                # Use main file if no specific file provided
                main_file_path = program_store.get_project_main_file(filename)
                if not main_file_path:
                    # Build candidate list to let the user choose
                    supported = {'python', 'shell', 'javascript', 'perl', 'ruby'}
                    candidates = []
                    for f in project_files:
                        if f.get('program_type') in supported or f.get('is_executable'):
                            candidates.append({
                                'relative_path': f.get('relative_path'),
                                'program_type': f.get('program_type'),
                                'size': f.get('size'),
                                'is_executable': f.get('is_executable')
                            })
                    return jsonify({
                        'success': False,
                        'error': f'Main file not set for project {filename}',
                        'need_main_file': True,
                        'project_id': filename,
                        'candidates': candidates
                    }), 400
                program_path = main_file_path
                # For projects, use the main file's type for execution
                main_file_info = next((f for f in project_files if f.get('full_path') == main_file_path), None)
                program_type = main_file_info['program_type'] if main_file_info else 'unknown'
        else:
            program_path = program_store.get_program_path(filename)
            if not program_path:
                return jsonify({
                    'success': False,
                    'error': f'Program file {filename} not accessible'
                }), 404
            program_type = program_info['program_type']
        
        # Determine execution command based on program type
        if program_type == 'python':
            cmd = ['python3', program_path] + args
        elif program_type == 'shell':
            cmd = ['bash', program_path] + args
        elif program_type == 'javascript':
            cmd = ['node', program_path] + args
        elif program_type == 'perl':
            cmd = ['perl', program_path] + args
        elif program_type == 'ruby':
            cmd = ['ruby', program_path] + args
        else:
            # Try to execute directly (if it has executable permissions)
            cmd = [program_path] + args
        
        # If interactive, use the interactive execution flow
        if interactive:
            return execute_interactive_program(cmd, os.path.dirname(program_path), use_sudo, sudo_password)

        # Prepare environment
        exec_env = os.environ.copy()
        if env_vars:
            exec_env.update(env_vars)
        
        # Execute command
        if use_sudo and sudo_password:
            # Use pexpect for sudo commands
            try:
                # Prepare the sudo command
                sudo_cmd = f"sudo {' '.join(cmd)}"
                
                # Spawn the process
                child = pexpect.spawn('bash', ['-c', sudo_cmd], timeout=timeout, env=exec_env)
                
                # Wait for password prompt
                i = child.expect(['password', 'Password', pexpect.TIMEOUT], timeout=5)
                if i == 0 or i == 1:
                    child.sendline(sudo_password)
                    child.expect(pexpect.EOF, timeout=timeout)
                    output = child.before.decode('utf-8', errors='replace')
                    exit_code = child.exitstatus
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Password prompt not found or timeout',
                        'hint': 'Verify sudo is required and password is correct'
                    }), 500
                
            except pexpect.TIMEOUT:
                return jsonify({
                    'success': False,
                    'error': f'Command execution timed out after {timeout} seconds',
                    'hint': 'Try increasing the timeout parameter or check if the program is hanging'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Sudo execution failed: {str(e)}',
                    'hint': 'Verify sudo password and permissions'
                }), 500
        else:
            # Regular command execution
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.path.dirname(program_path),
                    env=exec_env
                )
                output = result.stdout + result.stderr
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'error': f'Program execution timed out after {timeout} seconds',
                    'hint': 'Try increasing the timeout parameter or check if the program is hanging'
                }), 500
            except FileNotFoundError as e:
                return jsonify({
                    'success': False,
                    'error': f'Program interpreter not found: {str(e)}',
                    'hint': f'Ensure {program_type} interpreter is installed on the system'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Execution failed: {str(e)}',
                    'hint': 'Check program permissions and syntax'
                }), 500
        
        # Update execution statistics
        program_store.update_execution_stats(filename)
        # Record execution detail/history (monitoring disabled temporarily)
        try:
            duration_ms = int(1000 * max(0.0, time.perf_counter() - exec_start))
            program_store.record_execution(
                filename=filename,
                success=(exit_code == 0),
                exit_code=int(exit_code),
                duration_ms=duration_ms,
                command=' '.join(cmd),
                output_size=len(output or '')
            )
        except Exception:
            pass
        
        return jsonify({
            'success': True,
            'output': output,
            'exit_code': exit_code,
            'program_type': program_type,
            'command': ' '.join(cmd),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v2/programs/execute-terminal/<project_id>', methods=['POST'])
def execute_project_terminal_v2(project_id):
    """Execute a terminal command in a project's directory."""
    try:
        command = request.json.get('command', '') if request.json else ''
        use_sudo = request.json.get('use_sudo', False) if request.json else False
        sudo_password = request.json.get('sudo_password', '') if request.json else ''
        interactive = request.json.get('interactive', False) if request.json else False
        
        if not command:
            return jsonify({
                'success': False,
                'error': 'No command provided'
            }), 400
        
        # Get program info and verify it's a project
        program_info = program_store.get_program_info(project_id)
        if not program_info:
            return jsonify({
                'success': False,
                'error': f'Project {project_id} not found'
            }), 404
        
        if program_info.get('type') != 'project':
            return jsonify({
                'success': False,
                'error': f'{project_id} is not a project'
            }), 400
        
        # Get project directory
        project_dir = program_store.get_program_path(project_id)
        if not project_dir or not os.path.exists(project_dir):
            return jsonify({
                'success': False,
                'error': f'Project directory not found'
            }), 404
        
        # Parse command (handle shell syntax)
        import shlex
        try:
            cmd = shlex.split(command)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid command syntax: {str(e)}'
            }), 400
        
        # If interactive, use the interactive execution flow
        if interactive:
            return execute_interactive_program(cmd, project_dir, use_sudo, sudo_password)
        
        # Execute command
        if use_sudo and sudo_password:
            # Use pexpect for sudo commands
            try:
                import pexpect
                sudo_cmd = ' '.join(['sudo', '-S'] + cmd)
                child = pexpect.spawn('bash', ['-c', sudo_cmd], cwd=project_dir, timeout=60, encoding='utf-8')
                child.expect([pexpect.TIMEOUT, r'\[sudo\] password.*:', 'password.*:'], timeout=5)
                child.sendline(sudo_password)
                child.expect(pexpect.EOF, timeout=60)
                output = child.before
                child.close()
                exit_code = child.exitstatus if child.exitstatus is not None else 1
            except pexpect.TIMEOUT:
                return jsonify({
                    'success': False,
                    'error': 'Command execution timed out'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Sudo execution failed: {str(e)}'
                }), 500
        else:
            # Normal execution
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=project_dir,
                    shell=False
                )
                output = result.stdout + result.stderr
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'error': 'Command execution timed out (60 seconds)'
                }), 500
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Execution failed: {str(e)}'
                }), 500
        
        return jsonify({
            'success': True,
            'output': output,
            'return_code': exit_code,
            'completed': True,
            'command': command,
            'cwd': project_dir,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def execute_interactive_program(cmd, cwd, use_sudo=False, sudo_password=None):
    """Execute a program interactively using pexpect."""
    try:
        session_id = str(uuid.uuid4())
        
        # Prepare command
        full_command = ' '.join(cmd)
        if use_sudo:
            full_command = f"sudo {full_command}"

        # Set environment
        env = {
            'TERM': 'dumb',
            'NO_COLOR': '1',
            'FORCE_COLOR': '0',
            'COLORTERM': '',
            'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        }

        # Start the command with pexpect
        child = pexpect.spawn(full_command, timeout=60, encoding='utf-8', env=env, cwd=cwd)
        
        # Store session
        with session_lock:
            interactive_sessions[session_id] = {
                'child': child,
                'command': full_command,
                'sudo_password': sudo_password,
                'password_sent': False,
                'output_buffer': ''
            }

        # Handle initial password prompt for sudo
        if use_sudo and sudo_password:
            try:
                index = child.expect(['.*password.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=5)
                if index == 0:
                    child.sendline(sudo_password)
                    interactive_sessions[session_id]['password_sent'] = True
            except pexpect.TIMEOUT:
                pass  # May not ask for password, continue

        # Initial read to see if it's waiting for input or has output
        try:
            # A short timeout to gather initial output without blocking for too long
            child.expect(pexpect.EOF, timeout=0.5)
            output = child.before
            exit_code = child.exitstatus
            completed = True
        except pexpect.TIMEOUT:
            output = child.before
            exit_code = None
            completed = False

        clean_initial_output = clean_output(output)

        if completed:
            with session_lock:
                if session_id in interactive_sessions:
                    del interactive_sessions[session_id]
            return jsonify({
                'success': True,
                'command': full_command,
                'stdout': clean_initial_output,
                'return_code': exit_code,
                'completed': True,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'command': full_command,
                'stdout': clean_initial_output,
                'waiting_for_input': True,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start interactive program: {str(e)}'
        }), 500

@app.route('/api/v2/programs/project/<project_id>/set-main', methods=['POST'])
def set_project_main_v2(project_id):
    """Set the main executable file for a project."""
    try:
        data = request.get_json(silent=True) or {}
        relative_path = data.get('relative_path')
        if not relative_path:
            return jsonify({'success': False, 'error': 'relative_path is required'}), 400
        if not program_store.get_program_info(project_id):
            return jsonify({'success': False, 'error': f'Project {project_id} not found'}), 404
        ok = program_store.set_project_main_file(project_id, relative_path)
        if not ok:
            return jsonify({'success': False, 'error': 'Invalid file for project'}), 400
        return jsonify({'success': True, 'project': program_store.get_program_info(project_id)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v2/programs/delete/<filename>', methods=['DELETE'])
def delete_program_v2(filename):
    """Delete an uploaded program."""
    try:
        success = program_store.delete_program(filename)
        if success:
            return jsonify({
                'success': True,
                'message': f'Program {filename} deleted successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Program {filename} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/programs/info/<filename>', methods=['GET'])
def get_program_info_v2(filename):
    """Get information about a specific program."""
    try:
        program_info = program_store.get_program_info(filename)
        if program_info:
            return jsonify({
                'success': True,
                'program': program_info,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Program {filename} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# File Storage Routes
@app.route('/api/v2/files/upload', methods=['POST'])
def upload_files_v2():
    """Upload one or more files to storage."""
    try:
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400
        
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        uploaded_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
            
            try:
                # Read file data
                file_data = file.read()
                
                # Check if we can store this file
                can_store, message = file_store.can_store_file(len(file_data))
                if not can_store:
                    errors.append(f"{file.filename}: {message}")
                    continue
                
                # Store the file
                success, message, stored_filename = file_store.store_file(
                    file_data, 
                    file.filename,
                    file.filename
                )
                
                if success:
                    uploaded_files.append({
                        'filename': stored_filename,
                        'original_name': file.filename,
                        'size': len(file_data),
                        'message': message
                    })
                else:
                    errors.append(f"{file.filename}: {message}")
                    
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        if uploaded_files:
            return jsonify({
                'success': True,
                'message': f'Uploaded {len(uploaded_files)} file(s)',
                'files': uploaded_files,
                'errors': errors if errors else None,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No files were uploaded',
                'errors': errors
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/files/list', methods=['GET'])
def list_files_v2():
    """List all uploaded files."""
    try:
        files = file_store.list_files()
        storage_info = file_store.get_storage_info()
        
        # Add backward compatibility aliases
        storage_info['total_files'] = storage_info['file_count']
        storage_info['total_size_mb'] = storage_info['used_mb']
        
        return jsonify({
            'success': True,
            'files': files,
            'storage_info': storage_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/files/download/<filename>', methods=['GET'])
def download_file_v2(filename):
    """Download a file from storage."""
    try:
        success, file_data, metadata = file_store.get_file(filename)
        
        if not success:
            return jsonify({
                'success': False,
                'error': f'File {filename} not found'
            }), 404
        
        # Create response with file data
        from flask import send_file
        import io
        
        return send_file(
            io.BytesIO(file_data),
            mimetype=metadata.get('mime_type', 'application/octet-stream'),
            as_attachment=True,
            download_name=metadata.get('original_name', filename)
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/files/delete/<filename>', methods=['DELETE'])
def delete_file_v2(filename):
    """Delete a file from storage."""
    try:
        success, message = file_store.delete_file(filename)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/files/storage', methods=['GET'])
def get_storage_info_v2():
    """Get storage information and statistics."""
    try:
        storage_info = file_store.get_storage_info()
        
        return jsonify({
            'success': True,
            'storage': storage_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Tunnel Management Routes
@app.route('/api/v2/ngrok/start', methods=['POST'])
def api_start_ngrok_v2():
    """Start ngrok tunnel."""
    try:
        success = start_ngrok_tunnel()
        status = get_ngrok_status()
        
        return jsonify({
            'success': success,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'ngrok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/ngrok/stop', methods=['POST'])
def api_stop_ngrok_v2():
    """Stop ngrok tunnel."""
    try:
        success = stop_ngrok_tunnel()
        
        return jsonify({
            'success': success,
            'message': 'Ngrok tunnel stopped' if success else 'Failed to stop ngrok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/ngrok/status', methods=['GET'])
def api_ngrok_status_v2():
    """Get ngrok status."""
    try:
        status = get_ngrok_status()
        
        return jsonify({
            'success': True,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'ngrok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/localtunnel/start', methods=['POST'])
def api_start_localtunnel_v2():
    """Start localtunnel tunnel."""
    try:
        success = start_localtunnel_tunnel()
        status = get_localtunnel_status()
        
        return jsonify({
            'success': success,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'localtunnel',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/localtunnel/stop', methods=['POST'])
def api_stop_localtunnel_v2():
    """Stop localtunnel tunnel."""
    try:
        success = stop_localtunnel_tunnel()
        
        return jsonify({
            'success': success,
            'message': 'Localtunnel stopped' if success else 'Failed to stop localtunnel',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/localtunnel/status', methods=['GET'])
def api_localtunnel_status_v2():
    """Get localtunnel status."""
    try:
        status = get_localtunnel_status()
        
        return jsonify({
            'success': True,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'localtunnel',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/cloudflared/start', methods=['POST'])
def api_start_cloudflared_v2():
    """Start cloudflared tunnel."""
    try:
        success = start_cloudflared_tunnel()
        status = get_cloudflared_status()
        
        return jsonify({
            'success': success,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'cloudflared',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/cloudflared/stop', methods=['POST'])
def api_stop_cloudflared_v2():
    """Stop cloudflared tunnel."""
    try:
        success = stop_cloudflared_tunnel()
        
        return jsonify({
            'success': success,
            'message': 'Cloudflared tunnel stopped' if success else 'Failed to stop cloudflared',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/cloudflared/status', methods=['GET'])
def api_cloudflared_status_v2():
    """Get cloudflared status."""
    try:
        status = get_cloudflared_status()
        
        return jsonify({
            'success': True,
            'status': status['status'],
            'public_url': status['public_url'],
            'service': 'cloudflared',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/tunnels/status', methods=['GET'])
def api_all_tunnels_status_v2():
    """Get status of all tunnels."""
    try:
        ngrok_status = get_ngrok_status()
        localtunnel_status = get_localtunnel_status()
        cloudflared_status = get_cloudflared_status()
        
        return jsonify({
            'success': True,
            'tunnels': {
                'ngrok': ngrok_status,
                'localtunnel': localtunnel_status,
                'cloudflared': cloudflared_status
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/tunnels/stop-all', methods=['POST'])
def api_stop_all_tunnels_v2():
    """Stop all active tunnels."""
    try:
        results = {
            'ngrok': stop_ngrok_tunnel(),
            'localtunnel': stop_localtunnel_tunnel(),
            'cloudflared': stop_cloudflared_tunnel()
        }
        
        all_stopped = all(results.values())
        
        return jsonify({
            'success': all_stopped,
            'message': 'All tunnels stopped' if all_stopped else 'Some tunnels failed to stop',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Voice Chat Management Routes
@app.route('/api/v2/voice-chat/rooms', methods=['GET'])
def list_voice_rooms_v2():
    """List all active voice chat rooms."""
    try:
        with voice_chat_lock:
            rooms = []
            for room_id, room_data in voice_chat_rooms.items():
                rooms.append({
                    'room_id': room_id,
                    'name': room_data['name'],
                    'participants': len(room_data['participants']),
                    'created_at': room_data['created_at'],
                    'host': room_data['host']
                })
        
        return jsonify({
            'success': True,
            'rooms': rooms,
            'count': len(rooms),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Single persistent room ID
MAIN_ROOM_ID = 'main-voice-room'

def initialize_main_voice_room():
    """Initialize the main voice chat room with host."""
    with voice_chat_lock:
        if MAIN_ROOM_ID not in voice_chat_rooms:
            host_id = str(uuid.uuid4())
            voice_chat_rooms[MAIN_ROOM_ID] = {
                'room_id': MAIN_ROOM_ID,
                'name': 'Main Voice Chat',
                'host': 'Server Host',
                'host_id': host_id,
                'participants': {
                    host_id: {
                        'name': 'Server Host',
                        'joined_at': datetime.now().isoformat(),
                        'is_host': True
                    }
                },
                'created_at': datetime.now().isoformat(),
                'signaling_messages': []
            }

# Initialize the main room on startup
initialize_main_voice_room()

@app.route('/api/v2/voice-chat/create', methods=['POST'])
def create_voice_room_v2():
    """Get or create the main voice chat room (always returns the same room)."""
    try:
        with voice_chat_lock:
            if MAIN_ROOM_ID not in voice_chat_rooms:
                initialize_main_voice_room()
            
            room_info = voice_chat_rooms[MAIN_ROOM_ID]
        
        return jsonify({
            'success': True,
            'room_id': MAIN_ROOM_ID,
            'room_name': room_info['name'],
            'host': room_info['host'],
            'participants': len(room_info['participants']),
            'message': 'Connected to main voice chat room',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/voice-chat/join/<room_id>', methods=['POST'])
def join_voice_room_v2(room_id):
    """Join a voice chat room."""
    try:
        # Always use the main room
        room_id = MAIN_ROOM_ID
        
        request_data = request.get_json() or {}
        participant_name = request_data.get('name', f'User-{int(time.time())}')
        
        with voice_chat_lock:
            if room_id not in voice_chat_rooms:
                initialize_main_voice_room()
            
            participant_id = str(uuid.uuid4())
            voice_chat_rooms[room_id]['participants'][participant_id] = {
                'name': participant_name,
                'joined_at': datetime.now().isoformat(),
                'is_host': False
            }
            
            room_info = voice_chat_rooms[room_id]
        
        return jsonify({
            'success': True,
            'participant_id': participant_id,
            'room_id': room_id,
            'room_name': room_info['name'],
            'host': room_info['host'],
            'participants': len(room_info['participants']),
            'message': f'{participant_name} joined the room',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/voice-chat/leave/<room_id>/<participant_id>', methods=['POST'])
def leave_voice_room_v2(room_id, participant_id):
    """Leave a voice chat room."""
    try:
        # Always use the main room
        room_id = MAIN_ROOM_ID
        
        with voice_chat_lock:
            if room_id not in voice_chat_rooms:
                return jsonify({
                    'success': False,
                    'error': 'Room not found'
                }), 404
            
            # Don't allow host to leave
            if participant_id == voice_chat_rooms[room_id].get('host_id'):
                return jsonify({
                    'success': False,
                    'error': 'Host cannot leave the room',
                    'message': 'Server host is always present in the voice chat'
                }), 400
            
            if participant_id in voice_chat_rooms[room_id]['participants']:
                participant_name = voice_chat_rooms[room_id]['participants'][participant_id]['name']
                del voice_chat_rooms[room_id]['participants'][participant_id]
                
                return jsonify({
                    'success': True,
                    'message': f'{participant_name} left the voice chat room',
                    'participants': len(voice_chat_rooms[room_id]['participants']),
                    'timestamp': datetime.now().isoformat()
                })
        
        return jsonify({
            'success': True,
            'message': 'Left the voice chat room',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/voice-chat/signal/<room_id>', methods=['POST'])
def voice_chat_signal_v2(room_id):
    """Handle WebRTC signaling for voice chat."""
    try:
        request_data = request.get_json() or {}
        signal_type = request_data.get('type')
        signal_data = request_data.get('data')
        sender_id = request_data.get('sender_id')
        target_id = request_data.get('target_id')
        
        with voice_chat_lock:
            if room_id not in voice_chat_rooms:
                return jsonify({
                    'success': False,
                    'error': 'Room not found'
                }), 404
            
            # Store signaling message
            signal_message = {
                'type': signal_type,
                'data': signal_data,
                'sender_id': sender_id,
                'target_id': target_id,
                'timestamp': datetime.now().isoformat()
            }
            
            voice_chat_rooms[room_id]['signaling_messages'].append(signal_message)
            
            # Keep only last 100 messages
            if len(voice_chat_rooms[room_id]['signaling_messages']) > 100:
                voice_chat_rooms[room_id]['signaling_messages'] = \
                    voice_chat_rooms[room_id]['signaling_messages'][-100:]
        
        return jsonify({
            'success': True,
            'message': 'Signal sent',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v2/voice-chat/poll/<room_id>/<participant_id>', methods=['GET'])
def poll_voice_chat_v2(room_id, participant_id):
    """Poll for new signaling messages (simple polling for WebRTC)."""
    try:
        with voice_chat_lock:
            if room_id not in voice_chat_rooms:
                return jsonify({
                    'success': False,
                    'error': 'Room not found'
                }), 404
            
            # Get messages for this participant
            messages = [
                msg for msg in voice_chat_rooms[room_id]['signaling_messages']
                if msg.get('target_id') == participant_id or msg.get('target_id') is None
            ]
            
            participants = voice_chat_rooms[room_id]['participants']
        
        return jsonify({
            'success': True,
            'messages': messages,
            'participants': [
                {'id': pid, 'name': pdata['name']}
                for pid, pdata in participants.items()
            ],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/voice-chat')
def voice_chat_page_v2():
    """Serve the voice chat page."""
    return render_template('voice_chat.html')

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Connect to a remote address to determine local IP
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def start_ngrok_tunnel():
    """Start ngrok tunnel in the background."""
    global tunnel_info
    try:
        # Check if ngrok is installed
        try:
            subprocess.run(['ngrok', 'version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            tunnel_info['ngrok']['status'] = 'error: ngrok not installed. Download from https://ngrok.com/download'
            return False
        
        # Start ngrok process - try without config first for unauthenticated users
        process = subprocess.Popen(
            ['ngrok', 'http', '8000', '--log', 'stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        tunnel_info['ngrok']['process'] = process
        tunnel_info['ngrok']['status'] = 'starting'
        
        # Wait for ngrok to start and get the public URL
        time.sleep(5)  # Give ngrok more time to start
        
        # Try multiple times to get the tunnel info
        for attempt in range(10):
            try:
                # Get tunnel info from ngrok API
                response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        tunnel_info['ngrok']['public_url'] = tunnels[0]['public_url']
                        tunnel_info['ngrok']['status'] = 'running'
                        return True
                time.sleep(1)  # Wait before retrying
            except requests.exceptions.RequestException:
                time.sleep(1)  # Wait before retrying
                continue
        
        # If API doesn't work, check if process is still running
        if process.poll() is None:
            tunnel_info['ngrok']['status'] = 'running (URL detection failed - check ngrok web interface at http://localhost:4040)'
            return True
        else:
            # Process failed, check stderr for error
            error_output = process.stderr.read()
            if 'authentication required' in error_output.lower() or 'authtoken' in error_output.lower():
                tunnel_info['ngrok']['status'] = 'error: authentication required. Sign up at https://ngrok.com and add your authtoken'
            elif 'permission denied' in error_output.lower():
                tunnel_info['ngrok']['status'] = 'error: permission denied. Check ngrok installation'
            else:
                tunnel_info['ngrok']['status'] = f'error: {error_output.strip() or "failed to start"}'
            return False
        
    except Exception as e:
        tunnel_info['ngrok']['status'] = f'error: {str(e)}'
        return False

def stop_ngrok_tunnel():
    """Stop ngrok tunnel."""
    global tunnel_info
    try:
        if tunnel_info['ngrok']['process']:
            tunnel_info['ngrok']['process'].terminate()
            tunnel_info['ngrok']['process'] = None
        
        tunnel_info['ngrok']['public_url'] = None
        tunnel_info['ngrok']['status'] = 'stopped'
        return True
    except Exception as e:
        tunnel_info['ngrok']['status'] = f'error: {str(e)}'
        return False

def get_ngrok_status():
    """Get current ngrok tunnel status."""
    global tunnel_info
    
    if tunnel_info['ngrok']['process'] and tunnel_info['ngrok']['process'].poll() is not None:
        # Process has terminated
        tunnel_info['ngrok']['status'] = 'stopped'
        tunnel_info['ngrok']['public_url'] = None
        tunnel_info['ngrok']['process'] = None
    
    return {
        'status': tunnel_info['ngrok']['status'],
        'public_url': tunnel_info['ngrok']['public_url']
    }

def start_localtunnel_tunnel():
    """Start localtunnel tunnel in the background."""
    global tunnel_info
    try:
        # Check if localtunnel is installed
        try:
            subprocess.run(['lt', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            tunnel_info['localtunnel']['status'] = 'error: localtunnel not installed. Run: npm install -g localtunnel'
            return False
        
        # Generate a random subdomain to avoid conflicts
        import random
        import string
        subdomain = 'webserver-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        # Start localtunnel process with subdomain
        process = subprocess.Popen(
            ['lt', '--port', '8000', '--subdomain', subdomain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        tunnel_info['localtunnel']['process'] = process
        tunnel_info['localtunnel']['status'] = 'starting'
        
        # Wait for localtunnel to start and get the public URL
        time.sleep(8)  # Give localtunnel more time to start
        
        # Read the output to get the URL
        if process.poll() is None:  # Process is still running
            # Try to construct the URL from the subdomain
            public_url = f'https://{subdomain}.loca.lt'
            tunnel_info['localtunnel']['public_url'] = public_url
            tunnel_info['localtunnel']['status'] = 'running'
            return True
        else:
            # Process failed, check stderr for error
            error_output = process.stderr.read()
            if 'subdomain already requested' in error_output.lower():
                # Try without subdomain (random assignment)
                process = subprocess.Popen(
                    ['lt', '--port', '8000'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                tunnel_info['localtunnel']['process'] = process
                time.sleep(8)
                
                if process.poll() is None:
                    # Try to read URL from stdout
                    try:
                        # Read the first few lines of output
                        for i in range(10):  # Try up to 10 lines
                            line = process.stdout.readline()
                            if 'https://' in line and 'loca.lt' in line:
                                # Extract URL from line
                                url_start = line.find('https://')
                                url_end = line.find(' ', url_start) if ' ' in line[url_start:] else len(line)
                                if url_end == -1:
                                    url_end = len(line)
                                public_url = line[url_start:url_end].strip()
                                tunnel_info['localtunnel']['public_url'] = public_url
                                tunnel_info['localtunnel']['status'] = 'running'
                                return True
                    except:
                        pass
                        
        tunnel_info['localtunnel']['status'] = 'error: failed to establish tunnel. Localtunnel may require manual setup or account registration'
        return False
        
    except Exception as e:
        tunnel_info['localtunnel']['status'] = f'error: {str(e)}'
        return False

def stop_localtunnel_tunnel():
    """Stop localtunnel tunnel."""
    global tunnel_info
    try:
        if tunnel_info['localtunnel']['process']:
            tunnel_info['localtunnel']['process'].terminate()
            tunnel_info['localtunnel']['process'] = None
        
        tunnel_info['localtunnel']['public_url'] = None
        tunnel_info['localtunnel']['status'] = 'stopped'
        return True
    except Exception as e:
        tunnel_info['localtunnel']['status'] = f'error: {str(e)}'
        return False

def get_localtunnel_status():
    """Get current localtunnel tunnel status."""
    global tunnel_info
    
    if tunnel_info['localtunnel']['process'] and tunnel_info['localtunnel']['process'].poll() is not None:
        # Process has terminated
        tunnel_info['localtunnel']['status'] = 'stopped'
        tunnel_info['localtunnel']['public_url'] = None
        tunnel_info['localtunnel']['process'] = None
    
    return {
        'status': tunnel_info['localtunnel']['status'],
        'public_url': tunnel_info['localtunnel']['public_url']
    }

def start_cloudflared_tunnel():
    """Start cloudflared tunnel in the background."""
    global tunnel_info
    try:
        # Check if cloudflared is installed
        try:
            result = subprocess.run(['cloudflared', '--version'], capture_output=True, check=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            tunnel_info['cloudflared']['status'] = 'error: cloudflared not installed. Download from https://github.com/cloudflare/cloudflared/releases'
            return False
        
        # Start cloudflared process
        process = subprocess.Popen(
            ['cloudflared', 'tunnel', '--url', 'http://localhost:8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        tunnel_info['cloudflared']['process'] = process
        tunnel_info['cloudflared']['status'] = 'starting'
        
        # Wait for cloudflared to start and get the public URL
        time.sleep(10)  # Give cloudflared more time to start
        
        # Cloudflared prints the URL to stderr
        if process.poll() is None:  # Process is still running
            try:
                # Read from stderr where cloudflared outputs the URL
                for i in range(20):  # Try reading up to 20 lines
                    line = process.stderr.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    
                    # Look for the tunnel URL
                    if 'https://' in line and ('trycloudflare.com' in line or 'cfargotunnel.com' in line):
                        # Extract URL from the line
                        import re
                        url_match = re.search(r'https://[^\s]+', line)
                        if url_match:
                            public_url = url_match.group(0)
                            tunnel_info['cloudflared']['public_url'] = public_url
                            tunnel_info['cloudflared']['status'] = 'running'
                            return True
                    
                    # Check for errors
                    if 'error' in line.lower() or 'failed' in line.lower():
                        tunnel_info['cloudflared']['status'] = f'error: {line.strip()}'
                        return False
                        
            except Exception as e:
                tunnel_info['cloudflared']['status'] = f'error reading output: {str(e)}'
                return False
        else:
            # Process exited, check for errors
            error_output = process.stderr.read()
            tunnel_info['cloudflared']['status'] = f'error: process exited - {error_output}'
            return False
        
        tunnel_info['cloudflared']['status'] = 'error: tunnel started but no URL found'
        return False
        
    except Exception as e:
        tunnel_info['cloudflared']['status'] = f'error: {str(e)}'
        return False

def stop_cloudflared_tunnel():
    """Stop cloudflared tunnel."""
    global tunnel_info
    try:
        if tunnel_info['cloudflared']['process']:
            tunnel_info['cloudflared']['process'].terminate()
            tunnel_info['cloudflared']['process'] = None
        
        tunnel_info['cloudflared']['public_url'] = None
        tunnel_info['cloudflared']['status'] = 'stopped'
        return True
    except Exception as e:
        tunnel_info['cloudflared']['status'] = f'error: {str(e)}'
        return False

def get_cloudflared_status():
    """Get current cloudflared tunnel status."""
    global tunnel_info
    
    if tunnel_info['cloudflared']['process'] and tunnel_info['cloudflared']['process'].poll() is not None:
        # Process has terminated
        tunnel_info['cloudflared']['status'] = 'stopped'
        tunnel_info['cloudflared']['public_url'] = None
        tunnel_info['cloudflared']['process'] = None
    
    return {
        'status': tunnel_info['cloudflared']['status'],
        'public_url': tunnel_info['cloudflared']['public_url']
    }

def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def find_process_using_port(port):
    """Find the process ID using a specific port."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check all connections for this process
                for conn in proc.connections(kind='inet'):
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return proc.info
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
    except Exception as e:
        print(f"Error finding process: {e}")
    return None

def kill_process_on_port(port):
    """Kill any process using the specified port."""
    proc_info = find_process_using_port(port)
    if proc_info:
        pid = proc_info['pid']
        name = proc_info.get('name', 'unknown')
        cmdline = ' '.join(proc_info.get('cmdline', []))
        
        print(f"⚠️  Port {port} is in use by process {pid} ({name})")
        print(f"   Command: {cmdline}")
        print(f"   Terminating previous instance...")
        
        try:
            # Try graceful termination first
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            
            # Check if still running
            if psutil.pid_exists(pid):
                print(f"   Process still running, forcing termination...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            
            print(f"✅ Successfully freed port {port}")
            return True
        except ProcessLookupError:
            print(f"✅ Process already terminated")
            return True
        except Exception as e:
            print(f"❌ Error killing process: {e}")
            return False
    return False

def ensure_port_available(port):
    """Ensure the port is available, killing any existing process if needed."""
    if is_port_in_use(port):
        print(f"\n🔍 Checking port {port}...")
        killed = kill_process_on_port(port)
        
        # Wait a bit and verify
        time.sleep(1)
        if is_port_in_use(port):
            print(f"❌ Failed to free port {port}")
            print(f"   You may need to manually kill the process using this port")
            print(f"   Run: lsof -i :{port} or netstat -tulpn | grep {port}")
            return False
    return True


# ========================================
# PRIVILEGED COMMAND EXECUTION ENDPOINTS
# ========================================

@app.route('/api/privileged/execute', methods=['POST'])
def privileged_execute():
    """
    Execute a privileged (sudo) command. Requires special passphrase.
    
    Request Headers:
        X-Privileged-Passphrase: The privileged passphrase for sudo access
    
    Request Body:
        {
            "command": "sudo command to execute",
            "agent_id": "identifier for the AI agent",
            "timeout": 300,  // optional, default 300 seconds
            "working_dir": "/path/to/dir"  // optional
        }
    
    Returns:
        Execution result with stdout, stderr, and learning metadata
    """
    try:
        # Get passphrase from header
        passphrase = request.headers.get('X-Privileged-Passphrase')
        if not passphrase:
            return jsonify({
                'error': 'Missing X-Privileged-Passphrase header'
            }), 401
        
        # Verify passphrase
        priv_system = get_privileged_system()
        if not priv_system.verify_passphrase(passphrase):
            return jsonify({
                'error': 'Invalid passphrase'
            }), 403
        
        # Get request data
        data = request.get_json()
        command = data.get('command')
        agent_id = data.get('agent_id', 'unknown')
        timeout = data.get('timeout', 300)
        working_dir = data.get('working_dir')
        
        if not command:
            return jsonify({
                'error': 'Missing command field'
            }), 400
        
        # Execute privileged command
        result = priv_system.execute_privileged_command(
            command=command,
            agent_id=agent_id,
            timeout=timeout,
            working_dir=working_dir
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/privileged/history', methods=['GET'])
def privileged_history():
    """
    Get command execution history. No passphrase required - visible to all for learning.
    
    Query Parameters:
        agent_id: Filter by specific agent (optional)
        limit: Maximum number of results (default 100)
        success_only: Only return successful executions (default false)
    
    Returns:
        List of command execution records
    """
    try:
        agent_id = request.args.get('agent_id')
        limit = int(request.args.get('limit', 100))
        success_only = request.args.get('success_only', 'false').lower() == 'true'
        
        priv_system = get_privileged_system()
        history = priv_system.get_command_history(
            agent_id=agent_id,
            limit=limit,
            success_only=success_only
        )
        
        return jsonify({
            'count': len(history),
            'history': history
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/privileged/learning', methods=['GET'])
def privileged_learning():
    """
    Get learning insights from privileged command executions.
    No passphrase required - visible to all for learning and improvement.
    
    Returns:
        Learning insights including patterns, errors, and optimizations
    """
    try:
        priv_system = get_privileged_system()
        insights = priv_system.get_learning_insights()
        
        return jsonify(insights), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/privileged/improvements', methods=['GET'])
def privileged_improvements():
    """
    Get suggested service improvements based on command analysis.
    No passphrase required - visible to all for learning and improvement.
    
    Returns:
        List of suggested improvements with priorities
    """
    try:
        priv_system = get_privileged_system()
        improvements = priv_system.get_service_improvements()
        
        return jsonify({
            'count': len(improvements),
            'improvements': improvements
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/privileged/info', methods=['GET'])
def privileged_info():
    """
    Get information about the privileged system (without revealing passphrase).
    
    Returns:
        Passphrase metadata and system info
    """
    try:
        priv_system = get_privileged_system()
        info = priv_system.get_passphrase_info()
        
        return jsonify({
            'system': 'privileged_execution',
            'passphrase_info': info,
            'endpoints': {
                'execute': '/api/privileged/execute (POST, requires passphrase)',
                'history': '/api/privileged/history (GET, public)',
                'learning': '/api/privileged/learning (GET, public)',
                'improvements': '/api/privileged/improvements (GET, public)',
                'info': '/api/privileged/info (GET, public)'
            },
            'note': 'All command outputs are visible network-wide for learning purposes'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ==================== AIAGENTSTORAGE API ====================

# AIAGENTSTORAGE base path (use centralized path configuration)
# Previously hard-coded to external media mount. Now derives from PATHS so it can
# be overridden by AGENT_STORAGE_PATH env var and kept consistent across modules.
from path_config import PATHS as _PATHS_INTERNAL  # safe re-import; already imported above
AIAGENTSTORAGE_BASE = _PATHS_INTERNAL.get('agent_storage')

def is_safe_path(base_path, path, follow_symlinks=True):
    """Check if path is within base_path (security check)."""
    if follow_symlinks:
        return os.path.realpath(path).startswith(os.path.realpath(base_path))
    return os.path.abspath(path).startswith(os.path.abspath(base_path))


@app.route('/api/aiagentstorage/info', methods=['GET'])
def aiagentstorage_info():
    """
    Get information about AIAGENTSTORAGE system.
    
    Returns:
        Directory structure and available endpoints
    """
    try:
        if not os.path.exists(AIAGENTSTORAGE_BASE):
            return jsonify({
                'error': 'AIAGENTSTORAGE directory not found',
                'path': AIAGENTSTORAGE_BASE
            }), 404
        
        # Get directory stats
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for root, dirs, files in os.walk(AIAGENTSTORAGE_BASE):
            dir_count += len(dirs)
            file_count += len(files)
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        
        return jsonify({
            'system': 'AIAGENTSTORAGE',
            'base_path': AIAGENTSTORAGE_BASE,
            'status': 'available',
            'stats': {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directory_count': dir_count
            },
            'endpoints': {
                'info': 'GET /api/aiagentstorage/info - System information',
                'list': 'GET /api/aiagentstorage/list?path=<path> - List directory contents',
                'read': 'GET /api/aiagentstorage/read?path=<path> - Read file contents',
                'write': 'POST /api/aiagentstorage/write - Write file (body: {path, content, mode})',
                'delete': 'DELETE /api/aiagentstorage/delete?path=<path> - Delete file/directory',
                'mkdir': 'POST /api/aiagentstorage/mkdir - Create directory (body: {path})',
                'exists': 'GET /api/aiagentstorage/exists?path=<path> - Check if path exists',
                'tree': 'GET /api/aiagentstorage/tree?path=<path>&depth=<depth> - Get directory tree'
            },
            'note': 'Paths are relative to AIAGENTSTORAGE root. Use forward slashes.'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/list', methods=['GET'])
def aiagentstorage_list():
    """
    List contents of a directory in AIAGENTSTORAGE.
    
    Query params:
        path: Relative path (default: root)
    """
    try:
        rel_path = request.args.get('path', '').strip('/')
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path) if rel_path else AIAGENTSTORAGE_BASE
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        if not os.path.exists(full_path):
            return jsonify({
                'error': 'Path does not exist',
                'path': rel_path
            }), 404
        
        if not os.path.isdir(full_path):
            return jsonify({
                'error': 'Path is not a directory',
                'path': rel_path
            }), 400
        
        # List directory contents
        items = []
        for entry in os.listdir(full_path):
            entry_path = os.path.join(full_path, entry)
            entry_rel_path = os.path.join(rel_path, entry) if rel_path else entry
            
            try:
                stat = os.stat(entry_path)
                is_dir = os.path.isdir(entry_path)
                
                items.append({
                    'name': entry,
                    'path': entry_rel_path,
                    'type': 'directory' if is_dir else 'file',
                    'size': stat.st_size if not is_dir else None,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'permissions': oct(stat.st_mode)[-3:]
                })
            except Exception as e:
                items.append({
                    'name': entry,
                    'path': entry_rel_path,
                    'error': str(e)
                })
        
        return jsonify({
            'path': rel_path or '/',
            'full_path': full_path,
            'items': sorted(items, key=lambda x: (x.get('type') != 'directory', x['name'])),
            'count': len(items)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/read', methods=['GET'])
def aiagentstorage_read():
    """
    Read contents of a file in AIAGENTSTORAGE.
    
    Query params:
        path: Relative path to file
        encoding: Text encoding (default: utf-8)
        binary: Return base64 encoded binary data (default: false)
    """
    try:
        rel_path = request.args.get('path', '').strip('/')
        if not rel_path:
            return jsonify({
                'error': 'Path parameter is required'
            }), 400
        
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path)
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        if not os.path.exists(full_path):
            return jsonify({
                'error': 'File does not exist',
                'path': rel_path
            }), 404
        
        if not os.path.isfile(full_path):
            return jsonify({
                'error': 'Path is not a file',
                'path': rel_path
            }), 400
        
        encoding = request.args.get('encoding', 'utf-8')
        is_binary = request.args.get('binary', 'false').lower() == 'true'
        
        if is_binary:
            import base64
            with open(full_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
            content_type = 'binary'
        else:
            with open(full_path, 'r', encoding=encoding) as f:
                content = f.read()
            content_type = 'text'
        
        stat = os.stat(full_path)
        
        return jsonify({
            'path': rel_path,
            'content': content,
            'content_type': content_type,
            'encoding': encoding if not is_binary else 'base64',
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }), 200
        
    except UnicodeDecodeError:
        return jsonify({
            'error': 'File appears to be binary. Use binary=true parameter.',
            'path': rel_path
        }), 400
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/write', methods=['POST'])
def aiagentstorage_write():
    """
    Write content to a file in AIAGENTSTORAGE.
    
    Body (JSON):
        path: Relative path to file
        content: File content (string or base64 for binary)
        mode: 'write' (default) or 'append'
        encoding: Text encoding (default: utf-8)
        binary: Content is base64 encoded binary (default: false)
        create_dirs: Create parent directories if missing (default: true)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'JSON body is required'
            }), 400
        
        rel_path = data.get('path', '').strip('/')
        if not rel_path:
            return jsonify({
                'error': 'path is required'
            }), 400
        
        content = data.get('content', '')
        mode = data.get('mode', 'write')
        encoding = data.get('encoding', 'utf-8')
        is_binary = data.get('binary', False)
        create_dirs = data.get('create_dirs', True)
        
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path)
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        # Create parent directories if needed
        parent_dir = os.path.dirname(full_path)
        if create_dirs and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write file
        if is_binary:
            import base64
            binary_content = base64.b64decode(content)
            write_mode = 'ab' if mode == 'append' else 'wb'
            with open(full_path, write_mode) as f:
                f.write(binary_content)
        else:
            write_mode = 'a' if mode == 'append' else 'w'
            with open(full_path, write_mode, encoding=encoding) as f:
                f.write(content)
        
        stat = os.stat(full_path)
        
        return jsonify({
            'success': True,
            'path': rel_path,
            'full_path': full_path,
            'mode': mode,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/delete', methods=['DELETE'])
def aiagentstorage_delete():
    """
    Delete a file or directory in AIAGENTSTORAGE.
    
    Query params:
        path: Relative path to delete
        recursive: Delete directories recursively (default: false)
    """
    try:
        rel_path = request.args.get('path', '').strip('/')
        if not rel_path:
            return jsonify({
                'error': 'path parameter is required'
            }), 400
        
        recursive = request.args.get('recursive', 'false').lower() == 'true'
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path)
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        # Prevent deleting root
        if full_path == AIAGENTSTORAGE_BASE:
            return jsonify({
                'error': 'Cannot delete AIAGENTSTORAGE root directory'
            }), 403
        
        if not os.path.exists(full_path):
            return jsonify({
                'error': 'Path does not exist',
                'path': rel_path
            }), 404
        
        if os.path.isfile(full_path):
            os.remove(full_path)
            deleted_type = 'file'
        elif os.path.isdir(full_path):
            if recursive:
                import shutil
                shutil.rmtree(full_path)
                deleted_type = 'directory (recursive)'
            else:
                os.rmdir(full_path)
                deleted_type = 'directory'
        else:
            return jsonify({
                'error': 'Unknown file type',
                'path': rel_path
            }), 400
        
        return jsonify({
            'success': True,
            'path': rel_path,
            'deleted_type': deleted_type
        }), 200
        
    except OSError as e:
        if 'Directory not empty' in str(e):
            return jsonify({
                'error': 'Directory not empty. Use recursive=true to delete.',
                'path': rel_path
            }), 400
        return jsonify({
            'error': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/mkdir', methods=['POST'])
def aiagentstorage_mkdir():
    """
    Create a directory in AIAGENTSTORAGE.
    
    Body (JSON):
        path: Relative path to create
        parents: Create parent directories if missing (default: true)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'JSON body is required'
            }), 400
        
        rel_path = data.get('path', '').strip('/')
        if not rel_path:
            return jsonify({
                'error': 'path is required'
            }), 400
        
        parents = data.get('parents', True)
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path)
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        if os.path.exists(full_path):
            return jsonify({
                'error': 'Path already exists',
                'path': rel_path
            }), 409
        
        if parents:
            os.makedirs(full_path, exist_ok=True)
        else:
            os.mkdir(full_path)
        
        return jsonify({
            'success': True,
            'path': rel_path,
            'full_path': full_path
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/exists', methods=['GET'])
def aiagentstorage_exists():
    """
    Check if a path exists in AIAGENTSTORAGE.
    
    Query params:
        path: Relative path to check
    """
    try:
        rel_path = request.args.get('path', '').strip('/')
        if not rel_path:
            return jsonify({
                'error': 'path parameter is required'
            }), 400
        
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path)
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        exists = os.path.exists(full_path)
        
        result = {
            'path': rel_path,
            'exists': exists
        }
        
        if exists:
            stat = os.stat(full_path)
            result.update({
                'type': 'directory' if os.path.isdir(full_path) else 'file',
                'size': stat.st_size if os.path.isfile(full_path) else None,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/aiagentstorage/tree', methods=['GET'])
def aiagentstorage_tree():
    """
    Get directory tree structure from AIAGENTSTORAGE.
    
    Query params:
        path: Starting path (default: root)
        depth: Maximum depth (default: 3, max: 10)
    """
    try:
        rel_path = request.args.get('path', '').strip('/')
        max_depth = min(int(request.args.get('depth', 3)), 10)
        
        full_path = os.path.join(AIAGENTSTORAGE_BASE, rel_path) if rel_path else AIAGENTSTORAGE_BASE
        
        # Security check
        if not is_safe_path(AIAGENTSTORAGE_BASE, full_path):
            return jsonify({
                'error': 'Access denied: Path is outside AIAGENTSTORAGE'
            }), 403
        
        if not os.path.exists(full_path):
            return jsonify({
                'error': 'Path does not exist',
                'path': rel_path
            }), 404
        
        def build_tree(path, current_depth=0):
            """Recursively build directory tree."""
            if current_depth >= max_depth:
                return None
            
            try:
                items = []
                for entry in sorted(os.listdir(path)):
                    entry_path = os.path.join(path, entry)
                    entry_rel = os.path.relpath(entry_path, AIAGENTSTORAGE_BASE)
                    
                    stat = os.stat(entry_path)
                    is_dir = os.path.isdir(entry_path)
                    
                    item = {
                        'name': entry,
                        'path': entry_rel,
                        'type': 'directory' if is_dir else 'file',
                        'size': stat.st_size if not is_dir else None
                    }
                    
                    if is_dir:
                        children = build_tree(entry_path, current_depth + 1)
                        if children is not None:
                            item['children'] = children
                    
                    items.append(item)
                return items
            except PermissionError:
                return None
        
        tree = build_tree(full_path)
        
        return jsonify({
            'path': rel_path or '/',
            'max_depth': max_depth,
            'tree': tree
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# ============================================================================
# Mobile API Endpoints - For Mobile App Access via Persistent Tunnel
# ============================================================================

@app.route('/api/mobile/tunnel/start', methods=['POST'])
def mobile_tunnel_start():
    """Start persistent tunnel for mobile access."""
    try:
        # Use the currently configured server port instead of hardcoded 8000
        port = app.config.get('SERVER_PORT') or int(os.environ.get('PORT', '8000'))
        result = persistent_tunnel.start_tunnel(port=port)
        return api_ok(result)
    except Exception as e:
        return api_error(f"Failed to start tunnel: {str(e)}", status=500)

@app.route('/api/mobile/tunnel/stop', methods=['POST'])
def mobile_tunnel_stop():
    """Stop persistent tunnel."""
    try:
        result = persistent_tunnel.stop_tunnel()
        return api_ok(result)
    except Exception as e:
        return api_error(f"Failed to stop tunnel: {str(e)}", status=500)

@app.route('/api/mobile/tunnel/status', methods=['GET'])
def mobile_tunnel_status():
    """Get tunnel status."""
    try:
        status = persistent_tunnel.get_status()
        return api_ok(status)
    except Exception as e:
        return api_error(f"Failed to get status: {str(e)}", status=500)

@app.route('/api/mobile/config', methods=['GET'])
def mobile_config():
    """Get mobile app configuration including tunnel URL."""
    try:
        config = persistent_tunnel.get_mobile_config()
        return api_ok({
            'server': config,
            'features': {
                'data_storage': True,
                'file_management': True,
                'program_execution': True,
                'command_execution': True,
                'authentication': True
            },
            'version': '2.0.0'
        })
    except Exception as e:
        return api_error(f"Failed to get config: {str(e)}", status=500)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for mobile app."""
    return api_ok({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - getattr(app, '_start_time', time.time())
    })

# ============================================================================
# End Mobile API Endpoints
# ============================================================================


if __name__ == '__main__':
    def _extract_cli_port(argv):
        """Extract --port or --port=XXXX from CLI args if present."""
        for i, a in enumerate(argv):
            if a.startswith('--port='):
                return a.split('=', 1)[1]
            if a == '--port' and i + 1 < len(argv):
                return argv[i+1]
        return None

    requested_port = os.environ.get('PORT') or _extract_cli_port(sys.argv) or '8000'

    # Candidate list: user requested first, then common fallbacks
    _candidates = []
    try:
        _candidates.append(int(requested_port))
    except ValueError:
        print(f"⚠️  Invalid PORT value '{requested_port}', falling back to defaults")
    for c in (8000, 8080, 5000, 3000, 9000):
        if c not in _candidates:
            _candidates.append(c)

    PORT = None
    for cand in _candidates:
        if ensure_port_available(cand):
            PORT = cand
            break
    if PORT is None:
        print("❌ No available port found from candidates: " + ', '.join(map(str, _candidates)))
        sys.exit(1)

    os.environ['PORT'] = str(PORT)  # normalize
    app.config['SERVER_PORT'] = PORT
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("🚀 Starting Network Web Server")
    print("="*60)
    print(f"Server will be available at:")
    print(f"  Local:   http://localhost:{PORT}")
    print(f"  Network: http://{local_ip}:{PORT}")
    print("\nAPI Documentation:")
    print("  GET  /api/data          - Get all data")
    print("  POST /api/data          - Store data")
    print("  GET  /api/data/<key>    - Get data by key")
    print("  DELETE /api/data/<key>  - Delete data by key")
    print("  POST /api/execute       - Execute command")
    print("  GET  /health            - Health check")
    print("  POST /api/ngrok/start   - Start ngrok tunnel")
    print("  POST /api/ngrok/stop    - Stop ngrok tunnel")
    print("  GET  /api/ngrok/status  - Get ngrok status")
    print("  POST /api/files/upload  - Upload files")
    print("  GET  /api/files/list    - List uploaded files")
    print("  GET  /api/files/download/<filename> - Download file")
    print("  DELETE /api/files/delete/<filename> - Delete file")
    print("  GET  /api/files/storage - Get storage info")
    print("  POST /api/programs/upload - Upload executable programs")
    print("  GET  /api/programs/list  - List uploaded programs")
    print("  POST /api/programs/execute/<filename> - Execute program")
    print("  DELETE /api/programs/delete/<filename> - Delete program")
    print("  GET  /api/programs/info/<filename> - Get program info")
    print("\n📁 File Storage:")
    print("   5GB storage limit with file explorer interface")
    print("   Upload, download, and manage files through web interface")
    
    print("\n⚡ Program Management:")
    print("   Upload and execute programs/scripts directly on the server")
    print("   Supports Python, Shell, JavaScript, Perl, Ruby, and more")
    print("   Execution statistics tracking and secure sudo support")
    
    print("\n📁 Programs Terminal:")
    print("   Persistent terminal session in the programs directory")
    print(f"   All programs stored in: {os.path.abspath('data/programs')}")
    print("   Navigate and run commands directly in uploaded projects")
    
    print("\n🤖 AIAGENTSTORAGE API:")
    print("   GET  /api/aiagentstorage/info   - System information")
    print("   GET  /api/aiagentstorage/list   - List directory contents")
    print("   GET  /api/aiagentstorage/read   - Read file contents")
    print("   POST /api/aiagentstorage/write  - Write file")
    print("   DELETE /api/aiagentstorage/delete - Delete file/directory")
    print("   POST /api/aiagentstorage/mkdir  - Create directory")
    print("   GET  /api/aiagentstorage/exists - Check if path exists")
    print("   GET  /api/aiagentstorage/tree   - Get directory tree")
    print(f"   Base path: {AIAGENTSTORAGE_BASE}")
    
    print("\n🌐 Ngrok Integration:")
    print("   Use the web interface to start a public tunnel")
    print("   This will make your server accessible from anywhere!")
    print("\n⚠️  SECURITY WARNING: Server is accessible from your home network!")
    print("   Ngrok tunnel will make it accessible from ANYWHERE on the internet!")
    print("   Only use this in a trusted environment.")

    # Auto-start persistent tunnel for mobile access
    print("\n📱 Mobile Access Setup:")
    # To prevent accidental cloudflared installation/attempts during tests,
    # allow disabling auto-start via environment variable DISABLE_TUNNEL_AUTO=1
    if os.environ.get('DISABLE_TUNNEL_AUTO') != '1':
        print("   Starting persistent Cloudflare tunnel for mobile app...")
        tunnel_result = persistent_tunnel.start_tunnel(port=PORT)
        if tunnel_result.get('success'):
            print(f"   ✅ Mobile tunnel active: {tunnel_result.get('url')}")
            print(f"   📱 Use this URL in your mobile app")
            print(f"   🔒 Tunnel is hidden and secure (no public listing)")
        else:
            print(f"   ⚠️  Tunnel not started: {tunnel_result.get('message')}")
            print(f"   💡 Install cloudflared: wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared-linux-amd64.deb")
    else:
        print("   Auto-start of tunnel suppressed by DISABLE_TUNNEL_AUTO=1")

    print("\n💡 Tip: Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Store app start time
    app._start_time = time.time()

    try:
        app.run(host='0.0.0.0', port=PORT, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

