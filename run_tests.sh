#!/bin/bash
# Comprehensive test runner for webserver
# Tests all services: mobile API, auth, data storage, files, programs

set -e

cd "$(dirname "$0")"

echo "=================================="
echo "🧪 Running Webserver Smoke Tests"
echo "=================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Ensure dependencies are installed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt 2>/dev/null || true

echo ""
echo "🚀 Running Flask test client smoke tests..."
echo "   (This tests all endpoints in-process without starting the server)"
echo ""

# Run the smoke tests
python3 test_smoke.py

TEST_RESULT=$?

echo ""
echo "=================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo ""
    echo "Summary:"
    echo "  - Original webserver: ✅ Working"
    echo "  - Mobile API endpoints: ✅ Working"
    echo "  - Authentication: ✅ Working"
    echo "  - Data storage (CRUD): ✅ Working"
    echo "  - Tunnel endpoints: ✅ Available"
    echo ""
    echo "🎉 Your webserver is ready for mobile app access!"
else
    echo "❌ SOME TESTS FAILED"
    echo ""
    echo "Please review the output above for details."
fi
echo "=================================="

exit $TEST_RESULT

