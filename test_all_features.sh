#!/bin/bash
# Comprehensive test suite for webserver features

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Webserver Feature Test Suite"
echo "=========================================="
echo ""

# Function to test and report
test_feature() {
    local name="$1"
    local command="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    result=$(eval "$command" 2>&1)
    
    if echo "$result" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        return 1
    fi
}

# Health Check
test_feature "Health Check" \
    "curl -s $BASE_URL/health | jq -r '.success'" \
    "true"

# File Storage Tests
echo ""
echo "--- File Storage Tests ---"

# Create test file
echo "Test content $(date)" > /tmp/test_file.txt

test_feature "File Upload" \
    "curl -s -F 'files=@/tmp/test_file.txt' $BASE_URL/api/files/upload | jq -r '.success'" \
    "true"

test_feature "File List" \
    "curl -s $BASE_URL/api/files/list | jq -r '.success'" \
    "true"

test_feature "Storage Info" \
    "curl -s $BASE_URL/api/files/storage | jq -r '.success'" \
    "true"

# Program Execution Tests
echo ""
echo "--- Program Execution Tests ---"

# Create test program
cat > /tmp/test_prog.py << 'EOF'
#!/usr/bin/env python3
print("Program test successful")
EOF

test_feature "Program Upload" \
    "curl -s -F 'file=@/tmp/test_prog.py' $BASE_URL/api/programs/upload | jq -r '.success'" \
    "true"

# Get the program_id from last upload
PROGRAM_ID=$(curl -s "$BASE_URL/api/programs/list?limit=1" | jq -r '.data.programs[0].program_id // .programs[0].program_id // empty')

if [ -n "$PROGRAM_ID" ]; then
    test_feature "Program Execution" \
        "curl -s -X POST -H 'Content-Type: application/json' -d '{}' $BASE_URL/api/programs/execute/$PROGRAM_ID | jq -r '.success'" \
        "true"
else
    echo -e "${YELLOW}⚠ SKIP${NC} Program Execution (no program_id found)"
fi

test_feature "Program List" \
    "curl -s $BASE_URL/api/programs/list | jq -r '.success // .data.programs != null'" \
    "true"

# Tunnel Tests
echo ""
echo "--- Tunnel Tests ---"

test_feature "Mobile Tunnel Status" \
    "curl -s $BASE_URL/api/mobile/tunnel/status | jq -r '.success'" \
    "true"

test_feature "All Tunnels Status" \
    "curl -s $BASE_URL/api/tunnels/status | jq -r '.success'" \
    "true"

# Get tunnel URL
TUNNEL_URL=$(curl -s $BASE_URL/api/mobile/tunnel/status | jq -r '.data.url // empty')
if [ -n "$TUNNEL_URL" ]; then
    echo -e "${GREEN}✓${NC} Active Tunnel: $TUNNEL_URL"
else
    echo -e "${YELLOW}⚠${NC} No active tunnel URL"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Suite Complete"
echo "=========================================="
echo ""
echo "To access your server:"
echo "  Local:   http://localhost:8000"
echo "  Network: http://$(hostname -I | awk '{print $1}'):8000"
if [ -n "$TUNNEL_URL" ]; then
    echo "  Public:  $TUNNEL_URL"
fi
echo ""
echo "Web UI: Open http://localhost:8000 in your browser"
