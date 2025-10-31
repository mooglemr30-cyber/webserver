# 📱 Mobile App Quick Reference

## One-Command Setup

```bash
cd ~/Documents/webserver && ./setup_mobile.sh
```

## Manual Setup (3 Steps)

### 1️⃣ Install Cloudflared (Ubuntu Server)

```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### 2️⃣ Start Server

```bash
cd ~/Documents/webserver
source .venv/bin/activate
python src/app.py
```

### 3️⃣ Get Tunnel URL

Look for this in the output:
```
✅ Mobile tunnel active: https://xxxxx-xxxxx.trycloudflare.com
```

## Mobile App Setup (React Native)

### Quick Start

```bash
cd ~/Documents/webserver/mobile-app

# Install dependencies
npm install

# Update config with your tunnel URL
# Edit: src/config.js → DEFAULT_SERVER_URL

# Run on Android
npm run android

# Run on iOS (macOS only)
npm run ios
```

## Essential Commands

### Server Management

```bash
# Start (systemd)
sudo systemctl start webserver-mobile.service

# Stop
sudo systemctl stop webserver-mobile.service

# Status
sudo systemctl status webserver-mobile.service

# Logs
sudo journalctl -u webserver-mobile.service -f
```

### Tunnel Management

```bash
# Get tunnel URL
curl http://localhost:8000/api/mobile/tunnel/status | jq .

# Start tunnel (if not auto-started)
curl -X POST http://localhost:8000/api/mobile/tunnel/start

# Stop tunnel
curl -X POST http://localhost:8000/api/mobile/tunnel/stop
```

### Testing

```bash
# Test health (local)
curl http://localhost:8000/health

# Test health (via tunnel)
curl https://your-tunnel-url.trycloudflare.com/health

# Get mobile config
curl https://your-tunnel-url.trycloudflare.com/api/mobile/config
```

## Key Files

### Server Side
- `src/tunnel_manager.py` - Tunnel management
- `src/app.py` - Mobile API endpoints (lines 3827+)
- `webserver-mobile.service` - Systemd service
- `data/config/tunnel_config.json` - Tunnel configuration

### Mobile App
- `mobile-app/src/config.js` - Server URL configuration
- `mobile-app/src/App.js` - Main app UI
- `mobile-app/src/services/ApiService.js` - API client

## Troubleshooting

### Tunnel not starting?

```bash
# Check cloudflared
cloudflared --version

# Reinstall if needed
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

### Mobile app can't connect?

1. Verify tunnel URL: `curl http://localhost:8000/api/mobile/tunnel/status`
2. Update `mobile-app/src/config.js` with correct URL
3. Test URL in browser: `https://your-url.trycloudflare.com/health`
4. Restart mobile app completely

### Server not starting?

```bash
# Check port
sudo lsof -i :8000

# Check logs
tail -f ~/Documents/webserver/logs/service.log
```

## Default Credentials

```
Username: admin
Password: admin123
```

⚠️ **Change these immediately after first login!**

## URLs

- **Local Web**: http://localhost:8000
- **Mobile Tunnel**: https://xxxxx.trycloudflare.com (changes on restart)
- **Ngrok Web Interface**: http://localhost:4040 (if using ngrok)

## File Locations

### Logs
- Service: `~/Documents/webserver/logs/service.log`
- Errors: `~/Documents/webserver/logs/service-error.log`
- Systemd: `sudo journalctl -u webserver-mobile.service`

### Data
- Storage: `~/Documents/webserver/data/storage.json`
- Files: `~/Documents/webserver/data/files/`
- Config: `~/Documents/webserver/data/config/`

### Mobile
- App: `~/Documents/webserver/mobile-app/`
- Config: `~/Documents/webserver/mobile-app/src/config.js`

## API Endpoints (Mobile)

```bash
# Health check
GET /health

# Mobile configuration
GET /api/mobile/config

# Tunnel management
POST /api/mobile/tunnel/start
POST /api/mobile/tunnel/stop
GET  /api/mobile/tunnel/status

# Authentication
POST /auth/login
POST /auth/register

# Data storage
GET    /api/data
POST   /api/data
GET    /api/data/<key>
DELETE /api/data/<key>

# File management
GET    /api/files/list
POST   /api/files/upload
GET    /api/files/download/<filename>
DELETE /api/files/delete/<filename>
```

## Building Mobile App for Production

### Android APK

```bash
cd mobile-app/android
./gradlew assembleRelease

# APK location:
# android/app/build/outputs/apk/release/app-release.apk
```

### iOS (macOS only)

```bash
# Open Xcode
open mobile-app/ios/WebserverApp.xcworkspace

# Product → Archive → Distribute
```

## Security Notes

✅ **Secure:**
- HTTPS encrypted (Cloudflare)
- Hidden URL (not publicly listed)
- JWT authentication
- No port forwarding needed

⚠️ **Remember:**
- Tunnel URL changes on restart (free tier)
- Change default passwords
- Monitor logs regularly
- Keep server updated

## Documentation

- 📖 **Full Guide**: `MOBILE_APP_SETUP.md`
- 📝 **Implementation**: `MOBILE_IMPLEMENTATION_SUMMARY.md`
- 📱 **Mobile App**: `mobile-app/README.md`
- 🔧 **Main README**: `README.md`

## Quick Links

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/)
- [React Native Docs](https://reactnative.dev/)
- [Flask Docs](https://flask.palletsprojects.com/)

---

**Need help?** Check `MOBILE_APP_SETUP.md` for detailed troubleshooting.

