# Bio Guard Bot Deployment Guide

## Server Information
- **IP Address**: 140.245.240.202
- **Username**: root
- **Port**: 22
- **OS**: Ubuntu 22.04 LTS
- **Location**: Singapore

## Deployment Steps

### Step 1: Connect to Your Server
```bash
ssh -p 22 root@140.245.240.202
```

### Step 2: Install Required Dependencies
Once connected to your server, run these commands:

```bash
# Update package list
apt update

# Install Python and required packages
apt install -y python3 python3-pip python3-venv sqlite3

# Install systemd (usually pre-installed)
apt install -y systemd
```

### Step 3: Create Project Directory
```bash
mkdir -p /opt/bio_guard_bot
cd /opt/bio_guard_bot
```

### Step 4: Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 5: Transfer Files from Your Local Machine
On your local machine (in a new terminal), run these commands to transfer files:

```bash
# Transfer the main bot file
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/bio_guard_bot.py" root@140.245.240.202:/opt/bio_guard_bot/

# Transfer requirements file
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/requirements.txt" root@140.245.240.202:/opt/bio_guard_bot/

# Transfer environment variables
scp -P 22 "/Users/nishkarshkr/Desktop/bio link/.env" root@140.245.240.202:/opt/bio_guard_bot/
```

### Step 6: Install Python Dependencies
Back on your server:

```bash
cd /opt/bio_guard_bot
source venv/bin/activate
pip install -r requirements.txt
```

### Step 7: Set Proper Permissions
```bash
chmod 600 /opt/bio_guard_bot/.env
chmod 755 /opt/bio_guard_bot/bio_guard_bot.py
```

### Step 8: Create Systemd Service
Create the service file:

```bash
sudo nano /etc/systemd/system/bio-guard-bot.service
```

Add this content to the file:

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

### Step 9: Enable and Start the Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bio-guard-bot.service

# Start the service
sudo systemctl start bio-guard-bot.service
```

### Step 10: Check Service Status
```bash
# Check if service is running
sudo systemctl status bio-guard-bot.service

# View real-time logs
journalctl -u bio-guard-bot -f

# View recent logs
journalctl -u bio-guard-bot --since "1 hour ago"
```

## Useful Commands

### Service Management
```bash
# Restart the bot
sudo systemctl restart bio-guard-bot

# Stop the bot
sudo systemctl stop bio-guard-bot

# Start the bot
sudo systemctl start bio-guard-bot

# Check service status
sudo systemctl status bio-guard-bot
```

### Log Management
```bash
# View live logs
journalctl -u bio-guard-bot -f

# View logs from last hour
journalctl -u bio-guard-bot --since "1 hour ago"

# View logs with specific time range
journalctl -u bio-guard-bot --since "2026-03-02 10:00:00" --until "2026-03-02 12:00:00"
```

### File Management
```bash
# Check disk usage
df -h

# Check directory size
du -sh /opt/bio_guard_bot

# View running processes
ps aux | grep bio_guard
```

## Troubleshooting

### If the bot fails to start:
1. Check the logs: `journalctl -u bio-guard-bot -f`
2. Verify environment file: `cat /opt/bio_guard_bot/.env`
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
# Check for syntax errors in service file
sudo systemctl cat bio-guard-bot.service

# Validate service configuration
sudo systemctl daemon-reload
sudo systemctl reset-failed bio-guard-bot.service
```

## Security Notes

✅ Your bot is configured to:
- Run with minimal privileges (root user, but restricted to bot directory)
- Use systemd for automatic restarts
- Store sensitive data (.env) with restricted permissions
- Log to system journal for centralized logging

⚠️ Remember the server rules:
- No BTC mining or cracking activities
- No DDoS attacks or spamming
- No port scanning or unauthorized network activities
- No phishing or malicious content

## Verification

After deployment, you can verify everything is working by:
1. Checking the service status: `sudo systemctl status bio-guard-bot`
2. Viewing the logs: `journalctl -u bio-guard-bot -f`
3. Testing your bot in Telegram by sending the `/start` command

The bot should automatically start monitoring groups and protecting them from bio links once added with admin permissions.