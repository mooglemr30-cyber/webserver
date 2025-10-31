#!/bin/bash

# ========================================
# SIMPLE EXPO APP BUILDER (NO SUDO NEEDED!)
# ========================================

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SIMPLE WEBSERVER MOBILE APP BUILDER (LOCAL INSTALL)     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "This version installs everything locally - no sudo needed!"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MOBILE_APP_DIR="$SCRIPT_DIR/mobile-app"
STATIC_DIR="$SCRIPT_DIR/src/static"

cd "$MOBILE_APP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Check Node.js and npm"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "Install Node.js with: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node --version)${NC}"
echo -e "${GREEN}✓ npm $(npm --version)${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Create Assets Directory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p assets

cat > assets/README.txt << 'EOF'
Placeholder assets directory.
Expo will use default icons if actual icon files are not provided.
EOF

echo -e "${GREEN}✓ Assets directory ready${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Install Dependencies (Including Expo & EAS locally)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Installing all dependencies locally (no sudo required)..."
echo "This may take a few minutes..."

# Install expo-cli and eas-cli as local dependencies
npm install --save-dev expo-cli eas-cli

# Install app dependencies
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Some warnings during install, but continuing...${NC}"
fi

echo -e "${GREEN}✓ All dependencies installed locally${NC}"

# Add node_modules/.bin to PATH for this session
export PATH="$PWD/node_modules/.bin:$PATH"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Build APK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Choose your build method:"
echo ""
echo "1) EAS Build (Cloud - Recommended, No Android SDK needed!)"
echo "2) Install project only (skip build for now)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Building with EAS (Cloud Build)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        echo ""
        echo "EAS Build requires an Expo account (free at expo.dev)"
        echo ""
        echo "Steps:"
        echo "1. This will open a browser for you to login"
        echo "2. The build will happen in the cloud"
        echo "3. You'll get a download link when done"
        echo ""
        read -p "Press Enter to continue..."

        # Use local eas-cli
        echo "Using local EAS CLI installation..."

        # Configure EAS if needed
        if [ ! -f "eas.json" ]; then
            echo "Configuring EAS..."
            npx eas build:configure
        fi

        echo ""
        echo "Starting EAS build for Android..."
        echo "This will open a browser for login..."

        npx eas build --platform android --profile preview

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Build submitted to EAS!${NC}"
            echo ""
            echo "To check build status: npx eas build:list"
            echo "To download when ready: npx eas build:download --platform android --latest"
            echo ""
            echo "After downloading, move the APK to:"
            echo "  $STATIC_DIR/webserver-mobile.apk"
        else
            echo -e "${YELLOW}⚠ Build may have failed or you cancelled.${NC}"
            echo "You can try again by running:"
            echo "  cd $MOBILE_APP_DIR"
            echo "  npx eas build --platform android --profile preview"
        fi
        ;;

    2)
        echo ""
        echo -e "${GREEN}✓ Dependencies installed. Skipping build.${NC}"
        echo ""
        echo "To build later, run:"
        echo "  cd $MOBILE_APP_DIR"
        echo "  npx eas build --platform android --profile preview"
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE!                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Your mobile app is configured and ready!"
echo ""
echo "Useful commands (run from mobile-app directory):"
echo "  npx expo start          - Start development server"
echo "  npx eas build:list      - Check build status"
echo "  npx eas build:download  - Download completed build"
echo ""

