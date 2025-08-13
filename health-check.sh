#!/bin/bash

# Health check script for the Leaf Disease Detection API

echo "🔍 Health Check for Leaf Disease Detection API"
echo "=============================================="

# Check if PM2 is running
echo "📊 PM2 Status:"
pm2 status

echo ""
echo "🌐 Testing API endpoints..."

# Test main server health
echo -n "Main Server Health: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)
if [ "$response" = "200" ]; then
    echo "✅ OK"
else
    echo "❌ Failed (HTTP $response)"
fi

# Test Friend API health
echo -n "Friend API Health: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/friend/health)
if [ "$response" = "200" ]; then
    echo "✅ OK"
else
    echo "❌ Failed (HTTP $response)"
fi

# Test Main API health
echo -n "Main API Health: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/main/health)
if [ "$response" = "200" ]; then
    echo "✅ OK"
else
    echo "❌ Failed (HTTP $response)"
fi

echo ""
echo "💻 System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo ""
echo "📋 Recent Logs (last 10 lines):"
pm2 logs --lines 10 --nostream
