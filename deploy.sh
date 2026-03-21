#!/bin/bash

# Bio Guard Bot Deployment Script
# This script deploys the bot to your Ubuntu server

set -e  # Exit on any error

# Server configuration
SERVER_IP="140.245.240.202"
SERVER_USER="root"
SERVER_PORT="22"

# Local project directory
PROJECT_DIR="/Users/nishkarshkr/Desktop/bio link"
REMOTE_DIR="/opt/bio_guard_bot"

echo "🚀 Starting Bio Guard Bot Deployment..."
echo "Server: $SERVER_IP"
echo "User: $SERVER_USER"
echo "Port: $SERVER_PORT"
echo "Project Directory: $PROJECT_DIR"
echo "Remote Directory: $REMOTE_DIR"
echo "=========================================="

# Step 1: Create remote directory structure
echo "📁 Creating remote directory structure..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_DIR"

# Step 2: Transfer files to server
echo "📤 Transferring project files..."
scp -P $SERVER_PORT "$PROJECT_DIR/bio_guard_bot.py" $SERVER_USER@$SERVER_IP:$REMOTE_DIR/
scp -P $SERVER_PORT "$PROJECT_DIR/server_bot.py" $SERVER_USER@$SERVER_IP:$REMOTE_DIR/
scp -P $SERVER_PORT "$PROJECT_DIR/requirements.txt" $SERVER_USER@$SERVER_IP:$REMOTE_DIR/
scp -P $SERVER_PORT "$PROJECT_DIR/.env" $SERVER_USER@$SERVER_IP:$REMOTE_DIR/

# Step 3: Install system dependencies
echo "📦 Installing system dependencies..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'EOF'
# Update package list
apt update

# Install Python 3 and pip
apt install -y python3 python3-pip python3-venv

# Install system utilities
apt install -y git sqlite3

# Install systemd and other utilities
apt install -y systemd

echo "✅ System dependencies installed"
EOF

# Step 4: Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << EOF
cd $REMOTE_DIR

# Create virtual environment
python3 -m venv venv

# Activate virtual environment and install Python packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Python virtual environment set up"
EOF

# Step 5: Create systemd service file
echo "⚙️ Creating systemd service..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << EOF
cat > /etc/systemd/system/bio-guard-bot.service << 'SERVICEEOF'
[Unit]
Description=Bio Guard Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REMOTE_DIR
Environment=PATH=$REMOTE_DIR/venv/bin
ExecStart=$REMOTE_DIR/venv/bin/python bio_guard_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "✅ Systemd service created"
EOF

# Step 6: Set proper permissions
echo "🔒 Setting file permissions..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << EOF
chmod 600 $REMOTE_DIR/.env
chmod 755 $REMOTE_DIR/bio_guard_bot.py
chown -R root:root $REMOTE_DIR
EOF

# Step 7: Enable and start the service
echo "🚀 Starting the bot service..."
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'EOF'
# Reload systemd daemon
systemctl daemon-reload

# Enable service to start on boot
systemctl enable bio-guard-bot.service

# Start the service
systemctl start bio-guard-bot.service

# Check service status
systemctl status bio-guard-bot.service --no-pager

echo "✅ Bot service started"
EOF

# Step 8: Display deployment summary
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo "Bot is now running on your server"
echo "Service name: bio-guard-bot"
echo "Remote directory: $REMOTE_DIR"
echo ""
echo "🔧 Useful commands:"
echo "  Check bot status: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot'"
echo "  View bot logs: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'journalctl -u bio-guard-bot -f'"
echo "  Restart bot: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'systemctl restart bio-guard-bot'"
echo "  Stop bot: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP 'systemctl stop bio-guard-bot'"
echo ""
echo "📝 Notes:"
echo "- The bot will automatically restart if it crashes"
echo "- Logs are available via journalctl"
echo "- Environment variables are securely stored in .env file"
echo "- Database file will be created automatically in $REMOTE_DIR"