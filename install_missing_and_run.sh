#!/bin/bash
# Quick fix - install missing packages and start server

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           INSTALLING MISSING PACKAGES                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver

# Fix permissions on venv
echo "Fixing venv permissions..."
chmod +x .venv/bin/* 2>/dev/null || true

# Install missing packages
echo "Installing missing packages (PyJWT and bcrypt for authentication)..."
.venv/bin/pip install PyJWT==2.8.0 bcrypt==4.0.1

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              PACKAGES INSTALLED - STARTING SERVER            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Note: Redis connection error is normal if Redis is not installed."
echo "      Server will use memory cache instead (works fine)."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STARTING WEBSERVER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server
.venv/bin/python src/app.py

echo ""
echo "Server stopped."

