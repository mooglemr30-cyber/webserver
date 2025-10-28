# Getting Started Guide

Quick start guide to set up and run the Localhost Web Server project.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Basic Usage](#basic-usage)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Prerequisites

### Required

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **pip**: Python package manager (included with Python)
- **Git**: For cloning the repository

### Optional

- **Redis**: For caching (improves performance)
- **Docker**: For containerized deployment
- **ngrok/localtunnel**: For public tunneling

### System Requirements

- **OS**: Linux, macOS, or Windows (WSL recommended)
- **RAM**: 512MB minimum, 2GB recommended
- **Disk**: 10GB free space (5GB for file storage + overhead)
- **Network**: Internet connection for package installation

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/webserver.git
cd webserver
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies installed:**
- Flask 2.3.3 (web framework)
- Flask-CORS (cross-origin support)
- pexpect (interactive commands)
- psutil (system monitoring)
- prometheus-client (metrics)
- pydantic (data validation)
- python-dotenv (environment variables)
- pyyaml (YAML configuration)
- redis (optional caching)

### 4. Initialize Data Directory

The application will create the data directory automatically on first run, but you can create it manually:

```bash
mkdir -p data/{files,programs,logs,backups,config}
```

### 5. Configuration (Optional)

Create a `.env` file for custom configuration:

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=True
PORT=8000
MAX_FILE_SIZE=104857600  # 100MB
MAX_STORAGE_SIZE=5368709120  # 5GB
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

---

## Quick Start

### Run the Server

**Basic (Development Mode):**
```bash
python src/app.py
```

**Using VS Code Task:**
```bash
# In VS Code: Terminal > Run Task > Start Web Server
# Or press Ctrl+Shift+B
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:8000
 * Press CTRL+C to quit
```

### Access the Application

Open your browser and navigate to:
- **Main Interface**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **API Health**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **API Docs**: http://localhost:8000/api/docs

### Verify Installation

**1. Check Health:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "2.0.0"
}
```

**2. Test Data Storage:**
```bash
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "Hello World"}'
```

**3. Get Data:**
```bash
curl http://localhost:8000/api/data/test
```

---

## Basic Usage

### 1. Store and Retrieve Data

**Using the Web Interface:**
1. Go to http://localhost:8000
2. In "Data Storage" section:
   - Enter key name: `user_settings`
   - Enter value: `{"theme": "dark", "lang": "en"}`
   - Click "💾 Store Data"
   - Click "Get" to retrieve

**Using API:**
```bash
# Store data
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "key": "settings",
    "value": {"theme": "dark"}
  }'

# Get data
curl http://localhost:8000/api/data/settings

# Get all data
curl http://localhost:8000/api/data

# Delete data
curl -X DELETE http://localhost:8000/api/data/settings
```

### 2. Upload and Manage Files

**Using the Web Interface:**
1. Go to http://localhost:8000
2. In "File Storage" section:
   - Click "Choose Files"
   - Select one or more files
   - Click "📤 Upload Files"
   - Files appear in the list with download links

**Using API:**
```bash
# Upload file
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@/path/to/yourfile.pdf"

# List files
curl http://localhost:8000/api/files/list

# Download file
curl -O http://localhost:8000/api/files/download/filename.pdf

# Check storage
curl http://localhost:8000/api/files/storage-info
```

### 3. Execute Commands

**Using the Web Interface:**
1. Go to http://localhost:8000
2. In "Command Terminal" section:
   - Select "Normal User" or "Root (sudo)"
   - Enter command: `ls -la`
   - Click "▶️ Execute"
   - View output in terminal

**Using API:**
```bash
# Execute command
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "pwd"}'

# Execute with sudo
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "command": "apt update",
    "sudo_password": "your-password"
  }'
```

### 4. Upload and Run Programs

**Upload Single Script:**
```bash
# Create a test script
echo 'print("Hello from Python!")' > test.py

# Upload
curl -X POST http://localhost:8000/api/programs/upload \
  -F "file=@test.py"

# Execute
curl -X POST http://localhost:8000/api/programs/execute/test.py
```

**Upload Project ZIP:**
```bash
# Create test project
mkdir my_project
echo 'print("Hello from project!")' > my_project/main.py
zip -r project.zip my_project/

# Upload
curl -X POST http://localhost:8000/api/programs/upload-zip \
  -F "file=@project.zip" \
  -F "project_name=my_project"

# Execute (using project_id from response)
curl -X POST http://localhost:8000/api/programs/execute-terminal/project_123 \
  -H "Content-Type: application/json" \
  -d '{"command": "python main.py"}'
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Server Configuration
PORT=8000
HOST=0.0.0.0
FLASK_ENV=development
FLASK_DEBUG=True

# Storage Configuration
DATA_DIR=data
MAX_FILE_SIZE=104857600  # 100MB in bytes
MAX_STORAGE_SIZE=5368709120  # 5GB in bytes

# Security
SECRET_KEY=your-secret-key-here
CSRF_ENABLED=True
RATE_LIMIT_ENABLED=True

# Optional: Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=False

# Optional: Authentication
AUTH_ENABLED=False
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_DIR=data/logs

# Monitoring
METRICS_ENABLED=True
PROMETHEUS_PORT=9090
```

### Feature Flags

Edit `data/config/feature_flags.json`:

```json
{
  "websockets": true,
  "redis_cache": false,
  "authentication": false,
  "rate_limiting": true,
  "file_uploads": true,
  "command_execution": true,
  "program_uploads": true,
  "tunnel_management": true,
  "backup_system": true,
  "monitoring": true
}
```

### Server Configuration

Edit `data/config/server_config.json`:

```json
{
  "server": {
    "port": 8000,
    "host": "0.0.0.0",
    "debug": true,
    "workers": 4
  },
  "storage": {
    "max_file_size_mb": 100,
    "max_total_size_gb": 5,
    "allowed_extensions": [".pdf", ".txt", ".jpg", ".png", ".zip"],
    "blocked_extensions": [".exe", ".com", ".bat"]
  },
  "security": {
    "rate_limit_per_minute": 100,
    "session_timeout": 3600,
    "csrf_enabled": true
  }
}
```

---

## Troubleshooting

### Port Already in Use

**Problem:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use a different port
PORT=8080 python src/app.py
```

### Permission Denied

**Problem:**
```
PermissionError: [Errno 13] Permission denied: 'data/storage.json'
```

**Solution:**
```bash
# Fix permissions
chmod -R 755 data/
```

### Module Not Found

**Problem:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Redis Connection Error

**Problem:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Option 1: Install and start Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis  # macOS
redis-server

# Option 2: Disable Redis in config
# Edit .env: REDIS_ENABLED=False
```

### Storage Quota Exceeded

**Problem:**
```
{"error": "Storage quota exceeded"}
```

**Solution:**
```bash
# Check storage usage
curl http://localhost:8000/api/files/storage-info

# Delete old files
curl -X DELETE http://localhost:8000/api/files/delete/old_file.pdf

# Or increase quota in .env
MAX_STORAGE_SIZE=10737418240  # 10GB
```

### Command Execution Fails

**Problem:**
```
{"error": "Command failed: command not found"}
```

**Solution:**
```bash
# Use full path
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "/usr/bin/python3 --version"}'

# Check PATH
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "echo $PATH"}'
```

---

## Next Steps

### Explore Features

1. **View Dashboard**: http://localhost:8000/dashboard
   - See system statistics
   - Monitor storage usage
   - View recent activity

2. **Try Interactive Commands**:
   - Start Python REPL
   - Run interactive scripts
   - Test sudo commands

3. **Upload Projects**:
   - Create ZIP of your project
   - Upload via API or UI
   - Execute in isolated environment

4. **Set Up Tunneling**:
   - Install ngrok or localtunnel
   - Expose server publicly
   - Access from anywhere

### Production Deployment

For production use, see:
- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**: Docker, Kubernetes, production setup
- **[SECURITY_GUIDE.md](./SECURITY_GUIDE.md)**: Security best practices
- **[MONITORING_GUIDE.md](./MONITORING_GUIDE.md)**: Monitoring and alerting

### Learn More

- **[API_REFERENCE.md](./API_REFERENCE.md)**: Complete API documentation
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: System architecture
- **[STORAGE_SYSTEMS.md](./STORAGE_SYSTEMS.md)**: Storage details
- **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)**: Project overview

### Get Help

- **Check Logs**: `data/logs/app.log`
- **View Errors**: `data/logs/error.log`
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## Common Workflows

### Workflow 1: Store Configuration Data

```bash
# Store app configuration
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "key": "app_config",
    "value": {
      "api_key": "abc123",
      "endpoint": "https://api.example.com",
      "timeout": 30
    }
  }'

# Retrieve when needed
curl http://localhost:8000/api/data/app_config
```

### Workflow 2: Backup Files

```bash
# Upload files
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@document1.pdf" \
  -F "file=@document2.pdf"

# List to verify
curl http://localhost:8000/api/files/list

# Download later
curl -O http://localhost:8000/api/files/download/document1_123.pdf
```

### Workflow 3: Run Scheduled Task

```python
# task.py
import requests
import schedule
import time

def backup_data():
    # Get all data
    response = requests.get('http://localhost:8000/api/data')
    data = response.json()
    
    # Save to file
    with open('backup.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Backup completed: {len(data.get('data', {}))} keys")

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(backup_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Workflow 4: Deploy Python Script

```bash
# Create script
cat > hello.py << 'EOF'
import sys
import json

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    result = {"message": f"Hello, {name}!", "status": "success"}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
EOF

# Upload
curl -X POST http://localhost:8000/api/programs/upload \
  -F "file=@hello.py"

# Execute with arguments
curl -X POST http://localhost:8000/api/programs/execute/hello.py \
  -H "Content-Type: application/json" \
  -d '{"arguments": "Alice"}'
```

---

## Quick Reference

### Most Used Endpoints

```bash
# Health check
GET /health

# Store data
POST /api/data
{
  "key": "mykey",
  "value": {"data": "value"}
}

# Get data
GET /api/data/mykey

# Upload file
POST /api/files/upload
Content-Type: multipart/form-data
file: <binary>

# Execute command
POST /api/execute
{
  "command": "ls -la"
}

# Dashboard
GET /dashboard
```

### Keyboard Shortcuts (Web UI)

- **Enter** in command input: Execute command
- **Enter** in interactive input: Send response
- **Ctrl+L**: Clear terminal output (when focused)

### Default Locations

- **Application**: `src/app.py`
- **Data Storage**: `data/storage.json`
- **File Uploads**: `data/files/`
- **Programs**: `data/programs/`
- **Logs**: `data/logs/`
- **Backups**: `data/backups/`
- **Config**: `data/config/`

---

## Support

For issues or questions:
1. Check logs in `data/logs/`
2. Review documentation in `docs/`
3. Check health endpoint: `/health`
4. View metrics: `/metrics`

**Happy coding! 🚀**
