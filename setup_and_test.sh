#!/bin/bash
# Setup virtual environment and install dependencies
# For Ubuntu/Debian with externally managed Python

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     SETUP WITH VIRTUAL ENVIRONMENT (Ubuntu/Debian)          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver

# Check if virtual environment already exists
if [ -d ".venv" ]; then
    echo "✓ Virtual environment .venv already exists"
    echo ""
elif [ -d ".venv_new" ]; then
    echo "✓ Virtual environment .venv_new already exists"
    echo "  Renaming to .venv..."
    mv .venv_new .venv
    echo ""
else
    echo "Creating new virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created at .venv"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing dependencies from requirements.txt..."
echo "This will take 2-3 minutes..."
echo ""

# Install dependencies with error handling
if pip install -r requirements.txt; then
    echo ""
    echo "✓ All dependencies installed successfully"
else
    echo ""
    echo "⚠ Some dependencies had issues, retrying without cache..."
    pip install --no-cache-dir -r requirements.txt
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              INSTALLATION COMPLETE!                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Virtual environment is activated and ready to use!"
echo ""
echo "Now running tests..."
echo ""

python3 comprehensive_test.py

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    NEXT STEPS                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "To use the virtual environment in the future:"
echo "  cd /home/admin1/Documents/webserver"
echo "  source .venv/bin/activate"
echo ""
echo "To run the webserver:"
echo "  python src/app.py"
echo ""
echo "To deactivate virtual environment:"
echo "  deactivate"
echo ""

