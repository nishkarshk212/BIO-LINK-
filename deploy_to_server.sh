#!/bin/bash

# Deployment script for Bio Guard Bot
SERVER_IP="140.245.240.202"
SERVER_USER="root"

echo "Starting deployment of Bio Guard Bot to $SERVER_IP..."

# Check if files exist locally
if [ ! -f "bio_guard_bot.py" ] || [ ! -f "requirements.txt" ] || [ ! -f ".env" ]; then
    echo "Error: Required files not found in current directory!"
    echo "Files needed: bio_guard_bot.py, requirements.txt, .env"
    exit 1
fi

echo "✓ Local files verified"

# Create temporary archive of files
tar -czf bio_guard_bot.tar.gz bio_guard_bot.py requirements.txt .env

echo "✓ Created archive of files"

# Transfer the archive to the server
echo "Transferring files to server..."
scp -P 22 bio_guard_bot.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

if [ $? -ne 0 ]; then
    echo "Error: Failed to transfer files to server"
    rm bio_guard_bot.tar.gz
    exit 1
fi

echo "✓ Files transferred to server"

# Clean up local archive
rm bio_guard_bot.tar.gz

# SSH into the server and set up the bot
echo "Setting up bot on server..."
ssh -p 22 $SERVER_USER@$SERVER_IP << 'EOF'
set -e

# Create the project directory if it doesn't exist
mkdir -p /opt/bio_guard_bot

# Extract the files
cd /tmp
tar -xzf bio_guard_bot.tar.gz -C /opt/bio_guard_bot/
rm bio_guard_bot.tar.gz

# Change to the project directory
cd /opt/bio_guard_bot

# Set proper permissions for the .env file
chmod 600 .env

# Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

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

# Reload systemd to recognize the new service
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable bio-guard-bot.service

# Start the service
systemctl start bio-guard-bot.service

# Wait a moment for the service to start
sleep 3

# Check if the service is running
if systemctl is-active --quiet bio-guard-bot.service; then
    echo "✓ Bio Guard Bot service is running"
    echo "✓ Deployment completed successfully!"
    systemctl status bio-guard-bot.service --no-pager -l
else
    echo "✗ Bio Guard Bot service failed to start"
    systemctl status bio-guard-bot.service --no-pager -l
    exit 1
fi
EOF

if [ $? -eq 0 ]; then
    echo "✓ Server setup completed successfully!"
    echo "Bio Guard Bot is now running on the server."
    echo "You can check the status with: ssh -p 22 $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot.service'"
else
    echo "✗ Error occurred during server setup"
    exit 1
fi