#!/bin/bash

# Complete Repository-Based Deployment Script
# This script deploys your Bio Guard Bot directly from your GitHub repository

set -e

echo "🚀 Deploying Bio Guard Bot from GitHub Repository"
echo "=================================================="
echo "Repository: https://github.com/nishkarshk212/BIO-LINK-.git"
echo "Target Server: Ubuntu 22.04 LTS"
echo "=================================================="

# Server configuration
REPO_URL="https://github.com/nishkarshk212/BIO-LINK-.git"
PROJECT_DIR="/opt/bio_guard_bot"
SERVICE_NAME="bio-guard-bot"

# Update system and install dependencies
echo "📦 Installing system dependencies..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git sqlite3

# Create project directory
echo "📁 Setting up project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone repository
echo "📥 Cloning repository..."
git clone $REPO_URL .
# If directory already exists, pull latest changes
if [ -d ".git" ]; then
    git pull origin main
fi

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Set proper permissions
echo "🔒 Setting file permissions..."
chmod 600 .env
chmod 755 bio_guard_bot.py

# Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Bio Guard Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python bio_guard_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Starting bot service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service
systemctl start $SERVICE_NAME.service

echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo "Bot deployed from repository and is now running!"
echo ""
echo "🔧 Useful Commands:"
echo "  Check status: systemctl status $SERVICE_NAME"
echo "  View logs: journalctl -u $SERVICE_NAME -f"
echo "  Restart bot: systemctl restart $SERVICE_NAME"
echo "  Stop bot: systemctl stop $SERVICE_NAME"
echo ""
echo "📝 Repository Information:"
echo "  Local path: $PROJECT_DIR"
echo "  Repository: $REPO_URL"
echo "  Service name: $SERVICE_NAME"
echo ""
echo "🔄 To update from repository:"
echo "  cd $PROJECT_DIR && git pull origin main"
echo "  systemctl restart $SERVICE_NAME"
echo ""
echo "⚠️  Important Notes:"
echo "  - Bot will automatically restart if it crashes"
echo "  - Logs are available via journalctl"
echo "  - Environment variables are in .env file"
echo "  - Database will be created automatically"