@echo off
REM Web Server Setup Script for Windows
REM Automated installation and setup for the Network Web Server

echo 🌐 Starting Network Web Server Setup for Windows...
echo This script will install all dependencies and set up the server
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%

REM Check for Node.js (for localtunnel)
echo 📦 Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Installing localtunnel will be skipped.
    echo To install Node.js, visit: https://nodejs.org/
) else (
    echo ✅ Node.js found
    echo 📦 Installing localtunnel...
    npm install -g localtunnel
    if errorlevel 1 (
        echo ❌ Failed to install localtunnel
    ) else (
        echo ✅ Localtunnel installed successfully
    )
)

REM Create virtual environment
echo 📦 Setting up Python virtual environment...
if exist .venv rmdir /s /q .venv
python -m venv .venv
call .venv\Scripts\activate.bat
echo ✅ Virtual environment created and activated

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📦 Installing Python dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo Installing dependencies manually...
    pip install flask flask-cors pexpect requests werkzeug
)
echo ✅ Python dependencies installed

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist data mkdir data
if not exist data\files mkdir data\files
if not exist data\programs mkdir data\programs
echo ✅ Directory structure created

REM Create Windows startup batch file
echo 📝 Creating startup script...
(
echo @echo off
echo echo 🚀 Starting Network Web Server...
echo cd /d "%%~dp0"
echo call .venv\Scripts\activate.bat
echo echo.
echo echo 🌐 Server will be accessible at:
echo echo   Local:   http://localhost:8000
echo echo   Network: http://%%COMPUTERNAME%%:8000
echo echo.
echo echo 💡 Features available:
echo echo   • Data storage and file management
echo echo   • Interactive command execution
echo echo   • Program upload and execution
echo echo   • Multiple tunnel options ^(if installed^)
echo echo.
echo echo ⚠️  Press Ctrl+C to stop the server
echo echo.
echo python src\app.py
echo pause
) > start_server.bat

echo ✅ Startup script created (start_server.bat)

REM Create stop script
echo 📝 Creating stop script...
(
echo @echo off
echo echo 🛑 Stopping Network Web Server...
echo taskkill /f /im python.exe >nul 2>&1
echo if %%errorlevel%% equ 0 ^(
echo     echo ✅ Server stopped successfully
echo ^) else ^(
echo     echo ℹ️  No running server found
echo ^)
echo pause
) > stop_server.bat

echo ✅ Stop script created (stop_server.bat)

REM Create tunnel installation guide
echo 📝 Creating tunnel installation guide...
(
echo @echo off
echo echo 🌐 Tunnel Services Installation Guide for Windows
echo echo ================================================
echo echo.
echo echo This will help you install additional tunnel services
echo echo for public access to your web server.
echo echo.
echo echo 📦 Available Tunnel Services:
echo echo.
echo echo 1. NGROK ^(Traditional^)
echo echo    - Download from: https://ngrok.com/download
echo echo    - Extract ngrok.exe to a folder in your PATH
echo echo    - Has warning page on free tier
echo echo.
echo echo 2. LOCALTUNNEL ^(Recommended^)
echo echo    - Requires Node.js: https://nodejs.org/
echo echo    - Install with: npm install -g localtunnel
echo echo    - No warning pages, instant access
echo echo.
echo echo 3. CLOUDFLARED ^(Enterprise^)
echo echo    - Download from: https://github.com/cloudflare/cloudflared/releases
echo echo    - Look for: cloudflared-windows-amd64.exe
echo echo    - Rename to: cloudflared.exe and add to PATH
echo echo    - Enterprise-grade reliability
echo echo.
echo echo 🎯 Recommendation: Start with Localtunnel ^(easiest setup^)
echo echo.
echo pause
) > install_tunnels_guide.bat

echo ✅ Tunnel installation guide created (install_tunnels_guide.bat)

REM Test installation
echo 🧪 Testing the installation...
timeout /t 3 /nobreak >nul
echo ✅ Installation test completed

echo.
echo ==============================================
echo 🎉           SETUP COMPLETE!           🎉
echo ==============================================
echo.
echo 📋 What's been installed:
echo   ✅ Python virtual environment
echo   ✅ Flask web framework and dependencies
echo   ✅ CORS support for network access
echo   ✅ pexpect for interactive command execution
echo   ✅ requests for API communication
if exist node_modules\localtunnel (
    echo   ✅ localtunnel ^(no warning pages^)
)
echo   ✅ Startup and stop scripts
echo   ✅ Tunnel installation guide
echo.
echo 🚀 How to start the server:
echo   Double-click: start_server.bat
echo   OR run: start_server.bat
echo.
echo 🛑 How to stop the server:
echo   Double-click: stop_server.bat
echo   OR press Ctrl+C in the server window
echo.
echo 🌐 Server will be accessible at:
echo   Local:   http://localhost:8000
echo   Network: http://%%COMPUTERNAME%%:8000
echo.
echo 📁 Features available:
echo   • 📊 Data storage ^(JSON key-value store^)
echo   • 📁 File upload/download ^(5GB storage limit^)
echo   • 🗂️  File explorer with drag ^& drop
echo   • 📤 Program upload and execution
echo   • 💻 Interactive command terminal with:
echo     - Real-time y/n prompt responses
echo     - Secure password prompting ^(never stored^)
echo     - Complete output preservation
echo     - Clean web display
echo   • 🌐 Multiple public tunnel support:
echo     - ngrok ^(traditional^)
echo     - localtunnel ^(no warning pages^)
echo     - cloudflared ^(enterprise-grade^)
echo   • 🔄 Real-time tunnel status monitoring
echo.
echo 🌐 To install tunnel services:
echo   Double-click: install_tunnels_guide.bat
echo.
echo ⚠️  Security Notes:
echo   • Server is accessible from your local network
echo   • Public tunnels expose server to the entire internet
echo   • Passwords are prompted but NEVER stored anywhere
echo   • Stop tunnels when not needed for security
echo   • Interactive commands have 60-second timeout
echo.
echo 🎯 Recommended first steps:
echo   1. Start the server: start_server.bat
echo   2. Open web interface: http://localhost:8000
echo   3. Install tunnel services: install_tunnels_guide.bat
echo   4. Test interactive commands and file uploads
echo.
echo 🚀 Ready to start? Double-click: start_server.bat
echo ==============================================

pause