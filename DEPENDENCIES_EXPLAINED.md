# DEPENDENCIES REQUIRED

## Core Dependencies (Must Have)

These are the ESSENTIAL packages needed to run the webserver:

### 1. Flask (Web Framework)
```
flask==2.3.3
```
This is the main web framework that runs your server.

### 2. Flask-CORS (Cross-Origin Requests)
```
flask-cors==4.0.0
```
Allows mobile app to connect from different domains.

### 3. Werkzeug (WSGI Utilities)
```
Werkzeug==2.3.7
```
Core utilities for Flask.

### 4. Requests (HTTP Library)
```
requests==2.31.0
```
For making HTTP requests.

## Additional Dependencies

These provide extra features:

- **prometheus-client==0.20.0** - Metrics and monitoring
- **pydantic==1.10.15** - Data validation
- **pexpect==4.8.0** - Terminal automation
- **flask-limiter==3.5.0** - Rate limiting
- **cryptography==41.0.7** - Security and encryption
- **bleach==6.1.0** - HTML sanitization
- **python-magic==0.4.27** - File type detection
- **redis==5.0.1** - Caching (optional)
- **flask-socketio==5.3.6** - WebSocket support
- **eventlet==0.33.3** - Async networking
- **aiofiles==23.2.1** - Async file operations
- **schedule==1.2.0** - Job scheduling
- **PyYAML==6.0.1** - YAML configuration
- **psutil==5.9.6** - System monitoring

## HOW TO INSTALL

### Method 1: Using Virtual Environment (Recommended)
```bash
cd /home/admin1/Documents/webserver
source .venv/bin/activate
pip install -r requirements.txt
```

### Method 2: User Installation (No Virtual Environment)
```bash
cd /home/admin1/Documents/webserver
pip3 install --user -r requirements.txt
```

### Method 3: Use Install Script
```bash
cd /home/admin1/Documents/webserver
chmod +x INSTALL_DEPENDENCIES.sh
bash INSTALL_DEPENDENCIES.sh
```

## QUICK INSTALL COMMAND

**Copy and paste this single command:**

```bash
cd /home/admin1/Documents/webserver && if [ -d ".venv" ]; then source .venv/bin/activate && pip install -r requirements.txt; else pip3 install --user -r requirements.txt; fi
```

This will:
1. Go to webserver directory
2. Check if virtual environment exists
3. Install all dependencies from requirements.txt

## VERIFICATION

After installation, verify Flask is installed:

```bash
python3 -c "import flask; print('Flask version:', flask.__version__)"
```

Should output: `Flask version: 2.3.3`

## TROUBLESHOOTING

### Error: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Flask is not installed. Run:
```bash
pip3 install --user flask flask-cors
```

### Error: "Permission denied"
**Solution:** Use `--user` flag:
```bash
pip3 install --user -r requirements.txt
```

### Error: "command not found: pip3"
**Solution:** Install pip first:
```bash
sudo apt-get update
sudo apt-get install python3-pip
```

### Virtual Environment Not Activating
**Solution:** Create new virtual environment:
```bash
cd /home/admin1/Documents/webserver
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## MINIMAL INSTALL (Just to Run Tests)

If you just want to run the tests quickly, install only the essentials:

```bash
pip3 install --user flask flask-cors requests
```

This gives you enough to:
- ✓ Run the webserver
- ✓ Run the tests
- ✓ Check mobile app integration

Full features need all dependencies, but tests will work with just these 3.

## SYSTEM DEPENDENCIES (Linux)

Some Python packages need system libraries:

```bash
# For python-magic
sudo apt-get install libmagic1

# For cryptography
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

# For redis (if using caching)
sudo apt-get install redis-server
```

**Note:** These are optional. The webserver will run without them.

## SUMMARY

**Essential packages (must have):**
- flask
- flask-cors
- Werkzeug
- requests

**Install command:**
```bash
cd /home/admin1/Documents/webserver
pip3 install --user -r requirements.txt
```

**Then run tests:**
```bash
python3 comprehensive_test.py
```

