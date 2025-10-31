#!/bin/bash
# Quick install dependencies and run comprehensive tests

set -e

echo "============================================"
echo "Installing Dependencies and Running Tests"
echo "============================================"
echo ""

cd /home/admin1/Documents/webserver

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✓ Using existing virtual environment"
    source .venv/bin/activate
else
    echo "⚠ No virtual environment found"
    echo "Installing dependencies with pip3 --user..."
    pip3 install --user -r requirements.txt
fi

echo ""
echo "============================================"
echo "Running Comprehensive Tests"
echo "============================================"
echo ""

python3 comprehensive_test.py

echo ""
echo "Test complete!"

