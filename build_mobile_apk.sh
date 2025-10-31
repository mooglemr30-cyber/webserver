#!/bin/bash

# ========================================
# Mobile App APK Builder Script
# ========================================

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           WEBSERVER MOBILE APP APK BUILDER                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MOBILE_APP_DIR="$SCRIPT_DIR/mobile-app"
STATIC_DIR="$SCRIPT_DIR/src/static"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Check Mobile App Directory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "$MOBILE_APP_DIR" ]; then
    echo -e "${RED}✗ Mobile app directory not found: $MOBILE_APP_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found mobile app directory${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Check Node.js and npm"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "Please install Node.js from: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is not installed${NC}"
    echo "Please install npm"
    exit 1
fi

echo -e "${GREEN}✓ Node.js $(node --version)${NC}"
echo -e "${GREEN}✓ npm $(npm --version)${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Install Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$MOBILE_APP_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ npm install failed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Build APK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Choose your build method:"
echo "1) React Native CLI (Recommended for development)"
echo "2) Expo EAS Build (Requires Expo account)"
echo "3) Use pre-built APK (if you have one)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Building with React Native CLI"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Check for Android SDK
        if [ -z "$ANDROID_HOME" ]; then
            echo -e "${YELLOW}⚠ ANDROID_HOME not set${NC}"
            echo "You need Android Studio and SDK installed."
            echo "Set ANDROID_HOME environment variable to your SDK location."
            exit 1
        fi

        echo "Building Android APK..."
        cd android
        ./gradlew assembleRelease

        if [ $? -eq 0 ]; then
            APK_PATH="android/app/build/outputs/apk/release/app-release.apk"
            if [ -f "$APK_PATH" ]; then
                echo -e "${GREEN}✓ APK built successfully!${NC}"

                # Copy to static directory
                mkdir -p "$STATIC_DIR"
                cp "$APK_PATH" "$STATIC_DIR/webserver-mobile.apk"
                echo -e "${GREEN}✓ APK copied to: $STATIC_DIR/webserver-mobile.apk${NC}"
            else
                echo -e "${RED}✗ APK not found at expected location${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Building with Expo EAS"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Check for EAS CLI
        if ! command -v eas &> /dev/null; then
            echo "Installing EAS CLI..."
            npm install -g eas-cli
        fi

        echo "Starting EAS build..."
        echo "This will require:"
        echo "  1. An Expo account (free)"
        echo "  2. Login with: eas login"
        echo ""

        eas build --platform android --profile preview

        echo ""
        echo "After build completes, download the APK with:"
        echo "  eas build:download --platform android --latest"
        echo ""
        echo "Then move it to: $STATIC_DIR/webserver-mobile.apk"
        ;;

    3)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Copy Pre-built APK"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        read -p "Enter path to your APK file: " apk_path

        if [ -f "$apk_path" ]; then
            mkdir -p "$STATIC_DIR"
            cp "$apk_path" "$STATIC_DIR/webserver-mobile.apk"
            echo -e "${GREEN}✓ APK copied to: $STATIC_DIR/webserver-mobile.apk${NC}"
        else
            echo -e "${RED}✗ APK file not found: $apk_path${NC}"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    BUILD COMPLETE!                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "The APK is now available for download from your web interface!"
echo "Users can download it at: http://your-server:8000/"
echo ""
echo "Look for the \"📱 Mobile App Controls\" section at the top."
echo ""

