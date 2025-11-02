#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              QUICK FIX & BUILD (FINAL VERSION)               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver/mobile-app

echo "Step 1: Cleaning..."
rm -rf node_modules package-lock.json
echo "✓ Cleaned"

echo ""
echo "Step 2: Installing with --legacy-peer-deps..."
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Install failed!"
    exit 1
fi

echo "✓ Dependencies installed"

echo ""
echo "Step 3: Building APK..."
export PATH="$PWD/node_modules/.bin:$PATH"

# Check if eas is available
if [ ! -f "node_modules/.bin/eas" ]; then
    echo "❌ EAS CLI not found in node_modules!"
    echo "Installing eas-cli..."
    npm install --save-dev eas-cli --legacy-peer-deps
fi

echo ""
echo "Starting build..."
npx eas build --platform android --profile preview --clear-cache

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    BUILD SUBMITTED!                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Check status: npx eas build:list"
echo "Download when ready: npx eas build:download --platform android --latest"
echo "Then move: mv *.apk ../src/static/webserver-mobile.apk"
echo ""

