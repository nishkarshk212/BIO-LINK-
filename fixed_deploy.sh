#!/bin/bash

# Fixed deployment script for Bio Guard Bot with proper macOS base64 syntax
SERVER_IP="140.245.240.202"
SERVER_USER="root"

echo "🚀 Starting deployment of Bio Guard Bot to $SERVER_IP..."
echo "Includes latest button fixes and improvements"

# Check if files exist locally
if [ ! -f "bio_guard_bot.py" ] || [ ! -f "requirements.txt" ] || [ ! -f ".env" ]; then
    echo "❌ Error: Required files not found in current directory!"
    echo "Files needed: bio_guard_bot.py, requirements.txt, .env"
    exit 1
fi

echo "✅ Local files verified"

# Encode files as base64 using correct macOS syntax
BIO_GUARD_BOT=$(base64 -i bio_guard_bot.py)
REQUIREMENTS=$(base64 -i requirements.txt)
ENV_FILE=$(base64 -i .env)

echo "✅ Files encoded as base64"

# SSH into the server and deploy
echo "🔧 Deploying to server..."
ssh -p 22 $SERVER_USER@$SERVER_IP << EOF
set -e

echo "Connected to server, starting deployment..."

# Create project directory
mkdir -p /opt/bio_guard_bot
echo "✅ Created project directory"

# Decode and write files
echo '$BIO_GUARD_BOT' | base64 -d > /opt/bio_guard_bot/bio_guard_bot.py
echo '$REQUIREMENTS' | base64 -d > /opt/bio_guard_bot/requirements.txt
echo '$ENV_FILE' | base64 -d > /opt/bio_guard_bot/.env

echo "✅ Files transferred successfully"

# Set permissions
chmod 600 /opt/bio_guard_bot/.env
chmod 755 /opt/bio_guard_bot/bio_guard_bot.py
echo "✅ Permissions set"

# Install dependencies
cd /opt/bio_guard_bot

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    apt update
    apt install -y python3 python3-pip python3-venv
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Create systemd service
cat > /etc/systemd/system/bio-guard-bot.service << 'SERVICE_EOF'
[Unit]
Description=Bio Guard Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bio_guard_bot
Environment=PATH=/opt/bio_guard_bot/venv/bin
ExecStart=/opt/bio_guard_bot/venv/bin/python /opt/bio_guard_bot/bio_guard_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "✅ Service file created"

# Reload and start service
systemctl daemon-reload
systemctl enable bio-guard-bot.service
systemctl stop bio-guard-bot.service 2>/dev/null || true
systemctl start bio-guard-bot.service

# Wait for service to start
sleep 5

# Check if running
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "✅ Bio Guard Bot is now running with latest code!"
    echo ""
    echo "Deployment Summary:"
    echo "  - Files: /opt/bio_guard_bot/"
    echo "  - Service: bio-guard-bot.service"
    echo "  - View logs: journalctl -u bio-guard-bot.service -f"
    echo ""
    echo "Latest Features Deployed:"
    echo "  - Complete button functionality for settings menu"
    echo "  - Warn limit selection (1, 2, 3, 5, 10)"
    echo "  - Penalty options (mute, kick, ban)"
    echo "  - Apply-to settings (members, admins, everyone)"
    echo "  - Back navigation and save/close functionality"
else
    echo "❌ Service failed to start"
    systemctl status bio-guard-bot.service --no-pager
    exit 1
fi
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "======================================"
    echo "Your Bio Guard Bot is now running with all the latest button fixes."
    echo ""
    echo "Useful commands:"
    echo "  Check status: ssh -p 22 $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot'"
    echo "  View logs: ssh -p 22 $SERVER_USER@$SERVER_IP 'journalctl -u bio-guard-bot -f'"
    echo "  Restart bot: ssh -p 22 $SERVER_USER@$SERVER_IP 'systemctl restart bio-guard-bot'"
    echo ""
    echo "Latest improvements deployed:"
    echo " ✅ All settings buttons now fully functional"
    echo "  ✅ Database integration for persistent settings"
    echo " ✅ Improved user navigation and feedback"
    echo " ✅ Consistent button layouts across all menus"
else
    echo ""
    echo "❌ Deployment failed. Please check the error messages above."
    exit 1
fi