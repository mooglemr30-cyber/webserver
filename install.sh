#!/bin/bash

# ============================================================
# Network Web Server - Installation Script
# ============================================================
# This script sets up the complete environment for the web server
# including Python virtual environment, dependencies, and directories
# ============================================================

set -e  # Exit on error

echo "============================================================"
echo "🚀 Network Web Server - Installation"
echo "============================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_status "Installation directory: $SCRIPT_DIR"
echo ""

# ============================================================
# Step 1: Check system requirements
# ============================================================
print_status "Step 1/6: Checking system requirements..."

# Check for Python 3.8+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python found: $PYTHON_VERSION"
    
    # Check if version is 3.8 or higher
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed!"
    echo "Please install Python 3.8 or higher:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora/RHEL:   sudo dnf install python3 python3-pip"
    echo "  macOS:         brew install python3"
    exit 1
fi

# Check for pip
if command -v pip3 &> /dev/null; then
    print_success "pip3 found"
else
    print_warning "pip3 not found, will try to use python3 -m pip"
fi

# Check for system dependencies
print_status "Checking system dependencies..."

# Check for libmagic (required by python-magic)
if ldconfig -p | grep -q libmagic; then
    print_success "libmagic found"
else
    print_warning "libmagic not found - required for file type detection"
    echo "  Install with: sudo apt install libmagic1 (Ubuntu/Debian)"
    echo "               sudo dnf install file-libs (Fedora/RHEL)"
    echo "               brew install libmagic (macOS)"
fi

echo ""

# ============================================================
# Step 2: Create directory structure
# ============================================================
print_status "Step 2/6: Creating directory structure..."

# Main data directory
mkdir -p data
print_success "Created: data/"

# Configuration directory
mkdir -p data/config
print_success "Created: data/config/"

# File storage directory
mkdir -p data/files
print_success "Created: data/files/"

# Logs directory
mkdir -p data/logs
print_success "Created: data/logs/"

# Programs directory and subdirectories
mkdir -p data/programs
mkdir -p data/programs/db
mkdir -p data/programs/logs
print_success "Created: data/programs/ (with subdirectories)"

# Backups directory
mkdir -p data/backups
print_success "Created: data/backups/"

# Database directory (for SQLite if needed)
mkdir -p db
print_success "Created: db/"

# Logs directory (root level)
mkdir -p logs
print_success "Created: logs/"

echo ""

# ============================================================
# Step 3: Create initial configuration files
# ============================================================
print_status "Step 3/6: Creating initial configuration files..."

# Create storage.json if it doesn't exist
if [ ! -f "data/storage.json" ]; then
    echo '{}' > data/storage.json
    print_success "Created: data/storage.json"
else
    print_warning "data/storage.json already exists, skipping"
fi

# Create users.json if it doesn't exist
if [ ! -f "data/users.json" ]; then
    echo '{}' > data/users.json
    print_success "Created: data/users.json"
else
    print_warning "data/users.json already exists, skipping"
fi

# Create programs.json if it doesn't exist
if [ ! -f "data/programs/programs.json" ]; then
    echo '{}' > data/programs/programs.json
    print_success "Created: data/programs/programs.json"
else
    print_warning "data/programs/programs.json already exists, skipping"
fi

# Create backup_index.json if it doesn't exist
if [ ! -f "data/backups/backup_index.json" ]; then
    echo '{"backups": []}' > data/backups/backup_index.json
    print_success "Created: data/backups/backup_index.json"
else
    print_warning "data/backups/backup_index.json already exists, skipping"
fi

# Create config files
if [ ! -f "data/config/server_config.json" ]; then
    cat > data/config/server_config.json << 'EOF'
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
EOF
    print_success "Created: data/config/server_config.json"
else
    print_warning "data/config/server_config.json already exists, skipping"
fi

if [ ! -f "data/config/feature_flags.json" ]; then
    cat > data/config/feature_flags.json << 'EOF'
{
  "features": {
    "file_storage": true,
    "program_execution": true,
    "terminal_access": true,
    "tunnel_services": true,
    "websockets": true
  }
}
EOF
    print_success "Created: data/config/feature_flags.json"
else
    print_warning "data/config/feature_flags.json already exists, skipping"
fi

echo ""

# ============================================================
# Step 4: Create Python virtual environment
# ============================================================
print_status "Step 4/6: Creating Python virtual environment..."

if [ -d ".venv" ]; then
    print_warning "Virtual environment already exists at .venv"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing virtual environment..."
        rm -rf .venv
        python3 -m venv .venv
        print_success "Virtual environment recreated"
    else
        print_status "Using existing virtual environment"
    fi
else
    python3 -m venv .venv
    print_success "Virtual environment created at .venv"
fi

echo ""

# ============================================================
# Step 5: Install Python dependencies
# ============================================================
print_status "Step 5/6: Installing Python dependencies..."

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    print_success "All dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""

# ============================================================
# Step 6: Verify installation
# ============================================================
print_status "Step 6/6: Verifying installation..."

# Check if Flask is installed
if python -c "import flask" 2>/dev/null; then
    print_success "Flask installed correctly"
else
    print_error "Flask installation failed!"
    exit 1
fi

# Check if pexpect is installed
if python -c "import pexpect" 2>/dev/null; then
    print_success "pexpect installed correctly"
else
    print_error "pexpect installation failed!"
    exit 1
fi

# Check directory structure
REQUIRED_DIRS=(
    "data"
    "data/config"
    "data/files"
    "data/logs"
    "data/programs"
    "data/backups"
    "src"
    "src/static"
    "src/templates"
)

ALL_DIRS_OK=true
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Directory exists: $dir"
    else
        print_error "Directory missing: $dir"
        ALL_DIRS_OK=false
    fi
done

echo ""

# ============================================================
# Installation complete!
# ============================================================
if [ "$ALL_DIRS_OK" = true ]; then
    echo "============================================================"
    print_success "Installation completed successfully! 🎉"
    echo "============================================================"
    echo ""
    echo "📋 Quick Start Guide:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   ${GREEN}source .venv/bin/activate${NC}"
    echo ""
    echo "2. Start the server:"
    echo "   ${GREEN}python src/app.py${NC}"
    echo ""
    echo "3. Access the web interface:"
    echo "   ${BLUE}http://localhost:8000${NC}"
    echo ""
    echo "📁 Directory Structure:"
    echo "   data/           - Main data directory"
    echo "   data/config/    - Configuration files"
    echo "   data/files/     - Uploaded files"
    echo "   data/logs/      - Application logs"
    echo "   data/programs/  - Uploaded programs/projects"
    echo "   data/backups/   - Backup files"
    echo ""
    echo "💡 Tips:"
    echo "   - The server runs on port 8000 by default"
    echo "   - Access from network: http://YOUR_IP:8000"
    echo "   - Use Ctrl+C to stop the server"
    echo "   - Check logs in data/logs/ for debugging"
    echo ""
    echo "📖 For more information, see README.md"
    echo ""
else
    print_error "Installation completed with errors. Please check the output above."
    exit 1
fi
