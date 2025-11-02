#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           FINAL BUILD (FIXED REACT VERSION)                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver/mobile-app

echo "Step 1: Cleaning..."
rm -rf node_modules package-lock.json
echo "✓ Cleaned"

echo ""
echo "Step 2: Installing with correct React version (18.2.0)..."
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Install failed!"
    exit 1
fi

echo "✓ Dependencies installed"

echo ""
echo "Step 3: Building APK (will decline expo-updates if asked)..."
export PATH="$PWD/node_modules/.bin:$PATH"

# Check if eas is available
if [ ! -f "node_modules/.bin/eas" ]; then
    echo "❌ EAS CLI not found!"
    echo "Installing eas-cli..."
    npm install --save-dev eas-cli --legacy-peer-deps
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "IMPORTANT: If asked to install expo-updates, answer: n (no)"
echo "We don't need it for basic builds"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Starting build..."
echo "If you see 'Would you like to install expo-updates', type: n"
echo ""

# Use --non-interactive to skip expo-updates prompt
npx eas build --platform android --profile preview --clear-cache --non-interactive

BUILD_RESULT=$?

echo ""
if [ $BUILD_RESULT -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   BUILD SUBMITTED!                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Check status: npx eas build:list"
    echo "Download when ready: npx eas build:download --platform android --latest"
    echo "Then move: mv *.apk ../src/static/webserver-mobile.apk"
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   BUILD FAILED                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Check logs online: https://expo.dev/accounts/meowmeowthecat/projects/webserver-mobile/builds"
fi

echo ""

