#!/bin/bash

# Deployment Script for Bio Guard Bot
# Server: 161.118.250.195

SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PORT="22"
REMOTE_DIR="/root/bio-guard-bot"

echo "🚀 Starting deployment to $SERVER_IP..."

# Step 1: Connect to server and setup environment
echo "📦 Setting up server environment..."
ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} << 'EOF'
    # Update system
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git screen
    
    # Create project directory
    mkdir -p /root/bio-guard-bot
    cd /root/bio-guard-bot
    
    # Clone or pull latest from GitHub
    if [ -d ".git" ]; then
        echo "📥 Pulling latest changes..."
        git pull origin main
    else
        echo "📥 Cloning repository..."
        git clone https://github.com/nishkarshk212/BIO-LINK-.git .
    fi
    
    # Setup virtual environment
    if [ ! -d "venv" ]; then
        echo "🐍 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install NSFW requirements if exists
    if [ -f "requirements_nsfw.txt" ]; then
        pip install -r requirements_nsfw.txt
    fi
    
    # Stop existing bot if running
    echo "🛑 Stopping existing bot..."
    pkill -f "python3 bio_guard_bot.py" || true
    sleep 2
    
    # Start bot in background using screen
    echo "🚀 Starting bot..."
    screen -dmS bio_guard_bot bash -c 'cd /root/bio-guard-bot && source venv/bin/activate && python3 bio_guard_bot.py'
    
    echo "✅ Deployment complete!"
    echo "📊 Checking bot status..."
    sleep 3
    screen -list | grep bio_guard_bot
EOF

echo ""
echo "✅ Deployment finished successfully!"
echo "🔍 To check bot logs, run: ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} 'screen -r bio_guard_bot'"
echo "🛑 To stop bot, run: ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} 'screen -S bio_guard_bot -X quit'"
