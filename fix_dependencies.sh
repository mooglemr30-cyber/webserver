#!/bin/bash
# Fix missing dependencies in existing virtual environment

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         INSTALLING MISSING DEPENDENCIES                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

cd /home/admin1/Documents/webserver

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
    echo ""
else
    echo "✗ Virtual environment not found!"
    echo "Run: python3 -m venv .venv"
    exit 1
fi

# Install all dependencies
echo "Installing ALL dependencies from requirements.txt..."
echo "This includes: flask-cors, pydantic, and 16 other packages..."
echo ""

.venv/bin/python -m pip install -r requirements.txt

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         INSTALLATION COMPLETE - RUNNING TESTS                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Run tests
.venv/bin/python comprehensive_test.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              ✅ ALL TESTS PASSED!                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "✅ CONFIRMATION:"
    echo "   • Original webserver: READY ✓"
    echo "   • Mobile app integration: CONFIGURED ✓"
    echo "   • All dependencies: INSTALLED ✓"
    echo "   • Both services: CAN RUN TOGETHER ✓"
    echo ""
    echo "🚀 To start your webserver:"
    echo "   source .venv/bin/activate"
    echo "   python src/app.py"
    echo ""
else
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              ⚠️ SOME TESTS FAILED                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "See test output above for details."
    echo ""
fi

exit $EXIT_CODE

