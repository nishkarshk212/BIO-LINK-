# Bio Guard Bot - Deployment Instructions

## Overview
This document provides complete instructions for deploying the Bio Guard Bot to your Ubuntu server.

## Prerequisites

### 1. Telegram Bot Credentials
Before deploying, you need to obtain the following credentials:

- **Bot Token**: Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
- **API ID and API Hash**: Get these from [my.telegram.org](https://my.telegram.org)

### 2. Server Access
- Ubuntu server at IP: `140.245.240.202`
- SSH access with root privileges
- Port 22 open for SSH connections

### 3. Update Credentials
Update the `.env` file with your real credentials:

```bash
BOT_TOKEN=your_actual_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

Run the final deployment script:

```bash
./final_deploy.sh
```

This script will:
1. Check if credentials are properly configured
2. Install system dependencies on the server
3. Transfer all necessary files
4. Set up Python virtual environment
5. Configure systemd service
6. Start the bot service

### Method 2: Manual Deployment

If you prefer manual deployment, follow these steps:

#### Step 1: Connect to Your Server
```bash
ssh -p 22 root@140.245.240.202
```

#### Step 2: Install System Dependencies
```bash
apt update
apt install -y python3 python3-pip python3-venv sqlite3 git
```

#### Step 3: Create Project Directory
```bash
mkdir -p /opt/bio_guard_bot
cd /opt/bio_guard_bot
```

#### Step 4: Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

#### Step 5: Transfer Files
From your local machine, transfer the required files:
```bash
scp -P 22 bio_guard_bot.py root@140.245.240.202:/opt/bio_guard_bot/
scp -P 22 requirements.txt root@140.245.240.202:/opt/bio_guard_bot/
scp -P 22 .env root@140.245.240.202:/opt/bio_guard_bot/
```

#### Step 6: Install Python Dependencies
Back on your server:
```bash
cd /opt/bio_guard_bot
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 7: Set File Permissions
```bash
chmod 600 .env
chmod 755 bio_guard_bot.py
```

#### Step 8: Create Systemd Service
```bash
sudo nano /etc/systemd/system/bio-guard-bot.service
```

Add the following content:
```ini
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
```

Save and exit (Ctrl+X, then Y, then Enter).

#### Step 9: Start the Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable bio-guard-bot.service
sudo systemctl start bio-guard-bot.service
```

## Verification

After deployment, verify that everything is working:

```bash
# Check service status
sudo systemctl status bio-guard-bot.service

# View recent logs
journalctl -u bio-guard-bot --since "5 minutes ago"

# View live logs
journalctl -u bio-guard-bot -f
```

## Bot Usage

1. Search for your bot on Telegram (using the username from @BotFather)
2. Send `/start` to verify the bot is working
3. Add the bot to your Telegram groups with admin permissions
4. Use `/settings` in a private chat with the bot to configure warning limits, penalties, etc.

## Management Commands

```bash
# Check status
sudo systemctl status bio-guard-bot

# Restart bot
sudo systemctl restart bio-guard-bot

# Stop bot
sudo systemctl stop bio-guard-bot

# View logs
journalctl -u bio-guard-bot -f

# View recent logs
journalctl -u bio-guard-bot --since "1 hour ago"
```

## Troubleshooting

### If the bot fails to start:
1. Check logs: `journalctl -u bio-guard-bot -f`
2. Verify .env file: `cat /opt/bio_guard_bot/.env`
3. Test manual execution:
   ```bash
   cd /opt/bio_guard_bot
   source venv/bin/activate
   python bio_guard_bot.py
   ```

### If there are permission issues:
```bash
sudo chown -R root:root /opt/bio_guard_bot
sudo chmod 600 /opt/bio_guard_bot/.env
sudo chmod 755 /opt/bio_guard_bot/bio_guard_bot.py
```

### If the service won't start:
```bash
# Check service configuration
sudo systemctl cat bio-guard-bot.service
sudo systemctl daemon-reload
sudo systemctl reset-failed bio-guard-bot.service
```

## Features

The Bio Guard Bot provides:
- Automatic detection of links in user bios
- Configurable warning limits (1, 2, 3, or 5 warnings)
- Multiple penalty options (mute, kick, ban)
- Flexible application rules (apply to members, admins, or everyone)
- Interactive settings panel
- Automatic cleanup of warning messages after 1 minute
- Persistent storage using SQLite database

## Security Notes

- The bot runs as a systemd service with automatic restart capability
- Environment variables are stored securely with restricted permissions
- All logs are managed by the system journal
- The bot will automatically restart if it crashes or the server reboots