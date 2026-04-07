# Bio Guard Bot

A Telegram bot that monitors user bios for links and contact information, warning users and applying penalties when they violate group rules.

## Features

- Monitors user bios for links and contact information
- Configurable warning limits
- Multiple penalty options (mute, kick, ban)
- Flexible application rules (apply to members, admins, or everyone)
- Interactive settings panel

## Installation

1. Install the required packages:
   ```
   pip install aiogram aiosqlite
   ```

2. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram

3. Replace `YOUR_BOT_TOKEN` in the script with your actual bot token

## Usage

1. Run the bot:
   ```
   python bio_guard_bot.py
   ```

2. Add the bot to your Telegram group with admin rights

3. Use `/setting` command in the group to configure the bot settings:
   - Warning limit (1, 2, 3, or 5 warnings before penalty)
   - Penalty type (mute, kick, or ban)
   - Apply to (members, admins, or everyone)

## How It Works

- The bot continuously monitors messages in groups
- When a user sends a message, their bio is checked for links or contact information
- If a violation is detected, the user receives a warning
- After reaching the configured warning limit, the penalty is applied

## Configuration

The bot uses SQLite to store settings and warning counts persistently. The database file is created automatically as `bio_guard.db`.

## Commands

- `/setting` - Open the settings panel (only available to group owners)
