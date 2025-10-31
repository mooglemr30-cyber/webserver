# 📱 Mobile App APK Build & Distribution Guide

## Overview

This guide explains how to build the Android APK for your webserver mobile app and make it available for download through your web interface.

---

## 🎯 Quick Start

### Option 1: Automated Build Script (Recommended)

```bash
cd /home/admin1/Documents/webserver
chmod +x build_mobile_apk.sh
./build_mobile_apk.sh
```

The script will guide you through the build process!

---

## 📋 Prerequisites

### Required Software

1. **Node.js & npm**
   ```bash
   # Check if installed
   node --version
   npm --version
   
   # Install if needed (Ubuntu)
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Android Build Tools** (Choose one method)

   #### Method A: React Native CLI (Local Build)
   - Android Studio with SDK
   - Set ANDROID_HOME environment variable
   - Java Development Kit (JDK)
   
   ```bash
   # Install Android SDK
   sudo apt-get install android-sdk
   
   # Or download Android Studio from:
   # https://developer.android.com/studio
   ```

   #### Method B: Expo EAS (Cloud Build)
   - Expo account (free at expo.dev)
   - No local Android tools needed!
   
   ```bash
   # Install EAS CLI
   npm install -g eas-cli
   
   # Login
   eas login
   ```

---

## 🔨 Building the APK

### Method 1: React Native CLI (Local Build)

```bash
cd /home/admin1/Documents/webserver/mobile-app

# Install dependencies
npm install

# Go to android directory
cd android

# Build release APK
./gradlew assembleRelease

# APK will be at:
# android/app/build/outputs/apk/release/app-release.apk
```

Copy the APK to make it downloadable:
```bash
cp android/app/build/outputs/apk/release/app-release.apk \
   ../src/static/webserver-mobile.apk
```

### Method 2: Expo EAS (Cloud Build - Easier!)

```bash
cd /home/admin1/Documents/webserver/mobile-app

# Install dependencies
npm install

# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure EAS (first time only)
eas build:configure

# Build APK
eas build --platform android --profile preview

# After build completes, download it
eas build:download --platform android --latest

# Move to static directory
mv *.apk ../src/static/webserver-mobile.apk
```

### Method 3: Use Automated Script

```bash
cd /home/admin1/Documents/webserver
chmod +x build_mobile_apk.sh
./build_mobile_apk.sh
```

---

## 📦 Making APK Available for Download

Once you have the APK built, place it here:
```
/home/admin1/Documents/webserver/src/static/webserver-mobile.apk
```

The web interface will automatically detect it and allow users to download!

---

## 🌐 Web Interface Integration

### What's Been Added

A new **"📱 Mobile App Controls"** section has been added to the top of your web interface with:

1. **Tunnel Control Panel**
   - Start/Stop button for mobile tunnel
   - Status indicator (🔴 Stopped / 🟢 Running)
   - Tunnel URL display
   - Refresh button

2. **APK Download Button**
   - "📥 Download APK" button
   - Installation instructions
   - Automatic detection if APK exists

### Location

The mobile controls appear at: `http://localhost:8000/`

Right after the header, before all other sections - **highly visible!**

---

## 📲 Distribution to Users

### Step 1: Build APK (One Time)
```bash
cd /home/admin1/Documents/webserver
./build_mobile_apk.sh
```

### Step 2: Start Your Server
```bash
cd /home/admin1/Documents/webserver
source .venv/bin/activate
python src/app.py
```

### Step 3: Share Download Link

Users can download the APK from:
- **Local Network**: `http://YOUR-LOCAL-IP:8000/`
- **Remote**: Start tunnel from web interface, share tunnel URL

### Step 4: Installation Instructions for Users

1. On Android phone, visit your server URL
2. Look for **"📱 Mobile App Controls"** section (at the top!)
3. Click **"📥 Download APK"**
4. Enable "Install from Unknown Sources" in Android settings
5. Open the downloaded APK
6. Follow installation prompts
7. Open the app and enjoy!

---

## 🔒 Tunnel Control from Web Interface

### Starting Tunnel for Mobile Access

1. Open web browser: `http://localhost:8000/`
2. Find **"📱 Mobile App Controls"** section (top of page)
3. Click **"▶️ Start Tunnel"** button
4. Wait for green status: 🟢 **Tunnel: Running**
5. Copy the tunnel URL shown
6. Share URL with mobile app users

### Stopping Tunnel

1. In the same section, click **"⏹ Stop Tunnel"**
2. Status changes to: 🔴 **Tunnel: Stopped**
3. Mobile app returns to local-only mode

---

## 🎨 Visual Reference

### Web Interface - Mobile Controls Section

```
┌─────────────────────────────────────────────────────────────┐
│        📱 MOBILE APP CONTROLS (Top of Page!)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔒 Secure Tunnel for Mobile    │    📲 Download Mobile App│
│  ┌────────────────────────────┐ │    ┌───────────────────┐ │
│  │ 🔴 Tunnel: Stopped         │ │    │       📱          │ │
│  │                            │ │    │                   │ │
│  │ ┌──────┐  ┌──────────────┐│ │    │  Get the Android  │ │
│  │ │ ▶️ Start│  │⏹ Stop Tunnel││ │    │  app to access    │ │
│  │ │ Tunnel │  │  (disabled)  ││ │    │  from anywhere    │ │
│  │ └──────┘  └──────────────┘│ │    │                   │ │
│  │                            │ │    │  📥 Download APK  │ │
│  │  🔄 Refresh Status         │ │    │                   │ │
│  └────────────────────────────┘ │    └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Commands Reference

### Build APK
```bash
# Automated (easiest)
./build_mobile_apk.sh

# Manual with EAS (no Android SDK needed)
cd mobile-app
npm install -g eas-cli
eas login
eas build --platform android --profile preview

# Manual with React Native (requires Android SDK)
cd mobile-app/android
./gradlew assembleRelease
```

### Copy APK to Web Server
```bash
cp your-app.apk src/static/webserver-mobile.apk
```

### Start Server
```bash
source .venv/bin/activate
python src/app.py
```

---

## 🔧 Troubleshooting

### APK Not Showing on Web Interface

1. **Check file location**:
   ```bash
   ls -la src/static/webserver-mobile.apk
   ```

2. **Verify file permissions**:
   ```bash
   chmod 644 src/static/webserver-mobile.apk
   ```

3. **Restart server**:
   ```bash
   # Stop server (Ctrl+C)
   python src/app.py
   ```

### Build Errors

#### "ANDROID_HOME not set"
```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

#### "Gradle build failed"
```bash
cd mobile-app/android
./gradlew clean
./gradlew assembleRelease
```

#### "EAS build failed"
```bash
# Check EAS status
eas build:list

# View build logs
eas build:view --id YOUR-BUILD-ID
```

---

## 📊 Testing the Complete Flow

### 1. Build APK
```bash
./build_mobile_apk.sh
```

### 2. Start Server
```bash
source .venv/bin/activate
python src/app.py
```

### 3. Access Web Interface
Open browser: `http://localhost:8000/`

### 4. Verify Controls Visible
- See "📱 Mobile App Controls" at top
- See tunnel control buttons
- See APK download button

### 5. Test Tunnel
- Click "▶️ Start Tunnel"
- Verify status turns 🟢 green
- See tunnel URL appear
- Click "⏹ Stop Tunnel"
- Verify status turns 🔴 red

### 6. Test APK Download
- Click "📥 Download APK"
- Verify download starts OR see build instructions

---

## 🎉 Success Checklist

- ✅ APK built successfully
- ✅ APK placed in `src/static/webserver-mobile.apk`
- ✅ Web interface shows mobile controls section
- ✅ Tunnel start/stop buttons work
- ✅ Status indicator updates correctly
- ✅ APK download button appears
- ✅ APK downloads when clicked
- ✅ Users can install APK on Android
- ✅ Mobile app connects successfully

---

## 🆘 Getting Help

If you encounter issues:

1. **Check server logs**:
   ```bash
   tail -f server.log
   ```

2. **Check mobile app build logs**:
   ```bash
   cd mobile-app
   npm run android --verbose
   ```

3. **Verify all files exist**:
   ```bash
   ls -la src/static/webserver-mobile.apk
   ls -la src/templates/index.html
   ls -la src/static/main.js
   ```

---

## 📝 Summary

Your webserver now has:

1. ✅ **Visible tunnel controls** on web interface (top of page!)
2. ✅ **APK download button** with instructions
3. ✅ **Automated build script** for easy APK creation
4. ✅ **Status indicators** showing tunnel state
5. ✅ **One-click tunnel** start/stop for mobile access

**Users can now easily download your mobile app and you can control tunnel access from the web interface!**

