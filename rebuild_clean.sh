#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         FIXING BUILD & REBUILDING (CLEAN INSTALL)           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver/mobile-app

echo "Step 1: Cleaning old files..."
rm -rf node_modules package-lock.json
echo "✓ Cleaned"

echo ""
echo "Step 2: Installing dependencies..."
npm install
echo "✓ Dependencies installed"

echo ""
echo "Step 3: Starting EAS build..."
export PATH="$PWD/node_modules/.bin:$PATH"

npx eas build --platform android --profile preview --clear-cache

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    BUILD SUBMITTED!                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "To check status: cd mobile-app && npx eas build:list"
echo "To download: cd mobile-app && npx eas build:download --platform android --latest"
echo ""
echo "After download:"
echo "  mv *.apk ../src/static/webserver-mobile.apk"
echo ""

