#!/bin/bash

# Simple deployment script for Bio Guard Bot
SERVER_IP="140.245.240.202"
SERVER_USER="root"

echo "🚀 Starting deployment of Bio Guard Bot..."

# Create the archive
tar -czf bio_guard_bot.tar.gz bio_guard_bot.py requirements.txt .env
echo "✓ Created archive"

# Transfer files
scp bio_guard_bot.tar.gz $SERVER_USER@$SERVER_IP:/tmp/
if [ $? -ne 0 ]; then
    echo "❌ File transfer failed"
    rm -f bio_guard_bot.tar.gz
    exit 1
fi
echo "✓ Files transferred"

# Clean up local archive
rm -f bio_guard_bot.tar.gz

# Deploy on server
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e

echo "📦 Extracting files..."
cd /tmp
mkdir -p /opt/bio_guard_bot
tar -xzf bio_guard_bot.tar.gz -C /opt/bio_guard_bot/
rm bio_guard_bot.tar.gz

cd /opt/bio_guard_bot
chmod 600 .env

echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Configuring service..."
cat > /etc/systemd/system/bio-guard-bot.service << EOF
[Unit]
Description=Bio Guard Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bio_guard_bot
EnvironmentFile=/opt/bio_guard_bot/.env
ExecStart=/opt/bio_guard_bot/venv/bin/python /opt/bio_guard_bot/bio_guard_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Restarting service..."
systemctl daemon-reload
systemctl enable bio-guard-bot.service
systemctl restart bio-guard-bot.service

sleep 3

echo ""
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "✅ Deployment successful! Bot is running."
    systemctl status bio-guard-bot.service --no-pager -l
else
    echo "❌ Service failed to start"
    systemctl status bio-guard-bot.service --no-pager -l
    exit 1
fi
ENDSSH

echo ""
echo "✅ Deployment complete!"
