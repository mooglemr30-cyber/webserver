#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              FIXING EAS PROJECT ID & REBUILDING              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver/mobile-app

echo "Step 1: Configuring EAS project..."
echo "This will link your project to your Expo account and generate a proper project ID."
echo ""

# Add node_modules/.bin to PATH
export PATH="$PWD/node_modules/.bin:$PATH"

# Run EAS configure to generate proper project ID
npx eas build:configure

echo ""
echo "Step 2: Starting build..."
echo ""

# Now try the build
npx eas build --platform android --profile preview

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                      BUILD SUBMITTED!                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "To check status: cd mobile-app && npx eas build:list"
echo "To download: cd mobile-app && npx eas build:download --platform android --latest"
echo ""

