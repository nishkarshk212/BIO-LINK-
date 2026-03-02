# Manual Deployment Steps for Bio Guard Bot

## Server Information
- **IP Address**: 140.245.240.202
- **Username**: root
- **Password**: Akshay343402355468

## Step-by-Step Deployment Instructions

### Step 1: Connect to Your Server
Open your terminal and connect to your server:
```bash
ssh -p 22 root@140.245.240.202
```
When prompted, enter the password: `Akshay343402355468`

### Step 2: Install System Dependencies
Once connected to your server, run these commands:

```bash
# Update system packages
apt update

# Install required system dependencies
apt install -y python3 python3-pip python3-venv sqlite3 git curl wget

# Verify installations
python3 --version
pip3 --version
```

### Step 3: Create Project Directory and Set Up Python Environment
```bash
# Create project directory
mkdir -p /opt/bio_guard_bot
cd /opt/bio_guard_bot

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages directly
pip install aiogram==3.24.0 aiosqlite==0.22.1 python-dotenv==1.0.0
```

### Step 4: Upload Files to Server
You'll need to transfer the files from your local machine to the server using SCP. On your local machine (not the server), run:

```bash
# From your local terminal (not the server terminal)
scp -P 22 /Users/nishkarshkr/Desktop/bio\ link/bio_guard_bot.py root@140.245.240.202:/tmp/
scp -P 22 /Users/nishkarshkr/Desktop/bio\ link/requirements.txt root@140.245.240.202:/tmp/
scp -P 22 /Users/nishkarshkr/Desktop/bio\ link/.env root@140.245.240.202:/tmp/
```

### Step 5: Move Files and Set Permissions
Back on your server terminal, run:

```bash
# Move files to the project directory
mv /tmp/bio_guard_bot.py /opt/bio_guard_bot/
mv /tmp/requirements.txt /opt/bio_guard_bot/
mv /tmp/.env /opt/bio_guard_bot/

# Set proper permissions
chmod 600 /opt/bio_guard_bot/.env
chmod 755 /opt/bio_guard_bot/bio_guard_bot.py

# Verify files are in place
ls -la /opt/bio_guard_bot/
```

### Step 6: Test the Bot Manually (Optional)
```bash
# Navigate to the project directory
cd /opt/bio_guard_bot

# Activate virtual environment
source venv/bin/activate

# Test the bot (this will run until you press Ctrl+C)
python bio_guard_bot.py
```

### Step 7: Create Systemd Service
```bash
# Create the systemd service file
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
```

### Step 8: Start the Service
```bash
# Reload systemd to recognize the new service
systemctl daemon-reload

# Enable the service to start automatically on boot
systemctl enable bio-guard-bot.service

# Start the service now
systemctl start bio-guard-bot.service

# Check the status of the service
systemctl status bio-guard-bot.service
```

### Step 9: Verify the Deployment
```bash
# Check if the service is running
systemctl status bio-guard-bot.service

# View recent logs
journalctl -u bio-guard-bot --since "5 minutes ago"

# View live logs (press Ctrl+C to exit)
journalctl -u bio-guard-bot -f
```

## Expected Output
When you run `systemctl status bio-guard-bot.service`, you should see:
- Active: active (running) 
- Loaded: loaded (enabled)

## Managing the Service
```bash
# Start the bot
sudo systemctl start bio-guard-bot

# Stop the bot
sudo systemctl stop bio-guard-bot

# Restart the bot
sudo systemctl restart bio-guard-bot

# Check status
sudo systemctl status bio-guard-bot

# View logs
sudo journalctl -u bio-guard-bot -f
```

## Adding the Bot to Telegram
1. Search for your bot in Telegram using the username from @BotFather
2. Send `/start` to verify the bot is working
3. Add the bot to your Telegram groups with admin permissions
4. Use `/settings` in a private chat with the bot to configure warning limits, penalties, etc.

## Troubleshooting
If the service fails to start:
```bash
# Check logs for errors
journalctl -u bio-guard-bot -f

# Check if the .env file has the correct permissions
ls -la /opt/bio_guard_bot/.env

# Verify the bot file has execute permissions
ls -la /opt/bio_guard_bot/bio_guard_bot.py

# Test the bot manually
cd /opt/bio_guard_bot
source venv/bin/activate
python bio_guard_bot.py
```

The bot is now deployed and will automatically restart if it crashes or the server reboots!