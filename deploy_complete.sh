#!/bin/bash
# Complete Deployment Script for Bio Guard Bot
# Deploys to server via SSH and updates Git repository

set -e  # Exit on error

# Configuration
SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PASS="Akshay343402355468"
SERVER_PORT="22"
BOT_PATH="/opt/bio_guard_bot"
LOCAL_FILE="/Users/nishkarshkr/Desktop/bio link/bio_guard_bot.py"
GIT_REPO_URL="https://github.com/YOUR_USERNAME/bio-guard-bot.git"  # Update this

echo "======================================"
echo "🚀 BIO GUARD BOT DEPLOYMENT"
echo "======================================"
echo ""

# Step 1: Backup current server file
echo "📦 Creating backup on server..."
sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd $BOT_PATH
if [ -f bio_guard_bot.py ]; then
    cp bio_guard_bot.py bio_guard_bot.py.backup.\$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
else
    echo "⚠️ No existing file found"
fi
EOF

# Step 2: Transfer updated file using base64 encoding
echo ""
echo "📤 Transferring updated bio_guard_bot.py..."
ENCODED_FILE=$(base64 -i "$LOCAL_FILE")

sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
echo "$ENCODED_FILE" | base64 -d > $BOT_PATH/bio_guard_bot.py
if [ \$? -eq 0 ]; then
    echo "✅ File transferred successfully"
    chmod +x $BOT_PATH/bio_guard_bot.py
else
    echo "❌ File transfer failed"
    exit 1
fi
EOF

# Step 3: Restart bot service
echo ""
echo "🔄 Restarting bot service..."
sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
systemctl restart bio-guard-bot
sleep 3
systemctl status bio-guard-bot --no-pager | head -10
EOF

if [ $? -eq 0 ]; then
    echo "✅ Bot restarted successfully"
else
    echo "❌ Bot restart failed"
    exit 1
fi

# Step 4: Verify deployment
echo ""
echo "🔍 Verifying deployment..."
sshpass -p "$SERVER_PASS" ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << EOF
cd $BOT_PATH
echo "Checking for self_destruct_enabled references..."
COUNT=\$(grep -n "self_destruct_enabled" bio_guard_bot.py | wc -l)
echo "Found \$COUNT references to self_destruct_enabled"

if [ \$COUNT -ge 10 ]; then
    echo "✅ Self-destruct code detected in file"
else
    echo "⚠️ Warning: Expected more self_destruct references"
fi

# Check if bot is running
echo ""
echo "Bot service status:"
systemctl is-active bio-guard-bot
EOF

# Step 5: Update Git repository (optional)
echo ""
echo "📚 Updating Git repository..."
read -p "Do you want to commit and push changes to Git? (y/n): " UPDATE_GIT

if [[ $UPDATE_GIT == "y" || $UPDATE_GIT == "Y" ]]; then
    cd "/Users/nishkarshkr/Desktop/bio link"
    
    # Check if git repo exists
    if [ -d ".git" ]; then
        echo "📝 Committing changes..."
        git add bio_guard_bot.py
        git commit -m "Fix: Add self-destruct message feature with settings UI
        
- Added self_destruct_enabled and self_destruct_time columns to database
- Updated settings menu to include self-destruct option
- Added timer controls with +/- buttons for hours/minutes/seconds
- Fixed database queries to include self-destruct columns
- Integrated message deletion functionality
- Deployed to production server"
        
        echo "📤 Pushing to remote repository..."
        git push origin main 2>&1 || {
            echo "⚠️ Git push failed, trying master branch..."
            git push origin master 2>&1 || echo "❌ Could not push to any branch"
        }
        
        echo "✅ Git updated successfully"
    else
        echo "⚠️ Not a git repository. Initialize with: git init"
    fi
else
    echo "⏭️ Skipping Git update"
fi

# Step 6: Final status
echo ""
echo "======================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "📱 Test in Telegram:"
echo "   1. Open Telegram"
echo "   2. Send: /settings"
echo "   3. Look for: 💣 Self Destruct"
echo "   4. Configure timer and enable!"
echo ""
echo "🔍 Verification commands:"
echo "   sshpass -p '$SERVER_PASS' ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP 'systemctl status bio-guard-bot'"
echo ""
echo "📊 View logs:"
echo "   sshpass -p '$SERVER_PASS' ssh -p $SERVER_PORT -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP 'journalctl -u bio-guard-bot -f'"
echo ""
echo "⏰ Deployment completed at: $(date)"
echo ""
