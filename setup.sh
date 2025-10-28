#!/bin/bash
# Web Server Setup Script
# Automated installation and setup for the Network Web Server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root (don't use sudo)"
   print_status "Run it as a regular user, it will ask for sudo when needed"
   exit 1
fi

print_status "Starting Network Web Server Setup..."
print_status "This script will install all dependencies and set up the server"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Working directory: $SCRIPT_DIR"

# Check if we're in the right directory (look for src/app.py)
if [[ ! -f "src/app.py" ]]; then
    print_error "Cannot find src/app.py - make sure you're running this script from the webserver directory"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    print_success "System packages updated"
elif command -v yum >/dev/null 2>&1; then
    sudo yum update -y
    print_success "System packages updated"
elif command -v brew >/dev/null 2>&1; then
    brew update
    print_success "Homebrew updated"
else
    print_warning "Unknown package manager, skipping system update"
fi

# Install Python 3 and pip if not present
print_status "Checking Python installation..."
if ! command -v python3 >/dev/null 2>&1; then
    print_status "Installing Python 3..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3 python3-pip python3-venv
    elif command -v brew >/dev/null 2>&1; then
        brew install python3
    else
        print_error "Cannot install Python 3 automatically. Please install it manually."
        exit 1
    fi
else
    print_success "Python 3 is already installed"
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python version: $PYTHON_VERSION"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    print_success "Python version is compatible (3.8+)"
else
    print_error "Python 3.8+ is required, but you have $PYTHON_VERSION"
    exit 1
fi

# Install additional system dependencies
print_status "Installing system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y curl wget git build-essential
elif command -v yum >/dev/null 2>&1; then
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y curl wget git
elif command -v brew >/dev/null 2>&1; then
    # Most tools are already available on macOS
    print_success "System dependencies check complete"
else
    print_warning "Unknown package manager, some dependencies might be missing"
fi

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [[ -d ".venv" ]]; then
    print_warning "Virtual environment already exists, removing old one..."
    rm -rf .venv
fi

python3 -m venv .venv
source .venv/bin/activate
print_success "Virtual environment created and activated"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip
print_success "Pip upgraded"

# Install Python dependencies
print_status "Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
else
    print_status "No requirements.txt found, installing dependencies manually..."
    pip install flask flask-cors pexpect requests werkzeug flask-limiter cryptography bleach python-magic redis schedule
fi
print_success "Python dependencies installed"

# Install additional security and performance tools
print_status "Installing additional system tools..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get install -y python3-magic libmagic1 redis-server
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3-magic file-devel redis
elif command -v brew >/dev/null 2>&1; then
    brew install libmagic redis
fi
print_success "Additional tools installed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/files data/programs
chmod 755 data data/files data/programs
print_success "Directory structure created"

# Install ngrok (optional but recommended)
print_status "Checking for ngrok installation..."
if ! command -v ngrok >/dev/null 2>&1; then
    print_status "Installing ngrok for public tunnel support..."
    
    # Detect architecture
    ARCH=$(uname -m)
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    case $ARCH in
        x86_64) NGROK_ARCH="amd64" ;;
        arm64|aarch64) NGROK_ARCH="arm64" ;;
        armv7l) NGROK_ARCH="arm" ;;
        i386|i686) NGROK_ARCH="386" ;;
        *) print_warning "Unsupported architecture for ngrok: $ARCH"; NGROK_ARCH="" ;;
    esac
    
    if [[ -n "$NGROK_ARCH" ]]; then
        NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-${OS}-${NGROK_ARCH}.tgz"
        
        # Download and install ngrok
        curl -s -L "$NGROK_URL" | tar xz
        chmod +x ngrok
        
        # Move to a directory in PATH
        if [[ -d "$HOME/.local/bin" ]]; then
            mv ngrok "$HOME/.local/bin/"
        elif [[ -d "$HOME/bin" ]]; then
            mv ngrok "$HOME/bin/"
        else
            mkdir -p "$HOME/.local/bin"
            mv ngrok "$HOME/.local/bin/"
            export PATH="$HOME/.local/bin:$PATH"
        fi
        
        print_success "ngrok installed successfully"
        print_status "To use ngrok tunnels, you may want to sign up at https://ngrok.com and add your auth token"
    else
        print_warning "Could not install ngrok automatically"
    fi
else
    print_success "ngrok is already installed"
fi

# Install Node.js for localtunnel (if not present)
print_status "Checking for Node.js installation..."
if ! command -v npm >/dev/null 2>&1; then
    print_status "Installing Node.js for localtunnel support..."
    if command -v apt-get >/dev/null 2>&1; then
        # Ubuntu/Debian
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        sudo yum install -y nodejs npm
    elif command -v brew >/dev/null 2>&1; then
        # macOS
        brew install node
    else
        print_warning "Could not install Node.js automatically"
        print_status "Please install Node.js manually from https://nodejs.org/"
    fi
    
    if command -v npm >/dev/null 2>&1; then
        print_success "Node.js and npm installed successfully"
    else
        print_warning "Node.js installation may have failed"
    fi
else
    print_success "Node.js and npm are already installed"
fi

# Install localtunnel
print_status "Installing localtunnel..."
if command -v npm >/dev/null 2>&1; then
    if sudo npm install -g localtunnel; then
        print_success "localtunnel installed successfully"
        # Test localtunnel installation
        if command -v lt >/dev/null 2>&1; then
            print_success "localtunnel verified working"
        else
            print_warning "localtunnel installed but not in PATH"
        fi
    else
        print_warning "Failed to install localtunnel with sudo, trying without..."
        if npm install -g localtunnel; then
            print_success "localtunnel installed successfully"
        else
            print_warning "Failed to install localtunnel"
        fi
    fi
else
    print_warning "npm not available, skipping localtunnel installation"
fi

# Install cloudflared
print_status "Installing cloudflared..."
if ! command -v cloudflared >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        # Linux (Debian/Ubuntu)
        print_status "Installing cloudflared for Linux..."
        if curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb; then
            if sudo dpkg -i cloudflared.deb; then
                print_success "cloudflared installed successfully"
                rm cloudflared.deb
            else
                print_warning "Failed to install cloudflared package"
            fi
        else
            print_warning "Failed to download cloudflared"
        fi
    elif command -v yum >/dev/null 2>&1; then
        # CentOS/RHEL
        print_status "Installing cloudflared for CentOS/RHEL..."
        if curl -L --output cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm; then
            if sudo rpm -i cloudflared.rpm; then
                print_success "cloudflared installed successfully"
                rm cloudflared.rpm
            else
                print_warning "Failed to install cloudflared package"
            fi
        else
            print_warning "Failed to download cloudflared"
        fi
    elif command -v brew >/dev/null 2>&1; then
        # macOS
        print_status "Installing cloudflared for macOS..."
        if brew install cloudflared; then
            print_success "cloudflared installed via Homebrew"
        else
            print_warning "Failed to install cloudflared via Homebrew"
        fi
    else
        print_warning "Unknown OS. Please install cloudflared manually from:"
        print_status "https://github.com/cloudflare/cloudflared/releases"
    fi
else
    print_success "cloudflared is already installed"
fi

# Verify tunnel installations
print_status "Verifying tunnel service installations..."
TUNNEL_COUNT=0

if command -v ngrok >/dev/null 2>&1; then
    print_success "✓ ngrok: $(ngrok version 2>/dev/null | head -1)"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    print_warning "✗ ngrok: Not available"
fi

if command -v lt >/dev/null 2>&1; then
    LT_VERSION=$(lt --version 2>/dev/null || echo "version unknown")
    print_success "✓ localtunnel: $LT_VERSION"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    print_warning "✗ localtunnel: Not available"
fi

if command -v cloudflared >/dev/null 2>&1; then
    CF_VERSION=$(cloudflared --version 2>/dev/null | head -1)
    print_success "✓ cloudflared: $CF_VERSION"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    print_warning "✗ cloudflared: Not available"
fi

if [[ $TUNNEL_COUNT -gt 0 ]]; then
    print_success "$TUNNEL_COUNT tunnel service(s) available"
else
    print_warning "No tunnel services installed - only local network access will be available"
fi

# Get local IP address
print_status "Detecting network configuration..."
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
print_success "Local IP address: $LOCAL_IP"

# Create startup script
print_status "Creating startup script..."
cat > start_server.sh << 'EOF'
#!/bin/bash
# Web Server Startup Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Network Web Server...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [[ ! -f ".venv/bin/activate" ]]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run the setup script first: ./setup.sh${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check if server file exists
if [[ ! -f "src/app.py" ]]; then
    echo -e "${RED}❌ Server file (src/app.py) not found!${NC}"
    exit 1
fi

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")

echo -e "${BLUE}📡 Server will be accessible at:${NC}"
echo -e "   Local:   ${GREEN}http://localhost:8000${NC}"
echo -e "   Network: ${GREEN}http://$LOCAL_IP:8000${NC}"
echo ""
echo -e "${BLUE}🌐 Tunnel Services Available:${NC}"
if command -v ngrok >/dev/null 2>&1; then
    echo -e "   ✓ ngrok (traditional tunnel)"
fi
if command -v lt >/dev/null 2>&1; then
    echo -e "   ✓ localtunnel (no warning pages)"
fi
if command -v cloudflared >/dev/null 2>&1; then
    echo -e "   ✓ cloudflared (enterprise-grade)"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server
python3 src/app.py
EOF

chmod +x start_server.sh
print_success "Startup script created (start_server.sh)"

# Create stop script
print_status "Creating stop script..."
cat > stop_server.sh << 'EOF'
#!/bin/bash
# Web Server Stop Script

echo "🛑 Stopping Network Web Server..."

# Kill any running Python processes with app.py
pkill -f "python.*app.py"

if [[ $? -eq 0 ]]; then
    echo "✓ Server stopped successfully"
else
    echo "ℹ No running server found"
fi
EOF

chmod +x stop_server.sh
print_success "Stop script created (stop_server.sh)"

# Create system service file (optional)
print_status "Creating systemd service file (optional)..."
cat > webserver.service << EOF
[Unit]
Description=Network Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/.venv/bin
ExecStart=$SCRIPT_DIR/.venv/bin/python $SCRIPT_DIR/src/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created (webserver.service)"
print_status "To install as a system service, run:"
print_status "  sudo cp webserver.service /etc/systemd/system/"
print_status "  sudo systemctl enable webserver.service"
print_status "  sudo systemctl start webserver.service"

# Test the installation
print_status "Testing the installation..."
timeout 10s python src/app.py > /dev/null 2>&1 &
TEST_PID=$!
sleep 3

if kill -0 $TEST_PID 2>/dev/null; then
    kill $TEST_PID 2>/dev/null
    print_success "✓ Server test successful!"
else
    print_error "✗ Server test failed"
    exit 1
fi

# Final setup complete message
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 SETUP COMPLETE! 🎉${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📋 What's been installed:${NC}"
echo "  ✓ Python 3 and virtual environment"
echo "  ✓ Flask web framework and dependencies"
echo "  ✓ CORS support for network access"
echo "  ✓ pexpect for interactive command execution"
echo "  ✓ requests for API communication"
echo "  ✓ Multiple tunnel services for public access:"
if command -v ngrok >/dev/null 2>&1; then
    echo "    • ngrok (traditional, with warning page)"
fi
if command -v lt >/dev/null 2>&1; then
    echo "    • localtunnel (no warnings, instant access)"
fi
if command -v cloudflared >/dev/null 2>&1; then
    echo "    • cloudflared (enterprise-grade reliability)"
fi
echo "  ✓ Startup and stop scripts"
echo "  ✓ Optional systemd service file"
echo ""
echo -e "${BLUE}🚀 How to start the server:${NC}"
echo "  ./start_server.sh"
echo ""
echo -e "${BLUE}🛑 How to stop the server:${NC}"
echo "  ./stop_server.sh"
echo "  (or press Ctrl+C in the server terminal)"
echo ""
echo -e "${BLUE}🌐 Server will be accessible at:${NC}"
echo "  Local:   http://localhost:8000"
echo "  Network: http://$LOCAL_IP:8000"
echo ""
echo -e "${BLUE}📁 Features available:${NC}"
echo "  • 📊 Data storage (JSON key-value store)"
echo "  • 📁 File upload/download (5GB storage limit)"
echo "  • 🗂️  File explorer with drag & drop"
echo "  • 📤 Program upload and execution"
echo "  • 💻 Interactive command terminal with:"
echo "    - Real-time y/n prompt responses"
echo "    - Secure sudo password prompting"
echo "    - Complete output preservation"
echo "    - ANSI code cleaning for web display"
echo "  • 🌐 Multiple public tunnel options:"
echo "    - ngrok (traditional)"
echo "    - localtunnel (no warning pages)"
echo "    - cloudflared (enterprise-grade)"
echo "  • 🔄 Real-time tunnel status monitoring"
echo "  • 🛡️  Security features:"
echo "    - Password protection (never stored)"
echo "    - Command isolation"
echo "    - Timeout protection"
echo ""
echo -e "${YELLOW}⚠ Security Notes:${NC}"
echo "  • Server is accessible from your local network"
echo "  • Public tunnels expose server to the entire internet"
echo "  • Passwords are prompted but NEVER stored anywhere"
echo "  • Stop tunnels when not needed for security"
echo "  • Interactive commands have 60-second timeout"
echo ""
echo -e "${GREEN}🎯 Recommended first steps:${NC}"
echo "  1. Start the server: ${BLUE}./start_server.sh${NC}"
echo "  2. Open web interface: ${BLUE}http://localhost:8000${NC}"
echo "  3. Try localtunnel for public access (no warning pages)"
echo "  4. Test interactive commands and file uploads"
echo ""
echo -e "${GREEN}Ready to start? Run: ${BLUE}./start_server.sh${NC}"
echo "=============================================="