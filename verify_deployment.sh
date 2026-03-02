#!/bin/bash

# Verification script for Bio Guard Bot deployment

echo "🔍 Verifying Bio Guard Bot Deployment"
echo "====================================="

SERVER="root@140.245.240.202"
PORT="22"

echo "Checking server connectivity..."
if ssh -p $PORT -o ConnectTimeout=10 $SERVER "echo 'Connected'" 2>/dev/null; then
    echo "✅ Server connection: SUCCESS"
else
    echo "❌ Server connection: FAILED"
    echo "Please check your SSH connection and try again"
    exit 1
fi

echo ""
echo "Checking service status..."
ssh -p $PORT $SERVER "systemctl status bio-guard-bot.service --no-pager" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Service status check: SUCCESS"
else
    echo "❌ Service status check: FAILED"
    echo "The service might not be running or installed properly"
fi

echo ""
echo "Checking process status..."
PROCESS_COUNT=$(ssh -p $PORT $SERVER "ps aux | grep bio_guard_bot | grep -v grep | wc -l" 2>/dev/null)
if [ "$PROCESS_COUNT" -gt 0 ]; then
    echo "✅ Bot process running: YES ($PROCESS_COUNT process(es) found)"
else
    echo "❌ Bot process running: NO"
fi

echo ""
echo "Checking log files..."
LOG_LINES=$(ssh -p $PORT $SERVER "journalctl -u bio-guard-bot --since '1 hour ago' | wc -l" 2>/dev/null)
if [ "$LOG_LINES" -gt 0 ]; then
    echo "✅ Recent logs found: YES ($LOG_LINES lines in last hour)"
else
    echo "⚠️ Recent logs found: NO or empty"
fi

echo ""
echo "Checking file permissions..."
ssh -p $PORT $SERVER "ls -la /opt/bio_guard_bot/" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Project files accessible: YES"
else
    echo "❌ Project files accessible: NO"
fi

echo ""
echo "====================================="
echo "Verification Complete"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Check detailed logs: ssh -p $PORT $SERVER 'journalctl -u bio-guard-bot -f'"
echo "2. If service is not running: ssh -p $PORT $SERVER 'sudo systemctl start bio-guard-bot'"
echo "3. Test your bot in Telegram by adding it to a group with admin permissions"