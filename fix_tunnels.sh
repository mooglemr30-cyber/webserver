#!/bin/bash
# Quick Fix Script for Tunnel Issues
# Run this if tunnels are not working properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing Tunnel Issues...${NC}"
echo ""

# Check current directory
if [[ ! -f "src/app.py" ]]; then
    echo -e "${RED}❌ Please run this script from the webserver directory${NC}"
    exit 1
fi

# Check if localtunnel is working
echo -e "${YELLOW}🔍 Checking localtunnel...${NC}"
if command -v lt >/dev/null 2>&1; then
    echo -e "${GREEN}✅ localtunnel is installed${NC}"
    
    # Test localtunnel
    echo -e "${YELLOW}📡 Testing localtunnel connection...${NC}"
    timeout 10s lt --port 8000 --print-requests > /tmp/lt_test.log 2>&1 &
    LT_PID=$!
    sleep 5
    
    if kill -0 $LT_PID 2>/dev/null; then
        kill $LT_PID 2>/dev/null || true
        echo -e "${GREEN}✅ localtunnel test successful${NC}"
    else
        echo -e "${YELLOW}⚠️  localtunnel test failed - may require account verification${NC}"
        echo -e "${BLUE}ℹ️  Note: Recent localtunnel versions may require account verification${NC}"
        echo -e "${BLUE}ℹ️  Visit: https://localtunnel.github.io/www/ for more info${NC}"
    fi
else
    echo -e "${RED}❌ localtunnel not found. Installing...${NC}"
    if command -v npm >/dev/null 2>&1; then
        if sudo npm install -g localtunnel 2>/dev/null || npm install -g localtunnel; then
            echo -e "${GREEN}✅ localtunnel installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install localtunnel${NC}"
        fi
    else
        echo -e "${RED}❌ npm not found. Please install Node.js first${NC}"
        echo -e "${BLUE}ℹ️  Ubuntu/Debian: sudo apt install nodejs npm${NC}"
        echo -e "${BLUE}ℹ️  macOS: brew install node${NC}"
    fi
fi

echo ""

# Check if cloudflared is working
echo -e "${YELLOW}🔍 Checking cloudflared...${NC}"
if command -v cloudflared >/dev/null 2>&1; then
    echo -e "${GREEN}✅ cloudflared is installed${NC}"
    
    # Test cloudflared version
    CF_VERSION=$(cloudflared --version 2>/dev/null | head -1)
    echo -e "${BLUE}ℹ️  Version: $CF_VERSION${NC}"
    
    echo -e "${GREEN}✅ cloudflared ready to use${NC}"
else
    echo -e "${RED}❌ cloudflared not found. Installing...${NC}"
    
    # Detect OS and install
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo -e "${BLUE}🐧 Installing cloudflared for Linux...${NC}"
        if curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb; then
            if sudo dpkg -i /tmp/cloudflared.deb; then
                echo -e "${GREEN}✅ cloudflared installed successfully${NC}"
                rm /tmp/cloudflared.deb
            else
                echo -e "${RED}❌ Failed to install cloudflared${NC}"
            fi
        else
            echo -e "${RED}❌ Failed to download cloudflared${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${BLUE}🍎 Installing cloudflared for macOS...${NC}"
        if command -v brew >/dev/null 2>&1; then
            brew install cloudflared
            echo -e "${GREEN}✅ cloudflared installed via Homebrew${NC}"
        else
            echo -e "${RED}❌ Homebrew not found. Please install manually${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Unknown OS. Please install manually from:${NC}"
        echo -e "${BLUE}   https://github.com/cloudflare/cloudflared/releases${NC}"
    fi
fi

echo ""

# Check if ngrok is working
echo -e "${YELLOW}🔍 Checking ngrok...${NC}"
if command -v ngrok >/dev/null 2>&1; then
    NGROK_VERSION=$(ngrok version 2>/dev/null | head -1)
    echo -e "${GREEN}✅ ngrok is installed: $NGROK_VERSION${NC}"
    
    # Check for authtoken
    if ngrok config check 2>/dev/null | grep -q "valid"; then
        echo -e "${GREEN}✅ ngrok is authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️  ngrok is not authenticated${NC}"
        echo -e "${BLUE}ℹ️  To authenticate ngrok:${NC}"
        echo -e "${BLUE}   1. Sign up at https://ngrok.com${NC}"
        echo -e "${BLUE}   2. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken${NC}"
        echo -e "${BLUE}   3. Run: ngrok config add-authtoken YOUR_TOKEN${NC}"
        echo -e "${BLUE}   Note: ngrok works without authentication but with limitations${NC}"
    fi
else
    echo -e "${RED}❌ ngrok not found${NC}"
    echo -e "${BLUE}ℹ️  Download from: https://ngrok.com/download${NC}"
fi

echo ""
echo -e "${BLUE}📋 Tunnel Status Summary:${NC}"
echo "=========================="

# Final status check
TUNNEL_COUNT=0

if command -v ngrok >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ngrok: Available${NC}"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    echo -e "${RED}❌ ngrok: Not installed${NC}"
fi

if command -v lt >/dev/null 2>&1; then
    echo -e "${GREEN}✅ localtunnel: Available${NC}"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    echo -e "${RED}❌ localtunnel: Not installed${NC}"
fi

if command -v cloudflared >/dev/null 2>&1; then
    echo -e "${GREEN}✅ cloudflared: Available${NC}"
    TUNNEL_COUNT=$((TUNNEL_COUNT + 1))
else
    echo -e "${RED}❌ cloudflared: Not installed${NC}"
fi

echo ""
if [[ $TUNNEL_COUNT -gt 0 ]]; then
    echo -e "${GREEN}🎉 $TUNNEL_COUNT tunnel service(s) ready!${NC}"
    echo -e "${BLUE}💡 Recommendation:${NC}"
    if command -v cloudflared >/dev/null 2>&1; then
        echo -e "${BLUE}   Try cloudflared first - most reliable${NC}"
    elif command -v lt >/dev/null 2>&1; then
        echo -e "${BLUE}   Try localtunnel - no warning pages${NC}"
    else
        echo -e "${BLUE}   Try ngrok - most popular${NC}"
    fi
    echo ""
    echo -e "${GREEN}🚀 Start your server and use the web interface to test tunnels!${NC}"
else
    echo -e "${RED}❌ No tunnel services available${NC}"
    echo -e "${BLUE}💡 Install at least one tunnel service to enable public access${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Common Issues & Solutions:${NC}"
echo "=============================="
echo -e "${YELLOW}• localtunnel requires code:${NC} Recent versions may need account verification"
echo -e "${YELLOW}• ngrok authentication required:${NC} Sign up at ngrok.com for better features"
echo -e "${YELLOW}• cloudflared permission denied:${NC} Check installation and PATH"
echo -e "${YELLOW}• All tunnels fail:${NC} Check internet connection and firewall"

echo ""
echo -e "${GREEN}✅ Tunnel fix script completed!${NC}"