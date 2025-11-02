#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        CLEAN BUILD (GUARANTEED FRESH INSTALL)                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver/mobile-app

echo "Step 1: Complete cleanup..."
rm -rf node_modules package-lock.json .expo .expo-shared
echo "✓ All caches cleared"

echo ""
echo "Step 2: Verify React version in package.json..."
REACT_VERSION=$(grep '"react":' package.json | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
echo "Found React version: $REACT_VERSION"

if [ "$REACT_VERSION" != "18.2.0" ]; then
    echo "❌ ERROR: React is $REACT_VERSION but should be 18.2.0"
    echo "Fixing package.json..."
    sed -i 's/"react": "[^"]*"/"react": "18.2.0"/g' package.json
    echo "✓ Fixed to 18.2.0"
fi

echo ""
echo "Step 3: Fresh install with --legacy-peer-deps..."
npm install --legacy-peer-deps

if [ $? -ne 0 ]; then
    echo "❌ Install failed!"
    exit 1
fi

echo "✓ Dependencies installed"

echo ""
echo "Step 4: Verify EAS CLI..."
export PATH="$PWD/node_modules/.bin:$PATH"

if [ ! -f "node_modules/.bin/eas" ]; then
    echo "Installing eas-cli..."
    npm install --save-dev eas-cli --legacy-peer-deps
fi

echo "✓ EAS CLI ready"./setup_ai_intelligence.sh

echo ""
echo "Step 5: Building APK..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "IMPORTANT: We will skip expo-updates (not needed for basic builds)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build without interactive prompts
npx eas build --platform android --profile preview --clear-cache --non-interactive

BUILD_RESULT=$?

echo ""
if [ $BUILD_RESULT -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   BUILD SUBMITTED!                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Check status: cd mobile-app && npx eas build:list"
    echo "Download: cd mobile-app && npx eas build:download --platform android --latest"
    echo "Deploy: mv *.apk ../src/static/webserver-mobile.apk"
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   BUILD FAILED                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Check: https://expo.dev/accounts/meowmeowthecat/projects/webserver-mobile/builds"
fi

echo ""

