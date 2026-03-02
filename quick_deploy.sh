#!/bin/bash

# One-command deployment for Bio Guard Bot

echo "🚀 Deploying Bio Guard Bot to Server..."
echo "Server: 140.245.240.202"
echo "User: root"
echo "======================================"

# Step 1: Transfer files using scp with proper quoting
echo "📤 Transferring files..."
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/bio_guard_bot.py" root@140.245.240.202:/tmp/
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/requirements.txt" root@140.245.240.202:/tmp/
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/.env" root@140.245.240.202:/tmp/

# Step 2: Execute deployment commands on server
echo "🔧 Setting up server environment..."
ssh -p 22 root@140.245.240.202 << 'ENDSSH'
echo "Creating directory structure..."
mkdir -p /opt/bio_guard_bot

echo "Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv sqlite3

echo "Setting up Python environment..."
cd /opt/bio_guard_bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo "Moving files to final location..."
mv /tmp/bio_guard_bot.py /opt/bio_guard_bot/
mv /tmp/requirements.txt /opt/bio_guard_bot/
mv /tmp/.env /opt/bio_guard_bot/

echo "Installing Python dependencies..."
cd /opt/bio_guard_bot
source venv/bin/activate
pip install -r requirements.txt

echo "Setting proper permissions..."
chmod 600 /opt/bio_guard_bot/.env
chmod 755 /opt/bio_guard_bot/bio_guard_bot.py

echo "Creating systemd service..."
cat > /etc/systemd/system/bio-guard-bot.service << 'EOF'
[Unit]
Description=Bio Guard Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bio_guard_bot
Environment=PATH=/opt/bio_guard_bot/venv/bin
ExecStart=/opt/bio_guard_bot/venv/bin/python bio_guard_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Starting the service..."
systemctl daemon-reload
systemctl enable bio-guard-bot.service
systemctl start bio-guard-bot.service

echo "Checking service status..."
systemctl status bio-guard-bot.service --no-pager

echo "✅ Deployment completed successfully!"
echo "Bot is now running and will automatically restart if it crashes."
echo "View logs with: journalctl -u bio-guard-bot -f"
ENDSSH

echo "======================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================"
echo "Your Bio Guard Bot is now running on your server."
echo "Useful commands:"
echo "  Check status: ssh -p 22 root@140.245.240.202 'systemctl status bio-guard-bot'"
echo "  View logs: ssh -p 22 root@140.245.240.202 'journalctl -u bio-guard-bot -f'"
echo "  Restart bot: ssh -p 22 root@140.245.240.202 'systemctl restart bio-guard-bot'"