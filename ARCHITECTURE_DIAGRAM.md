# Mobile App Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                         MOBILE APP ARCHITECTURE                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
    │   Android App   │         │    iOS App      │         │  Web Browser    │
    │  (React Native) │         │ (React Native)  │         │   (Existing)    │
    └────────┬────────┘         └────────┬────────┘         └────────┬────────┘
             │                           │                           │
             └───────────────────────────┴───────────────────────────┘
                                         │
                                    HTTPS/SSL
                                    (Encrypted)
                                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TUNNEL LAYER                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │   Cloudflare Quick Tunnel     │
                         │  (Hidden, Secure, Free)       │
                         │                               │
                         │  https://xxxxx.trycloudflare  │
                         │         .com                  │
                         │                               │
                         │  Features:                    │
                         │  • HTTPS encryption          │
                         │  • No port forwarding        │
                         │  • Hidden URL                │
                         │  • DDoS protection           │
                         └───────────────┬───────────────┘
                                         │
                                    Port 8000
                                    (Tunneled)
                                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVER LAYER (Ubuntu)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │   Flask Application           │
                         │   (src/app.py)                │
                         │   Port: 8000 (localhost only) │
                         └───────────────┬───────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │   Mobile API Endpoints        │
                         │                               │
                         │  • /health                    │
                         │  • /api/mobile/config         │
                         │  • /api/mobile/tunnel/*       │
                         │  • /auth/*                    │
                         │  • /api/data/*                │
                         │  • /api/files/*               │
                         └───────────────┬───────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌────────────────┐            ┌────────────────┐            ┌────────────────┐
│ Data Storage   │            │ File Storage   │            │ Auth System    │
│ (data_store.py)│            │ (file_store.py)│            │(auth_system.py)│
│                │            │                │            │                │
│ storage.json   │            │ data/files/    │            │ users.json     │
└────────────────┘            └────────────────┘            └────────────────┘


╔══════════════════════════════════════════════════════════════════════════════╗
║                         COMPONENT BREAKDOWN                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. TUNNEL MANAGER (NEW)                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    src/tunnel_manager.py
    │
    ├── PersistentTunnelManager
    │   ├── start_tunnel()          → Launch cloudflared
    │   ├── stop_tunnel()           → Stop cloudflared
    │   ├── get_status()            → Check tunnel status
    │   ├── get_mobile_config()     → Config for mobile app
    │   └── _monitor_tunnel()       → Auto-restart if dies
    │
    └── Uses: cloudflared (external binary)

┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. MOBILE API ENDPOINTS (NEW - Added to app.py)                             │
└─────────────────────────────────────────────────────────────────────────────┘

    POST   /api/mobile/tunnel/start     → Start tunnel
    POST   /api/mobile/tunnel/stop      → Stop tunnel
    GET    /api/mobile/tunnel/status    → Get tunnel info
    GET    /api/mobile/config           → Get server config
    GET    /health                      → Health check

┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. MOBILE APP (NEW - React Native)                                          │
└─────────────────────────────────────────────────────────────────────────────┘

    mobile-app/
    │
    ├── src/App.js                  → Main UI component
    │   ├── Connection screen
    │   ├── Login screen
    │   └── Data management screen
    │
    ├── src/services/ApiService.js  → API communication
    │   ├── HTTP client (axios)
    │   ├── Token management
    │   ├── Request/response handling
    │   └── Error handling
    │
    └── src/config.js               → Configuration
        └── Server URL


╔══════════════════════════════════════════════════════════════════════════════╗
║                         DATA FLOW DIAGRAM                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

EXAMPLE: Store Data from Mobile App

┌─────────────┐                                              ┌──────────────┐
│ Mobile App  │                                              │ Flask Server │
└──────┬──────┘                                              └──────┬───────┘
       │                                                            │
       │ 1. POST /api/data                                          │
       │    {key: "test", value: "hello"}                           │
       │────────────────────────────────────────────────────────────>│
       │                                                            │
       │                                    2. Validate JWT token   │
       │                                    3. Store in data_store  │
       │                                    4. Save to storage.json │
       │                                                            │
       │ 5. Response: {success: true, ...}                          │
       │<────────────────────────────────────────────────────────────│
       │                                                            │
       │ 6. Update UI with success                                  │
       │                                                            │


╔══════════════════════════════════════════════════════════════════════════════╗
║                         DEPLOYMENT FLOW                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Server Setup (Ubuntu)                                                │
└──────────────────────────────────────────────────────────────────────────────┘

    ./setup_mobile.sh
         │
         ├─→ Install cloudflared
         ├─→ Setup Python venv
         ├─→ Install dependencies
         ├─→ Create systemd service
         └─→ Start server

┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Server Starts                                                        │
└──────────────────────────────────────────────────────────────────────────────┘

    python src/app.py
         │
         ├─→ Initialize Flask app
         ├─→ Load data stores
         ├─→ Initialize tunnel_manager
         ├─→ Start tunnel (auto)
         │   └─→ cloudflared tunnel --url http://localhost:8000
         │       └─→ Get tunnel URL: https://xxxxx.trycloudflare.com
         │
         └─→ Server ready ✅

┌──────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Mobile App Setup                                                     │
└──────────────────────────────────────────────────────────────────────────────┘

    cd mobile-app
         │
         ├─→ npm install
         ├─→ Update config.js with tunnel URL
         ├─→ npm run android (or ios)
         │
         └─→ App connects to server via tunnel ✅


╔══════════════════════════════════════════════════════════════════════════════╗
║                         SECURITY LAYERS                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    • HTTPS encryption (TLS 1.3)
    • Cloudflare DDoS protection
    • Server only listens on localhost (127.0.0.1)
    • No exposed ports on router

┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 2: Application Security                                               │
└─────────────────────────────────────────────────────────────────────────────┘

    • JWT token authentication
    • Password hashing (bcrypt)
    • Rate limiting
    • CSRF protection
    • Input validation

┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 3: Access Control                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

    • Role-based access (admin/user)
    • Hidden tunnel URL (secret)
    • Session management
    • Token expiration


╔══════════════════════════════════════════════════════════════════════════════╗
║                         FILE STRUCTURE                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

webserver/
│
├── src/
│   ├── app.py                      ← MODIFIED (5 endpoints added)
│   ├── tunnel_manager.py           ← NEW (tunnel management)
│   ├── data_store.py               ← Existing
│   ├── file_store.py               ← Existing
│   ├── auth_system.py              ← Existing
│   └── ... (other modules)
│
├── mobile-app/                     ← NEW (entire directory)
│   ├── src/
│   │   ├── App.js
│   │   ├── config.js
│   │   └── services/
│   │       └── ApiService.js
│   ├── package.json
│   └── ...
│
├── webserver-mobile.service        ← NEW (systemd service)
├── setup_mobile.sh                 ← NEW (setup script)
├── MOBILE_APP_SETUP.md             ← NEW (documentation)
├── MOBILE_IMPLEMENTATION_SUMMARY.md ← NEW (summary)
├── MOBILE_QUICK_REF.md             ← NEW (quick reference)
└── README.md                       ← MODIFIED (updated features)


╔══════════════════════════════════════════════════════════════════════════════╗
║                         SUMMARY                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ MINIMAL PATCH:
   • 1 new Python file (tunnel_manager.py)
   • 5 new API endpoints in app.py (~50 lines)
   • Mobile app in separate directory (no interference)

✅ KEY FEATURES:
   • Hidden, secure Cloudflare tunnel
   • Auto-start on boot (systemd)
   • React Native mobile app
   • Full CRUD operations
   • HTTPS encryption
   • No port forwarding needed

✅ PRODUCTION READY:
   • Auto-restart on failure
   • Comprehensive logging
   • Error handling
   • Security best practices
   • Documentation complete
