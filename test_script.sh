#!/bin/bash
# Test shell script for the program management system

echo "🐚 Hello from Shell Script Program Management!"
echo "⏰ Current time: $(date)"
echo "👤 Current user: $(whoami)"
echo "🖥️  System info: $(uname -a)"
echo "📁 Current directory: $(pwd)"

# Check if arguments were provided
if [ $# -gt 0 ]; then
    echo "📝 Arguments received: $@"
    for i in $(seq 1 $#); do
        echo "   Argument $i: ${!i}"
    done
else
    echo "📝 No arguments provided"
fi

# Simple system check
echo "💾 Disk usage:"
df -h | head -2

echo "🔍 Process count: $(ps aux | wc -l)"
echo "⚡ Load average: $(uptime | awk -F'load average:' '{print $2}')"

echo "✅ Shell script execution completed successfully!"