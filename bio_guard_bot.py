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
        
        # Get bot's profile photo
        photos = await bot.get_user_profile_photos((await bot.get_me()).id)
        start_msg = (
            f"๏ ᴛʜɪs ɪs <a href='https://t.me/{bot_username}'>{BOT_NAME}</a>\n\n"
            f"➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
            f"ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
            f"➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
            f"➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂"
        )
        
        if photos.total_count > 0:
            photo_id = photos.photos[0][0].file_id
            await message.answer_photo(
                photo=photo_id,
                caption=start_msg,
                reply_markup=kb.as_markup()
            )
        else:
            # No profile picture, send text only
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

# Settings command - Owner only access
@dp.message(Command("settings"))
async def open_settings(message: types.Message):
    # Check if user is group owner
    if message.chat.type in ["group", "supergroup"]:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status != "creator":  # Only owner can access settings
            await message.reply("❌ Only group owner can access settings!")
            return
    
    # Settings logic
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker, edit_apply_to) VALUES (?, ?, ?, ?, ?, ?)", 
                               (message.chat.id, 3, "mute", "members", 1, "members"))
                await db.commit()
                row = (3, "mute", "members", 1, "members")
    
    limit, penalty, apply_to, edit_checker, edit_apply_to = row
    kb = InlineKeyboardBuilder()
    
    # Show access options if in group
    if message.chat.type in ["group", "supergroup"]:
        kb.button(text="☞ Open Here", callback_data="open_settings_here")
        kb.button(text="☞ Open in Private", url=f"https://t.me/{(await bot.get_me()).username}?start=settings")
        kb.adjust(2)
        await message.reply("⚙ <b>Bio Guard Settings</b>\n\nChoose how to access settings:", reply_markup=kb.as_markup())
        return
    
    # Main settings menu (private chat or when opened directly)
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✎ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await message.reply("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())

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
    """Log bot activities"""
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
        
        if not bio_pattern.search(bio):
            return
            
        print(f"Bio link detected for user {message.from_user.id}")
        
    except Exception as e:
        print(f"Error getting user bio: {e}")
        return

    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to) VALUES (?, ?, ?, ?)", 
                               (message.chat.id, 3, "mute", "members"))
                await db.commit()
                limit, penalty, apply_to = 3, "mute", "members"
            else:
                limit, penalty, apply_to = row

        # Check if user should be affected based on settings
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
    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}")
    kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}")
    kb.adjust(2)
    
    warning_msg = await message.reply(
        f"⚠ ʏᴏᴜʀ ʙɪᴏ ᴄᴏɴᴛᴀɪɴ ʟɪɴᴋ . ᴘʟᴇᴀꜱᴇ ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ʟɪɴᴋ ꜰʀᴏᴍ ʙɪᴏ ᴀɴᴅ ᴛʜᴇɴ ᴍᴇꜱꜱᴀɢᴇ ʜᴇʀᴇ\n\n"
        f"📊 ᴡᴀʀɴɪɴɢꜱ: {count}/{limit}",
        reply_markup=kb.as_markup()
    )
    
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

# Monitor edited messages
@dp.edited_message()
async def monitor_edited_message(message: types.Message):
    """Detect when users edit their messages and warn them"""
    if await check_global_ban(message):
        return
    
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    # Skip owner editing (can bypass if needed)
    if message.from_user.username == OWNER_USERNAME:
        return
    
    # Get settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty, edit_checker, edit_apply_to = 3, "mute", 1, "members"
            else:
                limit, penalty, edit_checker, edit_apply_to = row
    
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
    
    # Update warning count
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
    
    # Send warning message with buttons
    kb = InlineKeyboardBuilder()
    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}")
    kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}")
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
        
        if penalty == "mute" and bot_member.can_restrict_members:
            await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                         permissions=types.ChatPermissions(can_send_messages=False))
            penalty_kb.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
            await message.answer(f"⚠️ User {message.from_user.id} muted! Reached warning limit ({count}/{limit}).", 
                               reply_markup=penalty_kb.as_markup())
        elif penalty == "kick" and bot_member.can_restrict_members:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            await bot.unban_chat_member(message.chat.id, message.from_user.id)
            penalty_kb.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
            await message.answer(f"⚠️ User {message.from_user.id} kicked! Reached warning limit ({count}/{limit}).", 
                               reply_markup=penalty_kb.as_markup())
        elif penalty == "ban" and bot_member.can_restrict_members:
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
@dp.callback_query(lambda c: c.data == "open_settings_menu")
async def open_settings_menu_callback(call: types.CallbackQuery):
    await call.answer("Opening settings...")
    
    # Get current settings
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker, edit_apply_to) VALUES (?, ?, ?, ?, ?, ?)", 
                               (call.message.chat.id, 3, "mute", "members", 1, "members"))
                await db.commit()
                row = (3, "mute", "members", 1, "members")
    
    limit, penalty, apply_to, edit_checker, edit_apply_to = row
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✎ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
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
async def refresh_settings_menu(call, new_limit=None, new_penalty=None, new_apply_to=None, new_edit_checker=None, new_edit_apply_to=None):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to, edit_checker, edit_apply_to = row
            else:
                limit, penalty, apply_to, edit_checker, edit_apply_to = 3, "mute", "members", 1, "members"
    
    # Use new values if provided
    if new_limit is not None:
        limit = new_limit
    if new_penalty is not None:
        penalty = new_penalty
    if new_apply_to is not None:
        apply_to = new_apply_to
    if new_edit_checker is not None:
        edit_checker = new_edit_checker
    if new_edit_apply_to is not None:
        edit_apply_to = new_edit_apply_to
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✎ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
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
    # Check if user is group owner
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status != "creator":
        await call.answer("❌ Only group owner can access settings!", show_alert=True)
        return
    
    # Open settings directly in the group
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker, edit_apply_to) VALUES (?, ?, ?, ?, ?, ?)", 
                               (call.message.chat.id, 3, "mute", "members", 1, "members"))
                await db.commit()
                row = (3, "mute", "members", 1, "members")
    
    limit, penalty, apply_to, edit_checker, edit_apply_to = row
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✎ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer("✅ Settings opened here")

@dp.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to, edit_checker, edit_apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to, edit_checker, edit_apply_to = row
            else:
                limit, penalty, apply_to, edit_checker, edit_apply_to = 3, "mute", "members", 1, "members"
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Bio Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"✎ Edit Checker: {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Edit Apply To: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ & Close", callback_data="save_and_close")
    kb.adjust(2)
    
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
    user_id = int(call.data.split("_")[2])
    
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
                    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{user_id}")
                kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{user_id}")
                
                # Get updated settings for display
                async with db.execute("SELECT warn_limit FROM settings WHERE chat_id=?", (call.message.chat.id,)) as cur:
                    row = await cur.fetchone()
                    display_limit = row[0] if row else 3
                
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
    user_id = int(call.data.split("_")[2])
    
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
