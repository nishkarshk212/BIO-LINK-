# Bio Guard Bot - Manual Deployment Guide

## Overview
This guide provides step-by-step instructions for manually deploying the Bio Guard Bot to your Linux server.

## Prerequisites
- Linux server with Python 3.8+ installed
- Root or sudo access to the server
- Telegram Bot Token (already configured in your `.env` file)

## Step 1: Prepare Files for Transfer

First, you'll need to prepare the files to transfer to the server. The following files are required:

1. `bio_guard_bot.py` - The main bot application
2. `requirements.txt` - Python dependencies
3. `.env` - Configuration file with your bot token

## Step 2: Transfer Files to Server

Use any of the following methods to transfer files to your server:

### Option A: SCP/SFTP
```bash
# Using SCP
scp bio_guard_bot.py requirements.txt .env root@140.245.240.202:/tmp/

# Using SFTP client like FileZilla, WinSCP, etc.
```

### Option B: Direct Download (if you have direct access)
If you have console access to the server, you can upload files to a cloud service and download them:

```bash
# Example: If you uploaded files to a web server
wget http://your-server.com/bio_guard_bot.py
wget http://your-server.com/requirements.txt
wget http://your-server.com/.env
```

## Step 3: Server Setup

Once you have access to your server, follow these steps:

### 1. Create Project Directory
```bash
sudo mkdir -p /opt/bio_guard_bot
```

### 2. Move Files to Project Directory
```bash
sudo mv /tmp/bio_guard_bot.py /opt/bio_guard_bot/
sudo mv /tmp/requirements.txt /opt/bio_guard_bot/
sudo mv /tmp/.env /opt/bio_guard_bot/
```

### 3. Set Proper Permissions
```bash
sudo chmod 600 /opt/bio_guard_bot/.env
sudo chown root:root /opt/bio_guard_bot/*
```

## Step 4: Install Dependencies

### 1. Install Python and Pip (if not already installed)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 2. Create Virtual Environment
```bash
cd /opt/bio_guard_bot
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Packages
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Test the Bot

Before setting up as a service, test if the bot runs correctly:

```bash
# Make sure you're in the virtual environment
source /opt/bio_guard_bot/venv/bin/activate
cd /opt/bio_guard_bot
python bio_guard_bot.py
```

If you see a message indicating the bot is running, press Ctrl+C to stop it.

## Step 6: Set Up as a System Service

### 1. Create Systemd Service File
```bash
sudo nano /etc/systemd/system/bio-guard-bot.service
```

### 2. Add the Following Content:
```
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
```

### 3. Save and Exit (Ctrl+X, then Y, then Enter in nano)

### 4. Enable and Start the Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable bio-guard-bot.service
sudo systemctl start bio-guard-bot.service
```

### 5. Check Service Status
```bash
sudo systemctl status bio-guard-bot.service
```

## Step 7: Verify the Bot is Running

Check if the bot is running and monitoring:

```bash
# Check the service status
sudo systemctl status bio-guard-bot.service

# View recent logs
sudo journalctl -u bio-guard-bot.service -f

# Check if the process is running
ps aux | grep bio_guard_bot
```

## Troubleshooting

### If the service fails to start:
```bash
# Check detailed logs
sudo journalctl -u bio-guard-bot.service --no-pager -l

# Test manually
source /opt/bio_guard_bot/venv/bin/activate
cd /opt/bio_guard_bot
python bio_guard_bot.py
```

### Common Issues:

1. **Invalid Bot Token**: Ensure your BOT_TOKEN in `.env` is correct
2. **Missing Dependencies**: Verify all packages from requirements.txt are installed
3. **Permission Issues**: Check that the .env file has proper permissions (600)
4. **Python Path**: Ensure the ExecStart path points to the correct Python interpreter in the virtual environment

## Updating the Bot

To update the bot in the future:

1. Download the new version of `bio_guard_bot.py`
2. Replace the file in `/opt/bio_guard_bot/`
3. Restart the service:
   ```bash
   sudo systemctl restart bio-guard-bot.service
   ```

## Stopping/Disabling the Bot

To stop the bot temporarily:
```bash
sudo systemctl stop bio-guard-bot.service
```

To disable the bot from starting automatically:
```bash
sudo systemctl disable bio-guard-bot.service
```

## Security Considerations

- Store your bot token securely and never share it publicly
- The .env file has restricted permissions (600) to protect sensitive data
- Regularly update your system and Python packages
- Monitor logs for any unusual activity