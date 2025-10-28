# Storage Systems

Comprehensive documentation of all storage systems used in the Localhost Web Server project.

## Table of Contents

1. [Overview](#overview)
2. [JSON Data Store](#json-data-store)
3. [File Storage System](#file-storage-system)
4. [Program Storage System](#program-storage-system)
5. [SQLite Databases](#sqlite-databases)
6. [Redis Cache](#redis-cache)
7. [Backup System](#backup-system)
8. [Storage Architecture](#storage-architecture)
9. [Data Models](#data-models)
10. [Storage Management](#storage-management)

---

## Overview

The application uses a multi-layered storage architecture with different systems for different data types:

| Storage Type | Purpose | Technology | Persistence | Size Limit |
|--------------|---------|------------|-------------|------------|
| **JSON Files** | Key-value data | JSON + fcntl | Persistent | ~1GB practical |
| **File System** | User uploads | Filesystem | Persistent | 5GB configurable |
| **Program Storage** | Uploaded programs/projects | Filesystem | Persistent | No limit |
| **SQLite** | Metrics, errors, logs | SQLite3 | Persistent | ~1TB theoretical |
| **Redis** | Cache, sessions | Redis (optional) | Volatile | RAM-limited |
| **Backups** | All data backups | tar.gz archives | Persistent | No limit |

### Storage Layout

```
data/
├── storage.json              # Main key-value data store
├── users.json                # User data (if auth enabled)
├── backups/                  # Backup archives
│   ├── backup_index.json     # Backup metadata
│   └── backup_*.tar.gz       # Compressed backups
├── config/                   # Configuration files
│   ├── feature_flags.json
│   ├── server_config.json
│   └── user_preferences.json
├── files/                    # User uploaded files
│   └── [filename_timestamp]  # Timestamped files
├── logs/                     # Application logs
│   ├── app.log
│   ├── error.log
│   ├── access.log
│   └── audit.log
└── programs/                 # Uploaded programs/projects
    ├── programs.json         # Program metadata
    ├── db/                   # SQLite databases
    │   ├── metrics.db
    │   └── errors.db
    ├── logs/                 # Program execution logs
    └── program_*/            # Individual program directories
        └── project_*/        # Project directories
```

---

## JSON Data Store

**Implementation**: `src/data_store.py` (130 lines)

### Purpose

Simple persistent key-value storage for application data, settings, and state.

### Features

- **Thread-safe**: Uses `fcntl` file locking for concurrent access
- **Atomic writes**: Writes to temp file then renames for crash safety
- **JSON format**: Human-readable and easily editable
- **Automatic initialization**: Creates storage file if missing
- **Error handling**: Comprehensive error handling with fallbacks

### Architecture

```python
class DataStore:
    """Thread-safe JSON key-value store with file locking"""
    
    def __init__(self, storage_file: str = "data/storage.json"):
        self.storage_file = storage_file
        self.lock = threading.Lock()
        self._ensure_storage_exists()
    
    def set(self, key: str, value: Any) -> None:
        """Store a key-value pair with atomic write"""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value by key"""
        
    def delete(self, key: str) -> bool:
        """Delete a key"""
        
    def get_all(self) -> Dict[str, Any]:
        """Get all stored data"""
```

### File Locking Strategy

```python
def _read_data(self) -> Dict:
    """Read data with shared lock (multiple readers allowed)"""
    with open(self.storage_file, 'r') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock
        try:
            return json.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

def _write_data(self, data: Dict) -> None:
    """Write data with exclusive lock (single writer)"""
    temp_file = f"{self.storage_file}.tmp"
    with open(temp_file, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    os.rename(temp_file, self.storage_file)  # Atomic replace
```

### Usage Examples

```python
# Initialize
data_store = DataStore("data/storage.json")

# Store data
data_store.set("user_preferences", {
    "theme": "dark",
    "language": "en",
    "notifications": True
})

# Retrieve data
prefs = data_store.get("user_preferences")
theme = prefs.get("theme", "light")

# Delete data
data_store.delete("temporary_data")

# Get all data
all_data = data_store.get_all()
```

### Data Schema

No enforced schema, but commonly stored data:

```json
{
  "user_preferences": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  },
  "app_settings": {
    "port": 8000,
    "debug": true,
    "log_level": "INFO"
  },
  "session_data": {
    "active_sessions": ["session-abc", "session-xyz"],
    "last_activity": "2024-01-01T12:00:00Z"
  },
  "feature_flags": {
    "enable_websockets": true,
    "enable_redis": false
  }
}
```

### Performance

- **Read**: O(1) with file I/O (< 10ms typical)
- **Write**: O(n) full file rewrite (< 50ms for < 1MB)
- **Concurrency**: Multiple readers, single writer
- **Bottleneck**: File I/O and JSON parsing for large files

### Limitations

- Not suitable for high-frequency writes (> 100/sec)
- Full file rewrite on every change
- No querying or indexing capabilities
- Size limited by memory (full file loaded on read)

### Best Practices

```python
# ✅ Good: Store small configuration data
data_store.set("config", {"port": 8000, "debug": True})

# ✅ Good: Store user preferences
data_store.set("user_123_prefs", {"theme": "dark"})

# ❌ Avoid: Large data sets
data_store.set("all_users", [1000+ users])  # Use SQLite instead

# ❌ Avoid: High-frequency updates
for i in range(1000):
    data_store.set(f"counter", i)  # Use Redis instead
```

---

## File Storage System

**Implementation**: `src/file_store.py` (300+ lines)

### Purpose

Secure file upload, storage, and management with quota enforcement and integrity checking.

### Features

- **Quota management**: 5GB default limit (configurable)
- **File validation**: Extension blacklist, size limits
- **Integrity checking**: SHA256 checksums
- **Metadata tracking**: Size, upload time, MIME type
- **Secure naming**: Timestamp-based unique filenames
- **Automatic cleanup**: Optional file expiration

### Architecture

```python
class FileStore:
    """Manages file uploads and storage with quotas"""
    
    def __init__(self, 
                 storage_dir: str = "data/files",
                 max_file_size: int = 100 * 1024 * 1024,  # 100MB
                 max_total_size: int = 5 * 1024 * 1024 * 1024):  # 5GB
        self.storage_dir = storage_dir
        self.max_file_size = max_file_size
        self.max_total_size = max_total_size
        self.metadata_file = os.path.join(storage_dir, "files_metadata.json")
        self._ensure_storage_exists()
    
    def upload_file(self, file) -> Dict[str, Any]:
        """Upload and store a file"""
        
    def get_file_path(self, filename: str) -> str:
        """Get full path to stored file"""
        
    def delete_file(self, filename: str) -> bool:
        """Delete a file and its metadata"""
        
    def list_files(self) -> List[Dict[str, Any]]:
        """List all files with metadata"""
        
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage usage information"""
```

### File Upload Flow

```
1. Receive file upload
   ├── Validate filename
   ├── Check extension against blacklist
   ├── Check file size < max_file_size
   └── Check total storage < max_total_size
   
2. Generate unique filename
   ├── Extract extension
   ├── Generate timestamp
   └── Format: {original_name}_{timestamp}.{ext}
   
3. Calculate checksums
   ├── SHA256 hash
   └── Store in metadata
   
4. Save file
   ├── Write to storage_dir
   ├── Verify write success
   └── Update metadata
   
5. Return file info
   ├── filename (storage name)
   ├── original_name
   ├── size
   ├── url
   └── checksum
```

### File Metadata Schema

```json
{
  "files": {
    "document_1640995200.pdf": {
      "original_name": "report.pdf",
      "filename": "document_1640995200.pdf",
      "size": 1048576,
      "size_mb": 1.0,
      "uploaded_at": "2024-01-01T12:00:00.000Z",
      "mime_type": "application/pdf",
      "hash": "abc123...",
      "uploader_ip": "127.0.0.1",
      "download_count": 0,
      "last_accessed": "2024-01-01T12:00:00.000Z"
    }
  },
  "total_size": 1048576,
  "file_count": 1
}
```

### Security Features

```python
# Blocked extensions
BLOCKED_EXTENSIONS = [
    '.exe', '.com', '.bat', '.cmd', '.vbs', 
    '.jar', '.msi', '.sh', '.ps1'
]

# Filename sanitization
def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from filename"""
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Limit length
    return filename[:255]

# Extension validation
def is_allowed_extension(filename: str) -> bool:
    """Check if file extension is allowed"""
    ext = os.path.splitext(filename)[1].lower()
    return ext not in BLOCKED_EXTENSIONS
```

### Quota Management

```python
def check_quota(self, file_size: int) -> Tuple[bool, str]:
    """Check if file upload would exceed quota"""
    current_usage = self.get_current_usage()
    
    # Check individual file size
    if file_size > self.max_file_size:
        return False, f"File too large. Max: {self.max_file_size / (1024**2)}MB"
    
    # Check total storage
    if current_usage + file_size > self.max_total_size:
        available = self.max_total_size - current_usage
        return False, f"Storage quota exceeded. Available: {available / (1024**2)}MB"
    
    return True, "OK"

def get_storage_info(self) -> Dict:
    """Get detailed storage information"""
    metadata = self._read_metadata()
    total_size = sum(f['size'] for f in metadata['files'].values())
    
    return {
        "used_bytes": total_size,
        "used_mb": total_size / (1024**2),
        "used_gb": total_size / (1024**3),
        "max_bytes": self.max_total_size,
        "max_gb": self.max_total_size / (1024**3),
        "available_bytes": self.max_total_size - total_size,
        "usage_percent": (total_size / self.max_total_size) * 100,
        "file_count": len(metadata['files'])
    }
```

### Performance Considerations

- **Upload speed**: Limited by disk I/O (typically 100-500 MB/s)
- **Checksum calculation**: CPU-bound for large files
- **Metadata updates**: JSON file rewrite (< 10ms)
- **List operations**: O(n) where n = file count

### Usage Examples

```python
# Initialize
file_store = FileStore(
    storage_dir="data/files",
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_total_size=5 * 1024 * 1024 * 1024  # 5GB
)

# Upload file (Flask route)
@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    result = file_store.upload_file(file)
    return jsonify(result)

# List files
files = file_store.list_files()

# Get storage info
storage_info = file_store.get_storage_info()

# Delete file
file_store.delete_file("document_1640995200.pdf")
```

---

## Program Storage System

**Implementation**: `src/program_store.py` (400+ lines)

### Purpose

Manage uploaded programs and projects with isolated storage, execution tracking, and metadata management.

### Features

- **Single file programs**: Python, Bash, JavaScript scripts
- **ZIP project support**: Multi-file projects with directory structure
- **Isolated storage**: Each program/project in separate directory
- **Execution tracking**: Track runs, outputs, errors
- **Metadata management**: Program info, statistics, logs
- **Main file detection**: Automatically detect entry points

### Architecture

```python
class ProgramStore:
    """Manages program/project storage and execution"""
    
    def __init__(self, storage_dir: str = "data/programs"):
        self.storage_dir = storage_dir
        self.metadata_file = os.path.join(storage_dir, "programs.json")
        self.db_dir = os.path.join(storage_dir, "db")
        self.logs_dir = os.path.join(storage_dir, "logs")
        self._initialize_storage()
    
    def upload_program(self, file) -> Dict[str, Any]:
        """Upload single program file"""
        
    def upload_project_zip(self, file, project_name: str = None) -> Dict[str, Any]:
        """Upload and extract ZIP project"""
        
    def get_program_path(self, program_id: str) -> str:
        """Get full path to program directory"""
        
    def execute_program(self, program_id: str, args: str = "") -> Dict[str, Any]:
        """Execute a program"""
        
    def list_programs(self) -> List[Dict[str, Any]]:
        """List all programs with metadata"""
```

### Storage Structure

```
data/programs/
├── programs.json                    # Metadata index
├── db/
│   ├── metrics.db                   # Execution metrics
│   └── errors.db                    # Error tracking
├── logs/
│   ├── program_1234_exec.log       # Execution logs
│   └── project_5678_exec.log
├── program_1234/                   # Single file program
│   ├── script.py
│   └── .metadata.json
└── project_5678/                   # ZIP project
    ├── main.py
    ├── utils.py
    ├── config.json
    ├── data/
    └── .metadata.json
```

### Program Metadata Schema

```json
{
  "programs": {
    "program_1640995200": {
      "program_id": "program_1640995200",
      "type": "single",
      "filename": "script.py",
      "original_name": "my_script.py",
      "language": "python",
      "size": 2048,
      "upload_time": "2024-01-01T12:00:00.000Z",
      "storage_path": "data/programs/program_1640995200/",
      "execution_count": 5,
      "last_executed": "2024-01-01T13:00:00.000Z",
      "success_count": 4,
      "error_count": 1,
      "avg_execution_time": 1.5
    },
    "project_1640995201": {
      "program_id": "project_1640995201",
      "type": "project",
      "filename": "my_project",
      "original_name": "my_project.zip",
      "main_file": "main.py",
      "file_count": 5,
      "files": ["main.py", "utils.py", "config.json", "data/"],
      "size": 10240,
      "upload_time": "2024-01-01T12:30:00.000Z",
      "storage_path": "data/programs/project_1640995201/",
      "execution_count": 2,
      "last_executed": "2024-01-01T14:00:00.000Z"
    }
  },
  "total_programs": 2,
  "total_projects": 1,
  "total_size": 12288
}
```

### ZIP Project Extraction

```python
def upload_project_zip(self, file, project_name: str = None) -> Dict:
    """Upload and extract ZIP project"""
    
    # Generate project ID
    project_id = f"project_{int(time.time())}"
    project_dir = os.path.join(self.storage_dir, project_id)
    
    # Save and validate ZIP
    zip_path = os.path.join(project_dir, "upload.zip")
    file.save(zip_path)
    
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Invalid ZIP file")
    
    # Extract with security checks
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Check for path traversal
        for member in zip_ref.namelist():
            if '..' in member or member.startswith('/'):
                raise ValueError("Unsafe ZIP contents")
        
        # Extract all files
        zip_ref.extractall(project_dir)
    
    # Remove ZIP file
    os.remove(zip_path)
    
    # Detect main file
    main_file = self._detect_main_file(project_dir)
    
    # Create metadata
    metadata = {
        "project_id": project_id,
        "type": "project",
        "main_file": main_file,
        "files": self._list_project_files(project_dir),
        "upload_time": datetime.utcnow().isoformat()
    }
    
    self._save_metadata(project_id, metadata)
    
    return metadata
```

### Main File Detection

```python
def _detect_main_file(self, project_dir: str) -> str:
    """Automatically detect project entry point"""
    
    # Common main file names
    main_file_candidates = [
        "main.py", "app.py", "run.py", "start.py",
        "index.js", "app.js", "main.js",
        "main.sh", "run.sh", "start.sh"
    ]
    
    # Check root directory
    for candidate in main_file_candidates:
        candidate_path = os.path.join(project_dir, candidate)
        if os.path.exists(candidate_path):
            return candidate
    
    # Check subdirectories
    for root, dirs, files in os.walk(project_dir):
        for candidate in main_file_candidates:
            if candidate in files:
                rel_path = os.path.relpath(
                    os.path.join(root, candidate),
                    project_dir
                )
                return rel_path
    
    # Default to first Python/JS file found
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.py', '.js')):
                rel_path = os.path.relpath(
                    os.path.join(root, file),
                    project_dir
                )
                return rel_path
    
    return None
```

### Execution Tracking

```python
def execute_program(self, program_id: str, args: str = "") -> Dict:
    """Execute program and track metrics"""
    
    metadata = self._get_metadata(program_id)
    program_path = self.get_program_path(program_id)
    
    # Determine execution command
    if metadata['type'] == 'single':
        file_path = os.path.join(program_path, metadata['filename'])
        command = self._build_command(file_path, args)
    else:  # project
        main_file = os.path.join(program_path, metadata['main_file'])
        command = self._build_command(main_file, args)
    
    # Execute with timing
    start_time = time.time()
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=program_path  # Run in program directory
    )
    execution_time = time.time() - start_time
    
    # Update metadata
    metadata['execution_count'] += 1
    metadata['last_executed'] = datetime.utcnow().isoformat()
    
    if result.returncode == 0:
        metadata['success_count'] += 1
    else:
        metadata['error_count'] += 1
    
    # Calculate average execution time
    total_time = metadata.get('total_execution_time', 0) + execution_time
    metadata['total_execution_time'] = total_time
    metadata['avg_execution_time'] = total_time / metadata['execution_count']
    
    self._save_metadata(program_id, metadata)
    
    # Log execution
    self._log_execution(program_id, command, result, execution_time)
    
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode,
        "execution_time": execution_time
    }
```

### SQLite Metrics Database

```sql
-- metrics.db schema

CREATE TABLE program_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id TEXT NOT NULL,
    command TEXT NOT NULL,
    arguments TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    execution_time REAL,
    return_code INTEGER,
    stdout_size INTEGER,
    stderr_size INTEGER,
    success BOOLEAN,
    error_message TEXT
);

CREATE INDEX idx_program_executions_program_id 
    ON program_executions(program_id);
CREATE INDEX idx_program_executions_start_time 
    ON program_executions(start_time);

-- Query examples
-- Get execution stats for program
SELECT 
    program_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
    AVG(execution_time) as avg_time,
    MAX(execution_time) as max_time
FROM program_executions
WHERE program_id = ?
GROUP BY program_id;

-- Get recent executions
SELECT * FROM program_executions
WHERE program_id = ?
ORDER BY start_time DESC
LIMIT 10;
```

---

## SQLite Databases

### Purpose

Structured data storage for metrics, errors, logs, and analytics.

### Databases

1. **metrics.db**: Performance and execution metrics
2. **errors.db**: Error tracking and analysis
3. **audit.db**: Audit logging

### Schema: metrics.db

```sql
-- HTTP request metrics
CREATE TABLE http_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INTEGER,
    duration REAL,
    request_size INTEGER,
    response_size INTEGER,
    ip_address TEXT,
    user_agent TEXT
);

-- System metrics
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cpu_percent REAL,
    memory_percent REAL,
    memory_mb REAL,
    disk_percent REAL,
    disk_mb REAL,
    active_connections INTEGER
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    tags TEXT  -- JSON
);

-- Indexes
CREATE INDEX idx_http_requests_timestamp ON http_requests(timestamp);
CREATE INDEX idx_http_requests_endpoint ON http_requests(endpoint);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
```

### Schema: errors.db

```sql
-- Error tracking
CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_id TEXT UNIQUE,
    category TEXT,
    severity TEXT,
    message TEXT NOT NULL,
    stack_trace TEXT,
    endpoint TEXT,
    method TEXT,
    request_data TEXT,  -- JSON
    user_id TEXT,
    ip_address TEXT,
    resolved BOOLEAN DEFAULT 0,
    resolved_at TIMESTAMP
);

-- Error occurrences (for duplicate tracking)
CREATE TABLE error_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context TEXT,  -- JSON
    FOREIGN KEY (error_id) REFERENCES errors(error_id)
);

-- Indexes
CREATE INDEX idx_errors_timestamp ON errors(timestamp);
CREATE INDEX idx_errors_category ON errors(category);
CREATE INDEX idx_errors_resolved ON errors(resolved);
```

### Performance Manager Integration

```python
class DatabaseManager:
    """Manage SQLite databases with connection pooling"""
    
    def __init__(self, db_dir: str = "data/programs/db"):
        self.db_dir = db_dir
        self.connections = {}  # Connection pool
        self._initialize_databases()
    
    def get_connection(self, db_name: str):
        """Get connection with pooling"""
        if db_name not in self.connections:
            db_path = os.path.join(self.db_dir, f"{db_name}.db")
            self.connections[db_name] = sqlite3.connect(
                db_path,
                check_same_thread=False
            )
        return self.connections[db_name]
    
    def record_http_request(self, method: str, endpoint: str, 
                           status: int, duration: float):
        """Record HTTP request metrics"""
        conn = self.get_connection('metrics')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO http_requests 
            (method, endpoint, status_code, duration)
            VALUES (?, ?, ?, ?)
        """, (method, endpoint, status, duration))
        conn.commit()
    
    def get_endpoint_metrics(self, endpoint: str, 
                            hours: int = 24) -> Dict:
        """Get metrics for specific endpoint"""
        conn = self.get_connection('metrics')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as request_count,
                AVG(duration) as avg_duration,
                MIN(duration) as min_duration,
                MAX(duration) as max_duration,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count
            FROM http_requests
            WHERE endpoint = ?
            AND timestamp > datetime('now', '-' || ? || ' hours')
        """, (endpoint, hours))
        
        result = cursor.fetchone()
        return {
            "request_count": result[0],
            "avg_duration": result[1],
            "min_duration": result[2],
            "max_duration": result[3],
            "error_count": result[4]
        }
```

---

## Redis Cache

**Implementation**: `src/performance.py` - CacheManager

### Purpose

High-performance caching for frequently accessed data and session storage.

### Features

- **Two-tier caching**: Memory (L1) + Redis (L2)
- **TTL support**: Automatic expiration
- **Cache invalidation**: Pattern-based deletion
- **Session storage**: Distributed session management
- **Rate limit storage**: Token bucket counters

### Architecture

```python
class CacheManager:
    """Two-tier cache: Memory (L1) + Redis (L2)"""
    
    def __init__(self, redis_url: str = None):
        self.memory_cache = {}  # L1 cache
        self.memory_ttl = {}
        self.redis_client = None
        
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
    
    def get(self, key: str) -> Any:
        """Get from L1, fallback to L2"""
        # Check L1
        if key in self.memory_cache:
            if self._is_valid(key):
                return self.memory_cache[key]
            else:
                del self.memory_cache[key]
        
        # Check L2 (Redis)
        if self.redis_client:
            value = self.redis_client.get(key)
            if value:
                # Promote to L1
                self.memory_cache[key] = json.loads(value)
                return self.memory_cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set in both L1 and L2"""
        # L1
        self.memory_cache[key] = value
        self.memory_ttl[key] = time.time() + ttl
        
        # L2
        if self.redis_client:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
```

### Cache Patterns

```python
# Cache-aside pattern
def get_user_data(user_id: str) -> Dict:
    """Get user with caching"""
    cache_key = f"user:{user_id}"
    
    # Try cache
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    # Cache miss - fetch from DB
    user_data = database.get_user(user_id)
    
    # Store in cache
    cache_manager.set(cache_key, user_data, ttl=600)
    
    return user_data

# Write-through pattern
def update_user_data(user_id: str, data: Dict):
    """Update user with cache"""
    # Update database
    database.update_user(user_id, data)
    
    # Update cache
    cache_key = f"user:{user_id}"
    cache_manager.set(cache_key, data, ttl=600)

# Cache invalidation
def invalidate_user_cache(user_id: str):
    """Invalidate user cache"""
    cache_key = f"user:{user_id}"
    cache_manager.delete(cache_key)
```

### Redis Data Structures

```python
# Session storage (Hash)
redis.hset(f"session:{session_id}", mapping={
    "user_id": "user_123",
    "created_at": "2024-01-01T12:00:00Z",
    "last_activity": "2024-01-01T12:30:00Z",
    "ip_address": "127.0.0.1"
})

# Rate limiting (String with TTL)
key = f"rate_limit:{ip}:{endpoint}"
redis.incr(key)
redis.expire(key, 60)  # 1 minute window

# Leaderboard (Sorted Set)
redis.zadd("program_executions", {
    "program_1": 100,
    "program_2": 250,
    "program_3": 175
})

# Recent items (List)
redis.lpush("recent_uploads", "file_123")
redis.ltrim("recent_uploads", 0, 99)  # Keep 100 most recent
```

---

## Backup System

**Implementation**: `src/backup_system.py` (800+ lines)

### Purpose

Automated backup and restore of all application data with integrity verification.

### Features

- **Full backups**: All data, files, programs, configs
- **Incremental backups**: Only changed files (planned)
- **Compression**: tar.gz format
- **Integrity verification**: Checksums for all backups
- **Automated scheduling**: Configurable backup intervals
- **Retention policies**: Automatic old backup cleanup
- **Selective restore**: Restore specific components

### Backup Contents

```
backup_2024-01-01_120000.tar.gz
├── storage.json
├── users.json
├── config/
│   ├── feature_flags.json
│   ├── server_config.json
│   └── user_preferences.json
├── files/
│   └── [all uploaded files]
├── programs/
│   ├── programs.json
│   └── [all programs/projects]
├── db/
│   ├── metrics.db
│   └── errors.db
└── backup_manifest.json
```

### Backup Manifest

```json
{
  "backup_id": "backup_2024-01-01_120000",
  "created_at": "2024-01-01T12:00:00.000Z",
  "type": "full",
  "files": [
    {
      "path": "storage.json",
      "size": 2048,
      "checksum": "abc123...",
      "modified": "2024-01-01T11:55:00.000Z"
    }
  ],
  "total_size": 52428800,
  "total_files": 150,
  "compression_ratio": 0.35,
  "checksum": "def456...",
  "integrity_verified": true
}
```

### Usage

```python
# Create backup
backup_manager = BackupManager("data/backups")
backup_info = backup_manager.create_backup()
# Returns: backup_id, file_path, size, checksum

# List backups
backups = backup_manager.list_backups()

# Restore from backup
backup_manager.restore_backup(backup_id="backup_2024-01-01_120000")

# Selective restore
backup_manager.restore_components(
    backup_id="backup_2024-01-01_120000",
    components=["storage.json", "config/"]
)

# Verify backup integrity
is_valid = backup_manager.verify_backup(backup_id)

# Cleanup old backups
backup_manager.cleanup_old_backups(keep_count=10)
```

---

## Storage Architecture

### Data Flow

```
Client Request
    ↓
Flask Route Handler
    ↓
┌─────────────────────┐
│  Storage Router     │
│  (determines type)  │
└─────────────────────┘
         ↓
    ┌────┴────┬─────────┬──────────┬─────────┐
    ↓         ↓         ↓          ↓         ↓
[JSON]   [Files]  [Programs]  [SQLite]  [Redis]
    ↓         ↓         ↓          ↓         ↓
 Disk     Disk      Disk       Disk      Memory
    ↓         ↓         ↓          ↓         ↓
    └─────────┴─────────┴──────────┴─────────┘
                     ↓
              Backup System
                     ↓
               tar.gz archives
```

### Storage Decision Matrix

| Data Type | Frequency | Size | Persistence | Storage Choice |
|-----------|-----------|------|-------------|----------------|
| Config | Low write | < 1MB | Critical | JSON |
| User preferences | Medium write | < 1MB | Critical | JSON |
| Session data | High R/W | Small | Temporary | Redis |
| Rate limit counters | Very high R/W | Tiny | Temporary | Redis |
| Uploaded files | Low write | Large | Critical | File System |
| Programs | Low write | Medium | Critical | File System |
| Metrics | High write | Growing | Important | SQLite |
| Error logs | Medium write | Growing | Important | SQLite |
| Cache | Very high R/W | Medium | Disposable | Redis + Memory |

---

## Data Models

### Storage Data Model

```python
@dataclass
class StoredData:
    """Key-value data model"""
    key: str
    value: Any
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

### File Data Model

```python
@dataclass
class StoredFile:
    """File metadata model"""
    filename: str
    original_name: str
    size: int
    mime_type: str
    hash: str
    uploaded_at: datetime
    uploader_ip: str
    download_count: int
    last_accessed: datetime
```

### Program Data Model

```python
@dataclass
class Program:
    """Program metadata model"""
    program_id: str
    type: Literal['single', 'project']
    filename: str
    original_name: str
    size: int
    upload_time: datetime
    storage_path: str
    execution_count: int
    last_executed: datetime
    success_count: int
    error_count: int
    avg_execution_time: float

@dataclass
class Project(Program):
    """Project-specific data"""
    main_file: str
    file_count: int
    files: List[str]
```

---

## Storage Management

### Disk Usage Monitoring

```python
def get_storage_usage() -> Dict:
    """Get comprehensive storage usage"""
    return {
        "data_store": {
            "size": os.path.getsize("data/storage.json"),
            "count": len(data_store.get_all())
        },
        "file_store": {
            "size": get_directory_size("data/files"),
            "count": len(file_store.list_files()),
            "quota_used": file_store.get_storage_info()['usage_percent']
        },
        "program_store": {
            "size": get_directory_size("data/programs"),
            "programs": program_store.get_storage_info()['total_programs'],
            "projects": program_store.get_storage_info()['total_projects']
        },
        "databases": {
            "size": get_directory_size("data/programs/db")
        },
        "backups": {
            "size": get_directory_size("data/backups"),
            "count": len(backup_manager.list_backups())
        },
        "total": get_directory_size("data/")
    }
```

### Cleanup Strategies

```python
# File cleanup (old files)
def cleanup_old_files(days: int = 30):
    """Remove files older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    files = file_store.list_files()
    
    for file in files:
        if file['uploaded_at'] < cutoff:
            if file['download_count'] == 0:  # Never downloaded
                file_store.delete_file(file['filename'])

# Database cleanup (old metrics)
def cleanup_old_metrics(days: int = 90):
    """Remove metrics older than specified days"""
    conn = db_manager.get_connection('metrics')
    conn.execute("""
        DELETE FROM http_requests
        WHERE timestamp < datetime('now', '-' || ? || ' days')
    """, (days,))
    conn.commit()
    
    # Vacuum to reclaim space
    conn.execute("VACUUM")

# Backup rotation
def rotate_backups(keep_count: int = 10):
    """Keep only N most recent backups"""
    backup_manager.cleanup_old_backups(keep_count)
```

### Performance Optimization

```python
# Database optimization
def optimize_databases():
    """Optimize all SQLite databases"""
    for db_name in ['metrics', 'errors']:
        conn = db_manager.get_connection(db_name)
        
        # Analyze for query optimization
        conn.execute("ANALYZE")
        
        # Rebuild indexes
        conn.execute("REINDEX")
        
        # Reclaim space
        conn.execute("VACUUM")

# Cache warming
def warm_cache():
    """Pre-load frequently accessed data"""
    # Load common configs
    cache_manager.set("server_config", 
                     config_manager.get_server_config())
    
    # Load recent programs
    recent = program_store.list_programs()[:10]
    for program in recent:
        cache_manager.set(
            f"program:{program['program_id']}",
            program,
            ttl=600
        )
```

---

## Best Practices

### 1. Choose the Right Storage

```python
# ✅ JSON for config (small, infrequent writes)
config_manager.set("server_port", 8000)

# ✅ Redis for sessions (high frequency, temporary)
session_cache.set(f"session:{session_id}", user_data, ttl=3600)

# ✅ SQLite for metrics (structured, queryable)
db_manager.record_http_request(method, endpoint, status, duration)

# ✅ File system for large files
file_store.upload_file(file)

# ❌ JSON for high-frequency data
for i in range(1000):
    data_store.set(f"counter", i)  # Too slow!

# ❌ File system for small data
with open("user_pref.txt", "w") as f:
    f.write(json.dumps(prefs))  # Use data_store instead!
```

### 2. Implement Caching

```python
# Cache expensive operations
@cache_result(ttl=300)
def get_dashboard_stats():
    """Cache dashboard stats for 5 minutes"""
    return {
        "total_programs": program_store.count(),
        "total_files": file_store.count(),
        "storage_used": get_storage_usage()
    }
```

### 3. Use Transactions

```python
# SQLite transactions for consistency
with db_manager.transaction('metrics'):
    db_manager.record_request(...)
    db_manager.update_stats(...)
    # Both commit or both rollback
```

### 4. Monitor Storage

```python
# Regular storage monitoring
@scheduler.every_hour
def check_storage():
    usage = get_storage_usage()
    
    if usage['file_store']['quota_used'] > 90:
        alert_manager.send_alert(
            "Storage quota nearly exceeded",
            severity="warning"
        )
```

### 5. Regular Backups

```python
# Automated backups
@scheduler.daily_at("02:00")
def create_daily_backup():
    backup_manager.create_backup()
    backup_manager.cleanup_old_backups(keep_count=7)
```

---

## Troubleshooting

### Storage Issues

**Problem**: "Storage quota exceeded"
```python
# Solution: Check usage and cleanup
usage = file_store.get_storage_info()
print(f"Usage: {usage['usage_percent']:.1f}%")

# Cleanup old files
cleanup_old_files(days=30)
```

**Problem**: "JSON file corrupted"
```python
# Solution: Restore from backup
backup_manager.restore_components(
    backup_id=latest_backup,
    components=["storage.json"]
)
```

**Problem**: "SQLite database locked"
```python
# Solution: Use WAL mode for better concurrency
conn = sqlite3.connect("metrics.db")
conn.execute("PRAGMA journal_mode=WAL")
```

### Performance Issues

**Problem**: Slow file uploads
```python
# Solution: Check disk I/O and quotas
import psutil

disk = psutil.disk_usage('/data')
print(f"Disk usage: {disk.percent}%")

io_counters = psutil.disk_io_counters()
print(f"Write speed: {io_counters.write_bytes / (1024**2):.2f} MB/s")
```

**Problem**: Slow database queries
```python
# Solution: Add indexes and optimize
conn.execute("CREATE INDEX idx_requests_timestamp ON http_requests(timestamp)")
conn.execute("ANALYZE")
```

---

## Summary

The storage system provides:

- **Multi-layered architecture**: Right storage for each data type
- **Thread-safe operations**: Concurrent access without corruption
- **Automatic backups**: Data protection and recovery
- **Performance optimization**: Caching, indexing, connection pooling
- **Quota management**: Prevent resource exhaustion
- **Integrity verification**: Checksums and validation

**Total Storage Capacity** (default configuration):
- JSON data: ~1GB practical limit
- File uploads: 5GB quota
- Programs: No limit
- SQLite databases: ~1TB theoretical
- Redis cache: RAM-limited
- Backups: No limit
