# Installation Quick Reference

## One-Command Installation

### Linux / macOS
```bash
./install.sh && source .venv/bin/activate && python src/app.py
```

### Windows
```batch
install.bat
.venv\Scripts\activate.bat
python src\app.py
```

## What Gets Installed

### Directory Structure
```
webserver/
├── .venv/              # Virtual environment
├── data/
│   ├── config/         # Configuration files
│   ├── files/          # File uploads (5GB limit)
│   ├── logs/           # Application logs
│   ├── programs/       # Uploaded programs
│   ├── backups/        # Backup files
│   ├── storage.json    # Data storage
│   └── users.json      # User data
├── db/                 # SQLite databases
└── logs/               # Root-level logs
```

### Python Packages (18 total)
- flask==2.3.3
- flask-cors==4.0.0
- Werkzeug==2.3.7
- requests==2.31.0
- prometheus-client==0.20.0
- pydantic==1.10.15
- pexpect==4.8.0
- flask-limiter==3.5.0
- cryptography==41.0.7
- bleach==6.1.0
- python-magic==0.4.27
- redis==5.0.1
- flask-socketio==5.3.6
- eventlet==0.33.3
- aiofiles==23.2.1
- schedule==1.2.0
- PyYAML==6.0.1
- psutil==5.9.6

### Configuration Files
1. `data/storage.json` - Data key-value storage
2. `data/users.json` - User information
3. `data/programs/programs.json` - Programs metadata
4. `data/backups/backup_index.json` - Backup tracking
5. `data/config/server_config.json` - Server settings
6. `data/config/feature_flags.json` - Feature toggles

## System Requirements

### Minimum
- Python 3.8+
- 500MB disk space
- 512MB RAM

### Recommended
- Python 3.10+
- 5GB+ disk space (for file storage)
- 2GB+ RAM
- libmagic (for file type detection)

## Installation Steps

The install script performs these steps:

1. **Check Requirements**
   - Verify Python 3.8+
   - Check pip availability
   - Verify system dependencies

2. **Create Directories**
   - data/ and subdirectories
   - db/ and logs/
   - All required paths

3. **Initialize Configs**
   - Create JSON files
   - Set default configurations
   - Initialize empty storage

4. **Setup Environment**
   - Create .venv/
   - Upgrade pip
   - Install all requirements

5. **Verify Installation**
   - Test imports
   - Verify directories
   - Check file permissions

## Quick Commands

### Start Server
```bash
source .venv/bin/activate  # Activate environment
python src/app.py          # Start server
```

### Access
- Local: http://localhost:8000
- Network: http://YOUR_IP:8000

### Stop Server
Press `Ctrl+C` in the terminal

## Troubleshooting

### Python not found
```bash
# Ubuntu/Debian
sudo apt install python3

# macOS
brew install python3
```

### libmagic missing
```bash
# Ubuntu/Debian
sudo apt install libmagic1

# macOS
brew install libmagic
```

### Port 8000 in use
```bash
# Find process
lsof -i :8000  # Linux/macOS

# Or change port in data/config/server_config.json
```

### Permission denied
```bash
chmod +x install.sh  # Make script executable
```

### Module not found
```bash
source .venv/bin/activate  # Activate environment
pip install -r requirements.txt  # Reinstall
```

## Files Created by Install Script

### Executables
- `.venv/bin/python` (or .venv\Scripts\python.exe on Windows)
- `.venv/bin/activate`

### Data Files
- `data/storage.json` - Empty object {}
- `data/users.json` - Empty object {}
- `data/programs/programs.json` - Empty object {}
- `data/backups/backup_index.json` - {"backups": []}
- `data/config/server_config.json` - Default server config
- `data/config/feature_flags.json` - All features enabled

### Directories
Total of 9 directories created:
1. data/
2. data/config/
3. data/files/
4. data/logs/
5. data/programs/
6. data/programs/db/
7. data/programs/logs/
8. data/backups/
9. db/
10. logs/

## Post-Installation

### First Run Checklist
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] Data storage works (test store/retrieve)
- [ ] File upload works
- [ ] Terminal commands execute
- [ ] Programs can be uploaded

### Optional Setup
1. Configure Redis for better caching
2. Set up ngrok for public access
3. Configure firewall rules
4. Set up SSL/HTTPS (production)
5. Enable authentication (production)

## Production Deployment

For production, see:
- `production/` directory
- Docker deployment options
- Kubernetes configs
- Security hardening guide

## Getting Help

- Check logs: `cat data/logs/*.log`
- Debug mode: Set `debug: true` in config
- Full docs: See INSTALL.md
- Troubleshooting: See INSTALL.md § Troubleshooting

## Uninstall

```bash
# Remove virtual environment
rm -rf .venv/

# Remove data (CAREFUL - deletes all data!)
rm -rf data/ db/ logs/

# Or keep data and just remove venv
rm -rf .venv/
```

---

**Installation time:** ~2-5 minutes  
**First run time:** Instant  
**Documentation:** INSTALL.md for full details
