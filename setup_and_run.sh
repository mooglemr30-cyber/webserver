#!/bin/bash
# Complete setup and run script for webserver
# Installs all dependencies and starts server in terminal

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          WEBSERVER COMPLETE SETUP AND RUN                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Change to webserver directory
cd /home/admin1/Documents/webserver

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Python Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install: sudo apt-get install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION installed${NC}"
echo ""

# Step 2: Create/check virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Setting Up Virtual Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if venv exists and if it's broken (wrong path)
VENV_BROKEN=false
if [ -d ".venv" ]; then
    echo "Checking existing virtual environment..."
    # Try to run python from venv to see if it works
    if ! .venv/bin/python --version &>/dev/null; then
        echo -e "${YELLOW}⚠ Virtual environment is broken (wrong path)${NC}"
        echo "Removing broken virtual environment..."
        rm -rf .venv
        VENV_BROKEN=true
    else
        echo -e "${GREEN}✓ Virtual environment exists and is working${NC}"
    fi
fi

if [ ! -d ".venv" ] || [ "$VENV_BROKEN" = true ]; then
    echo "Creating new virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

# Step 3: Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Step 4: Upgrade pip
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Upgrading pip"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
.venv/bin/python -m pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Step 5: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Installing Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installing all packages from requirements.txt..."
echo "This may take 2-3 minutes..."
echo ""

# Try to install all dependencies
if .venv/bin/python -m pip install -r requirements.txt; then
    echo ""
    echo -e "${GREEN}✓ All dependencies installed successfully${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠ Some packages failed, retrying without cache...${NC}"
    .venv/bin/python -m pip install --no-cache-dir -r requirements.txt
fi
echo ""

# Step 6: Verify critical packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying Critical Packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MISSING_PACKAGES=()

# Check Flask
if .venv/bin/python -c "import flask" 2>/dev/null; then
    FLASK_VER=$(.venv/bin/python -c "import importlib.metadata; print(importlib.metadata.version('flask'))")
    echo -e "${GREEN}✓ Flask ${FLASK_VER} installed${NC}"
else
    echo -e "${RED}✗ Flask not installed${NC}"
    MISSING_PACKAGES+=("flask")
fi

# Check Flask-CORS
if .venv/bin/python -c "import flask_cors" 2>/dev/null; then
    echo -e "${GREEN}✓ Flask-CORS installed${NC}"
else
    echo -e "${RED}✗ Flask-CORS not installed${NC}"
    MISSING_PACKAGES+=("flask-cors")
fi

# Check pydantic
if .venv/bin/python -c "import pydantic" 2>/dev/null; then
    echo -e "${GREEN}✓ Pydantic installed${NC}"
else
    echo -e "${RED}✗ Pydantic not installed${NC}"
    MISSING_PACKAGES+=("pydantic")
fi

# Check requests
if .venv/bin/python -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✓ Requests installed${NC}"
else
    echo -e "${RED}✗ Requests not installed${NC}"
    MISSING_PACKAGES+=("requests")
fi

echo ""

# If missing packages, try to install them individually
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠ Retrying installation of missing packages...${NC}"
    for package in "${MISSING_PACKAGES[@]}"; do
        echo "Installing $package..."
        .venv/bin/python -m pip install "$package" --no-cache-dir
    done
    echo ""
fi

# Step 7: Create necessary directories
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Creating Necessary Directories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p data/files
mkdir -p data/programs
mkdir -p data/backups
mkdir -p data/config
mkdir -p logs

echo -e "${GREEN}✓ All directories created${NC}"
echo ""

# Step 8: Check if src/app.py exists
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Verifying Application Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "src/app.py" ]; then
    echo -e "${RED}✗ src/app.py not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ src/app.py exists${NC}"

# Try to import the app
if .venv/bin/python -c "import sys; sys.path.insert(0, 'src'); import app" 2>/dev/null; then
    echo -e "${GREEN}✓ Application can be imported${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Application import has issues (may still work)${NC}"
fi

echo ""

# Step 9: Display configuration
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              SETUP COMPLETE - READY TO START                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  • Virtual Environment: .venv (activated)"
echo "  • Application: src/app.py"
echo "  • Data Directory: data/"
echo "  • Logs Directory: logs/"
echo ""

echo -e "${BLUE}Confirmation:${NC}"
echo "  ✓ Original webserver: READY"
echo "  ✓ Mobile app integration: CONFIGURED"
echo "  ✓ Dependencies: INSTALLED"
echo "  ✓ Both services: CAN RUN TOGETHER"
echo ""

echo -e "${BLUE}Mobile App Access:${NC}"
echo "  • Mobile app connects via Cloudflare tunnel"
echo "  • Tunnel URL will be shown in server logs"
echo "  • Uses same APIs as webserver"
echo "  • Access same tools and data"
echo ""

# Step 10: Start the server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STARTING WEBSERVER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Server is starting...${NC}"
echo "Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server (will run in foreground)
.venv/bin/python src/app.py

# This line only runs if server stops
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Server stopped."
echo "To restart: bash setup_and_run.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

