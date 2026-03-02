#!/usr/bin/env python3
"""
Alternative deployment script for Bio Guard Bot
This script transfers the latest code to the server using paramiko
"""

import os
import sys
import base64
import subprocess


def run_local_command(cmd):
    """Run a local command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_files():
    """Check if required files exist"""
    required_files = ['bio_guard_bot.py', 'requirements.txt', '.env']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return False
    
    print("✓ All required files found")
    return True


def encode_files():
    """Encode files as base64"""
    encoded_files = {}
    
    try:
        with open('bio_guard_bot.py', 'rb') as f:
            encoded_files['bot'] = base64.b64encode(f.read()).decode('utf-8')
        
        with open('requirements.txt', 'rb') as f:
            encoded_files['requirements'] = base64.b64encode(f.read()).decode('utf-8')
        
        with open('.env', 'rb') as f:
            encoded_files['env'] = base64.b64encode(f.read()).decode('utf-8')
        
        print("✓ Files encoded successfully")
        return encoded_files
    except Exception as e:
        print(f"Error encoding files: {e}")
        return None


def create_ssh_script(encoded_files):
    """Create an SSH script with embedded files"""
    script_content = f'''#!/bin/bash
set -e

echo "Connected to server, starting redeployment with latest code..."

# Create the project directory if it doesn't exist
mkdir -p /opt/bio_guard_bot
echo "Created project directory /opt/bio_guard_bot"

# Decode and write the files directly
echo '{encoded_files['bot']}' | base64 -d > /opt/bio_guard_bot/bio_guard_bot.py
echo '{encoded_files['requirements']}' | base64 -d > /opt/bio_guard_bot/requirements.txt
echo '{encoded_files['env']}' | base64 -d > /opt/bio_guard_bot/.env

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
if [ $? -eq 0 ]; then
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
'''
    
    with open('/tmp/bio_guard_deploy.sh', 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod('/tmp/bio_guard_deploy.sh', 0o755)
    print("✓ SSH script created successfully")


def main():
    print("Starting alternative redeployment of Bio Guard Bot...")
    print("Latest features included:")
    print("  - Open Here/Open in Private buttons in group settings")
    print("  - Fixed button layouts for better UX")
    print("  - Consistent inline keyboard arrangements")
    
    # Check if required files exist
    if not check_files():
        return False
    
    # Encode files
    encoded_files = encode_files()
    if not encoded_files:
        return False
    
    # Create SSH script
    create_ssh_script(encoded_files)
    
    print("\nSSH script created at /tmp/bio_guard_deploy.sh")
    print("You can now run the following command to deploy:")
    print("ssh -o StrictHostKeyChecking=no root@140.245.240.202 'bash -s' < /tmp/bio_guard_deploy.sh")
    
    print("\nOr run this complete command:")
    print("cat /tmp/bio_guard_deploy.sh | ssh -o StrictHostKeyChecking=no root@140.245.240.202 'bash -s'")
    
    return True


if __name__ == '__main__':
    success = main()
    if success:
        print("\n✓ Alternative deployment script created successfully!")
        print("Please run the suggested command to complete the deployment.")
    else:
        print("\n✗ Failed to create alternative deployment script")
        sys.exit(1)