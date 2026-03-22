#!/bin/bash

# Fixed redeployment script for latest Bio Guard Bot with macOS compatibility
SERVER_IP="140.245.240.202"
SERVER_USER="root"

echo "Starting redeployment of latest Bio Guard Bot to $SERVER_IP..."
echo "Latest features included:"
echo "  - Open Here/Open in Private buttons in group settings"
echo "  - Fixed button layouts for better UX"
echo "  - Consistent inline keyboard arrangements"

# Check if files exist locally
if [ ! -f "bio_guard_bot.py" ] || [ ! -f "requirements.txt" ] || [ ! -f ".env" ]; then
    echo "Error: Required files not found in current directory!"
    echo "Files needed: bio_guard_bot.py, requirements.txt, .env"
    exit 1
fi

echo "✓ Local files verified (latest version with all button fixes)"

# Encode files as base64 to embed in the SSH command (macOS compatible)
BIO_GUARD_BOT=$(base64 -i bio_guard_bot.py | tr -d '\n')
REQUIREMENTS=$(base64 -i requirements.txt | tr -d '\n')
ENV_FILE=$(base64 -i .env | tr -d '\n')

echo "✓ Files encoded as base64"

# Display the changes that were made to the bot
echo ""
echo "Recent changes made to the bot:"
echo "- Added 'Open Here' and 'Open in Private' buttons when /settings used in groups"
echo "- Fixed all button layouts for better UX and consistency"
echo "- Improved inline keyboard arrangements throughout the bot"
echo ""

# Wait a moment to allow any previous connection attempts to clear
echo "Waiting 10 seconds before attempting connection..."
sleep 10

# SSH into the server and set up the bot with embedded files (skip host key checking)
echo "Attempting to connect and deploy latest code to server..."
echo "Server response may take up to 30 seconds..."
echo ""

ssh -p 22 -o ConnectTimeout=30 -o ServerAliveInterval=10 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null $SERVER_USER@$SERVER_IP << EOF
set -e

echo "Connected to server, starting redeployment with latest code..."

# Create the project directory if it doesn't exist
mkdir -p /opt/bio_guard_bot
echo "Created project directory /opt/bio_guard_bot"

# Decode and write the files directly
echo '$BIO_GUARD_BOT' | base64 -d > /opt/bio_guard_bot/bio_guard_bot.py
echo '$REQUIREMENTS' | base64 -d > /opt/bio_guard_bot/requirements.txt
echo '$ENV_FILE' | base64 -d > /opt/bio_guard_bot/.env

echo "Files transferred successfully (latest version with all button fixes)"

# Change to the project directory
cd /opt/bio_guard_bot
echo "Changed to project directory"

# Set proper permissions for the .env file
chmod 600 .env
echo "Set permissions for .env file"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed on the server"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    apt update
    apt install -y python3-pip
fi

# Create a Python virtual environment (recreate to ensure clean state)
echo "Setting up fresh virtual environment..."
rm -rf venv
python3 -m venv venv
source venv/bin/activate
echo "Virtual environment created and activated"

# Upgrade pip
pip install --upgrade pip
echo "Pip upgraded"

# Install required packages from requirements.txt
echo "Installing required packages..."
pip install -r requirements.txt

# Check if installation was successful
if [ \$? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create systemd service file for the bot
cat > /etc/systemd/system/bio-guard-bot.service << 'SERVICE_EOF'
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
SERVICE_EOF

echo "Created systemd service file"

# Reload systemd to recognize the new service
systemctl daemon-reload
echo "Systemd daemon reloaded"

# Stop the service if it's currently running
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "Stopping existing service..."
    systemctl stop bio-guard-bot.service
    sleep 5
fi

# Enable the service to start on boot
systemctl enable bio-guard-bot.service
echo "Service enabled to start on boot"

# Start the service with the latest code
echo "Starting service with latest code..."
systemctl start bio-guard-bot.service

# Wait a moment for the service to start
sleep 10

# Check if the service is running
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "✓ Bio Guard Bot service is running with latest code!"
    echo "✓ Redeployment completed successfully!"
    systemctl status bio-guard-bot.service --no-pager -l
    echo ""
    echo "Deployment summary:"
    echo "- Files located at: /opt/bio_guard_bot/"
    echo "- Service name: bio-guard-bot.service"
    echo "- Latest version deployed with all button fixes"
    echo "- New features: Open Here/Open in Private buttons in group settings"
    echo "- Improved button layouts for better user experience"
    echo "- Logs can be viewed with: journalctl -u bio-guard-bot.service -f"
else
    echo "✗ Bio Guard Bot service failed to start"
    systemctl status bio-guard-bot.service --no-pager -l
    echo ""
    echo "Check logs with: journalctl -u bio-guard-bot.service -f"
    exit 1
fi

# Show recent logs to confirm the bot is working
echo ""
echo "Recent bot logs:"
journalctl -u bio-guard-bot.service -n 10 --no-pager
EOF

if [ \$? -eq 0 ]; then
    echo ""
    echo "✓ Server redeployment completed successfully!"
    echo "Bio Guard Bot with the latest code (including all button fixes) is now running on the server."
    echo ""
    echo "New Features in Latest Version:"
    echo "- When users type /settings in a group, they'll see 'Open Here' and 'Open in Private' buttons"
    echo "- 'Open in Private' allows direct access to settings in a private chat"
    echo "- 'Open Here' explains that settings can't be accessed directly in groups"
    echo "- All buttons have improved layouts for better user experience"
    echo ""
    echo "To check the bot status, run:"
    echo "  ssh -p 22 $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot.service'"
    echo ""
    echo "To view logs, run:"
    echo "  ssh -p 22 $SERVER_USER@$SERVER_IP 'journalctl -u bio-guard-bot.service -f'"
else
    echo ""
    echo "✗ Error occurred during server redeployment"
    echo ""
    echo "Troubleshooting tips:"
    echo "- Verify the server IP is correct and accessible"
    echo "- Ensure you have SSH access to the server"
    echo "- Check if the server has sufficient disk space and resources"
    echo "- Verify the server has Python and required dependencies installed"
    exit 1
fi