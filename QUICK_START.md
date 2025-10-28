# 🌐 Multi-Tunnel Web Server - Quick Setup Guide

A complete Flask web server with **multiple tunnel options** for public access, file storage, and command execution.

## 🚀 Quick Start (2 minutes)

### 1. **One-Command Setup**
```bash
# Linux/macOS
./setup.sh

# Windows
setup.bat
```

### 2. **Start Server**
```bash
# Linux/macOS
./start_server.sh

# Windows
start_server.bat
```

### 3. **Open Web Interface**
```
http://localhost:8000
```

## 🌐 Tunnel Options (No More Warning Pages!)

### ⚡ **Localtunnel (Recommended)**
- ✅ **No warning pages** - direct access
- ✅ **Free forever**
- ✅ **Instant setup**
- ❌ May require account verification (recent changes)

### ☁️ **Cloudflared (Most Reliable)**
- ✅ **Enterprise-grade reliability**
- ✅ **No warning pages**
- ✅ **Fast and stable**
- ✅ **Free forever**

### 🔧 **Ngrok (Traditional)**
- ✅ **Most popular**
- ✅ **Good documentation**
- ❌ **Warning page on free tier**
- ⚠️ **Better with paid account**

## 🛠️ Troubleshooting

### **Tunnels Not Working?**
```bash
./fix_tunnels.sh
```

### **Common Issues & Solutions**

#### 🔴 **"localtunnel needs a code"**
**Solution**: Recent localtunnel versions require account verification
```bash
# Try cloudflared instead (more reliable)
# Or sign up at localtunnel.github.io
```

#### 🔴 **"ngrok authentication required"**
**Solution**: Get free authtoken from ngrok.com
```bash
# 1. Sign up at https://ngrok.com
# 2. Get token from https://dashboard.ngrok.com/get-started/your-authtoken
# 3. Run: ngrok config add-authtoken YOUR_TOKEN
```

#### 🔴 **"cloudflared not found"**
**Solution**: Run the fix script or install manually
```bash
./fix_tunnels.sh
# Or download from: https://github.com/cloudflare/cloudflared/releases
```

#### 🔴 **"Virtual environment not found"**
**Solution**: Run setup script first
```bash
./setup.sh
```

### **Manual Installation**

#### **Localtunnel**
```bash
# Requires Node.js
npm install -g localtunnel
```

#### **Cloudflared**
```bash
# Linux
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# macOS
brew install cloudflared
```

#### **Ngrok**
```bash
# Download from: https://ngrok.com/download
# Extract and add to PATH
```

## 📁 Features

### **🌐 Public Access**
- **Multiple tunnel services** - choose what works best
- **Real-time status monitoring**
- **One-click start/stop**
- **No configuration needed**

### **💻 Command Execution**
- **Interactive commands** with y/n prompts
- **Secure sudo support** (passwords never stored)
- **Complete output preservation**
- **60-second timeout protection**

### **📁 File Management**
- **5GB storage limit**
- **Drag & drop uploads**
- **Download any file**
- **File explorer interface**

### **🔧 Program Management**
- **Upload and execute scripts**
- **Multiple language support**
- **Execution tracking**
- **Secure isolation**

## 🔒 Security Features

- **Passwords never stored** - prompted when needed
- **Command isolation** - each command runs separately
- **Timeout protection** - prevents hanging processes
- **Network security** - accessible only when tunnels active
- **Clean output** - ANSI codes removed for web display

## 🎯 Recommendations

### **Best Tunnel Choice:**
1. **Start with Cloudflared** - most reliable, no warnings
2. **Try Localtunnel** - if account verification isn't an issue
3. **Use Ngrok** - if you have an account or don't mind warnings

### **Quick Test:**
1. Start server: `./start_server.sh`
2. Open interface: `http://localhost:8000`
3. Click "Start Cloudflared" (usually works best)
4. Copy the generated URL and share!

## 📞 Need Help?

### **Quick Fixes:**
```bash
./fix_tunnels.sh        # Fix tunnel issues
./setup.sh              # Reinstall everything
./start_server.sh       # Start server
./stop_server.sh        # Stop server
```

### **Check Status:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/tunnels/status
```

### **Reset Everything:**
```bash
rm -rf .venv
./setup.sh
```

## 🎉 Success Indicators

✅ **Server running**: You can access `http://localhost:8000`  
✅ **Tunnels working**: Public URLs appear in the interface  
✅ **Commands working**: Interactive prompts respond  
✅ **Files uploading**: Drag & drop works  

---

**🚀 Ready? Run `./setup.sh` and start building!**