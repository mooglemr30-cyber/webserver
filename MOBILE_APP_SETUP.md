# Mobile App Setup Guide

## Complete Setup Instructions for Ubuntu Server + Mobile App

This guide walks you through setting up your webserver with a persistent hidden tunnel and connecting it to a mobile app.

## 🎯 Overview

Your setup will have:
- **Ubuntu Server**: Running the Flask webserver
- **Cloudflare Tunnel**: Secure, hidden HTTPS tunnel (no port forwarding needed)
- **Mobile App**: React Native app connecting via the tunnel
- **Auto-start**: Server and tunnel start automatically on boot

## 📋 Prerequisites

### On Ubuntu Server
- Ubuntu 18.04+ (or other Linux distro)
- Python 3.8+
- Internet connection
- Sudo access (for cloudflared installation)

### On Development Machine (for mobile app)
- Node.js 16+
- React Native CLI
- Android Studio (for Android) OR Xcode (for iOS/macOS only)

## 🚀 Part 1: Server Setup (Ubuntu)

### Step 1: Install the Server

```bash
cd ~/Documents/webserver

# If you haven't already, run the install script
./install.sh

# Activate virtual environment
source .venv/bin/activate
```

### Step 2: Install Cloudflared (Tunnel Software)

```bash
# Download and install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version

# Clean up installer
rm cloudflared-linux-amd64.deb
```

### Step 3: Test the Server

```bash
# Start the server manually
python src/app.py
```

You should see output like:
```
🚀 Starting Network Web Server
...
📱 Mobile Access Setup:
   Starting persistent Cloudflare tunnel for mobile app...
   ✅ Mobile tunnel active: https://xxxxx-xxxxx.trycloudflare.com
   📱 Use this URL in your mobile app
   🔒 Tunnel is hidden and secure (no public listing)
```

**IMPORTANT**: Copy the tunnel URL (e.g., `https://xxxxx-xxxxx.trycloudflare.com`) - you'll need it for the mobile app!

### Step 4: Setup Auto-Start on Boot

```bash
# Copy the systemd service file
sudo cp webserver-mobile.service /etc/systemd/system/

# Edit the service file if your paths are different
# sudo nano /etc/systemd/system/webserver-mobile.service

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable webserver-mobile.service

# Start the service now
sudo systemctl start webserver-mobile.service

# Check status
sudo systemctl status webserver-mobile.service
```

### Step 5: Get Your Tunnel URL

```bash
# View the logs to see the tunnel URL
sudo journalctl -u webserver-mobile.service -f

# Or check the service logs
tail -f ~/Documents/webserver/logs/service.log
```

Look for a line like:
```
✅ Mobile tunnel active: https://xxxxx-xxxxx.trycloudflare.com
```

### Step 6: Test the Tunnel

From any device with internet:
```bash
curl https://your-tunnel-url.trycloudflare.com/health
```

You should get:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "..."
  }
}
```

## 📱 Part 2: Mobile App Setup

### Step 1: Install React Native

```bash
# Install Node.js (if not already installed)
# Visit: https://nodejs.org/

# Verify Node.js installation
node --version  # Should be 16+
npm --version

# Install React Native CLI globally
npm install -g react-native-cli
```

### Step 2: Setup Mobile Development Environment

#### For Android:

1. Download and install [Android Studio](https://developer.android.com/studio)
2. Install Android SDK (API 33+) via Android Studio
3. Add Android SDK to PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/tools
export PATH=$PATH:$ANDROID_HOME/tools/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

#### For iOS (macOS only):

1. Install Xcode from App Store
2. Install Xcode Command Line Tools:
```bash
xcode-select --install
```
3. Install CocoaPods:
```bash
sudo gem install cocoapods
```

### Step 3: Setup Mobile App

```bash
cd ~/Documents/webserver/mobile-app

# Install dependencies
npm install

# For iOS (macOS only)
cd ios
pod install
cd ..
```

### Step 4: Configure Server URL

Edit `mobile-app/src/config.js`:

```javascript
const CONFIG = {
  // Replace with your actual tunnel URL from Step 5 above
  DEFAULT_SERVER_URL: 'https://your-actual-tunnel-url.trycloudflare.com',
  // ... rest of config
};
```

### Step 5: Run the Mobile App

#### On Android:

```bash
# Start an Android emulator from Android Studio
# OR connect a physical Android device via USB with USB debugging enabled

# Run the app
npm run android
```

#### On iOS (macOS only):

```bash
# Run the app
npm run ios
```

### Step 6: Connect to Your Server

1. App will open on your device/emulator
2. The tunnel URL should be pre-filled from config
3. Click "Connect"
4. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
5. You're connected! 🎉

## 🔧 Useful Commands

### Server Management

```bash
# Start server
sudo systemctl start webserver-mobile.service

# Stop server
sudo systemctl stop webserver-mobile.service

# Restart server
sudo systemctl restart webserver-mobile.service

# View logs
sudo journalctl -u webserver-mobile.service -f

# Check status
sudo systemctl status webserver-mobile.service
```

### Get Current Tunnel URL

```bash
# Using curl
curl http://localhost:8000/api/mobile/tunnel/status

# Using the web interface
# Open browser: http://localhost:8000
# The tunnel URL will be displayed on the page
```

### Tunnel Management via API

```bash
# Start tunnel
curl -X POST http://localhost:8000/api/mobile/tunnel/start

# Stop tunnel
curl -X POST http://localhost:8000/api/mobile/tunnel/stop

# Get status
curl http://localhost:8000/api/mobile/tunnel/status
```

## 🔐 Security Notes

### Tunnel Security

- **Hidden URLs**: Cloudflare Quick Tunnels use randomly generated URLs that are not publicly listed
- **HTTPS**: All traffic is encrypted via HTTPS
- **No Port Forwarding**: No need to open ports on your router
- **URL Changes**: The tunnel URL changes each time you restart (free tier limitation)

### Authentication

- Change the default admin password immediately:
```bash
# Via web interface: http://localhost:8000
# Or via API
curl -X POST http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin123","new_password":"your-new-password"}'
```

### Recommended Security Measures

1. **Change default credentials**
2. **Use strong passwords**
3. **Regularly update the server** (`git pull` and restart service)
4. **Monitor logs** for suspicious activity
5. **Limit API access** if needed (configure in `src/app.py`)

## 🐛 Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Kill process if needed
sudo kill <PID>

# Check logs
tail -f ~/Documents/webserver/logs/service.log
```

### Tunnel won't start

```bash
# Check if cloudflared is installed
cloudflared --version

# Reinstall if needed
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Mobile app won't connect

1. **Check tunnel URL is correct** in `mobile-app/src/config.js`
2. **Test tunnel URL** in browser: `https://your-url.trycloudflare.com/health`
3. **Check server is running**: `sudo systemctl status webserver-mobile.service`
4. **Check device has internet** connection
5. **Restart app** completely

### Android build issues

```bash
cd mobile-app/android
./gradlew clean
cd ..
npm run android
```

### iOS build issues (macOS)

```bash
cd mobile-app/ios
pod install --repo-update
cd ..
npm run ios
```

## 📊 Monitoring

### Check Server Health

```bash
# Via API
curl https://your-tunnel-url.trycloudflare.com/health

# Via web interface
# Open: https://your-tunnel-url.trycloudflare.com
```

### View Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Or via tunnel
curl https://your-tunnel-url.trycloudflare.com/metrics
```

## 🔄 Updating

### Update Server

```bash
cd ~/Documents/webserver
git pull  # If using git

# Restart service
sudo systemctl restart webserver-mobile.service
```

### Update Mobile App

```bash
cd ~/Documents/webserver/mobile-app
git pull  # If using git
npm install  # Update dependencies

# Rebuild and run
npm run android  # or npm run ios
```

## 📱 Building for Production

### Android APK

```bash
cd mobile-app/android
./gradlew assembleRelease

# APK will be at:
# android/app/build/outputs/apk/release/app-release.apk
```

### iOS App (macOS only)

1. Open Xcode: `open ios/WebserverApp.xcworkspace`
2. Select your device or "Any iOS Device"
3. Product → Archive
4. Distribute App → Ad Hoc or App Store

## 🎯 What's Next?

- **Add more features** to the mobile app
- **Customize the UI** to your liking
- **Setup persistent tunnel** with a custom domain (requires Cloudflare account)
- **Add push notifications** for server events
- **Implement file upload/download** in mobile app
- **Add program execution** interface

## 💡 Tips

1. **Save the tunnel URL**: It changes on restart, so save it or use the API to fetch it
2. **Use the web interface**: Still accessible at `http://localhost:8000` on the server
3. **Check logs regularly**: Monitor for errors or unauthorized access
4. **Backup your data**: Use the backup system regularly
5. **Test on local network first**: Use `http://<server-ip>:8000` before using the tunnel

## 📚 Additional Resources

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [React Native Docs](https://reactnative.dev/docs/getting-started)
- [Flask Docs](https://flask.palletsprojects.com/)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review server logs: `sudo journalctl -u webserver-mobile.service -f`
3. Test the tunnel URL manually: `curl https://your-url.trycloudflare.com/health`
4. Ensure all dependencies are installed correctly

---

**You're all set!** 🎉 Your server is now accessible via mobile app through a secure hidden tunnel.

