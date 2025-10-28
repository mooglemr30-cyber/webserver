# System Architecture

## Table of Contents
1. [Overview](#overview)
2. [Architectural Layers](#architectural-layers)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Storage Architecture](#storage-architecture)
6. [Security Architecture](#security-architecture)
7. [Monitoring Architecture](#monitoring-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Design Patterns](#design-patterns)
10. [Technology Decisions](#technology-decisions)

## Overview

The Localhost Web Server follows a layered architecture pattern with clear separation of concerns. The system is built on Flask with modular components for data management, security, monitoring, and deployment.

### Architectural Principles
1. **Modularity**: Each module has single responsibility
2. **Loose Coupling**: Minimal dependencies between modules
3. **High Cohesion**: Related functionality grouped together
4. **Security by Design**: Security integrated at every layer
5. **Observability**: Comprehensive logging and monitoring
6. **Scalability**: Horizontal and vertical scaling support
7. **Maintainability**: Clear code structure and documentation

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   HTML/CSS   │  │  JavaScript  │  │  WebSocket   │          │
│  │   Templates  │  │   (main.js)  │  │   Client     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Flask      │  │    CORS      │  │   Rate       │          │
│  │   Router     │  │   Handler    │  │  Limiting    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Data    │  │   File   │  │ Program  │  │ Command  │        │
│  │  Store   │  │  Store   │  │  Store   │  │ Executor │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Cross-Cutting Concerns                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Security  │  │ Logging  │  │ Monitor  │  │  Cache   │        │
│  │ Manager  │  │ System   │  │  System  │  │ Manager  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data/Storage Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   JSON   │  │  SQLite  │  │  Redis   │  │   File   │        │
│  │  Files   │  │    DB    │  │  Cache   │  │  System  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. app.py - Main Application (1726 lines)
**Purpose**: Primary Flask application and request routing

**Key Responsibilities**:
- HTTP request handling and routing
- Middleware integration (CORS, rate limiting, metrics)
- Session management
- Tunnel service integration
- Port management and conflict resolution

**Major Functions**:
- `@app.before_request`: Request context setup, monitoring init
- `@app.after_request`: Metrics collection, structured logging
- `ensure_port_available()`: Check and free ports before startup
- `is_port_in_use()`: Socket-based port detection
- `find_process_using_port()`: Process identification with psutil
- `kill_process_on_port()`: Graceful then forceful process termination

**API Route Categories**:
```python
# Data operations (4 routes)
GET  /api/data              # Get all data
POST /api/data              # Store data
GET  /api/data/<key>        # Get by key
DELETE /api/data/<key>      # Delete by key

# File operations (5 routes)
POST /api/files/upload      # Upload file
GET  /api/files/list        # List files
GET  /api/files/download/<filename>
DELETE /api/files/delete/<filename>
GET  /api/files/storage-info

# Program operations (8 routes)
POST /api/programs/upload   # Upload program
POST /api/programs/upload-zip  # Upload ZIP project
GET  /api/programs/list     # List programs
POST /api/programs/execute/<filename>
POST /api/programs/execute-terminal/<project_id>
DELETE /api/programs/delete/<filename>
POST /api/programs/project/<project_id>/set-main
GET  /api/programs/storage-info

# Command execution (4 routes)
POST /api/execute           # Execute command
POST /api/execute/interactive  # Start interactive session
POST /api/execute/send-input   # Send input to session
POST /api/execute/terminate-session

# Tunnel management (9 routes)
POST /api/ngrok/start
POST /api/ngrok/stop
GET  /api/ngrok/status
POST /api/localtunnel/start
POST /api/localtunnel/stop
GET  /api/localtunnel/status
POST /api/cloudflared/start
POST /api/cloudflared/stop
GET  /api/cloudflared/status

# System operations (10+ routes)
GET  /health
GET  /metrics               # Prometheus metrics
GET  /api/v1/health
GET  /api/v1/programs/list
GET  /api/v1/dashboard
GET  /dashboard
```

**Dependencies**:
```python
from data_store import DataStore
from file_store import FileStore
from program_store import ProgramStore
from performance import CacheManager
# Conditionally imports monitoring, error_handling, etc.
```

### 2. data_store.py - Key-Value Storage (130 lines)
**Purpose**: Thread-safe JSON-based key-value storage

**Architecture**:
```python
class DataStore:
    def __init__(self, storage_file='data/storage.json'):
        self.storage_file = storage_file
        self.lock = threading.Lock()  # Thread-safe operations
    
    def get(key: str) -> Any:
        # File locking with fcntl
        # Atomic read operation
    
    def set(key: str, value: Any) -> bool:
        # File locking with fcntl
        # Atomic write with tempfile
        # Ensures consistency
    
    def delete(key: str) -> bool:
        # Atomic delete operation
    
    def get_all() -> dict:
        # Return all stored data
```

**Key Features**:
- **File Locking**: Uses `fcntl.flock()` for concurrent access
- **Atomic Writes**: Uses `tempfile` + `os.replace()` for atomicity
- **Thread Safety**: `threading.Lock()` for in-process synchronization
- **JSON Serialization**: Supports Python objects via `default=str`

**Data Flow**:
```
Request → Lock Acquisition → Read JSON → Unlock → Return Data
Request → Lock Acquisition → Read → Modify → Atomic Write → Unlock
```

### 3. file_store.py - File Management (300+ lines)
**Purpose**: File upload, download, and quota management

**Architecture**:
```python
class FileStore:
    def __init__(self, storage_dir='data/files', max_size_gb=5.0):
        self.storage_dir = storage_dir
        self.max_size_bytes = int(max_size_gb * 1024 * 1024 * 1024)
        self.metadata_file = '.file_metadata.json'
    
    def store_file(file_data: bytes, filename: str) -> Tuple[bool, str, str]:
        # Quota check
        # Filename sanitization
        # Duplicate handling
        # SHA256 checksum
        # Metadata storage
    
    def get_file(filename: str) -> Tuple[bool, bytes, Dict]:
        # File retrieval
        # Metadata lookup
    
    def delete_file(filename: str) -> Tuple[bool, str]:
        # File deletion
        # Metadata cleanup
    
    def list_files() -> List[Dict]:
        # List with metadata
        # Sorted by upload date
```

**Key Features**:
- **Quota Management**: 5GB default limit (configurable)
- **Filename Sanitization**: Removes dangerous characters, path traversal
- **MIME Type Detection**: Based on file extension
- **Checksum Generation**: SHA256 for integrity verification
- **Metadata Tracking**: Upload time, size, original name, MIME type

**Security Measures**:
- Dangerous character removal: `<>:"/\\|?*`
- Length limits (255 characters)
- Path traversal prevention
- MIME type validation
- Executable file blocking

### 4. program_store.py - Program Execution (400+ lines)
**Purpose**: Program upload, storage, and execution management

**Architecture**:
```python
class ProgramStore:
    def __init__(self, storage_dir='data/programs'):
        self.storage_dir = storage_dir
        self.metadata_file = 'programs.json'
        self.lock = threading.Lock()
    
    def store_program(file_data: bytes, filename: str) -> Tuple[bool, str, str]:
        # Create isolated directory: program_<timestamp>
        # Store file in isolated dir
        # Update metadata
    
    def store_multiple_files(files_dict: Dict, project_name: str) -> Tuple[bool, str, str]:
        # Create project directory: project_<timestamp>
        # Store all files with structure
        # Set main file
        # Update metadata
    
    def execute_program(filename: str, arguments: str, sudo_password: str = None) -> Dict:
        # Resolve program path
        # Build execution command
        # Handle sudo if needed
        # Execute and capture output
    
    def execute_project_terminal(project_id: str, command: str) -> Dict:
        # Resolve project directory
        # Execute command in project context
        # Return output
```

**Key Features**:
- **Isolated Storage**: Each program/project in own directory
- **Metadata Tracking**: Execution count, last executed, file info
- **Multiple File Types**: Single scripts and ZIP projects
- **Execution History**: Track all executions with timestamps
- **Terminal Mode**: Execute commands in project context

**Directory Structure**:
```
data/programs/
├── programs.json              # Metadata index
├── program_1234567890/        # Single program storage
│   └── script.py
├── program_1234567891/
│   └── script.sh
└── project_1234567892/        # Project storage
    ├── main.py
    ├── utils.py
    └── config.json
```

### 5. security.py - Security Module (800+ lines)
**Purpose**: Comprehensive security features

**Components**:

#### RateLimiter
```python
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = {}
        self.limits = {
            'api': {'requests': 100, 'window': 60},
            'upload': {'requests': 10, 'window': 60},
            'command': {'requests': 20, 'window': 60},
            'auth': {'requests': 5, 'window': 300},
            'tunnel': {'requests': 5, 'window': 300},
        }
    
    def is_allowed(client_ip: str, endpoint_type: str) -> bool:
        # Check if IP is blocked
        # Count requests in time window
        # Block if limit exceeded
        # Escalating block duration
```

#### InputValidator
```python
class InputValidator:
    @staticmethod
    def validate_email(email: str) -> bool
    
    @staticmethod
    def is_safe_sql(query: str) -> bool
    
    @staticmethod
    def contains_xss(content: str) -> bool
    
    @staticmethod
    def sanitize_string(input_string: str, max_length: int, allow_html: bool) -> str
    
    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]
    
    @staticmethod
    def validate_command(command: str) -> Tuple[bool, str]
    
    @staticmethod
    def validate_file_upload(file_data: bytes, filename: str) -> Tuple[bool, str]
```

#### CSRFProtection
```python
class CSRFProtection:
    @staticmethod
    def generate_token() -> str
    
    @staticmethod
    def validate_token(provided_token: str, session_token: str) -> bool
```

#### AuthenticationManager
```python
class AuthenticationManager:
    def __init__(self):
        self.sessions = {}
        self.users = self._load_users()
        self.failed_attempts = defaultdict(list)
    
    def authenticate(username: str, password: str, client_ip: str) -> Tuple[bool, str]
    
    def validate_session(session_id: str, client_ip: str) -> Tuple[bool, Optional[Dict]]
    
    def logout(session_id: str) -> bool
```

**Security Features**:
1. Rate Limiting: Per-endpoint, per-IP limits
2. Input Validation: SQL injection, XSS, command injection prevention
3. CSRF Protection: Token-based validation
4. Session Management: Timeout and IP validation
5. File Upload Scanning: MIME type and content validation
6. Command Whitelisting: Dangerous command blocking
7. Security Headers: X-Frame-Options, CSP, etc.

### 6. enhanced_logging.py - Logging System (600+ lines)
**Purpose**: Structured logging, performance monitoring, audit trails

**Components**:

#### StructuredFormatter
```python
class StructuredFormatter(logging.Formatter):
    def format(record) -> str:
        # JSON-formatted log entries
        # Include request_id, user_id, duration, status_code
        # Exception stack traces
```

#### PerformanceMonitor
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(lambda: {...})
    
    def record_request(endpoint: str, duration: float, status_code: int):
        # Track count, total_time, min, max, recent_times
        # Error counting
    
    def get_metrics() -> Dict[str, Any]:
        # Calculate averages, error rates
    
    def get_health_status() -> Dict[str, Any]:
        # Overall health status
        # Slow endpoint detection
```

#### AuditLogger
```python
class AuditLogger:
    def __init__(self, log_file='data/audit.log'):
        self.logger = logging.getLogger('audit')
    
    def log_auth_event(event, username, client_ip, success, details)
    def log_file_event(event, filename, user_id, client_ip, details)
    def log_command_event(command, user_id, client_ip, success, output_length)
    def log_security_event(event, details, client_ip, severity)
```

**Log Files**:
- `data/logs/application.log`: General application logs
- `data/logs/security.log`: Security events
- `data/logs/performance.log`: Performance metrics
- `data/logs/api.log`: API request logs
- `data/audit.log`: Audit trail

### 7. error_handling.py - Error Management (900+ lines)
**Purpose**: Comprehensive error handling, circuit breakers, retries

**Components**:

#### ErrorHandler
```python
class ErrorHandler:
    def __init__(self, db_path='data/errors.db'):
        self.db_path = db_path
        self.circuit_breakers = {}
        self.error_counts = defaultdict(int)
        self.recent_errors = deque(maxlen=1000)
    
    def handle_error(error, category, severity, request_id, user_id, endpoint, custom_message) -> ErrorDetails
    
    def get_error_statistics(hours=24) -> Dict[str, Any]
    
    def mark_error_resolved(error_id: str) -> bool
```

#### CircuitBreaker
```python
class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
    
    def call(func: Callable, *args, **kwargs):
        # Execute with circuit breaker protection
        # Open circuit after failure threshold
        # Half-open for testing recovery
        # Close after recovery threshold
```

#### RetryConfig & retry_with_backoff
```python
def retry_with_backoff(config: RetryConfig):
    # Exponential backoff
    # Jitter to prevent thundering herd
    # Max attempts with configurable delays
```

#### GracefulDegradation
```python
class GracefulDegradation:
    def __init__(self):
        self.degraded_services = set()
        self.fallback_handlers = {}
    
    def handle_with_fallback(service_name, primary_func, *args, **kwargs):
        # Try primary function
        # Fall back to degraded mode on failure
```

**Error Categories**:
- VALIDATION, AUTHENTICATION, AUTHORIZATION
- NOT_FOUND, RATE_LIMIT
- SYSTEM, NETWORK, DATABASE
- FILE_SYSTEM, EXTERNAL_SERVICE

**Error Severity Levels**:
- LOW, MEDIUM, HIGH, CRITICAL

### 8. monitoring.py - System Monitoring (1000+ lines)
**Purpose**: System metrics, alerting, performance tracking

**Components**:

#### MetricsCollector
```python
class MetricsCollector:
    def collect_system_metrics() -> SystemMetrics:
        # CPU usage (psutil)
        # Memory usage
        # Disk usage
        # Network I/O
        # Process count
        # Load average
        # Temperature (if available)
```

#### MetricsStorage
```python
class MetricsStorage:
    def __init__(self, db_path='data/metrics.db'):
        # SQLite tables: system_metrics, application_metrics, alerts
    
    def store_system_metrics(metrics: SystemMetrics)
    def store_application_metrics(metrics: ApplicationMetrics)
    def get_metrics_history(metric_type, hours) -> List[Dict]
```

#### AlertManager
```python
class AlertManager:
    def __init__(self, storage, config):
        self.default_thresholds = {
            'cpu_percent': {'warning': 80, 'critical': 95},
            'memory_percent': {'warning': 85, 'critical': 95},
            'disk_usage_percent': {'warning': 85, 'critical': 95},
            ...
        }
    
    def check_system_metrics(metrics: SystemMetrics) -> List[Alert]
    def check_application_metrics(metrics: ApplicationMetrics) -> List[Alert]
    def process_alerts(alerts: List[Alert])
```

#### MonitoringManager
```python
class MonitoringManager:
    def __init__(self, config):
        self.collector = MetricsCollector()
        self.storage = MetricsStorage()
        self.alert_manager = AlertManager(self.storage, config)
    
    def start_monitoring(interval=60):
        # Background thread
        # Collect metrics periodically
        # Check alerts
        # Store data
    
    def get_dashboard_data() -> Dict[str, Any]:
        # Current metrics
        # Historical data
        # Active alerts
```

**Metrics Tracked**:
- System: CPU, memory, disk, network, temperature
- Application: Requests, errors, response times, sessions
- Custom: File operations, command executions, cache hits

### 9. performance.py - Performance Optimization (600+ lines)
**Purpose**: Caching, database optimization, async operations

**Components**:

#### CacheManager
```python
class CacheManager:
    def __init__(self, redis_url, memory_cache_size, use_redis):
        self.memory_cache = {}  # LRU cache
        self.redis_client = redis.from_url(redis_url) if use_redis else None
    
    def set(namespace, key, value, ttl, compress) -> bool:
        # Try Redis first
        # Fall back to memory cache
        # Compression for large values
    
    def get(namespace, key) -> Optional[Any]:
        # Check Redis
        # Check memory cache
        # Decompress if needed
    
    def delete(namespace, key) -> bool
    def clear_namespace(namespace) -> bool
```

#### DatabaseManager
```python
class DatabaseManager:
    def __init__(self, db_path='data/webserver.db'):
        self.connection_pool = {}
        # SQLite with WAL mode, optimized PRAGMA settings
    
    def get_connection() -> sqlite3.Connection:
        # Thread-local connection pooling
        # Performance optimizations:
        # - journal_mode=WAL
        # - synchronous=NORMAL
        # - cache_size=10000
        # - temp_store=MEMORY
        # - mmap_size=268435456 (256MB)
```

#### AsyncFileManager
```python
class AsyncFileManager:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def read_file_async(file_path) -> Optional[bytes]
    async def write_file_async(file_path, content) -> bool
    def read_file_threaded(file_path) -> bytes
    def write_file_threaded(file_path, content) -> bool
```

#### CompressionManager
```python
class CompressionManager:
    @staticmethod
    def compress_response(data, compression_level=6) -> bytes
    
    @staticmethod
    def should_compress(content_type, size) -> bool
```

**Performance Strategies**:
1. **Caching**: Redis + Memory two-tier caching
2. **Connection Pooling**: Thread-local SQLite connections
3. **Async I/O**: aiofiles for file operations
4. **Compression**: Gzip for responses > 1KB
5. **Database Optimization**: WAL mode, MMAP, optimized cache

### 10. backup_system.py - Backup/Restore (800+ lines)
**Purpose**: Automated backup, restore, data migration

**Components**:

#### BackupManager
```python
class BackupManager:
    def __init__(self, backup_dir='data/backups', config_manager=None):
        self.backup_dir = backup_dir
        self.backup_lock = threading.Lock()
    
    def create_backup(backup_type='manual', description='') -> str:
        # Create tar.gz archive
        # Include: storage.json, files/, programs/, config/, logs/, users.json
        # Generate metadata
        # Calculate checksum
        # Save backup index
    
    def restore_backup(backup_name, components=None, overwrite=False) -> Tuple[bool, str]:
        # Verify integrity
        # Create restore point
        # Extract components
        # Revert on failure
    
    def list_backups() -> List[Dict[str, Any]]
    def delete_backup(backup_name) -> Tuple[bool, str]
```

**Backup Components**:
- data_storage: storage.json
- file_storage: data/files/
- program_storage: data/programs/
- configuration: data/config/
- logs: data/logs/ (recent only)
- user_data: users.json

**Backup Types**:
- **manual**: User-initiated backups
- **scheduled**: Automated backups (configurable interval)
- **restore_point**: Auto-created before restore operations

**Features**:
- Automated scheduling with configurable intervals
- Selective component restore
- Integrity verification (SHA256 checksums)
- Restore point creation (safety net)
- Backup retention policy (auto-cleanup old backups)
- Compression (tar.gz format)

## Data Flow

### 1. HTTP Request Flow
```
Client Request
    ↓
Flask Router (app.py)
    ↓
@app.before_request
    - Request ID generation
    - Start timer
    - Monitoring init
    ↓
Rate Limiter (security.py)
    - Check client IP
    - Enforce limits
    - Block if exceeded
    ↓
CSRF Validation (if POST/PUT/DELETE)
    - Validate token
    ↓
Route Handler
    - Business logic
    - Data store operations
    - File operations
    - Command execution
    ↓
Response Generation
    - JSON formatting
    - Error handling
    ↓
@app.after_request
    - Metrics collection
    - Structured logging
    - Security headers
    ↓
Client Response
```

### 2. File Upload Flow
```
Client Upload
    ↓
Flask Request Handler
    ↓
Security Validation
    - Filename sanitization
    - MIME type check
    - Size validation
    - Malicious content scan
    ↓
Quota Check
    - Calculate current usage
    - Check available space
    ↓
File Storage
    - Generate safe filename
    - Handle duplicates
    - Calculate checksum
    - Write to disk
    ↓
Metadata Storage
    - Update .file_metadata.json
    - Atomic write
    ↓
Response
    - Return filename and URL
```

### 3. Program Execution Flow
```
Client Request
    ↓
Program Store
    - Resolve program path
    - Load metadata
    ↓
Command Builder
    - Build execution command
    - Add arguments
    - Handle sudo if needed
    ↓
Executor
    - Create subprocess
    - Set environment
    - Set working directory
    ↓
Output Capture
    - Capture stdout
    - Capture stderr
    - Record exit code
    ↓
Metadata Update
    - Increment execution count
    - Update last_executed
    - Add to execution history
    ↓
Response
    - Return output and status
```

### 4. Interactive Command Flow
```
Client Request (start session)
    ↓
Session Creation
    - Generate session ID
    - Create pexpect spawn
    - Store in sessions dict
    ↓
Client sends input
    ↓
Session Lookup
    - Find session by ID
    ↓
Send to pexpect
    - Write to child stdin
    ↓
Read Output
    - Non-blocking read
    - Timeout handling
    ↓
Response
    - Return output
    - Check if waiting for input
```

### 5. Caching Flow
```
Request
    ↓
Cache Check
    - Generate cache key
    - Check Redis
    - Check memory cache
    ↓
Cache Hit?
    Yes → Return cached data
    No → Continue
    ↓
Execute Operation
    - Database query
    - File operation
    - External API call
    ↓
Cache Result
    - Store in Redis (if available)
    - Store in memory cache
    - Set TTL
    ↓
Return Result
```

## Storage Architecture

### File-Based Storage
```
data/
├── storage.json              # Key-value data
├── users.json                # User accounts
├── files/                    # Uploaded files
│   └── .file_metadata.json   # File metadata
├── programs/                 # Programs and projects
│   ├── programs.json         # Program metadata
│   ├── program_*/            # Isolated program storage
│   └── project_*/            # Isolated project storage
├── config/                   # Configuration
│   ├── server_config.json
│   ├── user_preferences.json
│   └── feature_flags.json
├── logs/                     # Application logs
│   ├── application.log
│   ├── security.log
│   ├── performance.log
│   └── api.log
├── backups/                  # Backup archives
│   ├── backup_index.json
│   └── backup_*.tar.gz
└── db/                       # SQLite databases
    ├── errors.db             # Error tracking
    └── metrics.db            # Metrics storage
```

### Database Schema (SQLite)

#### errors.db
```sql
CREATE TABLE errors (
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
);
```

#### metrics.db
```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL,
    memory_percent REAL,
    memory_available INTEGER,
    memory_used INTEGER,
    disk_usage_percent REAL,
    disk_free INTEGER,
    disk_used INTEGER,
    network_bytes_sent INTEGER,
    network_bytes_recv INTEGER,
    process_count INTEGER,
    load_average TEXT,
    temperature REAL
);

CREATE TABLE application_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    active_sessions INTEGER,
    total_requests INTEGER,
    failed_requests INTEGER,
    average_response_time REAL,
    database_connections INTEGER,
    cache_hit_rate REAL,
    websocket_connections INTEGER,
    file_operations INTEGER,
    command_executions INTEGER
);

CREATE TABLE alerts (
    id TEXT PRIMARY KEY,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    timestamp TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    acknowledged BOOLEAN DEFAULT FALSE,
    metric_type TEXT,
    threshold_value REAL,
    current_value REAL
);
```

## Security Architecture

### Security Layers

1. **Network Layer**
   - CORS configuration
   - Rate limiting per IP
   - IP blocking for abuse
   - Secure headers (CSP, X-Frame-Options, etc.)

2. **Application Layer**
   - CSRF token validation
   - Session management with timeouts
   - Input validation and sanitization
   - Command whitelisting
   - File upload scanning

3. **Data Layer**
   - File locking for concurrent access
   - Atomic writes for consistency
   - Checksum verification
   - Encryption support (configurable)

4. **Audit Layer**
   - Comprehensive audit logging
   - Security event tracking
   - Failed authentication monitoring
   - Command execution logging

### Authentication Flow
```
Login Request
    ↓
Rate Limit Check (5 attempts per 5 min)
    ↓
Credential Validation
    - Username lookup
    - Password hash verification (PBKDF2-HMAC-SHA256)
    ↓
Session Creation
    - Generate session ID (32-byte random)
    - Store session data
    - Set timeout (2 hours inactivity, 24 hours max)
    ↓
Return Session Token
    ↓
Subsequent Requests
    - Validate session ID
    - Check timeout
    - Validate IP (optional)
    - Update last activity
```

## Monitoring Architecture

### Metrics Collection
```
Monitoring Manager (background thread)
    ↓
[Every 60 seconds]
    ↓
System Metrics Collection
    - CPU, memory, disk, network
    - Process count, load average
    - Temperature
    ↓
Application Metrics Aggregation
    - Request counts and errors
    - Response times
    - Cache hit rates
    - Active sessions
    ↓
Alert Checking
    - Compare metrics to thresholds
    - Generate alerts
    - Send notifications
    ↓
Storage
    - Write to SQLite database
    - Cleanup old data (30 days)
```

### Alert Thresholds (Default)
```yaml
cpu_percent:
  warning: 80%
  critical: 95%

memory_percent:
  warning: 85%
  critical: 95%

disk_usage_percent:
  warning: 85%
  critical: 95%

load_average:
  warning: 2.0
  critical: 5.0

response_time:
  warning: 1000ms
  critical: 5000ms

temperature:
  warning: 70°C
  critical: 85°C
```

## Deployment Architecture

### Development
```
┌─────────────────────────┐
│   Flask Dev Server      │
│   (app.py)              │
│   Port 8000             │
└─────────────────────────┘
```

### Docker (Local)
```
┌─────────────────────────┐
│   Docker Container      │
│   ┌───────────────────┐ │
│   │ Flask App         │ │
│   │ Port 8000         │ │
│   └───────────────────┘ │
│   Volume Mounts:        │
│   - ./data:/app/data    │
└─────────────────────────┘
```

### Docker Compose (Recommended)
```
┌───────────────────────────────────────┐
│         Nginx (Reverse Proxy)         │
│         Ports: 80, 443                │
│         SSL/TLS Termination           │
└─────────────────┬─────────────────────┘
                  ↓
┌──────────────────────────────────────┐
│      Web Server Containers (3x)      │
│      ┌────────┐ ┌────────┐ ┌────┐   │
│      │  Web1  │ │  Web2  │ │Web3│   │
│      │  :8000 │ │  :8000 │ │:8000   │
│      └────────┘ └────────┘ └────┘   │
│      Load Balanced                   │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│         Redis Cache                  │
│         Port: 6379                   │
│         Persistent Volume            │
└──────────────────────────────────────┘
```

### Kubernetes (Production)
```
┌─────────────────────────────────────────┐
│            Ingress Controller           │
│            (Nginx/Traefik)              │
│            SSL/TLS, Rate Limiting       │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         Service (ClusterIP)             │
│         Load Balancing                  │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│    Deployment (webserver)               │
│    ┌─────┐ ┌─────┐ ┌─────┐             │
│    │Pod 1│ │Pod 2│ │Pod 3│             │
│    │:8000│ │:8000│ │:8000│             │
│    └─────┘ └─────┘ └─────┘             │
│    HPA: 2-10 replicas                   │
│    Resources: 256Mi-512Mi, 250m-500m    │
└────────────┬────────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│    PersistentVolumeClaims            │
│    - Data Volume (RWX)               │
│    - Logs Volume (RWX)               │
└──────────────────────────────────────┘
             ↓
┌──────────────────────────────────────┐
│    Redis Service (ClusterIP)         │
│    ┌──────────────────────┐          │
│    │  Redis Pod           │          │
│    │  :6379               │          │
│    └──────────────────────┘          │
└──────────────────────────────────────┘
```

## Design Patterns

### 1. Singleton Pattern
**Used in**: Configuration management, monitoring manager, error handler

```python
# Global instances
config_manager = ConfigManager()
monitoring_manager = None

def initialize_monitoring(config):
    global monitoring_manager
    monitoring_manager = MonitoringManager(config)
    return monitoring_manager

def get_monitoring_manager():
    return monitoring_manager
```

### 2. Factory Pattern
**Used in**: Error creation, alert generation

```python
class ErrorHandler:
    def handle_error(self, error, category, severity, ...):
        error_details = ErrorDetails(
            error_id=self._generate_id(),
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            category=category,
            severity=severity,
            ...
        )
        return error_details
```

### 3. Decorator Pattern
**Used in**: Route handlers, logging, caching, performance monitoring

```python
@app.route('/api/data', methods=['GET'])
@require_rate_limit('api')
@log_performance('data_operations')
@cache_result('data', ttl=60)
def get_all_data():
    return data_store.get_all()
```

### 4. Strategy Pattern
**Used in**: Caching (Redis vs Memory), storage backends

```python
class CacheManager:
    def set(self, key, value, ttl):
        if self.redis_client:
            return self.redis_client.setex(key, ttl, value)
        else:
            return self._memory_cache_set(key, value, ttl)
```

### 5. Observer Pattern
**Used in**: WebSocket notifications, monitoring alerts

```python
class WebSocketManager:
    def broadcast_to_topic(self, topic, message):
        for client_id in self.subscription_clients[topic]:
            self.send_to_client(client_id, message)
```

### 6. Circuit Breaker Pattern
**Used in**: External service calls, tunnel management

```python
class CircuitBreaker:
    def call(self, func, *args, **kwargs):
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

### 7. Command Pattern
**Used in**: Command execution, undo/redo operations

```python
class ProgramStore:
    def execute_program(self, filename, arguments):
        command = self._build_command(filename, arguments)
        result = self._execute_command(command)
        self._record_execution(filename, result)
        return result
```

## Technology Decisions

### Why Flask?
- **Lightweight**: Minimal overhead for small to medium applications
- **Flexible**: Easy to add modules and customize
- **Well-documented**: Extensive documentation and community support
- **Production-ready**: Used by many large-scale applications
- **WSGI compatible**: Can run with Gunicorn, uWSGI in production

### Why JSON for Storage?
- **Simplicity**: Easy to read, write, and debug
- **Human-readable**: Can inspect data files directly
- **Python native**: Built-in json module
- **Portability**: Cross-platform compatible
- **Version control friendly**: Text-based, easy to diff

**Trade-offs**:
- Limited scalability vs relational databases
- No built-in querying (need to load and filter)
- File locking required for concurrency
- **Mitigation**: SQLite for structured data (metrics, errors)

### Why SQLite for Metrics/Errors?
- **Zero-configuration**: No separate database server
- **Embedded**: Runs in-process
- **ACID compliant**: Reliable transactions
- **Good performance**: Sufficient for metrics and errors
- **SQL support**: Rich querying capabilities

**Trade-offs**:
- Limited concurrency vs PostgreSQL/MySQL
- No network access (embedded only)
- **Mitigation**: WAL mode for better concurrency

### Why pexpect for Interactive Commands?
- **PTY support**: Full terminal emulation
- **Input/output**: Can send input and capture output
- **Non-blocking**: Async operations possible
- **Pattern matching**: Can wait for specific output

**Trade-offs**:
- Unix/Linux only (no Windows support)
- **Mitigation**: Document Windows limitations

### Why Redis for Caching?
- **Fast**: In-memory operations
- **Persistent**: Optional disk persistence
- **Distributed**: Can be shared across instances
- **Rich data types**: Strings, lists, sets, hashes, etc.

**Trade-offs**:
- Additional dependency
- Network latency (if remote)
- **Mitigation**: Optional + memory fallback

### Why Docker/Kubernetes?
- **Reproducibility**: Consistent environments
- **Scalability**: Easy horizontal scaling
- **Isolation**: Security and dependency management
- **Deployment**: Simplified deployment process

**Trade-offs**:
- Learning curve
- Resource overhead
- **Mitigation**: Comprehensive documentation and examples

---

This architecture is designed to be:
1. **Modular**: Easy to extend and modify
2. **Secure**: Multiple layers of security
3. **Observable**: Comprehensive monitoring and logging
4. **Scalable**: Can grow from single server to distributed
5. **Maintainable**: Clear structure and documentation

For specific implementation details, see the individual module documentation files.
