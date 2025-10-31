#!/bin/bash

# Mobile App Quick Setup Script
# This script automates the setup of the webserver with mobile tunnel access

set -e

echo "🚀 Mobile App Quick Setup"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}❌ This script is designed for Linux (Ubuntu)${NC}"
    echo "For macOS/Windows, please follow the manual setup in MOBILE_APP_SETUP.md"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "src/app.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the webserver root directory${NC}"
    exit 1
fi

echo "Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

echo ""
echo "Step 2: Checking/creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

echo ""
echo "Step 3: Installing Python dependencies..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"

echo ""
echo "Step 4: Checking cloudflared installation..."
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}⚠️  cloudflared not found. Installing...${NC}"

    # Download cloudflared
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

    # Install
    sudo dpkg -i cloudflared-linux-amd64.deb

    # Clean up
    rm cloudflared-linux-amd64.deb

    echo -e "${GREEN}✅ cloudflared installed${NC}"
else
    echo -e "${GREEN}✅ cloudflared is already installed${NC}"
fi

echo ""
echo "Step 5: Creating necessary directories..."
mkdir -p data/config
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

echo ""
echo "Step 6: Testing server startup..."
echo -e "${YELLOW}Starting server (will stop after 10 seconds for testing)...${NC}"

# Start server in background
python src/app.py &
SERVER_PID=$!

# Wait for server to start
sleep 10

# Get tunnel URL from logs
TUNNEL_URL=""
if [ -f "logs/service.log" ]; then
    TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' logs/service.log | tail -1)
fi

# Stop test server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

if [ -z "$TUNNEL_URL" ]; then
    echo -e "${YELLOW}⚠️  Could not detect tunnel URL from test run${NC}"
    echo "This is normal if cloudflared takes longer to start"
else
    echo -e "${GREEN}✅ Tunnel URL detected: $TUNNEL_URL${NC}"
fi

echo ""
echo "Step 7: Setting up systemd service for auto-start..."

# Update service file with correct user
SERVICE_FILE="webserver-mobile.service"
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

# Create temporary service file with correct paths
cat > /tmp/webserver-mobile.service << EOF
[Unit]
Description=Webserver with Mobile Tunnel
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$CURRENT_DIR/.venv/bin/python $CURRENT_DIR/src/app.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=false
PrivateTmp=true

# Logging
StandardOutput=append:$CURRENT_DIR/logs/service.log
StandardError=append:$CURRENT_DIR/logs/service-error.log

[Install]
WantedBy=multi-user.target
EOF

# Install service
sudo cp /tmp/webserver-mobile.service /etc/systemd/system/
sudo systemctl daemon-reload

echo -e "${GREEN}✅ Systemd service installed${NC}"

echo ""
read -p "Do you want to enable auto-start on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable webserver-mobile.service
    echo -e "${GREEN}✅ Auto-start enabled${NC}"
fi

echo ""
read -p "Do you want to start the server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl start webserver-mobile.service
    echo -e "${GREEN}✅ Server started${NC}"

    echo ""
    echo "Waiting for tunnel to initialize (30 seconds)..."
    sleep 30

    # Check service status
    if sudo systemctl is-active --quiet webserver-mobile.service; then
        echo -e "${GREEN}✅ Server is running${NC}"

        # Try to get tunnel URL
        echo ""
        echo "Checking for tunnel URL..."
        sleep 5

        TUNNEL_URL=$(sudo journalctl -u webserver-mobile.service -n 100 | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)

        if [ -n "$TUNNEL_URL" ]; then
            echo -e "${GREEN}✅ Tunnel is active!${NC}"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo -e "${GREEN}📱 Your Mobile Tunnel URL:${NC}"
            echo ""
            echo -e "   ${YELLOW}$TUNNEL_URL${NC}"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "📋 Next Steps:"
            echo ""
            echo "1. Copy the URL above"
            echo "2. Update mobile-app/src/config.js with this URL"
            echo "3. Follow MOBILE_APP_SETUP.md to setup the mobile app"
            echo ""
            echo "💡 To view logs: sudo journalctl -u webserver-mobile.service -f"
            echo "💡 To stop server: sudo systemctl stop webserver-mobile.service"
            echo ""
        else
            echo -e "${YELLOW}⚠️  Tunnel URL not detected yet${NC}"
            echo "Check logs: sudo journalctl -u webserver-mobile.service -f"
        fi
    else
        echo -e "${RED}❌ Server failed to start${NC}"
        echo "Check logs: sudo journalctl -u webserver-mobile.service -xe"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Documentation:"
echo "   - Full setup guide: MOBILE_APP_SETUP.md"
echo "   - Mobile app: mobile-app/README.md"
echo ""
echo "🔧 Useful Commands:"
echo "   - Start server:   sudo systemctl start webserver-mobile.service"
echo "   - Stop server:    sudo systemctl stop webserver-mobile.service"
echo "   - View logs:      sudo journalctl -u webserver-mobile.service -f"
echo "   - Server status:  sudo systemctl status webserver-mobile.service"
echo "   - Get tunnel URL: curl http://localhost:8000/api/mobile/tunnel/status"
echo ""
echo "🌐 Access:"
echo "   - Local:  http://localhost:8000"
echo "   - Mobile: Use the tunnel URL shown above"
echo ""

deactivate 2>/dev/null || true

