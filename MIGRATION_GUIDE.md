# Migration Guide: v1.x to v2.0

This guide helps you migrate from earlier versions to v2.0, which includes major dependency updates.

## Breaking Changes

### Python Version Requirement

**Previous**: Python 3.8+  
**New**: Python 3.9+

**Reason**: Flask 3.x requires Python 3.9 or higher.

**Action Required**:
```bash
# Check your Python version
python3 --version

# If using Python 3.8, upgrade to Python 3.9 or higher before upgrading
```

### Flask & Werkzeug Major Version Updates

**Previous**:
- Flask 2.3.3
- Werkzeug 2.3.7

**New**:
- Flask 3.1.x
- Werkzeug 3.1.x

**Action Required**:
1. Review Flask 3.x changes: https://flask.palletsprojects.com/en/stable/changes/
2. Test all routes and endpoints after upgrading
3. Update any Flask extensions to versions compatible with Flask 3.x

### Security Improvements

#### 1. Default Admin Password

**Previous**: Hardcoded password `admin123`

**New**: Random secure password generated at first startup

**Action Required**:
1. After first startup, find password in: `data/config/admin_credentials.txt`
2. Log in with the generated password
3. Change password immediately using the API or UI
4. Delete `data/config/admin_credentials.txt` after changing password

#### 2. Privileged Execution Path

**Previous**: Hardcoded path `/run/media/admin1/...`

**New**: Configurable via `CREDENTIALS_DIR` environment variable

**Action Required**:
1. If you use privileged execution, set `CREDENTIALS_DIR` in `.env`
2. Remove any hardcoded paths from custom code

#### 3. Secret Keys

**Previous**: Example code used `"your-secret-key-here"`

**New**: Requires secure random keys from environment variables

**Action Required**:
1. Copy `.env.example` to `.env`
2. Generate secure keys:
   ```bash
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
   python -c "import secrets; print('CSRF_SECRET_KEY=' + secrets.token_urlsafe(32))"
   ```
3. Add keys to `.env` file

## Step-by-Step Migration

### 1. Backup Your Data

```bash
# Backup data directory
cp -r data data_backup_$(date +%Y%m%d)

# Backup configuration
cp .env .env.backup 2>/dev/null || true
```

### 2. Update Python Version

```bash
# Check Python version
python3 --version

# If using Python 3.8, upgrade to 3.9+
# On Ubuntu/Debian:
sudo apt update
sudo apt install python3.9 python3.9-venv

# On macOS with Homebrew:
brew install python@3.9
```

### 3. Update Dependencies

```bash
# Remove old virtual environment
rm -rf .venv

# Create new virtual environment with Python 3.9+
python3.9 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install updated dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set secure values
nano .env  # or use your preferred editor
```

Required changes in `.env`:
- Set `JWT_SECRET_KEY` to a secure random value
- Set `CSRF_SECRET_KEY` to a secure random value
- Configure other options as needed

### 5. Test the Application

```bash
# Run tests
python quick_feature_test.py

# Start the server
python src/app.py
```

### 6. Update Admin Password

1. Start the server
2. Find generated password in `data/config/admin_credentials.txt`
3. Log in as admin
4. Change password immediately
5. Delete `data/config/admin_credentials.txt`

### 7. Verify All Features

Test critical functionality:
- [ ] Authentication works
- [ ] File uploads work
- [ ] Data storage works
- [ ] Command execution works (if enabled)
- [ ] Program execution works
- [ ] Tunnels work (if used)
- [ ] WebSockets work (if used)

## Potential Issues and Solutions

### Issue: "ImportError: cannot import name 'url_decode' from 'werkzeug.urls'"

**Cause**: Old extension versions incompatible with Werkzeug 3.x

**Solution**: Update all Flask extensions:
```bash
pip install --upgrade flask-cors flask-socketio flask-limiter
```

### Issue: "RuntimeError: Working outside of application context"

**Cause**: Flask 3.x has stricter application context requirements

**Solution**: Ensure all operations that need app context are wrapped properly:
```python
with app.app_context():
    # Your code here
```

### Issue: Server fails to start with dependency errors

**Cause**: Incompatible dependency versions

**Solution**:
```bash
# Clear pip cache
pip cache purge

# Reinstall all dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Issue: Tests fail after upgrade

**Cause**: Test fixtures may need updates for Flask 3.x

**Solution**: Review Flask 3.x testing documentation and update test fixtures

## Rollback Plan

If you encounter critical issues:

1. **Stop the server**
2. **Restore backup**:
   ```bash
   # Remove new installation
   rm -rf .venv
   
   # Restore data
   rm -rf data
   cp -r data_backup_YYYYMMDD data
   
   # Checkout previous version
   git checkout v1.x
   
   # Reinstall old dependencies
   python3.8 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Restart server**

## Getting Help

- Check [SECURITY.md](SECURITY.md) for security-related issues
- Review [docs/](docs/) directory for detailed documentation
- Check GitHub issues for known problems
- Open a new issue if you encounter problems not covered here

## Changelog Summary

See [CHANGELOG.md](CHANGELOG.md) for complete details.

### Added
- `.env.example` for configuration
- `SECURITY.md` with security best practices
- `setup.py` for proper package installation
- `requirements-dev.txt` for development dependencies
- Improved security in CI/CD workflows

### Changed
- Flask: 2.3.3 → 3.1.x
- Werkzeug: 2.3.7 → 3.1.x
- cryptography: 41.0.7 → 42.0.x
- PyYAML: 6.0.1 → 6.0.3
- eventlet: 0.33.3 → 0.36.1
- Python requirement: 3.8+ → 3.9+
- Default admin password now randomly generated

### Security
- Removed hardcoded credentials
- Removed hardcoded file paths
- Added security scanning to CI/CD
- Added comprehensive security documentation
