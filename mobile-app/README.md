# Mobile App for Webserver

This directory contains the React Native mobile application for accessing your webserver through a secure hidden tunnel.

## Features

- Secure connection via Cloudflare Tunnel
- Data storage management
- File upload/download
- Program execution
- Command execution
- Real-time status monitoring

## Prerequisites

```bash
# Install Node.js (16+)
# Install React Native CLI
npm install -g react-native-cli

# For iOS (macOS only)
# Install Xcode from App Store
# Install CocoaPods
sudo gem install cocoapods

# For Android
# Install Android Studio
# Install Android SDK (API 33+)
```

## Setup

```bash
cd mobile-app

# Install dependencies
npm install

# For iOS
cd ios && pod install && cd ..

# For Android (nothing additional needed)
```

## Configuration

1. Get your server's tunnel URL from the web interface or server logs
2. Update `src/config.js` with your server URL
3. The app will automatically connect via the secure tunnel

## Running

```bash
# Run on iOS
npm run ios

# Run on Android
npm run android

# Run Metro bundler separately (if needed)
npm start
```

## Building for Production

### Android

```bash
cd android
./gradlew assembleRelease
# APK will be at: android/app/build/outputs/apk/release/app-release.apk
```

### iOS

```bash
# Open Xcode
open ios/WebserverApp.xcworkspace

# Select your device/simulator
# Product > Archive
# Distribute to App Store or Ad Hoc
```

## Security

- The app uses JWT authentication
- All communication is encrypted via HTTPS (Cloudflare Tunnel)
- The tunnel URL is hidden and not publicly listed
- No port forwarding or firewall changes needed

## Troubleshooting

### Connection Issues

1. Check server is running: `http://your-tunnel-url/health`
2. Verify tunnel is active: `http://your-tunnel-url/api/mobile/tunnel/status`
3. Check network connectivity

### Build Issues

**iOS:**
```bash
cd ios && pod install --repo-update
```

**Android:**
```bash
cd android && ./gradlew clean
```

## Project Structure

```
mobile-app/
├── src/
│   ├── screens/          # App screens
│   ├── components/       # Reusable components
│   ├── services/         # API services
│   ├── config.js         # Configuration
│   └── App.js           # Main app component
├── android/             # Android native code
├── ios/                 # iOS native code
└── package.json         # Dependencies
```

## API Endpoints Used

- `GET /health` - Health check
- `GET /api/mobile/config` - Get server configuration
- `POST /auth/login` - User authentication
- `GET /api/data` - Get all data
- `POST /api/data` - Store data
- `POST /api/files/upload` - Upload files
- `GET /api/files/list` - List files
- `POST /api/execute` - Execute commands

## License

MIT

