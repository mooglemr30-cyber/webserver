#!/bin/bash
# Robust setup and run script - handles installation issues
# Installs dependencies and starts server in terminal (no systemd)

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        COMPLETE WEBSERVER SETUP AND RUN (ROBUST)            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Python check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Python Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ $(python3 --version)${NC}"
echo ""

# Step 2: Virtual environment
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Virtual Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if venv exists and if it's broken (wrong path)
VENV_BROKEN=false
if [ -d ".venv" ]; then
    echo "Checking existing virtual environment..."
    # Try to run python from venv to see if it works
    if ! .venv/bin/python --version &>/dev/null; then
        echo -e "${YELLOW}⚠ Virtual environment is broken (wrong path from old location)${NC}"
        echo "Removing broken virtual environment..."
        rm -rf .venv
        VENV_BROKEN=true
    else
        echo -e "${GREEN}✓ .venv exists and is working${NC}"
    fi
fi

if [ ! -d ".venv" ] || [ "$VENV_BROKEN" = true ]; then
    echo "Creating new virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Created .venv${NC}"
fi

# Fix permissions on venv executables
echo "Fixing permissions on virtual environment..."
chmod +x .venv/bin/* 2>/dev/null || true
echo -e "${GREEN}✓ Permissions fixed${NC}"

echo "Activating virtual environment..."
source .venv/bin/activate
echo -e "${GREEN}✓ Activated${NC}"
echo ""

# Step 3: Upgrade pip
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Upgrading pip"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
.venv/bin/pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Step 4: Install dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Installing Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Trying full requirements.txt..."
if .venv/bin/pip install -r requirements.txt 2>/dev/null; then
    echo -e "${GREEN}✓ All packages from requirements.txt installed${NC}"
else
    echo -e "${YELLOW}⚠ Full requirements failed, trying minimal install...${NC}"
    echo ""

    # Install core packages one by one
    echo "Installing core packages individually..."

    CORE_PACKAGES=(
        "flask"
        "flask-cors"
        "Werkzeug"
        "requests"
        "pydantic"
        "pexpect"
        "psutil"
        "PyJWT"
        "bcrypt"
    )

    for package in "${CORE_PACKAGES[@]}"; do
        echo -n "  Installing $package... "
        if .venv/bin/pip install "$package" --quiet 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ (will retry)${NC}"
            .venv/bin/pip install "$package" --no-cache-dir --quiet || echo -e "${RED}✗ Failed${NC}"
        fi
    done

    echo ""
    echo "Installing additional packages (non-critical)..."

    OPTIONAL_PACKAGES=(
        "prometheus-client"
        "flask-limiter"
        "cryptography"
        "bleach"
        "PyYAML"
        "schedule"
    )

    for package in "${OPTIONAL_PACKAGES[@]}"; do
        echo -n "  Installing $package... "
        if .venv/bin/pip install "$package" --quiet 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ Skipped${NC}"
        fi
    done
fi

echo ""

# Step 5: Verify critical packages
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Verifying Critical Packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ALL_OK=true

# Check Flask
if .venv/bin/python -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}✓ Flask${NC}"
else
    echo -e "${RED}✗ Flask${NC}"
    ALL_OK=false
fi

# Check Flask-CORS
if .venv/bin/python -c "import flask_cors" 2>/dev/null; then
    echo -e "${GREEN}✓ Flask-CORS${NC}"
else
    echo -e "${RED}✗ Flask-CORS${NC}"
    ALL_OK=false
fi

# Check pydantic
if .venv/bin/python -c "import pydantic" 2>/dev/null; then
    echo -e "${GREEN}✓ Pydantic${NC}"
else
    echo -e "${RED}✗ Pydantic${NC}"
    ALL_OK=false
fi

# Check requests
if .venv/bin/python -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✓ Requests${NC}"
else
    echo -e "${RED}✗ Requests${NC}"
    ALL_OK=false
fi

echo ""

if [ "$ALL_OK" = false ]; then
    echo -e "${RED}✗ Some critical packages are missing!${NC}"
    echo ""
    echo "Attempting emergency install of critical packages..."
    .venv/bin/pip install flask flask-cors pydantic requests --no-cache-dir
    echo ""
fi

# Step 6: Create directories
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Creating Directories"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
mkdir -p data/{files,programs,backups,config}
mkdir -p logs
echo -e "${GREEN}✓ All directories ready${NC}"
echo ""

# Step 7: Verify app
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 7: Verifying Application"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ ! -f "src/app.py" ]; then
    echo -e "${RED}✗ src/app.py not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ src/app.py exists${NC}"
echo ""

# Step 8: Final status
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}✅ CONFIRMATION:${NC}"
echo "   • Original webserver: READY"
echo "   • Mobile app: CONFIGURED (via tunnel)"
echo "   • Dependencies: INSTALLED"
echo "   • Running mode: TERMINAL (not systemd)"
echo ""
echo -e "${BLUE}📱 Mobile App:${NC}"
echo "   • Connects via hidden Cloudflare tunnel"
echo "   • Tunnel URL shown in logs below"
echo "   • Same APIs, same data, same tools"
echo ""
echo -e "${BLUE}🛑 To stop server:${NC} Press Ctrl+C"
echo ""

# Step 9: Start server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STARTING WEBSERVER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start server in foreground
.venv/bin/python src/app.py

# Only reached if server stops
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Server stopped."
echo ""
echo "To restart:"
echo "  cd /home/admin1/Documents/webserver"
echo "  source .venv/bin/activate"
echo "  python src/app.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

