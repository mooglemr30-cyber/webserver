#!/bin/bash
# Install all dependencies for webserver and mobile app

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           INSTALLING DEPENDENCIES                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver

# Check for virtual environment
if [ -d ".venv" ]; then
    echo "✓ Found virtual environment at .venv"
    echo "  Activating virtual environment..."
    source .venv/bin/activate
    echo ""
    echo "Installing dependencies in virtual environment..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo ""
    echo "✓ Dependencies installed in virtual environment"
    echo ""
    echo "To use the virtual environment, run:"
    echo "  source .venv/bin/activate"
    echo ""
elif [ -d ".venv_new" ]; then
    echo "✓ Found virtual environment at .venv_new"
    echo "  Activating virtual environment..."
    source .venv_new/bin/activate
    echo ""
    echo "Installing dependencies in virtual environment..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo ""
    echo "✓ Dependencies installed in virtual environment"
    echo ""
    echo "To use the virtual environment, run:"
    echo "  source .venv_new/bin/activate"
    echo ""
else
    echo "⚠ No virtual environment found"
    echo "  Installing dependencies with pip3 --user..."
    echo ""
    pip3 install --user --upgrade pip
    pip3 install --user -r requirements.txt
    echo ""
    echo "✓ Dependencies installed for current user"
    echo ""
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           INSTALLATION COMPLETE                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Now you can run the tests:"
echo "  python3 comprehensive_test.py"
echo ""

