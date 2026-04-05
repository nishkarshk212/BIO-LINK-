#!/bin/bash
# Quick Deploy Script - Just uploads file and restarts bot

SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PASS="Akshay343402355468"
SERVER_PORT="22"
BOT_PATH="/opt/bio_guard_bot"
LOCAL_FILE="/Users/nishkarshkr/Desktop/bio link/bio_guard_bot.py"

echo "🚀 Quick Deploy: Uploading bio_guard_bot.py to server..."

# Encode and transfer
ENCODED=$(base64 -i "$LOCAL_FILE")

sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd $BOT_PATH
cp bio_guard_bot.py bio_guard_bot.py.backup.quick
echo "$ENCODED" | base64 -d > bio_guard_bot.py
if [ \$? -eq 0 ]; then
    echo "✅ File uploaded successfully"
    systemctl restart bio-guard-bot
    sleep 2
    echo ""
    echo "📊 Bot Status:"
    systemctl is-active bio-guard-bot
else
    echo "❌ Upload failed!"
    exit 1
fi
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📱 Test now in Telegram:"
echo "   /settings → Look for 💣 Self Destruct"
