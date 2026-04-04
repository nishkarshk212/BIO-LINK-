import re
import asyncio
import aiosqlite
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Get bot name
BOT_NAME = "[ 🇵؜ᴀɴᴅᴀ 🆇 🇸؜ᴇᴄᴜʀɪᴛʏ ]"

# Owner username - only this user can access logs
OWNER_USERNAME = "Jayden_212"

# Log channel configuration
LOG_CHANNEL_ID = -1003757375746  # @music_24345
LOG_CHANNEL_USERNAME = "@music_24345"

# Store owner's chat ID for automatic notifications
owner_chat_id = None

# Database initialization
async def init_db():
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            warn_limit INTEGER DEFAULT 3,
            penalty TEXT DEFAULT 'mute',
            apply_to TEXT DEFAULT 'members',
            edit_checker INTEGER DEFAULT 1,
            edit_apply_to TEXT DEFAULT 'members'
        )
        """)
        # Add edit_checker column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN edit_checker INTEGER DEFAULT 1")
            print("✅ Added 'edit_checker' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add edit_apply_to column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN edit_apply_to TEXT DEFAULT 'members'")
            print("✅ Added 'edit_apply_to' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add edit_penalty column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN edit_penalty TEXT DEFAULT 'mute'")
            print("✅ Added 'edit_penalty' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add bio_checker_enabled column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN bio_checker_enabled INTEGER DEFAULT 1")
            print("✅ Added 'bio_checker_enabled' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add who_can_control column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN who_can_control TEXT DEFAULT 'owner'")
            print("✅ Added 'who_can_control' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add blocklist_penalty column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN blocklist_penalty TEXT DEFAULT 'mute'")
            print("✅ Added 'blocklist_penalty' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add blocklist_warn_limit column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN blocklist_warn_limit INTEGER DEFAULT 3")
            print("✅ Added 'blocklist_warn_limit' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add blocklist_warning_message column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN blocklist_warning_message TEXT DEFAULT 'ᴅᴏɴ''ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ'")
            print("✅ Added 'blocklist_warning_message' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add self_destruct_enabled column if it doesn't exist
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN self_destruct_enabled INTEGER DEFAULT 0")
            print("✅ Added 'self_destruct_enabled' column to settings table.")
        except Exception:
            pass # Already exists
        
        # Add self_destruct_time column if it doesn't exist (in seconds)
        try:
            await db.execute("ALTER TABLE settings ADD COLUMN self_destruct_time INTEGER DEFAULT 60")
            print("✅ Added 'self_destruct_time' column to settings table.")
        except Exception:
            pass # Already exists
        await db.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            chat_id INTEGER,
            user_id INTEGER,
            count INTEGER,
            PRIMARY KEY (chat_id, user_id)
        )
        """)
        # Activity log table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            user_id INTEGER,
            username TEXT,
            chat_id INTEGER,
            chat_name TEXT,
            details TEXT
        )
        """)
        # Global bans table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS global_bans (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            reason TEXT,
            timestamp TEXT
        )
        """)
        await db.commit()
        
        # Blocklist table for banned words/stickers/images
        await db.execute("""
        CREATE TABLE IF NOT EXISTS blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            content_type TEXT DEFAULT 'text',
            content_value TEXT,
            added_by INTEGER,
            timestamp TEXT
        )
        """)
        print("✅ Blocklist table created/verified")
        
        # Filters table for custom triggers and replies
        await db.execute("""
        CREATE TABLE IF NOT EXISTS filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            trigger_text TEXT,
            reply_text TEXT,
            added_by INTEGER,
            timestamp TEXT
        )
        """)
        print("✅ Filters table created/verified")
        
        # Locks table for locked items
        await db.execute("""
        CREATE TABLE IF NOT EXISTS locks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            lock_type TEXT,
            enabled INTEGER DEFAULT 1,
            warn_enabled INTEGER DEFAULT 1,
            updated_by INTEGER,
            timestamp TEXT
        )
        """)
        print("✅ Locks table created/verified")
        
        # Allowlist table for exempted items
        await db.execute("""
        CREATE TABLE IF NOT EXISTS allowlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            item_value TEXT,
            item_type TEXT,
            added_by INTEGER,
            timestamp TEXT
        )
        """)
        print("✅ Allowlist table created/verified")
        
        await db.commit()

# Start command
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Check if the command includes arguments (like /start settings)
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if command_args and command_args[0] == "settings":
        # If user clicked "Open in Private" from group, redirect to settings
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to) VALUES (?, ?, ?, ?)", 
                                   (message.chat.id, 3, "mute", "members"))
                    await db.commit()
                    row = (3, "mute", "members")
        
        limit, penalty, apply_to = row
        kb = InlineKeyboardBuilder()
        kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
        kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
        kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
        kb.button(text="✔︎ & Close", callback_data="save_and_close")
        kb.adjust(2)
        
        await message.reply("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
        return
    
    kb = InlineKeyboardBuilder()
    
    try:
        bot_username = (await bot.get_me()).username
        
        # Build buttons
        kb.button(text="✚ Add To Group", url=f"https://t.me/{bot_username}?startgroup=true")
        kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
        kb.button(text="⚙ Settings", callback_data="open_settings_menu")
        kb.button(text="☂ Updates", url="https://t.me/Tele_212_bots")
        kb.adjust(2)
        
        start_msg = (
            f"๏ ᴛʜɪs ɪs <a href='https://t.me/{bot_username}'>{BOT_NAME}</a>\n\n"
            f"➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
            f"ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
            f"➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
            f"➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂"
        )
        
        # List of video URLs to choose from randomly
        import random
        video_urls = [
            "https://files.catbox.moe/4ij8ag.mp4",
            "https://files.catbox.moe/z68nj0.mp4",
            "https://files.catbox.moe/nl65r9.mp4"
        ]
        
        # Select a random video URL
        selected_video = random.choice(video_urls)
        
        # Send video from URL
        try:
            await message.answer_video(
                video=selected_video,
                caption=start_msg,
                reply_markup=kb.as_markup()
            )
        except Exception as video_error:
            print(f"Error sending video {selected_video}: {video_error}")
            # Try another random video if first one fails
            remaining_videos = [v for v in video_urls if v != selected_video]
            for retry_video in remaining_videos:
                try:
                    await message.answer_video(
                        video=retry_video,
                        caption=start_msg,
                        reply_markup=kb.as_markup()
                    )
                    break
                except:
                    continue
            else:
                # Fallback to text if all videos fail
                await message.answer(
                    start_msg,
                    reply_markup=kb.as_markup()
                )
            # Fallback to text if video not found
            await message.answer(
                start_msg,
                reply_markup=kb.as_markup()
            )
    except Exception as e:
        print(f"Error in start command: {e}")
        # Fallback buttons
        kb = InlineKeyboardBuilder()
        kb.button(text="✚ Add To Group", url="https://t.me/your_bot_username?startgroup=true")
        kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
        kb.button(text="⚙ Settings", callback_data="open_settings_menu")
        kb.button(text="☂ Updates", url="https://t.me/Tele_212_bots")
        kb.adjust(2)
        
        start_msg = (
            f"๏ ᴛʜɪs ɪs <a href='https://t.me/your_bot_username'>{BOT_NAME}</a>\n\n"
            f"➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
            f"ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
            f"➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
            f"➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂"
        )
        await message.answer(
            start_msg,
            reply_markup=kb.as_markup()
        )

# Help command handler
@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Send detailed help message explaining all bot features"""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
    kb.button(text="☂ Updates", url="https://t.me/Tele_212_bots")
    kb.button(text="⚙ Settings", callback_data="open_settings_menu")
    kb.adjust(2)
    
    help_text = (
        "🤖 <b>Bio Guard Bot - Complete Feature Guide</b>\n\n"
        
        "📋 <b>Main Features:</b>\n\n"
        
        "🧬 <b>1. Bio Link Checker</b>\n"
        "• Monitors user bios for blocked links/words\n"
        "• Auto-detects and takes action on violations\n"
        "• Configurable warning limit (1-10)\n"
        "• Penalty options: warn/mute/kick/ban\n"
        "• Can apply to: members only or everyone\n"
        "• Toggle ON/OFF as needed\n\n"
        
        "✏️ <b>2. Edit Checker</b>\n"
        "• Detects when users edit their messages\n"
        "• Deletes edited messages automatically\n"
        "• Prevents bait-and-switch attacks\n"
        "• Configurable warning system\n"
        "• Apply to: members only or everyone\n"
        "• Toggle ON/OFF independently\n\n"
        
        "🚫 <b>3. Blocklist</b>\n"
        "• Block specific words, links, stickers, photos\n"
        "• Auto-delete blocked content\n"
        "• Fixed warning message: 'ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ'\n"
        "• Customizable warning limit (1-10)\n"
        "• Penalty options: warn/mute/kick/ban\n"
        "• Commands:\n"
        "  /addblock - Add blocked content\n"
        "  /removeblock - Remove blocked item\n"
        "  /blocklist - View all blocked items\n\n"
        
        "🔐 <b>4. Filters & Locks</b>\n"
        "• Filters: Auto-reply to specific words\n"
        "• Locks: Prevent certain content types\n"
        "• Lockable: photos, videos, stickers, etc.\n"
        "• Custom filter responses\n"
        "• Works automatically\n\n"
        
        "👥 <b>5. Access Control</b>\n"
        "• Choose who can control settings:\n"
        "  - Owner: Only bot owner\n"
        "  - Admin: Group admins\n"
        "  - Moderator: Any member (testing)\n"
        "• Prevents unauthorized changes\n\n"
        
        "⚙ <b>Settings Menu:</b>\n"
        "• Access via: /start → Settings button\n"
        "• Configure all features from one place\n"
        "• Real-time status indicators\n"
        "• Save & close when done\n\n"
        
        "💡 <b>Quick Start:</b>\n"
        "1. Add bot to group with admin rights\n"
        "2. Click Settings to configure\n"
        "3. Enable Bio Checker & Edit Checker\n"
        "4. Set up blocklist items\n"
        "5. Bot protects automatically!\n\n"
        
        "📞 <b>Support:</b>\n"
        "Contact @Jayden_212 for help\n"
        "Join @Tele_212_bots for updates"
    )
    
    try:
        await message.answer(help_text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await log_activity("help", message.from_user.id, message.from_user.username,
                          message.chat.id, message.chat.title if message.chat.type != "private" else "Private", "User requested help")
    except Exception as e:
        print(f"Error in help command: {e}")
        # Fallback without HTML formatting
        await message.answer("Bio Guard Bot Help - See documentation for features", reply_markup=kb.as_markup())

# Global ban command - Owner only
@dp.message(Command("gban"))
async def gban_user(message: types.Message):
    if message.from_user.username != OWNER_USERNAME:
        await message.reply("❌ Access denied! Only owner can use global ban.")
        return
    
    args = message.text.split()
    user_id = None
    reason = "No reason provided"
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.username
        if len(args) > 1:
            reason = " ".join(args[1:])
    elif len(args) > 1:
        if args[1].isdigit():
            user_id = int(args[1])
            username = "Unknown"
            if len(args) > 2:
                reason = " ".join(args[2:])
        else:
            await message.reply("❌ Please provide a valid user ID or reply to a message.")
            return
    else:
        await message.reply("❌ Please reply to a user or provide their ID: /gban [user_id] [reason]")
        return

    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute(
            "INSERT OR REPLACE INTO global_bans (user_id, username, reason, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, username, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()
    
    await message.reply(f"🚫 <b>Globally Banned</b>\n👤 User: {user_id}\n📝 Reason: {reason}")
    await log_activity("gban", user_id, username, message.chat.id, message.chat.title, f"Globally banned: {reason}")

# Global unban command - Owner only
@dp.message(Command("ungban"))
async def ungban_user(message: types.Message):
    if message.from_user.username != OWNER_USERNAME:
        await message.reply("❌ Access denied! Only owner can use global unban.")
        return
    
    args = message.text.split()
    user_id = None
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(args) > 1 and args[1].isdigit():
        user_id = int(args[1])
    else:
        await message.reply("❌ Please reply to a user or provide their ID: /ungban [user_id]")
        return

    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("DELETE FROM global_bans WHERE user_id = ?", (user_id,))
        await db.commit()
    
    await message.reply(f"✅ <b>Globally Unbanned</b>\n👤 User: {user_id}")
    await log_activity("ungban", user_id, None, message.chat.id, message.chat.title, "Globally unbanned")

# Settings command - Owner only access (default)
@dp.message(Command("settings"))
async def open_settings(message: types.Message):
    # Check permissions based on who_can_control setting
    if message.chat.type in ["group", "supergroup"]:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
                row = await cur.fetchone()
                who_can_control = row[0] if row else "owner"
        
        # Check if user has permission
        allowed = False
        if who_can_control == "owner":
            allowed = chat_member.status == "creator"
        elif who_can_control == "admin":
            allowed = chat_member.status in ["creator", "administrator"]
        elif who_can_control == "moderator":
            # Moderator means any member can access
            allowed = True
        
        if not allowed:
            await message.reply(f"❌ Only {who_can_control.capitalize()} can access settings!")
            return
    
    # Settings logic - Get ALL settings including blocklist and self destruct
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("""
            SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, 
                   edit_apply_to, edit_penalty, who_can_control, 
                   blocklist_penalty, blocklist_warn_limit, blocklist_warning_message,
                   self_destruct_enabled, self_destruct_time
            FROM settings WHERE chat_id = ?
        """, (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("""
                    INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, bio_checker_enabled, 
                                        edit_checker, edit_apply_to, edit_penalty, who_can_control,
                                        blocklist_penalty, blocklist_warn_limit, blocklist_warning_message,
                                        self_destruct_enabled, self_destruct_time) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (message.chat.id, 3, "mute", "members", 1, 1, "members", "mute", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ", 0, 60))
                await db.commit()
                row = (3, "mute", "members", 1, 1, "members", "mute", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ", 0, 60)
    
    limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, edit_penalty, who_can_control, blocklist_penalty, blocklist_warn_limit, blocklist_warning_message, self_destruct_enabled, self_destruct_time = row
    kb = InlineKeyboardBuilder()
    
    # Show access options if in group
    if message.chat.type in ["group", "supergroup"]:
        kb.button(text="☞ Open Here", callback_data="open_settings_here")
        kb.button(text="☞ Open in Private", url=f"https://t.me/{(await bot.get_me()).username}?start=settings")
        kb.adjust(2)
        await message.reply("⚙ <b>Bio Guard Settings</b>\n\nChoose how to access settings:", reply_markup=kb.as_markup())
        return
    
    # Main settings menu (private chat or when opened directly)
    kb = InlineKeyboardBuilder()
    
    # Who Can Control section - Top priority with cycle button
    control_display = who_can_control.capitalize()
    kb.button(text=f"👑 Access: {control_display}", callback_data="cycle_who_can_control")
    
    # Main category buttons - Bio Checker, Edit Checker, Self Destruct, and Blocklist Penalty
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    self_destruct_status = "ON ✅" if self_destruct_enabled == 1 else "OFF ❌"
    
    kb.button(text=f"🧬 Bio Checker {bio_status}", callback_data="bio_checker_menu")
    kb.button(text=f"✏️ Edit Checker {edit_status}", callback_data="edit_checker_menu")
    kb.button(text=f"💣 Self Destruct {self_destruct_status}", callback_data="self_destruct_menu")
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2)
    
    await message.reply("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())

# Self Destruct Command - Quick access to self-destruct settings
@dp.message(Command("selfdestruct"))
async def selfdestruct_command(message: types.Message):
    """Quick toggle for self-destruct feature"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("❌ This command only works in groups!")
        return
    
    # Check permissions
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            who_can_control = row[0] if row else "owner"
    
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    user_status = chat_member.status
    
    allowed = False
    if who_can_control == "owner":
        allowed = user_status in ["creator"]
    elif who_can_control == "admin":
        allowed = user_status in ["administrator", "creator"]
    elif who_can_control == "moderator":
        allowed = True  # Any member can use
    
    if not allowed:
        await message.reply(f"❌ Only {who_can_control} can use this command!")
        return
    
    # Get current self-destruct settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                # Initialize settings
                await db.execute("""
                    INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, bio_checker_enabled, 
                                        edit_checker, edit_apply_to, edit_penalty, who_can_control,
                                        blocklist_penalty, blocklist_warn_limit, blocklist_warning_message,
                                        self_destruct_enabled, self_destruct_time) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (message.chat.id, 3, "mute", "members", 1, 1, "members", "mute", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ", 0, 60))
                await db.commit()
                enabled, destruct_time = 0, 60
            else:
                enabled, destruct_time = row
    
    # Toggle on/off
    new_enabled = 0 if enabled == 1 else 1
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET self_destruct_enabled=? WHERE chat_id=?", (new_enabled, message.chat.id))
        await db.commit()
    
    status = "enabled" if new_enabled == 1 else "disabled"
    
    # Convert time to readable format
    hours = destruct_time // 3600
    minutes = (destruct_time % 3600) // 60
    seconds = destruct_time % 60
    
    if hours > 0:
        time_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"
    
    await message.reply(
        f"💣 <b>Self-Destruct {status.capitalize()}!</b>\n\n"
        f"⏱️ Timer: <code>{time_str}</code>\n\n"
        f"<i>All messages will be deleted after this time.</i>\n\n"
        f"Use /settings to configure timer."
    )

# Set Self Destruct Timer Command
@dp.message(Command("setdestruct"))
async def set_destruct_timer(message: types.Message):
    """Set self-destruct timer in seconds/minutes/hours"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("❌ This command only works in groups!")
        return
    
    # Check permissions
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            who_can_control = row[0] if row else "owner"
    
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    user_status = chat_member.status
    
    allowed = False
    if who_can_control == "owner":
        allowed = user_status in ["creator"]
    elif who_can_control == "admin":
        allowed = user_status in ["administrator", "creator"]
    elif who_can_control == "moderator":
        allowed = True
    
    if not allowed:
        await message.reply(f"❌ Only {who_can_control} can use this command!")
        return
    
    # Parse arguments
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.reply(
            "⏱️ <b>Set Self-Destruct Timer</b>\n\n"
            "Usage:\n"
            "<code>/setdestruct 30</code> - 30 seconds\n"
            "<code>/setdestruct 5m</code> - 5 minutes\n"
            "<code>/setdestruct 1h</code> - 1 hour\n"
            "<code>/setdestruct 2h30m</code> - 2 hours 30 minutes\n\n"
            "Range: 1 second to 24 hours"
        )
        return
    
    # Parse time string (supports formats like: 30, 5m, 1h, 2h30m, 1h30m15s)
    time_str = args[0].lower()
    total_seconds = 0
    
    import re
    
    # Try to parse complex format (1h30m15s)
    match = re.match(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$', time_str)
    if match and any(match.groups()):
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
    else:
        # Try simple number (assumed seconds)
        try:
            # Check if it's a number with suffix
            if time_str.endswith('s'):
                total_seconds = int(time_str[:-1])
            elif time_str.endswith('m'):
                total_seconds = int(time_str[:-1]) * 60
            elif time_str.endswith('h'):
                total_seconds = int(time_str[:-1]) * 3600
            else:
                total_seconds = int(time_str)
        except ValueError:
            await message.reply("❌ Invalid time format! Use numbers or formats like: 30, 5m, 1h, 2h30m")
            return
    
    # Validate range (1 second to 24 hours)
    if total_seconds < 1:
        await message.reply("❌ Timer must be at least 1 second!")
        return
    
    if total_seconds > 86400:  # 24 hours
        await message.reply("❌ Timer cannot exceed 24 hours (86400 seconds)!")
        return
    
    # Update database
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET self_destruct_time=?, self_destruct_enabled=1 WHERE chat_id=?", (total_seconds, message.chat.id))
        await db.commit()
    
    # Convert to readable format
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        time_display = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        time_display = f"{minutes}m {seconds}s"
    else:
        time_display = f"{seconds}s"
    
    await message.reply(
        f"✅ <b>Timer Set Successfully!</b>\n\n"
        f"⏱️ Self-destruct timer: <code>{time_display}</code>\n"
        f"💣 Status: <b>ENABLED</b>\n\n"
        f"<i>All messages will be automatically deleted after this time.</i>\n\n"
        f"Use /selfdestruct to toggle on/off."
    )

# Logs command - Owner only (@Jayden_212)
@dp.message(Command("logs"))
async def show_logs(message: types.Message):
    # Check if user is owner
    if message.from_user.username != OWNER_USERNAME:
        await message.reply("❌ Access denied! Only @Jayden_212 can view logs.")
        return
    
    # Store owner's chat ID for auto notifications
    global owner_chat_id
    owner_chat_id = message.chat.id
    
    # Parse command arguments for filtering
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    event_filter = None
    limit = 20  # Default limit
    
    for arg in args:
        if arg.startswith("--type="):
            event_filter = arg.split("=")[1]
        elif arg.isdigit():
            limit = min(int(arg), 100)  # Max 100
    
    async with aiosqlite.connect("bio_guard.db") as db:
        if event_filter:
            async with db.execute(
                "SELECT timestamp, event_type, username, chat_name, details FROM activity_log WHERE event_type=? ORDER BY id DESC LIMIT ?",
                (event_filter, limit)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                "SELECT timestamp, event_type, username, chat_name, details FROM activity_log ORDER BY id DESC LIMIT ?",
                (limit,)
            ) as cur:
                rows = await cur.fetchall()
        
        if not rows:
            await message.reply(f"📊 No logs found{' for type: ' + event_filter if event_filter else ''}.")
            return
        
        # Format logs
        log_text = f"📋 <b>Bio Guard Bot Activity Log</b>\n"
        log_text += f"<i>Last {len(rows)} events:</i>\n\n"
        
        for row in reversed(rows):
            timestamp, event_type, username, chat_name, details = row
            emoji = {"join": "➕", "leave": "➖", "warn": "⚠️", "ban": "🚫", 
                    "mute": "🔇", "kick": "👢", "unban": "✅", "unmute": "🔊"}.get(event_type, "📝")
            
            log_text += f"{emoji} <b>{event_type.upper()}</b>\n"
            log_text += f"   👤 User: @{username or 'Unknown'}\n"
            log_text += f"   💬 Chat: {chat_name or 'Private'}\n"
            log_text += f"   📝 {details}\n"
            log_text += f"   ⏰ {timestamp}\n\n"
        
        # Split long messages
        for i in range(0, len(log_text), 4000):
            await message.answer(log_text[i:i+4000])

# Send logs to channel command - Owner only
@dp.message(Command("sendlogs"))
async def send_logs_to_channel(message: types.Message):
    # Check if user is owner
    if message.from_user.username != OWNER_USERNAME:
        await message.reply("❌ Access denied! Only @Jayden_212 can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    limit = int(args[0]) if args and args[0].isdigit() else 50
    limit = min(limit, 100)
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT timestamp, event_type, username, chat_name, details FROM activity_log ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
        
        if not rows:
            await message.reply(f"📊 No logs found to send.")
            return
        
        # Send each log entry to channel
        sent_count = 0
        for row in reversed(rows):
            timestamp, event_type, username, chat_name, details = row
            emoji = {
                "join": "➕", "leave": "➖", "warn": "⚠️", "ban": "🚫", 
                "mute": "🔇", "kick": "👢", "unban": "✅", "unmute": "🔊",
                "gban": "🌍", "ungban": "🌍✅", "edit": "✏️"
            }.get(event_type, "📝")
            
            log_text = f"{emoji} <b>{event_type.upper()}</b>\n"
            log_text += f"👤 User: @{username or 'Unknown'} (ID: {row[3]})\n"
            log_text += f"💬 Chat: {chat_name or 'Private'}\n"
            log_text += f"📝 {details}\n"
            log_text += f"⏰ {timestamp}"
            
            try:
                await bot.send_message(LOG_CHANNEL_ID, log_text)
                sent_count += 1
                await asyncio.sleep(0.5)  # Avoid rate limiting
            except Exception as e:
                print(f"Failed to send log to channel: {e}")
        
        await message.reply(f"✅ Sent {sent_count} log entries to {LOG_CHANNEL_USERNAME}")

# Auto logs command - Enable/disable hourly automatic logs
@dp.message(Command("autologs"))
async def auto_logs_command(message: types.Message):
    # Check if user is owner
    if message.from_user.username != OWNER_USERNAME:
        await message.reply("❌ Access denied! Only @Jayden_212 can use this command.")
        return
    
    global owner_chat_id
    owner_chat_id = message.chat.id
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if args and args[0].lower() == "off":
        await message.reply("⏸️ Automatic hourly logs disabled.")
    else:
        await message.reply("▶️ Automatic hourly logs enabled. You'll receive updates every hour.")

# Send hourly automatic log report
async def send_hourly_logs():
    """Send automatic hourly log summary to owner"""
    global owner_chat_id
    
    if not owner_chat_id:
        return  # Owner chat ID not set yet
    
    try:
        # Get last hour's logs
        one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("""
                SELECT timestamp, event_type, username, chat_name, details 
                FROM activity_log 
                WHERE timestamp >= ? 
                ORDER BY id DESC
            """, (one_hour_ago,)) as cur:
                rows = await cur.fetchall()
            
            if not rows:
                # No activity in the last hour
                await bot.send_message(
                    owner_chat_id,
                    "⏰ <b>Hourly Activity Report</b>\n\n"
                    "📭 No activity in the last hour.\n"
                    f"⏰ Report time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                return
            
            # Count by type
            stats = {}
            for row in rows:
                event_type = row[1]
                stats[event_type] = stats.get(event_type, 0) + 1
            
            # Format summary
            log_text = f"⏰ <b>Hourly Activity Report</b>\n"
            log_text += f"📊 Summary of the last hour:\n\n"
            
            # Statistics
            for event_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                emoji = {"join": "➕", "leave": "➖", "warn": "⚠️", "ban": "🚫", 
                        "mute": "🔇", "kick": "👢", "unban": "✅", "unmute": "🔊"}.get(event_type, "📝")
                log_text += f"{emoji} <b>{event_type.capitalize()}</b>: {count}\n"
            
            log_text += f"\n📈 Total events: {len(rows)}\n"
            log_text += f"⏰ Report time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Recent activity (last 10)
            log_text += "<b>Recent Activity:</b>\n"
            for row in reversed(rows[-10:]):
                timestamp, event_type, username, chat_name, details = row
                emoji = {"join": "➕", "leave": "➖", "warn": "⚠️", "ban": "🚫", 
                        "mute": "🔇", "kick": "👢", "unban": "✅", "unmute": "🔊"}.get(event_type, "📝")
                log_text += f"{emoji} {event_type}: @{username or 'Unknown'} in {chat_name or 'Private'}\n"
            
            await bot.send_message(owner_chat_id, log_text)
    
    except Exception as e:
        print(f"Error sending hourly logs: {e}")

# Helper function to log activities
async def log_activity(event_type, user_id, username, chat_id=None, chat_name=None, details=""):
    """Log bot activities to database and log channel"""
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("""
            INSERT INTO activity_log (timestamp, event_type, user_id, username, chat_id, chat_name, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            event_type,
            user_id,
            username,
            chat_id,
            chat_name,
            details
        ))
        await db.commit()
    
    # Also send to log channel if configured
    try:
        await send_to_log_channel(event_type, user_id, username, chat_id, chat_name, details)
    except Exception as e:
        print(f"Error sending to log channel: {e}")

# Send activity to log channel
async def send_to_log_channel(event_type, user_id, username, chat_id, chat_name, details):
    """Send activity log to the log channel"""
    try:
        emoji = {
            "join": "➕", 
            "leave": "➖", 
            "warn": "⚠️", 
            "ban": "🚫", 
            "mute": "🔇", 
            "kick": "👢", 
            "unban": "✅", 
            "unmute": "🔊",
            "gban": "🌍",
            "ungban": "🌍✅",
            "edit": "✏️"
        }.get(event_type, "📝")
        
        log_text = f"{emoji} <b>{event_type.upper()}</b>\n"
        log_text += f"👤 User: @{username or 'Unknown'} (ID: {user_id})\n"
        if chat_id:
            log_text += f"💬 Chat: {chat_name or 'Private'} (ID: {chat_id})\n"
        log_text += f"📝 {details}\n"
        log_text += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await bot.send_message(LOG_CHANNEL_ID, log_text)
    except Exception as e:
        print(f"Failed to send to log channel: {e}")

# Blocklist Commands - For all chats
@dp.message(Command("blocklist"))
async def blocklist_command(message: types.Message):
    """Show blocklist for current chat"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT content_type, content_value, timestamp FROM blocklist WHERE chat_id = ? ORDER BY id DESC",
            (message.chat.id,)
        ) as cur:
            rows = await cur.fetchall()
    
    if not rows:
        await message.reply("📋 <b>Blocklist is empty</b>\n\nNo blocked items in this group.")
        return
    
    blocklist_text = "📋 <b>Current Blocklist:</b>\n\n"
    for i, (content_type, content_value, timestamp) in enumerate(rows, 1):
        emoji = {"text": "📝", "sticker": "🎭", "photo": "🖼️"}.get(content_type, "🚫")
        display_value = content_value[:50] + "..." if len(content_value) > 50 else content_value
        blocklist_text += f"{i}. {emoji} {content_type.upper()}: <code>{display_value}</code>\n"
    
    await message.reply(blocklist_text)

@dp.message(Command("addblock"))
async def add_block_command(message: types.Message):
    """Add item to blocklist"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply(
            "❌ Usage:\n"
            "<code>/addblock text word_to_block</code>\n"
            "<code>/addblock sticker</code> (reply to sticker)\n"
            "<code>/addblock photo</code> (reply to photo)"
        )
        return
    
    content_type = args[1].lower()
    
    if content_type not in ["text", "sticker", "photo"]:
        await message.reply("❌ Invalid type. Use: text, sticker, or photo")
        return
    
    if content_type == "text":
        content_value = args[2]
    elif content_type == "sticker" and message.reply_to_message and message.reply_to_message.sticker:
        content_value = message.reply_to_message.sticker.file_id
    elif content_type == "photo" and message.reply_to_message and message.reply_to_message.photo:
        content_value = message.reply_to_message.photo[-1].file_id
    else:
        await message.reply(f"❌ For sticker/photo, reply to the message with <code>/addblock {content_type}</code>")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute(
            "INSERT INTO blocklist (chat_id, content_type, content_value, added_by, timestamp) VALUES (?, ?, ?, ?, ?)",
            (message.chat.id, content_type, content_value, message.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()
    
    await message.reply(f"✅ Added <code>{content_value[:30]}</code> to blocklist.")
    await log_activity("block_add", message.from_user.id, message.from_user.username, message.chat.id, message.chat.title, f"Blocked {content_type}: {content_value[:30]}")

@dp.message(Command("removeblock"))
async def remove_block_command(message: types.Message):
    """Remove item from blocklist by ID"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.reply("❌ Usage: <code>/removeblock &lt;ID&gt;</code>\nUse /blocklist to see IDs.")
        return
    
    item_id = int(args[1])
    
    async with aiosqlite.connect("bio_guard.db") as db:
        cursor = await db.execute("SELECT content_type, content_value FROM blocklist WHERE chat_id = ? AND id = ?", (message.chat.id, item_id))
        row = await cursor.fetchone()
        
        if not row:
            await message.reply("❌ Item not found in blocklist.")
            return
        
        await db.execute("DELETE FROM blocklist WHERE chat_id = ? AND id = ?", (message.chat.id, item_id))
        await db.commit()
    
    await message.reply(f"✅ Removed blocklist item #{item_id}")
    await log_activity("block_remove", message.from_user.id, message.from_user.username, message.chat.id, message.chat.title, f"Removed block: {row[0]}")

# Auto-moderation for blocklist
@dp.message()
async def check_blocklist(message: types.Message):
    """Check messages against blocklist - applies to EVERYONE including owner"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # Skip if no blocklist for this chat
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT content_type, content_value FROM blocklist WHERE chat_id = ?", (message.chat.id,)) as cur:
            blocklist_items = await cur.fetchall()
    
    if not blocklist_items:
        return
    
    # Check text content
    text_to_check = message.text or ""
    if message.caption:
        text_to_check += "\n" + message.caption
    
    for content_type, block_content in blocklist_items:
        # Check text blocks
        if content_type == "text" and block_content.lower() in text_to_check.lower():
            try:
                await message.delete()
                # Give warning and apply penalty
                await give_blocklist_warning(message, block_content)
            except:
                pass
            return
        
        # Check stickers
        if content_type == "sticker" and message.sticker and message.sticker.file_id == block_content:
            try:
                await message.delete()
                await give_blocklist_warning(message, "sticker")
            except:
                pass
            return
        
        # Check photos
        if content_type == "photo" and message.photo:
            for photo in message.photo:
                if photo.file_id == block_content:
                    try:
                        await message.delete()
                        await give_blocklist_warning(message, "photo")
                    except:
                        pass
                    return

async def give_blocklist_warning(message: types.Message, blocked_content):
    """Give warning for blocklist violation with fixed message and penalty"""
    async with aiosqlite.connect("bio_guard.db") as db:
        # Get blocklist penalty settings (no need to fetch warning message anymore)
        async with db.execute("SELECT blocklist_warn_limit, blocklist_penalty FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty = 3, "mute"
            else:
                limit, penalty = row
        
        # Add warning count
        async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (message.chat.id, message.from_user.id)) as cur:
            warn_row = await cur.fetchone()
            if warn_row:
                count = warn_row[0] + 1
                await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", (count, message.chat.id, message.from_user.id))
            else:
                count = 1
                await db.execute("INSERT INTO warns VALUES (?, ?, ?)", (message.chat.id, message.from_user.id, count))
        await db.commit()
        
        # Send warning with FIXED message
        kb = InlineKeyboardBuilder()
        kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}_block")
        kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}_block")
        kb.adjust(2)
        
        try:
            # Use the fixed warning message
            fixed_warning_msg = "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ"
            warning_msg_formatted = f"⚠ {fixed_warning_msg}\n\n📊 ᴡᴀʀɴɪɴɢꜱ: {count}/{limit}"
            warning_message = await message.reply(warning_msg_formatted, reply_markup=kb.as_markup())
            
            # Auto-delete warning after 30 seconds
            async def delete_warning():
                await asyncio.sleep(30)
                try:
                    await warning_message.delete()
                except:
                    pass
            
            asyncio.create_task(delete_warning())
        except Exception as e:
            print(f"Error sending blocklist warning: {e}")
        
        # Log the warning
        await log_activity("block_warn", message.from_user.id, message.from_user.username, 
                         message.chat.id, message.chat.title, f"Warning {count}/{limit} - Blocked {blocked_content if isinstance(blocked_content, str) else 'content'}")
        
        # Apply penalty if limit reached
        if count >= limit:
            bot_member = await bot.get_chat_member(message.chat.id, bot.id)
            kb_penalty = InlineKeyboardBuilder()
            kb_penalty.adjust(1)
            action_taken = False
            
            if penalty == "mute" and bot_member.can_restrict_members:
                await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                             permissions=types.ChatPermissions(can_send_messages=False))
                kb_penalty.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
                action_taken = True
            elif penalty == "kick" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                await bot.unban_chat_member(message.chat.id, message.from_user.id)
                kb_penalty.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
                action_taken = True
            elif penalty == "ban" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                kb_penalty.button(text="🔓 Unban User", callback_data=f"unban_{message.from_user.id}")
                action_taken = True
            
            if action_taken:
                try:
                    action_msg = await message.reply(
                        f"🚨 <b>User {message.from_user.id}</b> has been {penalty}d after {limit} blocklist violations.",
                        reply_markup=kb_penalty.as_markup()
                    )
                    
                    # Auto-delete penalty message after 30 seconds
                    async def delete_penalty_success():
                        await asyncio.sleep(30)
                        try:
                            await action_msg.delete()
                        except:
                            pass
                    
                    asyncio.create_task(delete_penalty_success())
                except Exception as e:
                    print(f"Error applying blocklist penalty: {e}")

# ============================================================================
# FILTERS MODULE - Custom triggers and auto-replies
# ============================================================================

@dp.message(Command("filter"))
async def add_filter_command(message: types.Message):
    """Add a new filter to the chat"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    # Parse arguments
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply(
            "❌ Usage:\n"
            "<code>/filter \"trigger phrase\" \"reply message\"</code>\n\n"
            "Example:\n"
            "<code>/filter hello Hi there! How are you?</code>"
        )
        return
    
    trigger = args[1].strip('"\'')
    reply = args[2].strip('"\'')
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute(
            "INSERT INTO filters (chat_id, trigger_text, reply_text, added_by, timestamp) VALUES (?, ?, ?, ?, ?)",
            (message.chat.id, trigger.lower(), reply, message.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        await db.commit()
    
    await message.reply(f"✅ Filter added!\nTrigger: <code>{trigger}</code>\nReply: <i>{reply}</i>")
    await log_activity("filter_add", message.from_user.id, message.from_user.username, 
                      message.chat.id, message.chat.title, f"Added filter: {trigger[:30]}")

@dp.message(Command("filters"))
async def list_filters_command(message: types.Message):
    """List all filters in the chat"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT trigger_text, reply_text, timestamp FROM filters WHERE chat_id = ? ORDER BY id DESC",
            (message.chat.id,)
        ) as cur:
            rows = await cur.fetchall()
    
    if not rows:
        await message.reply("📋 <b>No filters set</b>\n\nNo custom filters in this group.")
        return
    
    filters_text = "📋 <b>Active Filters:</b>\n\n"
    for i, (trigger, reply, timestamp) in enumerate(rows, 1):
        display_trigger = trigger[:40] + "..." if len(trigger) > 40 else trigger
        display_reply = reply[:50] + "..." if len(reply) > 50 else reply
        filters_text += f"{i}. <b>Trigger:</b> <code>{display_trigger}</code>\n   <b>Reply:</b> <i>{display_reply}</i>\n\n"
    
    await message.reply(filters_text)

@dp.message(Command("stop"))
async def stop_filter_command(message: types.Message):
    """Remove a specific filter"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ Usage: <code>/stop &lt;trigger&gt;</code>")
        return
    
    trigger = args[1].strip('"\'').lower()
    
    async with aiosqlite.connect("bio_guard.db") as db:
        cursor = await db.execute("SELECT trigger_text FROM filters WHERE chat_id = ? AND LOWER(trigger_text) = ?", 
                                 (message.chat.id, trigger))
        row = await cursor.fetchone()
        
        if not row:
            await message.reply("❌ Filter not found.")
            return
        
        await db.execute("DELETE FROM filters WHERE chat_id = ? AND LOWER(trigger_text) = ?", (message.chat.id, trigger))
        await db.commit()
    
    await message.reply(f"✅ Filter <code>{trigger}</code> removed.")
    await log_activity("filter_remove", message.from_user.id, message.from_user.username, 
                      message.chat.id, message.chat.title, f"Removed filter: {trigger}")

@dp.message(Command("stopall"))
async def stop_all_filters_command(message: types.Message):
    """Remove all filters"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM filters WHERE chat_id = ?", (message.chat.id,))
        count_row = await cursor.fetchone()
        count = count_row[0]
        
        if count == 0:
            await message.reply("📋 No filters to remove.")
            return
        
        await db.execute("DELETE FROM filters WHERE chat_id = ?", (message.chat.id,))
        await db.commit()
    
    await message.reply(f"✅ Removed all {count} filters. This cannot be undone!")
    await log_activity("filter_remove_all", message.from_user.id, message.from_user.username, 
                      message.chat.id, message.chat.title, f"Removed {count} filters")

@dp.message()
async def check_filters(message: types.Message):
    """Check messages against filters and reply"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    if not message.text:
        return
    
    # Skip if sender is a bot
    if message.from_user.is_bot:
        return
    
    text_lower = message.text.lower()
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT trigger_text, reply_text FROM filters WHERE chat_id = ?", (message.chat.id,)) as cur:
            filters = await cur.fetchall()
    
    for trigger, reply in filters:
        # Check if trigger is in the message (as whole word or phrase)
        if trigger.lower() in text_lower:
            try:
                await message.reply(reply)
                await log_activity("filter_trigger", message.from_user.id, message.from_user.username, 
                                 message.chat.id, message.chat.title, f"Filter triggered: {trigger[:30]}")
            except Exception as e:
                print(f"Error replying with filter: {e}")
            break

# ============================================================================
# LOCKS MODULE - Lock various message types
# ============================================================================

# Lockable items and their types
LOCK_TYPES = {
    "sticker": "sticker",
    "stickers": "sticker",
    "photo": "photo",
    "photos": "photo", 
    "image": "photo",
    "images": "photo",
    "video": "video",
    "videos": "video",
    "audio": "audio",
    "music": "audio",
    "voice": "voice",
    "document": "document",
    "file": "document",
    "files": "document",
    "link": "url",
    "links": "url",
    "url": "url",
    "urls": "url",
    "invite": "invite",
    "invites": "invite",
    "invitelink": "invite",
    "invitelinks": "invite",
    "forward": "forward",
    "forwards": "forward",
    "inline": "inline",
    "command": "command",
    "commands": "command",
    "emoji": "emoji",
    "emojis": "emoji",
}

@dp.message(Command("lock"))
async def lock_command(message: types.Message):
    """Lock one or more item types"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.reply(
            "❌ Usage: <code>/lock &lt;item(s)&gt;</code>\n\n"
            "Examples:\n"
            "<code>/lock sticker</code>\n"
            "<code>/lock photo video</code>\n"
            "<code>/lock link forward invite</code>\n\n"
            "Use /locktypes to see all lockable items."
        )
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        for item in args:
            item_lower = item.lower()
            lock_type = LOCK_TYPES.get(item_lower)
            
            if not lock_type:
                continue
            
            # Check if already locked
            cursor = await db.execute(
                "SELECT enabled FROM locks WHERE chat_id = ? AND lock_type = ?",
                (message.chat.id, lock_type)
            )
            row = await cursor.fetchone()
            
            if row and row[0] == 1:
                continue  # Already locked
            
            # Insert or update lock
            await db.execute("""
                INSERT INTO locks (chat_id, lock_type, enabled, warn_enabled, updated_by, timestamp)
                VALUES (?, ?, 1, 1, ?, ?)
                ON CONFLICT(chat_id, lock_type) DO UPDATE SET
                enabled = 1,
                warn_enabled = 1,
                updated_by = ?,
                timestamp = ?
            """, (message.chat.id, lock_type, message.from_user.id, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  message.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        await db.commit()
    
    locked_items = [item for item in args if LOCK_TYPES.get(item.lower())]
    if locked_items:
        await message.reply(f"🔒 Locked: <code>{', '.join(locked_items)}</code>")
        await log_activity("lock_add", message.from_user.id, message.from_user.username,
                          message.chat.id, message.chat.title, f"Locked: {', '.join(locked_items)}")
    else:
        await message.reply("❌ No valid lock types specified. Use /locktypes to see available types.")

@dp.message(Command("unlock"))
async def unlock_command(message: types.Message):
    """Unlock one or more item types"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.reply(
            "❌ Usage: <code>/unlock &lt;item(s)&gt;</code>\n\n"
            "Examples:\n"
            "<code>/unlock sticker</code>\n"
            "<code>/unlock photo video</code>"
        )
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        for item in args:
            item_lower = item.lower()
            lock_type = LOCK_TYPES.get(item_lower)
            
            if not lock_type:
                continue
            
            # Update or insert as unlocked
            await db.execute("""
                INSERT INTO locks (chat_id, lock_type, enabled, warn_enabled, updated_by, timestamp)
                VALUES (?, ?, 0, 1, ?, ?)
                ON CONFLICT(chat_id, lock_type) DO UPDATE SET
                enabled = 0,
                updated_by = ?,
                timestamp = ?
            """, (message.chat.id, lock_type, message.from_user.id,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  message.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        await db.commit()
    
    unlocked_items = [item for item in args if LOCK_TYPES.get(item.lower())]
    if unlocked_items:
        await message.reply(f"🔓 Unlocked: <code>{', '.join(unlocked_items)}</code>")
        await log_activity("lock_remove", message.from_user.id, message.from_user.username,
                          message.chat.id, message.chat.title, f"Unlocked: {', '.join(unlocked_items)}")
    else:
        await message.reply("❌ No valid unlock types specified.")

@dp.message(Command("locks"))
async def list_locks_command(message: types.Message):
    """List currently locked items"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT lock_type, enabled, warn_enabled FROM locks WHERE chat_id = ? ORDER BY id",
            (message.chat.id,)
        ) as cur:
            rows = await cur.fetchall()
    
    if not rows:
        await message.reply("🔓 <b>No locks set</b>\n\nNo items are currently locked in this group.")
        return
    
    locks_text = "🔒 <b>Current Locks:</b>\n\n"
    for lock_type, enabled, warn_enabled in rows:
        status = "🔒 Locked" if enabled else "🔓 Unlocked"
        warns = "(warns enabled)" if warn_enabled else "(warns disabled)"
        locks_text += f"• {lock_type.upper()}: {status} {warns}\n"
    
    await message.reply(locks_text)

@dp.message(Command("lockwarns"))
async def lock_warns_command(message: types.Message):
    """Enable or disable warnings for locked items"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.reply(
            "❌ Usage: <code>/lockwarns &lt;yes/no/on/off&gt;</code>\n\n"
            "Enable or disable whether users should be warned when using locked items."
        )
        return
    
    enable = args[0].lower() in ["yes", "on", "enable", "true"]
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute(
            "UPDATE locks SET warn_enabled = ? WHERE chat_id = ?",
            (1 if enable else 0, message.chat.id)
        )
        await db.commit()
    
    status = "enabled" if enable else "disabled"
    await message.reply(f"✅ Lock warnings {status}.")
    await log_activity("lock_setting_change", message.from_user.id, message.from_user.username,
                      message.chat.id, message.chat.title, f"Lock warnings {status}")

@dp.message(Command("locktypes"))
async def locktypes_command(message: types.Message):
    """Show list of all lockable items"""
    lock_types_list = sorted(set(LOCK_TYPES.keys()))
    
    types_text = "🔒 <b>Lockable Items:</b>\n\n"
    categories = {
        "Media": ["sticker", "photo", "video", "audio", "voice", "document"],
        "Links": ["link", "url", "invite", "invitelink"],
        "Actions": ["forward", "inline", "command", "emoji"]
    }
    
    for category, items in categories.items():
        available = [item for item in items if item in lock_types_list]
        if available:
            types_text += f"<b>{category}:</b>\n"
            types_text += ", ".join(available) + "\n\n"
    
    types_text += "\nUse <code>/lock &lt;item&gt;</code> to lock any of these items."
    
    await message.reply(types_text)

@dp.message(Command("allowlist"))
async def allowlist_command(message: types.Message):
    """Add items to allowlist or show current allowlist"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        # Show current allowlist
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute(
                "SELECT item_value, item_type FROM allowlist WHERE chat_id = ? ORDER BY id",
                (message.chat.id,)
            ) as cur:
                rows = await cur.fetchall()
        
        if not rows:
            await message.reply("📋 <b>Allowlist is empty</b>\n\nNo items are allowlisted.")
            return
        
        allowlist_text = "✅ <b>Current Allowlist:</b>\n\n"
        for item_value, item_type in rows:
            allowlist_text += f"• {item_type}: <code>{item_value}</code>\n"
        
        await message.reply(allowlist_text)
        return
    
    # Add items to allowlist
    async with aiosqlite.connect("bio_guard.db") as db:
        for item in args:
            # Determine item type
            if item.startswith("@"):
                item_type = "username"
            elif item.startswith("/") or item.startswith("!"):
                item_type = "command"
            elif item.startswith("http") or "t.me" in item or "telegram.me" in item:
                item_type = "url"
            elif item.isdigit():
                item_type = "id"
            else:
                item_type = "other"
            
            await db.execute(
                "INSERT INTO allowlist (chat_id, item_value, item_type, added_by, timestamp) VALUES (?, ?, ?, ?, ?)",
                (message.chat.id, item, item_type, message.from_user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
        
        await db.commit()
    
    await message.reply(f"✅ Added {len(args)} item(s) to allowlist.")
    await log_activity("allowlist_add", message.from_user.id, message.from_user.username,
                      message.chat.id, message.chat.title, f"Added {len(args)} items to allowlist")

@dp.message(Command("rmallowlist"))
async def remove_allowlist_command(message: types.Message):
    """Remove items from allowlist"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if not args:
        await message.reply("❌ Usage: <code>/rmallowlist &lt;item(s)&gt;</code>")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        removed_count = 0
        for item in args:
            cursor = await db.execute(
                "DELETE FROM allowlist WHERE chat_id = ? AND item_value = ?",
                (message.chat.id, item)
            )
            if cursor.rowcount > 0:
                removed_count += 1
        
        await db.commit()
    
    if removed_count > 0:
        await message.reply(f"✅ Removed {removed_count} item(s) from allowlist.")
        await log_activity("allowlist_remove", message.from_user.id, message.from_user.username,
                          message.chat.id, message.chat.title, f"Removed {removed_count} items")
    else:
        await message.reply("❌ No matching items found in allowlist.")

@dp.message(Command("rmallowlistall"))
async def remove_all_allowlist_command(message: types.Message):
    """Remove all allowlisted items"""
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply("This command can only be used in groups.")
        return
    
    # Check if user is admin/creator
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await message.reply("❌ Only administrators can use this command.")
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM allowlist WHERE chat_id = ?", (message.chat.id,))
        count_row = await cursor.fetchone()
        count = count_row[0]
        
        if count == 0:
            await message.reply("📋 No allowlisted items to remove.")
            return
        
        await db.execute("DELETE FROM allowlist WHERE chat_id = ?", (message.chat.id,))
        await db.commit()
    
    await message.reply(f"✅ Removed all {count} allowlisted items.")
    await log_activity("allowlist_remove_all", message.from_user.id, message.from_user.username,
                      message.chat.id, message.chat.title, f"Removed all {count} allowlist items")

@dp.message()
async def check_locks(message: types.Message):
    """Check messages against locks and delete if locked"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # Skip bots
    if message.from_user and message.from_user.is_bot:
        return
    
    # Get all active locks for this chat
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT lock_type, warn_enabled FROM locks WHERE chat_id = ? AND enabled = 1",
            (message.chat.id,)
        ) as cur:
            locks = await cur.fetchall()
        
        # Get allowlist
        async with db.execute(
            "SELECT item_value FROM allowlist WHERE chat_id = ?",
            (message.chat.id,)
        ) as cur:
            allowlist_rows = await cur.fetchall()
            allowlist = [row[0] for row in allowlist_rows]
    
    if not locks:
        return
    
    # Check each lock type
    for lock_type, warn_enabled in locks:
        should_delete = False
        
        # Sticker lock
        if lock_type == "sticker" and message.sticker:
            if message.sticker.file_id not in allowlist:
                should_delete = True
        
        # Photo lock
        elif lock_type == "photo" and message.photo:
            should_delete = True
        
        # Video lock
        elif lock_type == "video" and message.video:
            should_delete = True
        
        # Audio lock
        elif lock_type == "audio" and message.audio:
            should_delete = True
        
        # Voice lock
        elif lock_type == "voice" and message.voice:
            should_delete = True
        
        # Document lock
        elif lock_type == "document" and message.document:
            should_delete = True
        
        # URL lock
        elif lock_type == "url":
            text = message.text or message.caption or ""
            if any(url in text for url in ["http://", "https://", "www."]):
                if not any(allowed in text for allowed in allowlist):
                    should_delete = True
        
        # Invite link lock
        elif lock_type == "invite":
            text = message.text or message.caption or ""
            if any(invite in text for invite in ["t.me/joinchat/", "t.me/+"]):
                should_delete = True
        
        # Forward lock
        elif lock_type == "forward" and message.forward_from:
            should_delete = True
        
        # Inline query lock
        elif lock_type == "inline" and message.via_bot:
            should_delete = True
        
        # Command lock
        elif lock_type == "command" and message.text and message.text.startswith("/"):
            command = message.text.split()[0][1:]
            if f"/{command}" not in allowlist and command not in allowlist:
                should_delete = True
        
        # Emoji lock (basic implementation)
        elif lock_type == "emoji" and message.text:
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"
                u"\U0001F300-\U0001F5FF"
                u"\U0001F680-\U0001F6FF"
                u"\U0001F1E0-\U0001F1FF"
                "]+", flags=re.UNICODE)
            if emoji_pattern.search(message.text):
                should_delete = True
        
        if should_delete:
            try:
                await message.delete()
                
                # Send warning if enabled
                if warn_enabled:
                    try:
                        warning = await message.reply(
                            f"⚠️ This type of message is locked in this group."
                        )
                        asyncio.create_task(delete_after_delay(warning, 30))
                    except:
                        pass
                
                await log_activity("lock_trigger", message.from_user.id if message.from_user else 0,
                                 message.from_user.username if message.from_user else "Unknown",
                                 message.chat.id, message.chat.title, f"Deleted locked content: {lock_type}")
            except Exception as e:
                print(f"Error deleting locked content: {e}")
            break

async def delete_after_delay(message, delay):
    """Delete message after delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# Bio checking logic - Improved detection
bio_pattern = re.compile(r"(https?://|t\.me/|@\w+|telegram\.me/|t\.me/joinchat/|t\.me/\+|telegram\.dog/)", re.IGNORECASE)

async def check_bio(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    try:
        # Get user's bio with proper error handling
        user = await bot.get_chat(message.from_user.id)
        bio = user.bio or ""
        
        # Debug logging (can be removed in production)
        print(f"User {message.from_user.id} bio: '{bio}'")
        
        # Check if bio is empty
        if not bio or len(bio.strip()) == 0:
            print(f"Bio is empty for user {message.from_user.id}")
            return
        
        # Check for links in bio
        if not bio_pattern.search(bio):
            print(f"No link pattern found in bio for user {message.from_user.id}")
            return
            
        print(f"✅ Bio link detected for user {message.from_user.id}: '{bio}'")
        
    except Exception as e:
        print(f"❌ Error getting user bio: {e}")
        return

    async with aiosqlite.connect("bio_guard.db") as db:
        # Get settings
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, bio_checker_enabled) VALUES (?, ?, ?, ?, ?)", 
                               (message.chat.id, 3, "mute", "members", 1))
                await db.commit()
                limit, penalty, apply_to, bio_checker_enabled = 3, "mute", "members", 1
            else:
                limit, penalty, apply_to, bio_checker_enabled = row
        
        # Check if bio checker is enabled
        if bio_checker_enabled == 0:
            print(f"Bio checker is disabled for chat {message.chat.id}")
            return
        
        # Check if user should be affected based on settings
        try:
            chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
            user_status = chat_member.status
            
            # Apply filtering based on settings
            should_apply = False
            
            if apply_to == "members":
                # Only apply to regular members (not admins/creators)
                if user_status in ["member", "left"]:
                    should_apply = True
            elif apply_to == "admins":
                # Only apply to administrators and creators
                if user_status in ["administrator", "creator"]:
                    should_apply = True
            elif apply_to == "members_and_admins":
                # Apply to both members and admins (everyone except left members)
                if user_status in ["member", "administrator", "creator"]:
                    should_apply = True
            elif apply_to == "everyone":
                # Apply to everyone including bots and all statuses
                should_apply = True
            
            # Exit if this setting doesn't apply to this user
            if not should_apply:
                print(f"Bio detection skipped for user {message.from_user.id} (status: {user_status}, apply_to: {apply_to})")
                return
        except Exception as e:
            print(f"Error checking user status: {e}")
            return
        
        # Add warning
        async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (message.chat.id, message.from_user.id)) as cur:
            row = await cur.fetchone()
            if row:
                count = row[0] + 1
                await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", (count, message.chat.id, message.from_user.id))
            else:
                count = 1
                await db.execute("INSERT INTO warns VALUES (?, ?, ?)", (message.chat.id, message.from_user.id, count))
        await db.commit()
        
        # Send warning with custom format and buttons
        kb = InlineKeyboardBuilder()
        kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}_bio")
        kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}_bio")
        kb.adjust(2)
        
        try:
            warning_msg = await message.reply(
                f"⚠ ʏᴏᴜʀ ʙɪᴏ ᴄᴏɴᴛᴀɪɴ ʟɪɴᴋ . ᴘʟᴇᴀꜱᴇ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ʟɪɴᴋ ꜰʀᴏᴍ ʙɪᴏ ᴀɴᴅ ᴛʜᴇɴ ᴍᴇꜱꜱᴀɢᴇ ʜᴇʀᴇ\n\n"
                f"📊 ᴡᴀʀɴɪɴɢꜱ: {count}/{limit}",
                reply_markup=kb.as_markup()
            )
            print(f"✅ Warning sent to user {message.from_user.id}")
        except Exception as e:
            print(f"❌ Error sending warning message: {e}")
            return
        
        # Log the warning
        await log_activity(
            event_type="warn",
            user_id=message.from_user.id,
            username=message.from_user.username or "Unknown",
            chat_id=message.chat.id,
            chat_name=message.chat.title,
            details=f"Warning {count}/{limit} - Bio contains link"
        )
        
        # Auto-delete warning after 30 seconds (shorter time for better UX)
        async def delete_warning():
            await asyncio.sleep(30)
            try:
                await warning_msg.delete()
            except:
                pass
        
        asyncio.create_task(delete_warning())
        
        # Auto-delete bot's own message after 30 seconds
        async def delete_bot_message():
            await asyncio.sleep(30)
            try:
                await message.delete()
            except:
                pass
        
        asyncio.create_task(delete_bot_message())

        # Apply penalty if limit reached
        if count >= limit:
            bot_member = await bot.get_chat_member(message.chat.id, bot.id)
            kb = InlineKeyboardBuilder()
            kb.adjust(1)
            action_taken = False
            
            if penalty == "mute" and bot_member.can_restrict_members:
                await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                             permissions=types.ChatPermissions(can_send_messages=False))
                kb.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
                action_taken = True
            elif penalty == "kick" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                await bot.unban_chat_member(message.chat.id, message.from_user.id)
                kb.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
                action_taken = True
            elif penalty == "ban" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                kb.button(text="🔓 Unban User", callback_data=f"unban_{message.from_user.id}")
                action_taken = True
            
            if action_taken:
                action_msg = await message.reply(
                    f"🚨 <b>User {message.from_user.id}</b> has been {penalty}d after {limit} warnings.",
                    reply_markup=kb.as_markup()
                )
                
                # Auto-delete penalty success message
                async def delete_penalty_success():
                    await asyncio.sleep(30)
                    try:
                        await action_msg.delete()
                    except:
                        pass
                
                asyncio.create_task(delete_penalty_success())
            else:
                action_msg = await message.reply(
                    f"🚨 <b>User {message.from_user.id}</b> reached {limit} warnings but bot doesn't have permission to {penalty}."
                )
            
            async def delete_action():
                await asyncio.sleep(30)  # Shorter time for better UX
                try:
                    await action_msg.delete()
                except:
                    pass
            
            asyncio.create_task(delete_action())

# Global ban check logic
async def check_global_ban(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return False

    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT reason FROM global_bans WHERE user_id = ?", (message.from_user.id,)) as cur:
            row = await cur.fetchone()
            if row:
                reason = row[0]
                try:
                    # Ban the user from the current group
                    await bot.ban_chat_member(message.chat.id, message.from_user.id)
                    await message.reply(f"🚫 <b>ɢʟᴏʙᴀʟ ʙᴀɴ ᴅᴇᴛᴇᴄᴛᴇᴅ</b>\n\n👤 ᴜsᴇʀ: @{message.from_user.username or 'NoUsername'}\n📝 ʀᴇᴀsᴏɴ: {reason}\n\n<i>ᴛʜɪs ᴜsᴇʀ ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.</i>")
                    await log_activity("gban_auto", message.from_user.id, message.from_user.username, message.chat.id, message.chat.title, f"Auto-banned due to global ban: {reason}")
                    return True
                except Exception as e:
                    print(f"Error auto-banning globally banned user: {e}")
    return False

# Monitor all messages and bio changes
@dp.message()
async def monitor(message: types.Message):
    if await check_global_ban(message):
        return
    await check_bio(message)
    await check_self_destruct(message)

async def check_self_destruct(message: types.Message):
    """Check if self-destruct is enabled and schedule message deletion"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # Skip bot messages
    if message.from_user and message.from_user.is_bot:
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return
            
            enabled, destruct_time = row
            
            # If self-destruct is disabled, skip
            if enabled != 1:
                return
            
            # Schedule message deletion after configured time
            try:
                asyncio.create_task(delete_message_after_delay(message, destruct_time))
                print(f"✅ Self-destruct scheduled for message in chat {message.chat.id} after {destruct_time}s")
            except Exception as e:
                print(f"❌ Error scheduling self-destruct: {e}")

async def delete_message_after_delay(message, delay):
    """Delete message after specified delay in seconds"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
        print(f"✅ Self-destructed message after {delay}s")
    except Exception as e:
        print(f"❌ Error deleting self-destruct message: {e}")

# Monitor edited messages
@dp.edited_message()
async def monitor_edited_message(message: types.Message):
    """Detect when users edit their messages and warn them"""
    if await check_global_ban(message):
        return
    
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # Get settings - use ONLY edit checker settings, not bio settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, edit_checker, edit_apply_to, edit_penalty FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty, edit_checker, edit_apply_to, edit_penalty = 3, "mute", 1, "members", "mute"
            else:
                limit, penalty, edit_checker, edit_apply_to, edit_penalty = row
    
    # Use edit_penalty for edit checker, fallback to regular penalty if not set
    effective_penalty = edit_penalty if edit_penalty else penalty
    
    # Check if edit checker is enabled
    if edit_checker == 0:
        return
    
    # Check user status for edit checker
    try:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        user_status = chat_member.status
        
        should_apply = False
        if edit_apply_to == "members":
            if user_status in ["member", "left"]:
                should_apply = True
        elif edit_apply_to == "admins":
            if user_status in ["administrator", "creator"]:
                should_apply = True
        elif edit_apply_to == "members_and_admins":
            if user_status in ["member", "administrator", "creator"]:
                should_apply = True
        elif edit_apply_to == "everyone":
            # Apply to EVERYONE including owner when set to everyone
            should_apply = True
            
        if not should_apply:
            return
            
    except Exception as e:
        print(f"Error checking status for edit: {e}")
        # Default to apply if check fails? Or skip? Let's skip to be safe.
        return
    
    # Delete the edited message
    try:
        await message.delete()
        print(f"✅ Deleted edited message from user {message.from_user.id}")
    except Exception as e:
        print(f"❌ Error deleting edited message: {e}")
        # Bot needs admin rights with delete permission
        return
    
    # Check if penalty is "warn only" - don't count warnings
    if effective_penalty == "warn":
        # Just send a warning without counting
        try:
            warning_msg = await message.answer(
                f"⚠️ <b>ᴇᴅɪᴛᴛɪɴɢ ɪꜱ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ!</b>\n\n"
                f"<i>ᴘʟᴇᴀsᴇ ᴅᴏ ɴᴏᴛ ᴇᴅɪᴛ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.</i>"
            )
            print(f"✅ Sent warn-only message for edited message to {message.from_user.id}")
        except Exception as e:
            print(f"❌ Error sending warning: {e}")
        
        # Log the warning
        await log_activity(
            event_type="warn",
            user_id=message.from_user.id,
            username=message.from_user.username or "Unknown",
            chat_id=message.chat.id,
            chat_name=message.chat.title,
            details=f"Warn only - Edited message"
        )
        
        print(f"✅ Edit checker logged: User {message.from_user.id} warned for editing (warn only, no count)")
        
        # Auto-delete warning after 30 seconds
        async def delete_warning():
            await asyncio.sleep(30)
            try:
                await warning_msg.delete()
            except:
                pass
        
        asyncio.create_task(delete_warning())
        return  # Exit early, no warning count added
    
    # Update warning count (only if not warn-only)
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", 
                            (message.chat.id, message.from_user.id)) as cur:
            row = await cur.fetchone()
            if row:
                count = row[0] + 1
                await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", 
                               (count, message.chat.id, message.from_user.id))
            else:
                count = 1
                await db.execute("INSERT INTO warns VALUES (?, ?, ?)", 
                               (message.chat.id, message.from_user.id, count))
        await db.commit()
    
    # Send warning message with buttons (only if not warn-only)
    kb = InlineKeyboardBuilder()
    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}_edit")
    kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}_edit")
    kb.adjust(2)
    
    try:
        warning_msg = await message.answer(
            f"⚠️ <b>ᴇᴅɪᴛᴛɪɴɢ ɪꜱ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ!</b>\n\n"
            f"📊 ᴡᴀʀɴɪɴɢꜱ: {count}/{limit}\n\n"
            f"<i>ᴘʟᴇᴀsᴇ ᴅᴏ ɴᴏᴛ ᴇᴅɪᴛ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.</i>",
            reply_markup=kb.as_markup()
        )
        print(f"✅ Sent warning message for edited message to {message.from_user.id}")
    except Exception as e:
        print(f"❌ Error sending warning: {e}")
    
    # Log the warning
    await log_activity(
        event_type="warn",
        user_id=message.from_user.id,
        username=message.from_user.username or "Unknown",
        chat_id=message.chat.id,
        chat_name=message.chat.title,
        details=f"Warning {count}/{limit} - Edited message"
    )
    
    print(f"✅ Edit checker logged: User {message.from_user.id} warned for editing")
    
    # Auto-delete warning after 30 seconds
    async def delete_warning():
        await asyncio.sleep(30)
        try:
            await warning_msg.delete()
        except:
            pass
    
    asyncio.create_task(delete_warning())
    
    # Apply penalty if limit reached
    if count >= limit:
        bot_member = await bot.get_chat_member(message.chat.id, bot.id)
        penalty_kb = InlineKeyboardBuilder()
        penalty_kb.adjust(1)
        
        # Check if penalty is "warn only" - no action needed
        if effective_penalty == "warn":
            await message.answer(f"⚠️ User {message.from_user.id} reached warning limit ({count}/{limit}) but penalty is set to 'warn only' - no action taken.")
        elif effective_penalty == "mute" and bot_member.can_restrict_members:
            await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                         permissions=types.ChatPermissions(can_send_messages=False))
            penalty_kb.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
            await message.answer(f"⚠️ User {message.from_user.id} muted! Reached warning limit ({count}/{limit}).", 
                               reply_markup=penalty_kb.as_markup())
        elif effective_penalty == "kick" and bot_member.can_restrict_members:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            await bot.unban_chat_member(message.chat.id, message.from_user.id)
            penalty_kb.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
            await message.answer(f"⚠️ User {message.from_user.id} kicked! Reached warning limit ({count}/{limit}).", 
                               reply_markup=penalty_kb.as_markup())
        elif effective_penalty == "ban" and bot_member.can_restrict_members:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            penalty_kb.button(text="🔓 Unban User", callback_data=f"unban_{message.from_user.id}")
            await message.answer(f"⚠️ User {message.from_user.id} banned! Reached warning limit ({count}/{limit}).", 
                               reply_markup=penalty_kb.as_markup())

# Monitor chat member updates (join/leave)
@dp.chat_member()
async def on_chat_member_update(message: types.ChatMemberUpdated):
    """Track when users join or leave groups"""
    old_member = message.old_chat_member
    new_member = message.new_chat_member
    
    # User joined
    if old_member.status == ChatMemberStatus.LEFT and new_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        username = new_member.user.username or "Unknown"
        await log_activity(
            event_type="join",
            user_id=new_member.user.id,
            username=username,
            chat_id=message.chat.id,
            chat_name=message.chat.title,
            details=f"Joined as {new_member.status}"
        )
    
    # User left
    elif new_member.status == ChatMemberStatus.LEFT:
        username = old_member.user.username or "Unknown"
        await log_activity(
            event_type="leave",
            user_id=old_member.user.id,
            username=username,
            chat_id=message.chat.id,
            chat_name=message.chat.title,
            details=f"Left group (was {old_member.status})"
        )

# Callback handler for Settings button
@dp.callback_query(lambda c: c.data == "bio_checker_menu")
async def bio_checker_menu_callback(call: types.CallbackQuery):
    await call.answer("Opening Bio Checker settings...")
    
    # Get bio checker settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty, apply_to, bio_checker_enabled = 3, "mute", "members", 1
            else:
                limit, penalty, apply_to, bio_checker_enabled = row
    
    kb = InlineKeyboardBuilder()
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    
    # Bio Checker specific settings
    kb.button(text=f"🧬 Toggle: {bio_status}", callback_data="toggle_bio_checker")
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    kb.button(text="↩️ Back", callback_data="back_to_main_settings")
    kb.adjust(2, 2, 1)
    
    await call.message.edit_text(
        "🧬 <b>Bio Checker Settings</b>\n\n"
        "Configure bio link monitoring:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "edit_checker_menu")
async def edit_checker_menu_callback(call: types.CallbackQuery):
    await call.answer("Opening Edit Checker settings...")
    
    # Get edit checker settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, edit_penalty, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, edit_penalty, edit_checker, edit_apply_to = 3, "mute", 1, "members"
            else:
                limit, edit_penalty, edit_checker, edit_apply_to = row
    
    kb = InlineKeyboardBuilder()
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    
    # Edit Checker specific settings
    kb.button(text=f"✏️ Toggle: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {edit_penalty}", callback_data="change_edit_penalty")
    kb.button(text=f"👥 Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    kb.button(text="↩️ Back", callback_data="back_to_main_settings")
    kb.adjust(2, 2, 1)
    
    await call.message.edit_text(
        "✏️ <b>Edit Checker Settings</b>\n\n"
        "Configure message edit monitoring:",
        reply_markup=kb.as_markup()
    )


@dp.callback_query(lambda c: c.data == "self_destruct_menu")
async def self_destruct_menu_callback(call: types.CallbackQuery):
    await call.answer("Opening Self Destruct settings...")
    
    # Get self destruct settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                enabled, destruct_time = 0, 60
            else:
                enabled, destruct_time = row
    
    kb = InlineKeyboardBuilder()
    destruct_status = "ON ✅" if enabled == 1 else "OFF ❌"
    
    # Convert seconds to hours, minutes, seconds
    hours = destruct_time // 3600
    minutes = (destruct_time % 3600) // 60
    seconds = destruct_time % 60
    
    # Self Destruct specific settings
    kb.button(text=f"💣 Toggle: {destruct_status}", callback_data="toggle_self_destruct")
    kb.button(text=f"⏱️ Hours: {hours}", callback_data="sd_hours_display")
    kb.button(text=f"▲ + Hour", callback_data="sd_hours_up")
    kb.button(text=f"▼ - Hour", callback_data="sd_hours_down")
    kb.button(text=f"⏱️ Minutes: {minutes}", callback_data="sd_minutes_display")
    kb.button(text=f"▲ + Min", callback_data="sd_minutes_up")
    kb.button(text=f"▼ - Min", callback_data="sd_minutes_down")
    kb.button(text=f"⏱️ Seconds: {seconds}", callback_data="sd_seconds_display")
    kb.button(text=f"▲ + Sec", callback_data="sd_seconds_up")
    kb.button(text=f"▼ - Sec", callback_data="sd_seconds_down")
    kb.button(text="↩️ Back", callback_data="back_to_main_settings")
    kb.adjust(3, 3, 3, 1)
    
    time_display = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    await call.message.edit_text(
        f"💣 <b>Self Destruct Settings</b>\n\n"
        f"Auto-delete all messages after: <b>{time_display}</b>\n\n"
        f"<i>Messages will be automatically deleted after the specified time</i>",
        reply_markup=kb.as_markup()
    )



@dp.callback_query(lambda c: c.data == "toggle_self_destruct")
async def toggle_self_destruct_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_enabled FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_status = row[0]
                new_status = 0 if current_status == 1 else 1
                await db.execute("UPDATE settings SET self_destruct_enabled=? WHERE chat_id=?", (new_status, call.message.chat.id))
                await db.commit()
                await self_destruct_menu_callback(call)
                status_text = "Enabled" if new_status == 1 else "Disabled"
                await call.answer(f"✅ Self Destruct {status_text}")
            else:
                await db.execute("INSERT INTO settings (chat_id, self_destruct_enabled, self_destruct_time) VALUES (?, ?, ?)", 
                               (call.message.chat.id, 1, 60))
                await db.commit()
                await self_destruct_menu_callback(call)
                await call.answer("✅ Self Destruct Enabled")



@dp.callback_query(lambda c: c.data == "sd_hours_up")
async def sd_hours_up_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_hours = min(hours + 1, 24)  # Max 24 hours
            new_time = new_hours * 3600 + minutes * 60 + seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {new_hours}h {minutes}m {seconds}s")

@dp.callback_query(lambda c: c.data == "sd_hours_down")
async def sd_hours_down_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_hours = max(hours - 1, 0)  # Min 0 hours
            new_time = new_hours * 3600 + minutes * 60 + seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {new_hours}h {minutes}m {seconds}s")

@dp.callback_query(lambda c: c.data == "sd_minutes_up")
async def sd_minutes_up_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_minutes = min(minutes + 1, 59)  # Max 59 minutes
            new_time = hours * 3600 + new_minutes * 60 + seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {hours}h {new_minutes}m {seconds}s")

@dp.callback_query(lambda c: c.data == "sd_minutes_down")
async def sd_minutes_down_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_minutes = max(minutes - 1, 0)  # Min 0 minutes
            new_time = hours * 3600 + new_minutes * 60 + seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {hours}h {new_minutes}m {seconds}s")

@dp.callback_query(lambda c: c.data == "sd_seconds_up")
async def sd_seconds_up_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_seconds = min(seconds + 1, 59)  # Max 59 seconds
            new_time = hours * 3600 + minutes * 60 + new_seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {hours}h {minutes}m {new_seconds}s")

@dp.callback_query(lambda c: c.data == "sd_seconds_down")
async def sd_seconds_down_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current_time = row[0] if row else 60
            
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            
            new_seconds = max(seconds - 1, 1)  # Min 1 second
            new_time = hours * 3600 + minutes * 60 + new_seconds
            
            await db.execute("UPDATE settings SET self_destruct_time=? WHERE chat_id=?", (new_time, call.message.chat.id))
            await db.commit()
            await self_destruct_menu_callback(call)
            await call.answer(f"⏱️ Timer set to {hours}h {minutes}m {new_seconds}s")


@dp.callback_query(lambda c: c.data == "blocklist_penalty_menu")
async def blocklist_penalty_menu_callback(call: types.CallbackQuery):
    await call.answer("Opening Blocklist Penalty settings...")
    
    # Get blocklist penalty settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT blocklist_warn_limit, blocklist_penalty FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty = 3, "mute"
            else:
                limit, penalty = row
    
    kb = InlineKeyboardBuilder()
    
    # Blocklist Penalty specific settings - only limit and penalty
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_blocklist_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_blocklist_penalty")
    kb.button(text="↩️ Back", callback_data="back_to_main_settings")
    kb.adjust(2, 1)
    
    await call.message.edit_text(
        "🚫 <b>Blocklist Penalty Settings</b>\n\n"
        "Configure penalties for blocked content violations:\n\n"
        "<i>Warning message is fixed</i>",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(lambda c: c.data == "open_settings_menu")
async def open_settings_menu_callback(call: types.CallbackQuery):
    # Check permissions based on who_can_control setting
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            who_can_control = row[0] if row else "owner"
    
    # Check if user has permission
    allowed = False
    if who_can_control == "owner":
        allowed = chat_member.status == "creator"
    elif who_can_control == "admin":
        allowed = chat_member.status in ["creator", "administrator"]
    elif who_can_control == "moderator":
        # Moderator means any member can access (for testing/demo)
        allowed = True
    
    if not allowed:
        await call.answer(f"❌ Only {who_can_control.capitalize()} can access settings!", show_alert=True)
        return
    
    await call.answer("Opening settings...")
    
    # Get current settings including self destruct
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, blocklist_warning_message, self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, blocklist_warning_message, self_destruct_enabled, self_destruct_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                               (call.message.chat.id, 3, "mute", "members", 1, 1, "members", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ", 0, 60))
                await db.commit()
                row = (3, "mute", "members", 1, 1, "members", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ", 0, 60)
    
    limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, blocklist_warning_message, self_destruct_enabled, self_destruct_time = row
    kb = InlineKeyboardBuilder()
    
    # Who Can Control section - Top priority with cycle button
    control_display = who_can_control.capitalize()
    kb.button(text=f"👑 Access: {control_display}", callback_data="cycle_who_can_control")
    
    # Main category buttons - Bio Checker, Edit Checker, and Blocklist Penalty
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    
    kb.button(text=f"🧬 Bio Checker {bio_status}", callback_data="bio_checker_menu")
    kb.button(text=f"✏️ Edit Checker {edit_status}", callback_data="edit_checker_menu")
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2)
    
    # Delete the original message (works for both text and photo)
    try:
        await call.message.delete()
    except Exception:
        pass
    
    # Send new settings message
    await call.message.answer("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())

# Callback handlers for settings
@dp.callback_query(lambda c: c.data == "change_limit")
async def change_limit_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    # Custom limit with +/- buttons
    kb.button(text="▲ Increase", callback_data="limit_up")
    kb.button(text="▼ Decrease", callback_data="limit_down")
    kb.button(text="↩︎ Back", callback_data="back_to_settings")
    kb.adjust(2)
    
    await call.message.edit_text("⚠ Select Warn Limit:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "limit_up")
async def limit_up_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_limit = row[0]
                new_limit = min(current_limit + 1, 10)  # Max 10
                await db.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", (new_limit, call.message.chat.id))
                await db.commit()
                await refresh_settings_menu(call, new_limit, None, None)
            else:
                await refresh_settings_menu(call, 3, None, None)

@dp.callback_query(lambda c: c.data == "limit_down")
async def limit_down_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_limit = row[0]
                new_limit = max(current_limit - 1, 1)  # Min 1
                await db.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", (new_limit, call.message.chat.id))
                await db.commit()
                await refresh_settings_menu(call, new_limit, None, None)
            else:
                await refresh_settings_menu(call, 3, None, None)

# Penalty selection for Edit Checker
@dp.callback_query(lambda c: c.data == "change_edit_penalty")
async def change_edit_penalty_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    penalties = ["warn", "mute", "kick", "ban"]
    for penalty in penalties:
        kb.button(text=penalty.capitalize(), callback_data=f"set_edit_penalty_{penalty}")
    kb.button(text="↩️ Back", callback_data="edit_checker_menu")
    kb.adjust(2)
    
    await call.message.edit_text("🚨 Select Edit Penalty:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("set_edit_penalty_"))
async def set_edit_penalty_callback(call: types.CallbackQuery):
    penalty = call.data.split("_")[3]
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_penalty=? WHERE chat_id=?", (penalty, call.message.chat.id))
        await db.commit()
    
    await edit_checker_menu_callback(call)
    await call.answer(f"✅ Edit Penalty set to {penalty}")

# Blocklist Penalty Handlers
@dp.callback_query(lambda c: c.data == "change_blocklist_limit")
async def change_blocklist_limit_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    # Custom limit with +/- buttons
    kb.button(text="▲ Increase", callback_data="blocklist_limit_up")
    kb.button(text="▼ Decrease", callback_data="blocklist_limit_down")
    kb.button(text="↩️ Back", callback_data="blocklist_penalty_menu")
    kb.adjust(2)
    
    await call.message.edit_text("⚠ Select Blocklist Warn Limit:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "blocklist_limit_up")
async def blocklist_limit_up_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT blocklist_warn_limit FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_limit = row[0]
                new_limit = min(current_limit + 1, 10)  # Max 10
                await db.execute("UPDATE settings SET blocklist_warn_limit=? WHERE chat_id=?", (new_limit, call.message.chat.id))
                await db.commit()
                await blocklist_penalty_menu_callback(call)
            else:
                await blocklist_penalty_menu_callback(call)

@dp.callback_query(lambda c: c.data == "blocklist_limit_down")
async def blocklist_limit_down_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT blocklist_warn_limit FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_limit = row[0]
                new_limit = max(current_limit - 1, 1)  # Min 1
                await db.execute("UPDATE settings SET blocklist_warn_limit=? WHERE chat_id=?", (new_limit, call.message.chat.id))
                await db.commit()
                await blocklist_penalty_menu_callback(call)
            else:
                await blocklist_penalty_menu_callback(call)

@dp.callback_query(lambda c: c.data == "change_blocklist_penalty")
async def change_blocklist_penalty_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    penalties = ["warn", "mute", "kick", "ban"]
    for penalty in penalties:
        kb.button(text=penalty.capitalize(), callback_data=f"set_blocklist_penalty_{penalty}")
    kb.button(text="↩️ Back", callback_data="blocklist_penalty_menu")
    kb.adjust(2)
    
    await call.message.edit_text("🚨 Select Blocklist Penalty:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("set_blocklist_penalty_"))
async def set_blocklist_penalty_callback(call: types.CallbackQuery):
    penalty = call.data.split("_")[3]
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET blocklist_penalty=? WHERE chat_id=?", (penalty, call.message.chat.id))
        await db.commit()
    
    await blocklist_penalty_menu_callback(call)
    await call.answer(f"✅ Blocklist Penalty set to {penalty}")

@dp.callback_query(lambda c: c.data == "blocklist_penalty_menu")
async def back_to_blocklist_menu_callback(call: types.CallbackQuery):
    await blocklist_penalty_menu_callback(call)

@dp.callback_query(lambda c: c.data == "change_penalty")
async def change_penalty_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    penalties = ["mute", "kick", "ban"]
    for penalty in penalties:
        kb.button(text=penalty.capitalize(), callback_data=f"set_penalty_{penalty}")
    kb.button(text="⬅ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("🚨 Select Penalty:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("set_penalty_"))
async def set_penalty_callback(call: types.CallbackQuery):
    penalty = call.data.split("_")[2]
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET penalty=? WHERE chat_id=?", (penalty, call.message.chat.id))
        await db.commit()
    
    # Refresh settings menu
    await refresh_settings_menu(call, None, penalty, None)
    await call.answer(f"✅ Penalty set to {penalty}")

# Helper function to refresh settings menu
async def refresh_settings_menu(call, new_limit=None, new_penalty=None, new_apply_to=None, new_bio_checker_enabled=None, new_edit_checker=None, new_edit_apply_to=None):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, self_destruct_enabled, self_destruct_time = row
            else:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, self_destruct_enabled, self_destruct_time = 3, "mute", "members", 1, 1, "members", 0, 60
    
    # Use new values if provided
    if new_limit is not None:
        limit = new_limit
    if new_penalty is not None:
        penalty = new_penalty
    if new_apply_to is not None:
        apply_to = new_apply_to
    if new_bio_checker_enabled is not None:
        bio_checker_enabled = new_bio_checker_enabled
    if new_edit_checker is not None:
        edit_checker = new_edit_checker
    if new_edit_apply_to is not None:
        edit_apply_to = new_edit_apply_to
    
    kb = InlineKeyboardBuilder()
    
    # Bio Checker Settings Section
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    kb.button(text=f"🧬 Bio Checker: {bio_status}", callback_data="toggle_bio_checker")
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    # Edit Checker Settings Section
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✏️ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"👥 Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    # Close button - full width
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2, 1)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "change_apply")
async def change_apply_callback(call: types.CallbackQuery):
    # Get current setting
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current = row[0] if row else "members"
    
    kb = InlineKeyboardBuilder()
    # Show checkmark for selected option
    kb.button(text=("✅ " if current == "members" else "") + "Members", callback_data="apply_members")
    kb.button(text=("✅ " if current == "admins" else "") + "Admins", callback_data="apply_admins")
    kb.button(text=("✅ " if current == "members_and_admins" else "") + "Members & Admins", callback_data="apply_both")
    kb.button(text=("✅ " if current == "everyone" else "") + "Everyone", callback_data="apply_everyone")
    kb.button(text="↩︎ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("👥 Bio Checker - Apply To:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "apply_members")
async def apply_members_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET apply_to=? WHERE chat_id=?", ("members", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, "members")
    await call.answer("✅ Apply to: Members")

@dp.callback_query(lambda c: c.data == "apply_admins")
async def apply_admins_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET apply_to=? WHERE chat_id=?", ("admins", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, "admins")
    await call.answer("✅ Apply to: Admins")

@dp.callback_query(lambda c: c.data == "apply_both")
async def apply_both_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET apply_to=? WHERE chat_id=?", ("members_and_admins", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, "members_and_admins")
    await call.answer("✅ Apply to: Members & Admins")

@dp.callback_query(lambda c: c.data == "apply_everyone")
async def apply_everyone_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET apply_to=? WHERE chat_id=?", ("everyone", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, "everyone")
    await call.answer("✅ Apply to: Everyone")

@dp.callback_query(lambda c: c.data == "toggle_bio_checker")
async def toggle_bio_checker_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT bio_checker_enabled FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_status = row[0]
                new_status = 0 if current_status == 1 else 1
                await db.execute("UPDATE settings SET bio_checker_enabled=? WHERE chat_id=?", (new_status, call.message.chat.id))
                await db.commit()
                await refresh_settings_menu(call, None, None, None, new_status, None, None)
                status_text = "Enabled" if new_status == 1 else "Disabled"
                await call.answer(f"✅ Bio Checker {status_text}")
            else:
                await refresh_settings_menu(call, None, None, None, 1, None, None)
                await call.answer("✅ Bio Checker Enabled")

@dp.callback_query(lambda c: c.data == "toggle_edit_checker")
async def toggle_edit_checker_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT edit_checker FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                current_status = row[0]
                new_status = 0 if current_status == 1 else 1
                await db.execute("UPDATE settings SET edit_checker=? WHERE chat_id=?", (new_status, call.message.chat.id))
                await db.commit()
                await refresh_settings_menu(call, None, None, None, new_status)
                status_text = "Enabled" if new_status == 1 else "Disabled"
                await call.answer(f"✅ Edit Checker {status_text}")
            else:
                await refresh_settings_menu(call, None, None, None, 1)
                await call.answer("✅ Edit Checker Enabled")

@dp.callback_query(lambda c: c.data == "change_edit_apply")
async def change_edit_apply_callback(call: types.CallbackQuery):
    # Get current setting
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current = row[0] if row else "members"
    
    kb = InlineKeyboardBuilder()
    # Show checkmark for selected option
    kb.button(text=("✅ " if current == "members" else "") + "Members", callback_data="edit_apply_members")
    kb.button(text=("✅ " if current == "admins" else "") + "Admins", callback_data="edit_apply_admins")
    kb.button(text=("✅ " if current == "members_and_admins" else "") + "Members & Admins", callback_data="edit_apply_both")
    kb.button(text=("✅ " if current == "everyone" else "") + "Everyone", callback_data="edit_apply_everyone")
    kb.button(text="↩︎ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("👥 Edit Checker - Apply To:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "edit_apply_members")
async def edit_apply_members_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("members", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, None, None, "members")
    await call.answer("✅ Edit Apply to: Members")

@dp.callback_query(lambda c: c.data == "edit_apply_admins")
async def edit_apply_admins_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("admins", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, None, None, "admins")
    await call.answer("✅ Edit Apply to: Admins")

@dp.callback_query(lambda c: c.data == "edit_apply_both")
async def edit_apply_both_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("members_and_admins", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, None, None, "members_and_admins")
    await call.answer("✅ Edit Apply to: Members & Admins")

@dp.callback_query(lambda c: c.data == "edit_apply_everyone")
async def edit_apply_everyone_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("everyone", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, None, None, None, None, "everyone")
    await call.answer("✅ Edit Apply to: Everyone")

@dp.callback_query(lambda c: c.data == "open_settings_here")
async def open_settings_here_callback(call: types.CallbackQuery):
    # Check permissions based on who_can_control setting
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            who_can_control = row[0] if row else "owner"
    
    # Check if user has permission
    allowed = False
    if who_can_control == "owner":
        allowed = chat_member.status == "creator"
    elif who_can_control == "admin":
        allowed = chat_member.status in ["creator", "administrator"]
    elif who_can_control == "moderator":
        allowed = True
    
    if not allowed:
        await call.answer(f"❌ Only {who_can_control.capitalize()} can access settings!", show_alert=True)
        return
    
    # Open settings directly in the group - include blocklist settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("""
            SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, 
                   edit_apply_to, edit_penalty, who_can_control,
                   blocklist_penalty, blocklist_warn_limit, blocklist_warning_message 
            FROM settings WHERE chat_id = ?
        """, (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("""
                    INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, bio_checker_enabled, 
                                        edit_checker, edit_apply_to, edit_penalty, who_can_control,
                                        blocklist_penalty, blocklist_warn_limit, blocklist_warning_message) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (call.message.chat.id, 3, "mute", "members", 1, 1, "members", "mute", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ"))
                await db.commit()
                row = (3, "mute", "members", 1, 1, "members", "mute", "owner", "mute", 3, "ᴅᴏɴ'ᴛ ᴜꜱᴇ ʙʟᴏᴄᴋ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴛʜɪꜱ ɢʀᴏᴜᴘ")
    
    limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, edit_penalty, who_can_control, blocklist_penalty, blocklist_warn_limit, blocklist_warning_message = row
    kb = InlineKeyboardBuilder()
    
    # Who Can Control section - Top priority with cycle button
    control_display = who_can_control.capitalize()
    kb.button(text=f"👑 Access: {control_display}", callback_data="cycle_who_can_control")
    
    # Main category buttons - Bio Checker, Edit Checker, and Blocklist Penalty
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    
    kb.button(text=f"🧬 Bio Checker {bio_status}", callback_data="bio_checker_menu")
    kb.button(text=f"✏️ Edit Checker {edit_status}", callback_data="edit_checker_menu")
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer("✅ Settings opened here")

@dp.callback_query(lambda c: c.data == "back_to_main_settings")
async def back_to_main_settings_callback(call: types.CallbackQuery):
    # Get current settings including blocklist settings and self destruct
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time = row
            else:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time = 3, "mute", "members", 1, 1, "members", "owner", "mute", 3, 0, 60
    
    kb = InlineKeyboardBuilder()
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    self_destruct_status = "ON ✅" if self_destruct_enabled == 1 else "OFF ❌"
    control_display = who_can_control.capitalize()
    
    kb.button(text=f"👑 Access: {control_display}", callback_data="cycle_who_can_control")
    kb.button(text=f"🧬 Bio Checker {bio_status}", callback_data="bio_checker_menu")
    kb.button(text=f"✏️ Edit Checker {edit_status}", callback_data="edit_checker_menu")
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2)
    
    await call.message.edit_text(
        "⚙ <b>Bio Guard Settings</b>",
        reply_markup=kb.as_markup()
    )
    await call.answer()

# Who Can Control cycle handler
@dp.callback_query(lambda c: c.data == "cycle_who_can_control")
async def cycle_who_can_control_callback(call: types.CallbackQuery):
    # Cycle through: owner -> admin -> moderator -> owner
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT who_can_control FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            current = row[0] if row else "owner"
        
        # Cycle to next option
        if current == "owner":
            new_value = "admin"
        elif current == "admin":
            new_value = "moderator"
        else:
            new_value = "owner"
        
        await db.execute("UPDATE settings SET who_can_control=? WHERE chat_id=?", (new_value, call.message.chat.id))
        await db.commit()
    
    await back_to_main_settings_callback(call)
    await call.answer(f"✅ Settings access changed to {new_value.capitalize()}")

@dp.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time = row
            else:
                limit, penalty, apply_to, bio_checker_enabled, edit_checker, edit_apply_to, who_can_control, blocklist_penalty, blocklist_warn_limit, self_destruct_enabled, self_destruct_time = 3, "mute", "members", 1, 1, "members", "owner", "mute", 3, 0, 60
    
    kb = InlineKeyboardBuilder()
    
    # Who Can Control section
    control_display = who_can_control.capitalize()
    kb.button(text=f"👑 Access: {control_display}", callback_data="cycle_who_can_control")
    
    # Main category buttons - Bio Checker, Edit Checker, Self Destruct, and Blocklist Penalty
    bio_status = "ON ✅" if bio_checker_enabled == 1 else "OFF ❌"
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    self_destruct_status = "ON ✅" if self_destruct_enabled == 1 else "OFF ❌"
    
    kb.button(text=f"🧬 Bio Checker {bio_status}", callback_data="bio_checker_menu")
    kb.button(text=f"✏️ Edit Checker {edit_status}", callback_data="edit_checker_menu")
    kb.button(text=f"💣 Self Destruct {self_destruct_status}", callback_data="self_destruct_menu")
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2)
    
    # Blocklist Penalty
    kb.button(text=f"🚫 Blocklist Penalty", callback_data="blocklist_penalty_menu")
    
    # Close button - full width
    kb.button(text="✔︎ Save & Close", callback_data="save_and_close")
    kb.adjust(2, 2, 2, 2, 1)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "save_and_close")
async def save_and_close_callback(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer("✅ Settings saved and closed!")

@dp.callback_query(lambda c: c.data == "open_here_group")
async def open_here_group_callback(call: types.CallbackQuery):
    await call.answer(
        "❌ Settings cannot be opened directly in groups. "
        "Please use the 'Open in Private' option to configure settings.", 
        show_alert=True
    )

@dp.callback_query(lambda c: c.data.startswith("unmute_"))
async def unmute_user(call: types.CallbackQuery):
    # Check if user is admin or owner
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can unmute users!", show_alert=True)
        return
    
    # Check if admin has permission
    if chat_member.status == "administrator" and not chat_member.can_restrict_members:
        await call.answer("❌ You don't have permission to unmute users!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[1])
    try:
        await bot.restrict_chat_member(
            chat_id=call.message.chat.id,
            user_id=user_id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        await call.answer(f"✅ User {user_id} unmuted successfully!")
        await call.message.delete()
    except Exception as e:
        await call.answer(f"Error unmuting user: {str(e)}", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("unban_"))
async def unban_user(call: types.CallbackQuery):
    # Check if user is admin or owner
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can unban users!", show_alert=True)
        return
    
    # Check if admin has permission
    if chat_member.status == "administrator" and not chat_member.can_restrict_members:
        await call.answer("❌ You don't have permission to unban users!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[1])
    try:
        await bot.unban_chat_member(chat_id=call.message.chat.id, user_id=user_id)
        await call.answer(f"🔓 User {user_id} unbanned successfully!")
        await call.message.delete()
    except Exception as e:
        await call.answer(f"Error unbanning user: {str(e)}", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("readd_"))
async def readd_user(call: types.CallbackQuery):
    # Check if user is admin or owner
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can re-add users!", show_alert=True)
        return
    
    # Check if admin has permission
    if chat_member.status == "administrator" and not chat_member.can_restrict_members:
        await call.answer("❌ You don't have permission to re-add users!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[1])
    try:
        await bot.unban_chat_member(chat_id=call.message.chat.id, user_id=user_id)
        await call.answer(f"🔄 User {user_id} can be re-added to the group!")
        await call.message.delete()
    except Exception as e:
        await call.answer(f"Error re-adding user: {str(e)}", show_alert=True)

# Remove single warning handler
@dp.callback_query(lambda c: c.data.startswith("remove_warn_"))
async def remove_warn_handler(call: types.CallbackQuery):
    parts = call.data.split("_")
    user_id = int(parts[2])
    warn_type = parts[3] if len(parts) > 3 else "bio"  # Default to bio for backward compatibility
    
    # Check if admin is clicking
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can remove warnings!", show_alert=True)
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", 
                            (call.message.chat.id, user_id)) as cur:
            row = await cur.fetchone()
            if row and row[0] > 0:
                new_count = row[0] - 1
                if new_count > 0:
                    await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", 
                                   (new_count, call.message.chat.id, user_id))
                else:
                    await db.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", 
                                   (call.message.chat.id, user_id))
                await db.commit()
                
                # Update the warning message with new count and reset button
                kb = InlineKeyboardBuilder()
                if new_count > 0:
                    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{user_id}_{warn_type}")
                kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{user_id}_{warn_type}")
                
                # Get updated settings for display
                async with db.execute("SELECT warn_limit FROM settings WHERE chat_id=?", (call.message.chat.id,)) as cur:
                    row = await cur.fetchone()
                    display_limit = row[0] if row else 3
                
                # Show appropriate message based on warning type
                if warn_type == "edit":
                    await call.message.edit_text(
                        f"⚠️ <b>ᴇᴅɪᴛᴛɪɴɢ ɪꜱ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ!</b>\n\n"
                        f"📊 ᴡᴀʀɴɪɴɢꜱ: {new_count}/{display_limit}\n\n"
                        f"<i>ᴘʟᴇᴀsᴇ ᴅᴏ ɴᴏᴛ ᴇᴅɪᴛ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.</i>",
                        reply_markup=kb.as_markup()
                    )
                else:  # bio warning
                    await call.message.edit_text(
                        f"⚠ ʏᴏᴜʀ ʙɪᴏ ᴄᴏɴᴛᴀɪɴ ʟɪɴᴋ . ᴘʟᴇᴀꜱᴇ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ʟɪɴᴋ ꜰʀᴏᴍ ʙɪᴏ ᴀɴᴅ ᴛʜᴇɴ ᴍᴇꜱꜱᴀɢᴇ ʜᴇʀᴇ\n\n"
                        f"📊 ᴡᴀʀɴɪɴɢꜱ: {new_count}/{display_limit}",
                        reply_markup=kb.as_markup()
                    )
                await call.answer("✅ Warning removed!")
            else:
                await call.answer("No warnings to remove!", show_alert=True)

# Reset all warnings handler
@dp.callback_query(lambda c: c.data.startswith("reset_warn_"))
async def reset_warn_handler(call: types.CallbackQuery):
    parts = call.data.split("_")
    user_id = int(parts[2])
    warn_type = parts[3] if len(parts) > 3 else "bio"  # Default to bio for backward compatibility
    
    # Check if admin is clicking
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can reset warnings!", show_alert=True)
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        # Delete all warnings for this user
        await db.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", 
                        (call.message.chat.id, user_id))
        await db.commit()
        
        # Update the message
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Warnings Reset", callback_data="noop")
        
        # Show appropriate message based on warning type
        if warn_type == "edit":
            await call.message.edit_text(
                f"✅ ᴀʟʟ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ ꜰᴏʀ ᴜꜱᴇʀ\n\n"
                f"⚠️ <b>ᴇᴅɪᴛᴛɪɴɢ ɪꜱ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ!</b>\n\n"
                f"<i>ᴘʟᴇᴀsᴇ ᴅᴏ ɴᴏᴛ ᴇᴅɪᴛ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.</i>",
                reply_markup=kb.as_markup()
            )
        else:  # bio warning
            await call.message.edit_text(
                f"✅ ᴀʟʟ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ ꜰᴏʀ ᴜꜱᴇʀ\n\n"
                f"⚠ ʏᴏᴜʀ ʙɪᴏ ᴄᴏɴᴛᴀɪɴ ʟɪɴᴋ . ᴘʟᴇᴀꜱᴇ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ʟɪɴᴋ ꜰʀᴏᴍ ʙɪᴏ ᴀɴᴅ ᴛʜᴇɴ ᴍᴇꜱꜱᴀɢᴇ ʜᴇʀᴇ",
                reply_markup=kb.as_markup()
            )
        await call.answer("✅ All warnings reset!")

# No-op handler for informational buttons
@dp.callback_query(lambda c: c.data == "noop")
async def noop_handler(call: types.CallbackQuery):
    await call.answer()

# Main function
async def main():
    await init_db()
    
    # Start hourly log scheduler
    async def hourly_logs_scheduler():
        while True:
            await asyncio.sleep(3600)  # Wait 1 hour (3600 seconds)
            await send_hourly_logs()
    
    # Start scheduler task
    asyncio.create_task(hourly_logs_scheduler())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
