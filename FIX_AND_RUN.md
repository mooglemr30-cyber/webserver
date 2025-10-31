# 🚀 RUN THESE COMMANDS (COPY & PASTE)

## ⚡ The Problem
The script isn't executable yet. Here's how to fix it:

---

## ✅ SOLUTION - Copy and Run These Commands:

### Option 1: Make Script Executable (RECOMMENDED)
```bash
cd /home/admin1/Documents/webserver
chmod +x build_expo_app.sh
./build_expo_app.sh
```

### Option 2: Run with Bash Directly
```bash
cd /home/admin1/Documents/webserver
bash build_expo_app.sh
```

### Option 3: Use the Quick Fix Script
```bash
cd /home/admin1/Documents/webserver
bash run_build.sh
```

---

## 📝 What Each Command Does

### `chmod +x build_expo_app.sh`
Makes the script executable (adds execute permission)

### `./build_expo_app.sh`
Runs the script

### `bash build_expo_app.sh`
Runs the script using bash directly (no chmod needed)

---

## ⚠️ IMPORTANT: Don't Use Sudo!

**DON'T RUN:**
```bash
sudo ./build_expo_app.sh  # ❌ WRONG!
```

**DO RUN:**
```bash
./build_expo_app.sh       # ✅ CORRECT!
```

You don't need sudo because:
- Expo installs in user space
- npm installs globally with user permissions
- No system files are modified

---

## 🎯 JUST COPY THIS:

```bash
cd /home/admin1/Documents/webserver && chmod +x build_expo_app.sh && ./build_expo_app.sh
```

**That's ONE command that does everything!**

---

## 🔧 If You Still Get "Command Not Found"

Try running with bash directly:

```bash
cd /home/admin1/Documents/webserver
bash build_expo_app.sh
```

This bypasses the need for execute permissions.

---

## ✅ When It Works, You'll See:

```
╔══════════════════════════════════════════╗
║   WEBSERVER MOBILE APP - EXPO APK BUILDER║
╚══════════════════════════════════════════╝

━━━━ Step 1: Check Node.js and npm ━━━━
✓ Node.js v18.x.x
✓ npm 9.x.x

━━━━ Step 2: Create Assets Directory ━━━━
...
```

---

## 🚀 READY? COPY AND RUN THIS:

```bash
cd /home/admin1/Documents/webserver && chmod +x build_expo_app.sh && bash build_expo_app.sh
```

Press Enter and let it run!

When prompted, **choose option 1** (EAS Build)!

