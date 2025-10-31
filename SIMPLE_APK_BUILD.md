# 📱 SIMPLE APK BUILD GUIDE

## 🚀 Quick Build (Recommended)

### Option 1: EAS Cloud Build (EASIEST - No Android SDK needed!)

```bash
cd /home/admin1/Documents/webserver
chmod +x build_expo_app.sh
./build_expo_app.sh
```

**Choose Option 1** when prompted.

This will:
1. Install Expo CLI
2. Install EAS CLI  
3. Install app dependencies
4. Build APK in the cloud (free!)
5. Give you a download link

**You'll need**:
- Expo account (free at expo.dev)
- Internet connection

**Steps**:
1. Run the script
2. Login to Expo when prompted (browser opens)
3. Wait for cloud build (~5-10 minutes)
4. Download APK when ready
5. Move to `src/static/webserver-mobile.apk`

---

## 📦 After Building

### Download Your APK

```bash
# Check build status
cd mobile-app
eas build:list

# Download the latest build
eas build:download --platform android --latest

# Move to static directory
mv *.apk ../src/static/webserver-mobile.apk
```

### Test Download from Web

1. Start server: `python src/app.py`
2. Open: `http://localhost:8000/`
3. Look for "📱 Mobile App Controls" section
4. Click "📥 Download APK"
5. APK should download!

---

## 🔧 Alternative: Manual Steps

If you prefer to do it manually:

### 1. Install Tools

```bash
# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Expo CLI
npm install -g expo-cli

# Install EAS CLI
npm install -g eas-cli
```

### 2. Setup App

```bash
cd /home/admin1/Documents/webserver/mobile-app

# Install dependencies
npm install --legacy-peer-deps

# Create assets folder
mkdir -p assets
```

### 3. Build APK

```bash
# Login to Expo
eas login

# Build APK
eas build --platform android --profile preview

# Wait for build to complete (~5-10 min)

# Download when ready
eas build:download --platform android --latest
```

### 4. Deploy

```bash
# Move APK to static directory
mv *.apk ../src/static/webserver-mobile.apk

# Make accessible
chmod 644 ../src/static/webserver-mobile.apk
```

---

## 🎯 What Each Method Does

### EAS Build (Cloud)
✅ **Easiest** - No Android SDK needed
✅ **Free** - Up to 30 builds/month
✅ **Fast** - 5-10 minutes
✅ **Reliable** - Professional build servers
❌ Requires Expo account
❌ Requires internet

### Local Build
✅ **Offline** - No internet needed after setup
✅ **No account** needed
❌ **Complex** - Need Android SDK
❌ **Slow** - First build 30+ minutes
❌ **Large** - Android SDK is 3-4GB

---

## 🆘 Troubleshooting

### "expo: command not found"
```bash
npm install -g expo-cli
```

### "eas: command not found"
```bash
npm install -g eas-cli
```

### "npm install failed"
```bash
cd mobile-app
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### "Build failed"
Check build logs:
```bash
eas build:list
eas build:view --id [BUILD_ID]
```

### "Can't login to Expo"
1. Create account at: https://expo.dev/signup
2. Run: `eas login`
3. Enter credentials

---

## 📊 Build Status

Check your builds:

```bash
# List all builds
eas build:list

# View specific build
eas build:view --id [BUILD_ID]

# Download latest
eas build:download --platform android --latest
```

---

## ✅ Success Checklist

- [ ] Expo CLI installed (`expo --version`)
- [ ] EAS CLI installed (`eas --version`)
- [ ] Dependencies installed (`ls mobile-app/node_modules`)
- [ ] Expo account created
- [ ] Logged in to EAS (`eas whoami`)
- [ ] Build submitted (`eas build --platform android`)
- [ ] Build completed (check with `eas build:list`)
- [ ] APK downloaded
- [ ] APK moved to `src/static/webserver-mobile.apk`
- [ ] APK downloadable from web interface

---

## 🎉 You're Done!

Once the APK is at `src/static/webserver-mobile.apk`:

1. Users visit your web interface
2. See "📱 Mobile App Controls" section
3. Click "📥 Download APK"
4. Install on Android phone
5. Connect and use!

---

## 💡 Pro Tips

### Tip 1: Use EAS Build Profile "preview"
This creates APKs that can be directly installed (vs Google Play)

### Tip 2: Check Build Queue
Builds can queue during peak times. Be patient!

### Tip 3: Save Build ID
Keep the build ID from output - makes downloading easier later

### Tip 4: Version Your APK
Rename downloaded APK to include version:
```bash
mv app-build.apk webserver-mobile-v1.0.0.apk
```

---

## 🚀 Quick Reference

```bash
# Complete build process (one command!)
chmod +x build_expo_app.sh && ./build_expo_app.sh

# Check build status
cd mobile-app && eas build:list

# Download latest build
eas build:download --platform android --latest

# Deploy to web
mv *.apk ../src/static/webserver-mobile.apk
```

**That's it! Run the script and choose Option 1 for easiest build!** 🎉

