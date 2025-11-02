#!/bin/bash
# Test all bot IDs from 1-10 to find their specialties

API_URL="https://gpt.ecigdis.co.nz/ai-agent/api/chat.php"

echo "Testing Bot IDs to find capabilities..."
echo "=========================================="
echo ""

for bot_id in {1..10}; do
    echo "Bot ID: $bot_id"
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"Who are you and what can you do?\", \"bot_id\": $bot_id}")
    
    # Extract message from JSON
    message=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('message', 'ERROR')[:200])" 2>/dev/null)
    
    echo "Response: $message"
    echo "---"
    echo ""
done
