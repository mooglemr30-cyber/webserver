# Network Web Server - Installation Guide

Complete installation guide for setting up the Network Web Server on a new machine.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Install](#quick-install)
- [Manual Installation](#manual-installation)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Starting the Server](#starting-the-server)
- [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Required:
- **Python 3.8 or higher**
- **pip** (Python package manager)
- **500MB+ disk space** (for application and dependencies)
- **5GB+ recommended** (for file storage)

### Operating Systems:
- ✅ Linux (Ubuntu, Debian, Fedora, RHEL, etc.)
- ✅ macOS (10.14+)
- ✅ Windows 10/11

### System Dependencies:
- **libmagic** (for file type detection)
  - Ubuntu/Debian: `sudo apt install libmagic1`
  - Fedora/RHEL: `sudo dnf install file-libs`
  - macOS: `brew install libmagic`
  - Windows: Included in python-magic-bin

---

## 🚀 Quick Install

### Linux / macOS

```bash
# 1. Navigate to the webserver directory
cd /path/to/webserver

# 2. Run the installation script
./install.sh

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Start the server
python src/app.py
```

### Windows

```batch
REM 1. Navigate to the webserver directory
cd C:\path\to\webserver

REM 2. Run the installation script
install.bat

REM 3. Activate the virtual environment
.venv\Scripts\activate.bat

REM 4. Start the server
python src\app.py
```

The installation script will:
- ✅ Check system requirements
- ✅ Create all necessary directories
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Create initial configuration files
- ✅ Verify the installation

---

## 🛠️ Manual Installation

If you prefer to install manually or the script fails:

### Step 1: Install Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv libmagic1
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip file-libs
```

**macOS:**
```bash
brew install python3
brew install libmagic
```

**Windows:**
- Download Python from [python.org](https://www.python.org/downloads/)
- Check "Add Python to PATH" during installation

### Step 2: Create Directory Structure

```bash
# Main directories
mkdir -p data/{config,files,logs,programs,backups}
mkdir -p data/programs/{db,logs}
mkdir -p db logs

# Or use this one-liner
mkdir -p data/config data/files data/logs data/programs/db data/programs/logs data/backups db logs
```

### Step 3: Create Configuration Files

Create `data/storage.json`:
```json
{}
```

Create `data/users.json`:
```json
{}
```

Create `data/programs/programs.json`:
```json
{}
```

Create `data/backups/backup_index.json`:
```json
{"backups": []}
```

Create `data/config/server_config.json`:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": true
  },
  "storage": {
    "max_file_size_gb": 5.0,
    "max_program_size_mb": 500
  },
  "security": {
    "enable_rate_limiting": true,
    "max_requests_per_minute": 100
  }
}
```

Create `data/config/feature_flags.json`:
```json
{
  "features": {
    "file_storage": true,
    "program_execution": true,
    "terminal_access": true,
    "tunnel_services": true,
    "websockets": true
  }
}
```

### Step 4: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate.bat
```

### Step 5: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 6: Verify Installation

```bash
# Check Flask
python -c "import flask; print('Flask OK')"

# Check pexpect
python -c "import pexpect; print('pexpect OK')"

# Check directory structure
ls -la data/
```

---

## 📁 Directory Structure

After installation, your directory structure should look like this:

```
webserver/
├── .venv/                      # Python virtual environment
├── data/                       # Main data directory
│   ├── config/                 # Configuration files
│   │   ├── server_config.json
│   │   └── feature_flags.json
│   ├── files/                  # Uploaded files storage
│   ├── logs/                   # Application logs
│   ├── programs/               # Uploaded programs/projects
│   │   ├── db/                 # Program database files
│   │   ├── logs/               # Program execution logs
│   │   └── programs.json       # Programs metadata
│   ├── backups/                # Backup files
│   │   └── backup_index.json
│   ├── storage.json            # Data storage
│   └── users.json              # User data
├── db/                         # SQLite databases (if needed)
├── logs/                       # Root-level logs
├── src/                        # Source code
│   ├── app.py                  # Main application
│   ├── static/                 # CSS, JS files
│   └── templates/              # HTML templates
├── requirements.txt            # Python dependencies
├── install.sh                  # Linux/Mac installer
├── install.bat                 # Windows installer
└── README.md                   # Project documentation
```

---

## ⚙️ Configuration

### Server Configuration

Edit `data/config/server_config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",        // Listen on all interfaces
    "port": 8000,              // Port number
    "debug": true              // Debug mode (disable in production)
  },
  "storage": {
    "max_file_size_gb": 5.0,  // Maximum file storage size
    "max_program_size_mb": 500 // Maximum program size
  },
  "security": {
    "enable_rate_limiting": true,
    "max_requests_per_minute": 100
  }
}
```

### Feature Flags

Edit `data/config/feature_flags.json` to enable/disable features:

```json
{
  "features": {
    "file_storage": true,      // File upload/download
    "program_execution": true,  // Execute uploaded programs
    "terminal_access": true,    // Terminal command execution
    "tunnel_services": true,    // Ngrok/Localtunnel support
    "websockets": true          // WebSocket support
  }
}
```

---

## 🎬 Starting the Server

### Development Mode

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate.bat  # Windows

# Start the server
python src/app.py
```

The server will start on:
- **Local:** http://localhost:8000
- **Network:** http://YOUR_IP:8000

### Production Mode

For production deployment, use the production scripts:

```bash
# Linux/macOS
cd production/scripts
./deploy.sh

# Or use Docker
docker-compose -f production/docker/docker-compose.production.yml up -d
```

See `production/` directory for production deployment options.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Python not found

**Error:** `python3: command not found`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3

# macOS
brew install python3
```

#### 2. Permission denied on install.sh

**Error:** `Permission denied: ./install.sh`

**Solution:**
```bash
chmod +x install.sh
./install.sh
```

#### 3. Module not found errors

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Port already in use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in config
```

#### 5. libmagic not found

**Error:** `ImportError: failed to find libmagic`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install libmagic1

# macOS
brew install libmagic

# Windows
pip install python-magic-bin
```

#### 6. Redis connection failed

**Warning:** `Redis connection failed`

This is not critical - the server will use in-memory cache instead. To enable Redis:

```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS

# Start Redis
sudo systemctl start redis     # Linux
brew services start redis      # macOS
```

### Check Installation

Verify everything is working:

```bash
# Check directory structure
ls -la data/

# Check Python environment
which python
python --version

# Check installed packages
pip list | grep -E "flask|pexpect"

# Test server startup
python src/app.py
# Press Ctrl+C to stop after confirming it starts
```

### Getting Help

If you encounter issues:

1. Check the logs: `cat data/logs/*.log`
2. Run in debug mode: Edit `src/app.py` and set `debug=True`
3. Check system requirements are met
4. Verify all files/directories exist

---

## 🔄 Updating

To update the server on an existing installation:

```bash
# 1. Backup your data
cp -r data/ data_backup/

# 2. Pull latest code
git pull origin main  # If using git

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Update dependencies
pip install --upgrade -r requirements.txt

# 5. Restart server
python src/app.py
```

---

## 🔒 Security Notes

**⚠️ Important Security Considerations:**

1. **Change default settings** before exposing to the internet
2. **Use HTTPS** in production (see production deployment guide)
3. **Enable authentication** for sensitive operations
4. **Restrict file execution** permissions
5. **Limit network access** with firewall rules
6. **Monitor logs** regularly for suspicious activity

For production deployment, see the security guide in `docs/SECURITY.md`.

---

## 📚 Additional Resources

- [README.md](README.md) - Project overview
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture

---

## ✅ Installation Checklist

Use this checklist to verify your installation:

- [ ] Python 3.8+ installed
- [ ] System dependencies installed (libmagic, etc.)
- [ ] Virtual environment created (`.venv/`)
- [ ] All directories created (`data/`, `data/config/`, etc.)
- [ ] Configuration files created
- [ ] Python dependencies installed
- [ ] Server starts without errors
- [ ] Can access web interface at http://localhost:8000
- [ ] All features working (test upload, terminal, etc.)

---

**Installation complete! 🎉**

You're now ready to use the Network Web Server. Access it at **http://localhost:8000**
