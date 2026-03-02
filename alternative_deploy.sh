#!/bin/bash

# Alternative deployment script for Bio Guard Bot using rsync
SERVER_IP="140.245.240.202"
SERVER_USER="root"

echo "Starting alternative deployment of Bio Guard Bot to $SERVER_IP..."

# Check if files exist locally
if [ ! -f "bio_guard_bot.py" ] || [ ! -f "requirements.txt" ] || [ ! -f ".env" ]; then
    echo "Error: Required files not found in current directory!"
    echo "Files needed: bio_guard_bot.py, requirements.txt, .env"
    exit 1
fi

echo "✓ Local files verified"

# Create a tar archive to send to the server
echo "Creating archive..."
tar -czf bio_guard_bot.tar.gz bio_guard_bot.py requirements.txt .env

# Try to establish connection first with a simple command
echo "Testing connection to server..."
if ssh -p 22 $SERVER_USER@$SERVER_IP "echo 'Connection test successful'" 2>/dev/null; then
    echo "✓ Connection to server successful"
else
    echo "✗ Cannot connect to server. Please check:"
    echo "  - Server IP address is correct"
    echo "  - Server is running and accepting SSH connections"
    echo "  - Port 22 is open"
    echo "  - SSH service is running on the server"
    rm -f bio_guard_bot.tar.gz
    exit 1
fi

# Transfer the archive to the server using rsync
echo "Transferring files to server using rsync..."
rsync -avz -e "ssh -p 22" bio_guard_bot.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

if [ $? -ne 0 ]; then
    echo "Error: Failed to transfer files to server using rsync"
    rm -f bio_guard_bot.tar.gz
    exit 1
fi

echo "✓ Files transferred to server"

# Clean up local archive
rm -f bio_guard_bot.tar.gz

# SSH into the server and set up the bot
echo "Setting up bot on server..."
ssh -p 22 $SERVER_USER@$SERVER_IP << 'EOF'
set -e

echo "Connected to server, starting setup..."

# Create the project directory if it doesn't exist
mkdir -p /opt/bio_guard_bot
echo "Created project directory /opt/bio_guard_bot"

# Extract the files
cd /tmp
if [ -f "bio_guard_bot.tar.gz" ]; then
    echo "Extracting files to /opt/bio_guard_bot..."
    tar -xzf bio_guard_bot.tar.gz -C /opt/bio_guard_bot/
    rm -f bio_guard_bot.tar.gz
    echo "Files extracted successfully"
else
    echo "Error: Archive file not found in /tmp"
    exit 1
fi

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

# Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate the virtual environment
source venv/bin/activate
echo "Virtual environment activated"

# Upgrade pip
pip install --upgrade pip
echo "Pip upgraded"

# Install required packages from requirements.txt
echo "Installing required packages..."
pip install -r requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Create systemd service file for the bot
cat > /etc/systemd/system/bio-guard-bot.service << SERVICE_EOF
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

# Enable the service to start on boot
systemctl enable bio-guard-bot.service
echo "Service enabled to start on boot"

# Start the service
systemctl start bio-guard-bot.service
echo "Service started"

# Wait a moment for the service to start
sleep 5

# Check if the service is running
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "✓ Bio Guard Bot service is running"
    echo "✓ Deployment completed successfully!"
    systemctl status bio-guard-bot.service --no-pager -l
    echo ""
    echo "Deployment summary:"
    echo "- Files located at: /opt/bio_guard_bot/"
    echo "- Service name: bio-guard-bot.service"
    echo "- Logs can be viewed with: journalctl -u bio-guard-bot.service -f"
else
    echo "✗ Bio Guard Bot service failed to start"
    systemctl status bio-guard-bot.service --no-pager -l
    echo ""
    echo "Check logs with: journalctl -u bio-guard-bot.service -f"
    exit 1
fi
EOF

if [ $? -eq 0 ]; then
    echo "✓ Server setup completed successfully!"
    echo "Bio Guard Bot is now running on the server."
    echo ""
    echo "To check the bot status, run:"
    echo "  ssh -p 22 $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot.service'"
    echo ""
    echo "To view logs, run:"
    echo "  ssh -p 22 $SERVER_USER@$SERVER_IP 'journalctl -u bio-guard-bot.service -f'"
else
    echo "✗ Error occurred during server setup"
    exit 1
fi