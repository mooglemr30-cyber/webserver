# API Usage Guide - All Features Working! ✅

## ✅ Status: ALL FEATURES OPERATIONAL

I've fixed all the API endpoints. Everything now works correctly from both the web UI and command line!

## 🔧 What Was Fixed

1. **File Storage** - Added missing v1 API endpoints (`/api/files/*`)
2. **Tunnel Management** - Added missing tunnel control endpoints (`/api/ngrok/*`, `/api/cloudflared/*`, `/api/tunnels/*`)
3. **Program Execution** - Already working, just needed correct usage
4. **Persistent Tunnel** - Auto-starts with server, provides public HTTPS URL

## 🌐 Tunnel Status

Your Cloudflare tunnel is **ACTIVE** and **AUTOMATIC**:
- Starts automatically when server starts
- Provides secure HTTPS public URL
- No authentication required from your side
- Access from anywhere using the tunnel URL

### Get Tunnel Info
```bash
# Check persistent tunnel (auto-started)
curl http://localhost:8000/api/mobile/tunnel/status

# Check all tunnels
curl http://localhost:8000/api/tunnels/status
```

### Start Additional Tunnels
```bash
# Start ngrok (requires ngrok installation and auth)
curl -X POST http://localhost:8000/api/ngrok/start

# Start cloudflared (manual control)
curl -X POST http://localhost:8000/api/cloudflared/start

# Stop all tunnels
curl -X POST http://localhost:8000/api/tunnels/stop-all
```

## 📁 File Storage (WORKING ✅)

### Upload Files
**Works from both web UI and API!** Use field name `files` (plural)
```bash
# Single file (v1 or v2 endpoints both work)
curl -F "files=@myfile.txt" http://localhost:8000/api/files/upload
curl -F "files=@myfile.txt" http://localhost:8000/api/v2/files/upload

# Multiple files
curl -F "files=@file1.txt" -F "files=@file2.pdf" http://localhost:8000/api/files/upload
```

### List Files
```bash
curl http://localhost:8000/api/files/list
```

### Download File
```bash
curl http://localhost:8000/api/files/download/filename.txt -o downloaded.txt
```

### Delete File
```bash
curl -X DELETE http://localhost:8000/api/files/delete/filename.txt
```

### Storage Info
```bash
curl http://localhost:8000/api/files/storage
```

## ⚡ Program Execution (WORKING ✅)

### Upload Program
```bash
# Both endpoints work
curl -F "file=@script.py" http://localhost:8000/api/programs/upload
curl -F "file=@script.py" http://localhost:8000/api/v2/programs/upload
```

**Response includes `program_id`** - save this!

### Execute Program
**Important:** Use `program_id` from upload response, not filename
```bash
# Get program_id from list or upload response
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8000/api/programs/execute/program_1762091505
```

### Execute with Arguments
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"args": ["arg1", "arg2"]}' \
  http://localhost:8000/api/v2/programs/execute/program_1762091505
```

### List Programs
```bash
curl http://localhost:8000/api/v2/programs/list
```

### Get Program Info
```bash
curl http://localhost:8000/api/v2/programs/info/program_1762091505
```

### Delete Program
```bash
curl -X DELETE http://localhost:8000/api/v2/programs/delete/program_1762091505
```

## 🔍 Common Patterns

### Upload and Execute Python Script
```bash
# 1. Upload
RESPONSE=$(curl -s -F "file=@myscript.py" http://localhost:8000/api/v2/programs/upload)
echo "$RESPONSE" | jq .

# 2. Extract program_id
PROGRAM_ID=$(echo "$RESPONSE" | jq -r '.program.program_id')
echo "Program ID: $PROGRAM_ID"

# 3. Execute
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  "http://localhost:8000/api/v2/programs/execute/$PROGRAM_ID" | jq .
```

### Upload Project (Zip File)
```bash
# Create zip
zip -r myproject.zip myproject/

# Upload
curl -F "file=@myproject.zip" http://localhost:8000/api/v2/programs/upload

# The server automatically extracts and creates a project
```

## 🛠️ Testing Commands

### Quick Test Suite
```bash
# Health check
curl http://localhost:8000/health

# Storage info
curl http://localhost:8000/api/v2/files/storage

# Tunnel status
curl http://localhost:8000/api/mobile/tunnel/status

# List programs
curl http://localhost:8000/api/v2/programs/list

# List files
curl http://localhost:8000/api/v2/files/list
```

## 📱 Mobile Access

Your tunnel URL changes each restart but is always available at:
```bash
curl http://localhost:8000/api/mobile/tunnel/status | jq -r '.data.url'
```

Use this URL from your mobile app to access the server from anywhere.

## 🎯 Key Points

1. **File uploads**: Use `files=@filename` (plural)
2. **Program execution**: Use `program_id`, not filename
3. **Tunnels**: Automatic Cloudflare tunnel on startup
4. **Content-Type**: Use `application/json` for program execution
5. **Program args**: Pass as JSON: `{"args": ["arg1", "arg2"]}`

## 🚨 Troubleshooting

### "No files provided"
✅ Use `files=@filename` not `file=@filename`

### "Program not found"
✅ Use `program_id` (e.g., `program_1762091505`) not filename

### "Unsupported Media Type"
✅ Add header: `-H "Content-Type: application/json"`

### Tunnel not working
✅ Check status: `curl http://localhost:8000/api/mobile/tunnel/status`

## 📊 Server Info

- **Port**: 8000
- **Local**: http://localhost:8000
- **Network**: http://192.168.1.98:8000
- **Public**: Check tunnel status endpoint
- **Storage Limit**: 5GB
- **Supported Languages**: Python, Shell, JavaScript, Perl, Ruby, and more

---

**Everything works!** Just follow the correct API patterns above. 🎉
