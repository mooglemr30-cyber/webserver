#!/bin/bash

# ========================================
# EXPO MOBILE APP BUILDER
# ========================================

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        WEBSERVER MOBILE APP - EXPO APK BUILDER               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
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

# Create simple placeholder images using ImageMagick or basic echo
echo -e "${BLUE}Creating placeholder assets...${NC}"

# Create a simple text file as placeholder (Expo will use defaults)
cat > assets/README.txt << 'EOF'
Placeholder assets directory.
Expo will use default icons if actual icon files are not provided.
To customize:
- icon.png (1024x1024)
- splash.png (1284x2778)
- adaptive-icon.png (1024x1024)
- favicon.png (48x48)
EOF

echo -e "${GREEN}✓ Assets directory ready${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Install Expo CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v expo &> /dev/null; then
    echo "Installing Expo CLI globally (requires sudo)..."
    echo "You may be prompted for your password..."
    sudo npm install -g expo-cli
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Expo CLI${NC}"
        echo "Trying with --unsafe-perm flag..."
        sudo npm install -g expo-cli --unsafe-perm
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Still failed. Trying alternative method...${NC}"
            # Try installing locally in the project instead
            npm install expo-cli
            export PATH="$PWD/node_modules/.bin:$PATH"
        fi
    fi
fi

echo -e "${GREEN}✓ Expo CLI installed${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Install EAS CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v eas &> /dev/null; then
    echo "Installing EAS CLI globally (requires sudo)..."
    echo "You may be prompted for your password..."
    sudo npm install -g eas-cli
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install EAS CLI${NC}"
        echo "Trying with --unsafe-perm flag..."
        sudo npm install -g eas-cli --unsafe-perm
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Still failed. Trying alternative method...${NC}"
            # Try installing locally in the project instead
            npm install eas-cli
            export PATH="$PWD/node_modules/.bin:$PATH"
        fi
    fi
fi

echo -e "${GREEN}✓ EAS CLI installed${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Install Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Installing npm packages..."
npm install
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ npm install had issues, trying with --legacy-peer-deps...${NC}"
    npm install --legacy-peer-deps
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Build APK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Choose your build method:"
echo ""
echo "1) EAS Build (Cloud - Recommended, No Android SDK needed!)"
echo "2) Expo Build (Classic - Deprecated but simpler)"
echo "3) Local Build (Requires Android SDK)"
echo "4) Skip build (Just install dependencies)"
echo ""
read -p "Enter choice [1-4]: " choice

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

        # Configure EAS if needed
        if [ ! -f "eas.json" ]; then
            echo "Configuring EAS..."
            eas build:configure
        fi

        echo ""
        echo "Starting EAS build for Android..."
        eas build --platform android --profile preview --non-interactive || eas build --platform android --profile preview

        echo ""
        echo -e "${GREEN}✓ Build submitted to EAS!${NC}"
        echo ""
        echo "To check build status: eas build:list"
        echo "To download when ready: eas build:download --platform android --latest"
        echo ""
        echo "After downloading, move the APK to:"
        echo "  $STATIC_DIR/webserver-mobile.apk"
        ;;

    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Building with Expo Classic Build"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        echo ""
        echo "Note: This method is deprecated but still works"
        echo ""

        expo build:android -t apk

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ Build started!${NC}"
            echo ""
            echo "Expo will build your APK in the cloud."
            echo "Check status at: https://expo.dev/accounts/[your-account]/projects"
            echo ""
            echo "Download the APK when ready and move it to:"
            echo "  $STATIC_DIR/webserver-mobile.apk"
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;

    3)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Local Build (Requires Android SDK)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if [ -z "$ANDROID_HOME" ]; then
            echo -e "${RED}✗ ANDROID_HOME not set${NC}"
            echo "You need Android Studio and SDK installed."
            echo "Set ANDROID_HOME environment variable to your SDK location."
            exit 1
        fi

        echo "Building locally..."
        expo prebuild
        cd android
        ./gradlew assembleRelease

        if [ $? -eq 0 ]; then
            APK_PATH="android/app/build/outputs/apk/release/app-release.apk"
            if [ -f "$APK_PATH" ]; then
                echo -e "${GREEN}✓ APK built successfully!${NC}"

                mkdir -p "$STATIC_DIR"
                cp "$APK_PATH" "$STATIC_DIR/webserver-mobile.apk"
                echo -e "${GREEN}✓ APK copied to: $STATIC_DIR/webserver-mobile.apk${NC}"
            fi
        else
            echo -e "${RED}✗ Build failed${NC}"
            exit 1
        fi
        ;;

    4)
        echo ""
        echo -e "${GREEN}✓ Dependencies installed. Skipping build.${NC}"
        echo ""
        echo "To build later, run this script again."
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
echo "To test locally:"
echo "  cd $MOBILE_APP_DIR"
echo "  npm start"
echo ""
echo "To build APK in the future:"
echo "  Run this script again and choose your build method"
echo ""

