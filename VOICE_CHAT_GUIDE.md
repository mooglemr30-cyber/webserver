# 🎤 Voice Chat Feature Guide

## Overview

The web server now includes a **real-time voice chat system** that allows the host and users to communicate using their microphones. The system uses WebRTC technology for peer-to-peer audio streaming.

## Features

### ✅ Core Functionality
- **Create Voice Rooms**: Start a new voice chat room with a custom name
- **Join Existing Rooms**: Browse and join active rooms
- **Real-time Participant List**: See who's in the room
- **Microphone Control**: Mute/unmute your microphone
- **Auto-cleanup**: Rooms automatically close when empty
- **Browser-based**: No installation required - works in any modern browser

### 🎯 Key Capabilities
- Requests microphone permission when joining a room
- Echo cancellation and noise suppression
- Auto gain control for balanced audio levels
- Visual indicators for active participants
- Simple, intuitive interface
- Mobile-responsive design

## How to Use

### For the Host (Creating a Room)

1. **Access the Voice Chat**:
   ```
   http://localhost:8000/voice-chat
   or
   http://192.168.1.13:8000/voice-chat
   ```

2. **Create a Room**:
   - Enter your name
   - Enter a room name (optional - auto-generated if left blank)
   - Click "Create Room"
   - Allow microphone access when prompted

3. **Control Your Audio**:
   - Click the 🎤 button to mute/unmute
   - Click the 📞 button to leave the room

### For Users (Joining a Room)

1. **Access the Voice Chat** at the same URL

2. **Join an Existing Room**:
   - Click "Refresh Rooms" to see available rooms
   - Find the room you want to join
   - Enter your name
   - Click "Join" on the room card
   - Allow microphone access when prompted

3. **Participate**:
   - Your audio will be transmitted to all participants
   - You'll hear all other participants
   - Use the microphone button to mute/unmute

## API Endpoints

### List Rooms
```bash
GET /api/voice-chat/rooms
```
Returns all active voice chat rooms.

### Create Room
```bash
POST /api/voice-chat/create
Content-Type: application/json

{
  "name": "My Room",
  "host_name": "Host"
}
```

### Join Room
```bash
POST /api/voice-chat/join/{room_id}
Content-Type: application/json

{
  "name": "User Name"
}
```

### Leave Room
```bash
POST /api/voice-chat/leave/{room_id}/{participant_id}
```

### Send Signal (WebRTC)
```bash
POST /api/voice-chat/signal/{room_id}
Content-Type: application/json

{
  "type": "offer|answer|ice-candidate",
  "data": {},
  "sender_id": "uuid",
  "target_id": "uuid"
}
```

### Poll for Messages
```bash
GET /api/voice-chat/poll/{room_id}/{participant_id}
```

## Browser Compatibility

### ✅ Fully Supported
- Chrome/Chromium 74+
- Firefox 70+
- Edge 79+
- Safari 14.1+
- Opera 62+

### ⚠️ Requirements
- **HTTPS or localhost**: Browsers require secure context for microphone access
- **Microphone permission**: Users must allow microphone access
- **Modern browser**: WebRTC support required

## Security & Privacy

### 🔒 Security Features
- Microphone access requires explicit user permission
- Audio streams are not recorded on the server
- Rooms automatically close when empty
- No audio data is stored

### 🔐 Important Notes
- **Local network only by default**: Server runs on localhost/local network
- **Tunnel for remote access**: Use ngrok/cloudflared for internet access
- **No authentication**: Anyone with the URL can join (add authentication if needed)
- **Unencrypted on HTTP**: Use HTTPS in production for encrypted audio

## Technical Details

### Architecture
```
Browser (WebRTC) <-> Server (Signaling) <-> Other Browsers (WebRTC)
     |                                              |
  Microphone                                   Speakers
```

### How It Works
1. **User joins room**: Browser requests microphone access
2. **WebRTC connection**: Browsers establish peer-to-peer connections
3. **Signaling**: Server facilitates connection setup (no audio routing)
4. **Audio streaming**: Audio flows directly between browsers (P2P)
5. **Monitoring**: Server tracks participants and room state

### Data Storage
- **In-memory**: All room data stored in RAM (cleared on restart)
- **No persistence**: Rooms don't survive server restarts
- **No recording**: Audio is never saved to disk

## Troubleshooting

### Microphone Not Working
1. Check browser permissions: `chrome://settings/content/microphone`
2. Verify microphone is connected and working
3. Try refreshing the page and allowing permission again
4. Check browser console for errors (F12)

### Can't Hear Other Participants
1. Check your computer's speaker/headphone settings
2. Verify other participants have joined and unmuted
3. Try leaving and rejoining the room
4. Check browser audio settings

### Connection Issues
1. Ensure server is running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Verify network connectivity
4. Try a different browser

### Room Not Appearing
1. Click "Refresh Rooms" button
2. Check if room was created successfully
3. Verify server is running
4. Check browser console for API errors

## Example Usage Scenarios

### 1. Team Meeting
- Host creates room: "Team Standup"
- Team members join from different computers
- Everyone can speak and be heard
- Meeting ends when last person leaves

### 2. Remote Support
- Support agent creates room: "Support Session"
- Customer joins with provided room name
- Voice communication while screen sharing (separate tool)
- Room auto-closes when done

### 3. Gaming Voice Chat
- Player creates room: "Game Night"
- Friends join before game starts
- Low-latency voice during gameplay
- Persistent across game sessions

## Integration with Other Features

### Works With:
- ✅ Terminal sessions (run commands while talking)
- ✅ Program execution (discuss outputs in real-time)
- ✅ File management (coordinate file transfers)
- ✅ Tunnels (enable remote voice chat via internet)
- ✅ Dashboard (monitor server while in voice chat)

## Future Enhancements

### Potential Features
- Video chat support
- Screen sharing
- Text chat alongside voice
- Recording capability (opt-in)
- Room passwords
- User authentication
- Push-to-talk mode
- Volume controls per participant
- Room capacity limits
- Persistent room URLs

## Performance Notes

### Resource Usage
- **CPU**: Minimal server load (signaling only)
- **Memory**: ~1KB per participant
- **Bandwidth**: Audio streams don't go through server (P2P)
- **Browser**: Moderate CPU for audio encoding/decoding

### Scalability
- Server can handle many rooms simultaneously
- Audio quality depends on participants' bandwidth
- No server bandwidth bottleneck (P2P design)
- Memory usage scales with number of participants

## Quick Start Commands

### Test the Feature
```bash
# Check if server is running
curl http://localhost:8000/health

# Open voice chat
xdg-open http://localhost:8000/voice-chat

# List active rooms
curl http://localhost:8000/api/voice-chat/rooms | jq
```

### Access from Network
```bash
# From another computer on the network
# Replace with your server's IP
http://192.168.1.13:8000/voice-chat
```

### Access from Internet (with tunnel)
```bash
# Start ngrok tunnel first
curl -X POST http://localhost:8000/api/ngrok/start

# Then access via the ngrok URL
# Example: https://abc123.ngrok.io/voice-chat
```

## Support

For issues or questions:
1. Check this guide
2. Review browser console (F12)
3. Check server logs
4. Test with different browsers
5. Verify microphone works in other apps

---

**Enjoy real-time voice communication on your web server! 🎤**
