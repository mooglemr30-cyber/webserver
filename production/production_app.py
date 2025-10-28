"""
Production-ready Flask application with enhanced security, monitoring, and performance.
"""

import os
import sys
import logging
import signal
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.serving import WSGIRequestHandler
import ssl
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import production modules
try:
    from production.config.production_config import config
    from production.production_data_store import ProductionDataStore
    from src.security import RateLimiter, InputValidator, CSRFProtection, AuthenticationManager
    from src.enhanced_logging import setup_production_logging
    from src.monitoring import MetricsCollector, AlertManager
    from src.error_handling import ErrorHandler
    from src.performance import CacheManager
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Set up production logging
setup_production_logging(
    log_level=config.LOG_LEVEL,
    log_file=config.LOG_FILE,
    structured=config.STRUCTURED_LOGGING
)

logger = logging.getLogger(__name__)

class ProductionApp:
    """Production Flask application wrapper."""
    
    def __init__(self):
        self.app = None
        self.data_store = None
        self.metrics = None
        self.cache = None
        self.limiter = None
        self.error_handler = None
        self.auth_manager = None
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def create_app(self) -> Flask:
        """Create and configure the Flask application."""
        self.app = Flask(__name__)
        
        # Load configuration
        self._configure_app()
        
        # Initialize components
        self._initialize_components()
        
        # Setup middleware
        self._setup_middleware()
        
        # Register routes
        self._register_routes()
        
        # Setup error handlers
        self._setup_error_handlers()
        
        # Setup health checks
        self._setup_health_checks()
        
        logger.info("Production Flask application created successfully")
        return self.app
    
    def _configure_app(self) -> None:
        """Configure Flask application settings."""
        self.app.config.update({
            'SECRET_KEY': config.SECRET_KEY,
            'WTF_CSRF_SECRET_KEY': config.WTF_CSRF_SECRET_KEY,
            'MAX_CONTENT_LENGTH': config.MAX_CONTENT_LENGTH,
            'UPLOAD_FOLDER': config.UPLOAD_FOLDER,
            'DEBUG': config.DEBUG,
            'TESTING': config.TESTING,
            'PREFERRED_URL_SCHEME': 'https' if config.FORCE_HTTPS else 'http',
        })
        
        # Ensure upload directory exists
        os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    
    def _initialize_components(self) -> None:
        """Initialize application components."""
        # Data store with production features
        self.data_store = ProductionDataStore(
            data_file='data/production_storage.json',
            backup_enabled=config.BACKUP_ENABLED,
            backup_interval=config.BACKUP_INTERVAL,
            enable_sqlite=True,
            sqlite_db='data/production.db'
        )
        
        # Metrics and monitoring
        if config.METRICS_ENABLED:
            self.metrics = MetricsCollector()
            self.alert_manager = AlertManager(
                smtp_config={
                    'host': config.SMTP_HOST,
                    'port': config.SMTP_PORT,
                    'username': config.SMTP_USERNAME,
                    'password': config.SMTP_PASSWORD,
                    'use_tls': config.SMTP_USE_TLS,
                },
                alert_email_from=config.ALERT_EMAIL_FROM,
                alert_email_to=config.ALERT_EMAIL_TO
            )
        
        # Cache manager
        self.cache = CacheManager(
            redis_url=config.REDIS_URL,
            default_timeout=config.CACHE_DEFAULT_TIMEOUT,
            use_redis=True
        )
        
        # Authentication
        self.auth_manager = AuthenticationManager()
        
        # Error handling
        self.error_handler = ErrorHandler()
        
        logger.info("Application components initialized")
    
    def _setup_middleware(self) -> None:
        """Setup middleware for production."""
        # Proxy fix for reverse proxy deployments
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        
        # Compression
        if config.ENABLE_COMPRESSION:
            Compress(self.app)
        
        # Rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            storage_uri=config.RATE_LIMIT_STORAGE_URL,
            default_limits=["1000 per day", "100 per hour"]
        )
        
        # Security headers middleware
        @self.app.before_request
        def add_security_headers():
            """Add security headers to all responses."""
            g.start_time = time.time()
            
            # Force HTTPS in production
            if config.FORCE_HTTPS and not request.is_secure:
                if request.method == 'GET':
                    return redirect(request.url.replace('http://', 'https://'))
                else:
                    return jsonify({'error': 'HTTPS required'}), 400
        
        @self.app.after_request
        def set_security_headers(response):
            """Set security headers on response."""
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # Remove server header
            response.headers.pop('Server', None)
            
            # Record metrics
            if config.METRICS_ENABLED and hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                self.metrics.record_request(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status_code=response.status_code,
                    duration=duration
                )
            
            return response
    
    def _register_routes(self) -> None:
        """Register application routes."""
        
        @self.app.route('/', methods=['GET'])
        def index():
            """Main dashboard."""
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Production Web Server</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .header { text-align: center; border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }
                    .status { display: flex; justify-content: space-around; margin: 20px 0; }
                    .status-item { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px; }
                    .status-ok { border-left: 4px solid #28a745; }
                    .status-warning { border-left: 4px solid #ffc107; }
                    .status-error { border-left: 4px solid #dc3545; }
                    .api-section { margin-top: 30px; }
                    .endpoint { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 4px; font-family: monospace; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 Production Web Server</h1>
                        <p>Enhanced Flask server with security, monitoring, and performance features</p>
                    </div>
                    
                    <div class="status">
                        <div class="status-item status-ok">
                            <h3>✅ Server Status</h3>
                            <p>Running</p>
                        </div>
                        <div class="status-item status-ok">
                            <h3>🔒 Security</h3>
                            <p>Active</p>
                        </div>
                        <div class="status-item status-ok">
                            <h3>📊 Monitoring</h3>
                            <p>{{ 'Enabled' if metrics_enabled else 'Disabled' }}</p>
                        </div>
                        <div class="status-item status-ok">
                            <h3>💾 Data Store</h3>
                            <p>{{ storage_items }} items</p>
                        </div>
                    </div>
                    
                    <div class="api-section">
                        <h3>🔗 API Endpoints</h3>
                        <div class="endpoint">GET /health - Health check</div>
                        <div class="endpoint">GET /metrics - System metrics</div>
                        <div class="endpoint">GET /api/data - Get all data</div>
                        <div class="endpoint">POST /api/data - Store data</div>
                        <div class="endpoint">GET /api/data/&lt;key&gt; - Get specific data</div>
                        <div class="endpoint">DELETE /api/data/&lt;key&gt; - Delete data</div>
                        {% if command_execution_enabled %}
                        <div class="endpoint">POST /api/execute - Execute commands (⚠️ Use with caution)</div>
                        {% endif %}
                    </div>
                    
                    <div class="footer">
                        <p>Server Time: {{ server_time }}</p>
                        <p>Environment: Production | Version: 2.0.0</p>
                    </div>
                </div>
            </body>
            </html>
            ''', 
            metrics_enabled=config.METRICS_ENABLED,
            storage_items=self.data_store.size() if hasattr(self.data_store, 'size') else len(self.data_store.get_all()),
            command_execution_enabled=config.ENABLE_COMMAND_EXECUTION,
            server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
        
        @self.app.route('/api/data', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_all_data():
            """Get all stored data."""
            try:
                data = self.data_store.get_all()
                return jsonify({
                    'success': True,
                    'data': data,
                    'count': len(data),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting all data: {e}")
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
        
        @self.app.route('/api/data/<key>', methods=['GET'])
        @self.limiter.limit("200 per minute")
        def get_data(key):
            """Get data by key."""
            try:
                # Validate key
                if not InputValidator.validate_key(key):
                    return jsonify({'success': False, 'error': 'Invalid key format'}), 400
                
                value = self.data_store.get(key)
                if value is None:
                    return jsonify({'success': False, 'error': 'Key not found'}), 404
                
                return jsonify({
                    'success': True,
                    'key': key,
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting data for key '{key}': {e}")
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
        
        @self.app.route('/api/data', methods=['POST'])
        @self.limiter.limit("50 per minute")
        def store_data():
            """Store new data."""
            try:
                if not request.is_json:
                    return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
                
                data = request.get_json()
                if not data or 'key' not in data or 'value' not in data:
                    return jsonify({'success': False, 'error': 'Key and value are required'}), 400
                
                key = str(data['key'])
                value = data['value']
                
                # Validate inputs
                if not InputValidator.validate_key(key):
                    return jsonify({'success': False, 'error': 'Invalid key format'}), 400
                
                # Store data
                success = self.data_store.set(key, value)
                if not success:
                    return jsonify({'success': False, 'error': 'Failed to store data'}), 500
                
                return jsonify({
                    'success': True,
                    'message': 'Data stored successfully',
                    'key': key,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error storing data: {e}")
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
        
        @self.app.route('/api/data/<key>', methods=['DELETE'])
        @self.limiter.limit("30 per minute")
        def delete_data(key):
            """Delete data by key."""
            try:
                # Validate key
                if not InputValidator.validate_key(key):
                    return jsonify({'success': False, 'error': 'Invalid key format'}), 400
                
                success = self.data_store.delete(key)
                if not success:
                    return jsonify({'success': False, 'error': 'Key not found'}), 404
                
                return jsonify({
                    'success': True,
                    'message': 'Data deleted successfully',
                    'key': key,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error deleting data for key '{key}': {e}")
                return jsonify({'success': False, 'error': 'Internal server error'}), 500
        
        # Command execution (disabled by default in production)
        if config.ENABLE_COMMAND_EXECUTION:
            @self.app.route('/api/execute', methods=['POST'])
            @self.limiter.limit("5 per minute")
            def execute_command():
                """Execute system command (USE WITH EXTREME CAUTION)."""
                try:
                    if not request.is_json:
                        return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
                    
                    data = request.get_json()
                    if not data or 'command' not in data:
                        return jsonify({'success': False, 'error': 'Command is required'}), 400
                    
                    command = str(data['command'])
                    
                    # Security validation
                    is_safe, result = InputValidator.validate_command(command)
                    if not is_safe:
                        logger.warning(f"Blocked unsafe command from {request.remote_addr}: {command}")
                        return jsonify({'success': False, 'error': f'Command blocked: {result}'}), 400
                    
                    # Execute with timeout
                    import subprocess
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=os.path.dirname(__file__)
                        )
                        
                        return jsonify({
                            'success': True,
                            'command': command,
                            'return_code': result.returncode,
                            'stdout': result.stdout,
                            'stderr': result.stderr,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                    except subprocess.TimeoutExpired:
                        return jsonify({'success': False, 'error': 'Command timeout (30s limit)'}), 408
                    
                except Exception as e:
                    logger.error(f"Error executing command: {e}")
                    return jsonify({'success': False, 'error': 'Internal server error'}), 500
    
    def _setup_error_handlers(self) -> None:
        """Setup custom error handlers."""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'code': 404,
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'code': 429,
                'retry_after': error.retry_after,
                'timestamp': datetime.now().isoformat()
            }), 429
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 500,
                'timestamp': datetime.now().isoformat()
            }), 500
    
    def _setup_health_checks(self) -> None:
        """Setup health check endpoints."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Comprehensive health check."""
            try:
                # Check data store
                data_store_healthy, data_store_info = self.data_store.health_check()
                
                # Check cache
                cache_healthy = True
                try:
                    self.cache.get('__health_check__')
                except:
                    cache_healthy = False
                
                # Overall health
                overall_healthy = data_store_healthy and cache_healthy
                
                return jsonify({
                    'status': 'healthy' if overall_healthy else 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'checks': {
                        'data_store': {
                            'status': 'healthy' if data_store_healthy else 'unhealthy',
                            'details': data_store_info
                        },
                        'cache': {
                            'status': 'healthy' if cache_healthy else 'unhealthy'
                        },
                        'metrics': {
                            'status': 'healthy' if config.METRICS_ENABLED else 'disabled'
                        }
                    },
                    'version': '2.0.0',
                    'environment': 'production'
                }), 200 if overall_healthy else 503
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 503
        
        @self.app.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get system metrics."""
            if not config.METRICS_ENABLED:
                return jsonify({'error': 'Metrics disabled'}), 404
            
            try:
                metrics_data = {
                    'data_store': self.data_store.get_metrics(),
                    'timestamp': datetime.now().isoformat()
                }
                
                if hasattr(self.metrics, 'get_metrics'):
                    metrics_data['system'] = self.metrics.get_metrics()
                
                return jsonify(metrics_data)
                
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                return jsonify({'error': 'Failed to get metrics'}), 500

def create_production_app():
    """Factory function to create production app."""
    production_app = ProductionApp()
    return production_app.create_app()

def run_production_server():
    """Run the production server with appropriate configuration."""
    app = create_production_app()
    
    # SSL context for HTTPS
    ssl_context = None
    if config.SSL_CERT_PATH and config.SSL_KEY_PATH:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(config.SSL_CERT_PATH, config.SSL_KEY_PATH)
        logger.info("SSL/TLS enabled")
    
    # Custom request handler to hide server info
    class CustomRequestHandler(WSGIRequestHandler):
        server_version = "ProductionServer/2.0"
        sys_version = ""
    
    logger.info(f"Starting production server on {config.HOST}:{config.PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Metrics enabled: {config.METRICS_ENABLED}")
    logger.info(f"Command execution: {config.ENABLE_COMMAND_EXECUTION}")
    
    try:
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            ssl_context=ssl_context,
            request_handler=CustomRequestHandler,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == '__main__':
    run_production_server()