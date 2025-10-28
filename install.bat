@echo off
REM ============================================================
REM Network Web Server - Installation Script (Windows)
REM ============================================================
REM This script sets up the complete environment for the web server
REM including Python virtual environment, dependencies, and directories
REM ============================================================

echo ============================================================
echo Network Web Server - Installation
echo ============================================================
echo.

REM Check for Python
echo [INFO] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo [SUCCESS] Python found
echo.

REM ============================================================
REM Step 1: Create directory structure
REM ============================================================
echo [INFO] Step 1/5: Creating directory structure...

if not exist "data" mkdir data
echo [SUCCESS] Created: data\

if not exist "data\config" mkdir data\config
echo [SUCCESS] Created: data\config\

if not exist "data\files" mkdir data\files
echo [SUCCESS] Created: data\files\

if not exist "data\logs" mkdir data\logs
echo [SUCCESS] Created: data\logs\

if not exist "data\programs" mkdir data\programs
echo [SUCCESS] Created: data\programs\

if not exist "data\programs\db" mkdir data\programs\db
if not exist "data\programs\logs" mkdir data\programs\logs
echo [SUCCESS] Created: data\programs\ subdirectories

if not exist "data\backups" mkdir data\backups
echo [SUCCESS] Created: data\backups\

if not exist "db" mkdir db
echo [SUCCESS] Created: db\

if not exist "logs" mkdir logs
echo [SUCCESS] Created: logs\

echo.

REM ============================================================
REM Step 2: Create initial configuration files
REM ============================================================
echo [INFO] Step 2/5: Creating initial configuration files...

if not exist "data\storage.json" (
    echo {}> data\storage.json
    echo [SUCCESS] Created: data\storage.json
) else (
    echo [WARNING] data\storage.json already exists, skipping
)

if not exist "data\users.json" (
    echo {}> data\users.json
    echo [SUCCESS] Created: data\users.json
) else (
    echo [WARNING] data\users.json already exists, skipping
)

if not exist "data\programs\programs.json" (
    echo {}> data\programs\programs.json
    echo [SUCCESS] Created: data\programs\programs.json
) else (
    echo [WARNING] data\programs\programs.json already exists, skipping
)

if not exist "data\backups\backup_index.json" (
    echo {"backups": []}> data\backups\backup_index.json
    echo [SUCCESS] Created: data\backups\backup_index.json
) else (
    echo [WARNING] data\backups\backup_index.json already exists, skipping
)

if not exist "data\config\server_config.json" (
    (
        echo {
        echo   "server": {
        echo     "host": "0.0.0.0",
        echo     "port": 8000,
        echo     "debug": true
        echo   },
        echo   "storage": {
        echo     "max_file_size_gb": 5.0,
        echo     "max_program_size_mb": 500
        echo   },
        echo   "security": {
        echo     "enable_rate_limiting": true,
        echo     "max_requests_per_minute": 100
        echo   }
        echo }
    ) > data\config\server_config.json
    echo [SUCCESS] Created: data\config\server_config.json
) else (
    echo [WARNING] data\config\server_config.json already exists, skipping
)

if not exist "data\config\feature_flags.json" (
    (
        echo {
        echo   "features": {
        echo     "file_storage": true,
        echo     "program_execution": true,
        echo     "terminal_access": true,
        echo     "tunnel_services": true,
        echo     "websockets": true
        echo   }
        echo }
    ) > data\config\feature_flags.json
    echo [SUCCESS] Created: data\config\feature_flags.json
) else (
    echo [WARNING] data\config\feature_flags.json already exists, skipping
)

echo.

REM ============================================================
REM Step 3: Create Python virtual environment
REM ============================================================
echo [INFO] Step 3/5: Creating Python virtual environment...

if exist ".venv" (
    echo [WARNING] Virtual environment already exists at .venv
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q .venv
        python -m venv .venv
        echo [SUCCESS] Virtual environment recreated
    ) else (
        echo [INFO] Using existing virtual environment
    )
) else (
    python -m venv .venv
    echo [SUCCESS] Virtual environment created at .venv
)

echo.

REM ============================================================
REM Step 4: Activate virtual environment and install dependencies
REM ============================================================
echo [INFO] Step 4/5: Installing Python dependencies...

call .venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

if exist "requirements.txt" (
    echo [INFO] Installing packages from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo [SUCCESS] All dependencies installed
) else (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo.

REM ============================================================
REM Step 5: Verify installation
REM ============================================================
echo [INFO] Step 5/5: Verifying installation...

python -c "import flask" 2>nul
if errorlevel 1 (
    echo [ERROR] Flask installation failed!
    pause
    exit /b 1
) else (
    echo [SUCCESS] Flask installed correctly
)

python -c "import pexpect" 2>nul
if errorlevel 1 (
    echo [WARNING] pexpect may not work on Windows
    echo [INFO] Installing pexpect-windows alternative...
    pip install wexpect
) else (
    echo [SUCCESS] pexpect installed correctly
)

echo.

REM ============================================================
REM Installation complete!
REM ============================================================
echo ============================================================
echo [SUCCESS] Installation completed successfully!
echo ============================================================
echo.
echo Quick Start Guide:
echo.
echo 1. Activate the virtual environment:
echo    .venv\Scripts\activate.bat
echo.
echo 2. Start the server:
echo    python src\app.py
echo.
echo 3. Access the web interface:
echo    http://localhost:8000
echo.
echo Directory Structure:
echo    data\           - Main data directory
echo    data\config\    - Configuration files
echo    data\files\     - Uploaded files
echo    data\logs\      - Application logs
echo    data\programs\  - Uploaded programs/projects
echo    data\backups\   - Backup files
echo.
echo Tips:
echo    - The server runs on port 8000 by default
echo    - Access from network: http://YOUR_IP:8000
echo    - Use Ctrl+C to stop the server
echo    - Check logs in data\logs\ for debugging
echo.
echo For more information, see README.md
echo.

pause
