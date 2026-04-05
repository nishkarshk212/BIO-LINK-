#!/bin/bash
# Deploy Streamlined Bio Guard Bot to Server

SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PASS="Akshay343402355468"
SERVER_PORT="22"

echo "🚀 Deploying Streamlined Bio Guard Bot..."
echo "=========================================="
echo ""

# Step 1: Upload new bot file
echo "📤 Uploading bio_guard_bot.py..."
sshpass -p "$SERVER_PASS" scp -P $SERVER_PORT -o StrictHostKeyChecking=no \
    bio_guard_bot.py $SERVER_USER@$SERVER_IP:/opt/bio_guard_bot/

if [ $? -eq 0 ]; then
    echo "✅ bio_guard_bot.py uploaded successfully"
else
    echo "❌ Failed to upload bio_guard_bot.py"
    exit 1
fi

# Step 2: Upload font.py module
echo "📤 Uploading font.py..."
sshpass -p "$SERVER_PASS" scp -P $SERVER_PORT -o StrictHostKeyChecking=no \
    font.py $SERVER_USER@$SERVER_IP:/opt/bio_guard_bot/

if [ $? -eq 0 ]; then
    echo "✅ font.py uploaded successfully"
else
    echo "❌ Failed to upload font.py"
    exit 1
fi

# Step 3: Restart bot service
echo ""
echo "🔄 Restarting bot service..."
sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no \
    $SERVER_USER@$SERVER_IP "systemctl restart bio-guard-bot"

if [ $? -eq 0 ]; then
    echo "✅ Bot service restarted"
else
    echo "❌ Failed to restart bot service"
    exit 1
fi

# Step 4: Wait and check status
echo ""
echo "⏳ Waiting for bot to start..."
sleep 3

sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no \
    $SERVER_USER@$SERVER_IP "systemctl is-active bio-guard-bot"

echo ""
echo "📊 Recent logs:"
sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no \
    $SERVER_USER@$SERVER_IP "journalctl -u bio-guard-bot --since '1 minute ago' --no-pager | tail -10"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo ""
echo "🎯 New Features:"
echo "   • Font styling integrated"
echo "   • Only bio detection + edit deletion"
echo "   • Removed logging & tracking features"
echo "   • Cleaner, lighter codebase (629 lines)"
echo ""
echo "📝 Next Steps:"
echo "   1. Test with /start command"
echo "   2. Check settings with /settings"
echo "   3. Monitor logs: journalctl -u bio-guard-bot -f"
echo ""
