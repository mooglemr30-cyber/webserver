# Mobile App UI - Tunnel Control Section

## New UI Layout

```
┌─────────────────────────────────────────┐
│  ✅ Connected                           │
│  http://localhost:8000                  │
├─────────────────────────────────────────┤
│                                         │
│  🔒 Secure Tunnel                       │
│  ┌───────────────────────────────────┐  │
│  │ 🔴 Tunnel: Stopped          🔄    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌──────────────┐ ┌──────────────────┐ │
│  │ ▶ Start      │ │ ⏹ Stop Tunnel   │ │
│  │   Tunnel     │ │   (disabled)     │ │
│  └──────────────┘ └──────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 💡 By default, the app uses local │  │
│  │ connection. Start the tunnel only │  │
│  │ when accessing remotely.          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## When Tunnel is Running

```
┌─────────────────────────────────────────┐
│  ✅ Connected                           │
│  http://localhost:8000                  │
├─────────────────────────────────────────┤
│                                         │
│  🔒 Secure Tunnel                       │
│  ┌───────────────────────────────────┐  │
│  │ 🟢 Tunnel: Running          🔄    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ Tunnel URL:                       │  │
│  │ https://abc123.trycloudflare.com  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌──────────────┐ ┌──────────────────┐ │
│  │ ▶ Start      │ │ ⏹ Stop Tunnel   │ │
│  │   Tunnel     │ │                  │ │
│  │ (disabled)   │ │  [ACTIVE]        │ │
│  └──────────────┘ └──────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ 💡 By default, the app uses local │  │
│  │ connection. Start the tunnel only │  │
│  │ when accessing remotely.          │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Status Indicator Details

### 🔴 Red Dot + "Tunnel: Stopped"
- Tunnel is not running
- App uses local connection only
- Safe - not exposed to internet
- Works only on same network

### 🟢 Green Dot + "Tunnel: Running"  
- Tunnel is active
- App can connect remotely
- Tunnel URL is displayed
- Accessible from anywhere

### 🔄 Refresh Button
- Manually check current tunnel status
- Updates indicator and URL
- Useful for verification

## Button States

### Start Tunnel Button (Green)
- **Enabled**: When tunnel is stopped
- **Disabled**: When tunnel is running
- **Loading**: Shows "Starting..." during startup

### Stop Tunnel Button (Red)
- **Enabled**: When tunnel is running
- **Disabled**: When tunnel is stopped
- **Loading**: Shows "Stopping..." during shutdown

## User Flow Examples

### Scenario 1: Local Use (Default)
```
1. Open App
2. Auto-connect to localhost:8000
3. See "Tunnel: Stopped" 🔴
4. Login and use normally
5. No tunnel needed!
```

### Scenario 2: Remote Access Needed
```
1. In app, see "Tunnel: Stopped" 🔴
2. Tap "▶ Start Tunnel"
3. Wait for status to change to 🟢
4. See tunnel URL appear
5. Use app remotely
6. When done, tap "⏹ Stop Tunnel"
7. Verify status returns to 🔴
```

### Scenario 3: Check Tunnel Status
```
1. Not sure if tunnel is running?
2. Tap refresh button 🔄
3. Status updates immediately
4. See current tunnel state
```

## Color Coding

| Element | Color | Meaning |
|---------|-------|---------|
| 🟢 Green Dot | #34C759 | Tunnel Active |
| 🔴 Red Dot | #FF3B30 | Tunnel Inactive |
| Start Button | #34C759 | Safe to start |
| Stop Button | #FF3B30 | Active - can stop |
| Disabled Button | #C7C7CC | Cannot interact |
| Tunnel URL | #007AFF | Link/Info blue |
| Info Box | #FFF3CD | Warning/Info yellow |

## Integration Points

The tunnel control section appears:
- ✅ After login (authenticated view)
- ✅ Before data storage section
- ✅ At top of scrollable content
- ✅ Always visible when logged in

This ensures users always have easy access to tunnel controls while using the app!

