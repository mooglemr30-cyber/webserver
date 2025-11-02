# Git Commit Instructions

## Project: Localhost Web Server with Mobile App

### Current Status (October 31, 2025)

**Backend**: ✅ Complete and working  
**Web Interface**: ✅ Complete with mobile controls  
**Mobile App**: ⚠️ In progress - build configuration complete

---

## Commit Message Guidelines

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `build`: Build system changes

### Recent Major Changes (October 2025)

#### Mobile Integration
- Added mobile app controls to web interface (top of page)
- Implemented tunnel control API endpoints
- Created React Native/Expo mobile app
- Configured EAS Build system
- Added APK download functionality

#### Build System Fixes
- Fixed React version compatibility (18.2.0 for RN 0.72.6)
- Added .easignore to reduce upload size
- Configured babel for Expo managed workflow
- Updated eas.json with proper settings
- Removed expo-updates requirement

#### Web Interface Enhancements
- Mobile App Controls section (blue gradient, top of page)
- Tunnel start/stop/status buttons
- APK download button with instructions
- Status indicators (🔴/🟢)
- JavaScript functions for tunnel management

---

## Example Commits

### Feature
```
feat(mobile): add tunnel control to web interface

- Added Mobile App Controls section to top of page
- Implemented tunnel start/stop/status buttons
- Added APK download functionality
- Created JavaScript handlers for tunnel API calls

Closes #123
```

### Fix
```
fix(mobile): resolve React version conflict in build

- Downgraded React from 18.3.1 to 18.2.0
- React Native 0.72.6 requires React 18.2.0
- Removed expo-updates dependency
- Updated eas.json to remove channel requirement

Fixes #124
```

### Documentation
```
docs: update copilot instructions with mobile app details

- Added complete mobile app documentation
- Documented all API endpoints
- Updated build system information
- Added troubleshooting guide
```

### Build
```
build(mobile): optimize EAS build configuration

- Added .easignore to reduce upload from 863 MB to 50 MB
- Configured babel-preset-expo
- Updated build scripts with --legacy-peer-deps
- Removed expo-updates channel requirement
```

---

## Pre-Commit Checklist

### Backend Changes
- [ ] Virtual environment activated
- [ ] All dependencies in requirements.txt
- [ ] API endpoints documented
- [ ] Error handling implemented
- [ ] Server starts without errors

### Frontend/Web Changes
- [ ] HTML/CSS validates
- [ ] JavaScript has no console errors
- [ ] Mobile controls remain visible
- [ ] Status indicators work
- [ ] Responsive on different screen sizes

### Mobile App Changes
- [ ] package.json dependencies valid
- [ ] React version matches React Native (18.2.0 for RN 0.72.6)
- [ ] .easignore present
- [ ] babel.config.js configured
- [ ] eas.json valid
- [ ] Build tested (or documented as untested)

### Documentation
- [ ] Copilot instructions updated if needed
- [ ] README updated for major changes
- [ ] Code comments clear
- [ ] API changes documented

---

## Current Branch Structure

### Main Branches
- `main` - Stable, production-ready code
- `develop` - Development integration branch

### Feature Branches
- `feature/mobile-app` - Mobile app development
- `feature/tunnel-control` - Tunnel management
- `feature/web-controls` - Web interface enhancements

---

## Important Files to Check

### When Committing Backend Changes
- `src/app.py` - Main Flask application
- `src/auth_system.py` - Authentication
- `src/tunnel_manager.py` - Tunnel management
- `requirements.txt` - Python dependencies

### When Committing Web Changes
- `src/templates/index.html` - Main page (has mobile controls)
- `src/static/main.js` - JavaScript (tunnel functions)
- `src/static/style.css` - Styles

### When Committing Mobile Changes
- `mobile-app/package.json` - Dependencies (React 18.2.0!)
- `mobile-app/app.json` - Expo config
- `mobile-app/eas.json` - Build config (no channels!)
- `mobile-app/.easignore` - Upload optimization
- `mobile-app/babel.config.js` - Babel config
- `mobile-app/src/App.js` - Main app component

### When Committing Build Scripts
- `build_no_updates.sh` - Current working build script
- `final_build.sh` - Alternative build script
- Build script tests and validation

---

## Common Issues to Avoid

### Mobile App
❌ Don't use React 18.3.1 - use 18.2.0  
❌ Don't include channels in eas.json without expo-updates  
❌ Don't forget .easignore - upload will be huge  
❌ Don't commit node_modules  

### Backend
❌ Don't commit .venv directory  
❌ Don't commit .env files with secrets  
❌ Don't commit database files in data/  
❌ Don't expose sensitive endpoints without auth  

### Web Interface
❌ Don't remove mobile controls from top of page  
❌ Don't break tunnel status indicators  
❌ Don't forget to test APK download button  

---

## Useful Commands

### Git Workflow
```bash
# Check status
git status

# Stage files
git add <file>

# Commit
git commit -m "type(scope): message"

# Push
git push origin <branch>
```

### Before Committing
```bash
# Test server
cd /home/admin1/Documents/webserver
source .venv/bin/activate
python src/app.py

# Check mobile build config
cd mobile-app
cat package.json | grep '"react"'  # Should be 18.2.0
cat eas.json | grep 'channel'      # Should NOT exist

# Verify files
ls -la .easignore babel.config.js
```

---

## Post-Commit Actions

### After Pushing Backend Changes
- Test server starts
- Verify API endpoints work
- Check logs for errors

### After Pushing Web Changes
- Clear browser cache
- Test on different browsers
- Verify mobile controls visible

### After Pushing Mobile Changes
- Run build script to verify
- Check EAS build logs
- Update documentation if needed

---

## Notes

- **Mobile app is in progress** - build scripts ready but not yet successfully built
- **React version critical** - Must be 18.2.0 for React Native 0.72.6
- **No expo-updates** - We removed channel requirements to simplify builds
- **Test incrementally** - Don't commit large untested changes

---

## Quick Reference

**Current React Version**: 18.2.0  
**Current React Native Version**: 0.72.6  
**Current Expo SDK**: ~49.0.0  
**Build Script**: build_no_updates.sh  
**EAS Project**: meowmeowthecat/webserver-mobile  
**Last Updated**: October 31, 2025

