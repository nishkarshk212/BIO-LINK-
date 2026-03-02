#!/bin/bash

# Simple deployment script for Bio Guard Bot
# Run this ON YOUR UBUNTU SERVER

echo "🚀 Setting up Bio Guard Bot on Ubuntu Server..."

# Navigate to project directory
cd /opt/bio_guard_bot

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
aiogram==3.24.0
aiosqlite==0.22.1
python-dotenv==1.0.0
EOF

# Create .env file
echo "Creating environment file..."
cat > .env << 'EOF'
BOT_TOKEN=8760760963:AAHx0_QhmQbnyOd3iji_YdKjQ3pHt6oJWWo
API_ID=37004193
API_HASH=6001bbc724920244c612e0f96de20abe
EOF

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Set proper permissions
echo "Setting file permissions..."
chmod 600 .env
chmod 755 bio_guard_bot.py

echo "✅ Setup complete!"
echo "To start the bot, run:"
echo "cd /opt/bio_guard_bot && source venv/bin/activate && python bio_guard_bot.py"