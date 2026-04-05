import re
import asyncio
import aiosqlite
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from font import Fonts
from settings import SettingsPanel, register_settings_handlers
from nsfw_detector import NSFWDetector, register_nsfw_handlers
from config import START_IMG_URL, OWNER_USERNAME, OWNER_URL, BOT_NAME, BOT_DESCRIPTION

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "")  # Optional: Log channel ID for NSFW reports
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Owner username
# Moved to config.py

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
            bio_apply_to TEXT DEFAULT 'members',
            bio_penalty TEXT DEFAULT 'mute',
            edit_apply_to TEXT DEFAULT 'members',
            edit_penalty TEXT DEFAULT 'mute',
            bio_checker_enabled INTEGER DEFAULT 1
        )
        """)
        
        # Add new columns if they don't exist
        columns_to_add = [
            ("bio_apply_to", "TEXT DEFAULT 'members'"),
            ("bio_penalty", "TEXT DEFAULT 'mute'"),
            ("edit_apply_to", "TEXT DEFAULT 'members'"),
            ("edit_penalty", "TEXT DEFAULT 'mute'"),
            ("bio_checker_enabled", "INTEGER DEFAULT 1"),
            ("nsfw_checker_enabled", "INTEGER DEFAULT 1"),
            ("nsfw_apply_to", "TEXT DEFAULT 'members'"),
            ("nsfw_penalty", "TEXT DEFAULT 'mute'"),
            ("nsfw_check_name", "INTEGER DEFAULT 1"),
            ("nsfw_check_username", "INTEGER DEFAULT 1"),
            ("nsfw_check_bio", "INTEGER DEFAULT 1"),
            ("nsfw_check_messages", "INTEGER DEFAULT 1")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                await db.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added '{col_name}' column to settings table.")
            except Exception:
                pass  # Already exists
        
        await db.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            chat_id INTEGER,
            user_id INTEGER,
            count INTEGER,
            PRIMARY KEY (chat_id, user_id)
        )
        """)
        await db.commit()

# Start command with styled text
@dp.message(Command("start"))
async def start_command(message: types.Message):
    kb = InlineKeyboardBuilder()
    
    try:
        # Fetch live bot info from Telegram
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        bot_first_name = bot_info.first_name or BOT_NAME
        
        kb.button(text="✚ Add To Group", url=f"https://t.me/{bot_username}?startgroup=true")
        kb.button(text="♛ Owner", url=OWNER_URL)
        kb.button(text="⚙ Settings", callback_data="open_settings_menu")
        kb.adjust(2)
        
        # Select random video from START_IMG_URL
        media_url = random.choice(START_IMG_URL)
        
        # Create clickable bot name link
        bot_display_name = f"<a href='http://t.me/{bot_username}'>{bot_first_name}</a>"
        welcome_text = Fonts.mono_upper(bot_first_name)
        caption = f"🛡️ <b>{welcome_text}</b>\n\n"
        caption += Fonts.mono_upper(BOT_DESCRIPTION)
        
        # Check if it's a video URL
        if media_url.endswith('.mp4'):
            await message.answer_video(video=media_url, caption=caption, reply_markup=kb.as_markup())
        else:
            await message.answer_photo(photo=media_url, caption=caption, reply_markup=kb.as_markup())
    except Exception as e:
        print(f"Error in start command: {e}")
        kb = InlineKeyboardBuilder()
        kb.button(text="✚ Add To Group", url="https://t.me/your_bot_username?startgroup=true")
        kb.button(text="♛ Owner", url=OWNER_URL)
        kb.button(text="⚙ Settings", callback_data="open_settings_menu")
        kb.adjust(2)
        welcome_text = Fonts.mono_upper(BOT_NAME)
        await message.answer(f"🛡️ <b>{welcome_text}</b>\n\nBot is running!", reply_markup=kb.as_markup())

# Settings command - uses new SettingsPanel
@dp.message(Command("settings"))
async def open_settings(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        
        # Check if user is admin with ban permission
        if chat_member.status not in ["creator", "administrator"]:
            await message.reply(Fonts.strike("Only admins can access settings!"))
            return
        
        # Check if admin has ban permission (or is creator)
        if chat_member.status == "administrator":
            if not chat_member.can_restrict_members:
                await message.reply(Fonts.strike("You need ban permission to access settings!"))
                return
    
    await SettingsPanel.show_settings(message, message.chat.id, is_callback=False)

# Bio checking logic
bio_pattern = re.compile(r"(https?://|t\.me/|@\w+|telegram\.me/|t\.me/joinchat/|t\.me/\+|telegram\.dog/)", re.IGNORECASE)

async def check_bio(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    try:
        user = await bot.get_chat(message.from_user.id)
        bio = user.bio or ""
        
        if not bio_pattern.search(bio):
            return
            
        print(f"Bio link detected for user {message.from_user.id}")
        
    except Exception as e:
        print(f"Error getting user bio: {e}")
        return

    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("""
            SELECT warn_limit, bio_penalty, bio_apply_to, bio_checker_enabled
            FROM settings WHERE chat_id = ?
        """, (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("""
                    INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker,
                                        bio_apply_to, bio_penalty, edit_apply_to, edit_penalty,
                                        bio_checker_enabled) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (message.chat.id, 3, "mute", "members", 1, "members", "mute", "members", "mute", 1))
                await db.commit()
                limit, penalty, bio_apply_to, bio_checker_enabled = 3, "mute", "members", 1
            else:
                limit, penalty, bio_apply_to, bio_checker_enabled = row
        
        # Check if bio checker is enabled
        if bio_checker_enabled == 0:
            return

        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        user_status = chat_member.status
        
        should_apply = False
        
        if bio_apply_to == "members":
            if user_status in ["member", "left"]:
                should_apply = True
        elif bio_apply_to == "admins":
            if user_status in ["administrator", "creator"]:
                should_apply = True
        elif bio_apply_to == "members_and_admins":
            if user_status in ["member", "administrator", "creator"]:
                should_apply = True
        elif bio_apply_to == "everyone":
            should_apply = True
        
        if not should_apply:
            return

        async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (message.chat.id, message.from_user.id)) as cur:
            row = await cur.fetchone()
            if row:
                count = row[0] + 1
                await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", (count, message.chat.id, message.from_user.id))
            else:
                count = 1
                await db.execute("INSERT INTO warns VALUES (?, ?, ?)", (message.chat.id, message.from_user.id, count))
        await db.commit()

    # Only show buttons if penalty is not "warn"
    kb = InlineKeyboardBuilder()
    if penalty != "warn":
        kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}")
        kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}")
        kb.adjust(2)
    
    warning_text = Fonts.mono_upper("Your bio contains a link!")
    warning_msg = await message.reply(
        f"⚠ {warning_text}\n{Fonts.mono_upper('Please remove the link from bio')}",
        reply_markup=kb.as_markup() if penalty != "warn" else None
    )
    
    async def delete_warning():
        await asyncio.sleep(30)
        try:
            await warning_msg.delete()
        except:
            pass
    
    asyncio.create_task(delete_warning())
    
    async def delete_user_message():
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass
    
    asyncio.create_task(delete_user_message())

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
            penalty_text = Fonts.mono_upper(f"User {penalty}d!")
            action_msg = await message.reply(
                f"🚨 {penalty_text}\n{Fonts.mono_upper(f'After {limit} warnings')}",
                reply_markup=kb.as_markup()
            )
            
            async def delete_penalty():
                await asyncio.sleep(30)
                try:
                    await action_msg.delete()
                except:
                    pass
            
            asyncio.create_task(delete_penalty())
        else:
            await message.reply(
                f"🚨 {Fonts.mono_upper(f'User reached {limit} warnings')}\n{Fonts.mono_upper('Bot needs admin permission')}"
            )

# Monitor all messages for bio checking
@dp.message()
async def monitor(message: types.Message):
    """Monitor messages for both bio links and NSFW content"""
    # Check for bio links
    await check_bio(message)
    
    # Check for NSFW content with log channel
    await nsfw_detector.check_message(message, bot, LOG_CHANNEL_ID)

# Monitor edited messages - delete them
@dp.edited_message()
async def monitor_edited_message(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    if message.from_user.username == OWNER_USERNAME:
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("""
            SELECT warn_limit, edit_penalty, edit_apply_to, edit_checker 
            FROM settings WHERE chat_id = ?
        """, (message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                limit, penalty, edit_apply_to, edit_checker = 3, "mute", "members", 1
            else:
                limit, penalty, edit_apply_to, edit_checker = row
    
    if edit_checker == 0:
        return
    
    # Check if user should be affected based on edit_apply_to setting
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
    
    try:
        await message.delete()
        print(f"✅ Deleted edited message from user {message.from_user.id}")
    except Exception as e:
        print(f"❌ Error deleting edited message: {e}")
        return
    
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
    
    # Only show buttons if penalty is not "warn"
    kb = InlineKeyboardBuilder()
    if penalty != "warn":
        kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}")
        kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}")
        kb.adjust(2)
    
    try:
        edit_warning = Fonts.mono_upper("Editing not allowed!")
        warning_msg = await message.answer(
            f"📢 {edit_warning}\n{Fonts.mono_upper('Message editing is disabled')}",
            reply_markup=kb.as_markup() if penalty != "warn" else None
        )
    except Exception as e:
        print(f"❌ Error sending warning: {e}")
        return
    
    async def delete_warning():
        await asyncio.sleep(30)
        try:
            await warning_msg.delete()
        except:
            pass
    
    asyncio.create_task(delete_warning())
    
    if count >= limit:
        bot_member = await bot.get_chat_member(message.chat.id, bot.id)
        penalty_kb = InlineKeyboardBuilder()
        penalty_kb.adjust(1)
        action_taken = False
        
        if penalty == "warn":
            # Just warn, no action needed
            action_taken = True
            penalty_text = Fonts.mono_upper("Warned!")
            await message.answer(f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}")
        elif penalty == "mute" and bot_member.can_restrict_members:
            await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                         permissions=types.ChatPermissions(can_send_messages=False))
            penalty_kb.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
            action_taken = True
            penalty_text = Fonts.mono_upper("Muted!")
            await message.answer(
                f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                reply_markup=penalty_kb.as_markup()
            )
        elif penalty == "kick" and bot_member.can_restrict_members:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            await bot.unban_chat_member(message.chat.id, message.from_user.id)
            penalty_kb.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
            action_taken = True
            penalty_text = Fonts.mono_upper("Kicked!")
            await message.answer(
                f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                reply_markup=penalty_kb.as_markup()
            )
        elif penalty == "ban" and bot_member.can_restrict_members:
            await bot.ban_chat_member(message.chat.id, message.from_user.id)
            penalty_kb.button(text="🔓 Unban User", callback_data=f"unban_{message.from_user.id}")
            action_taken = True
            penalty_text = Fonts.mono_upper("Banned!")
            await message.answer(
                f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                reply_markup=penalty_kb.as_markup()
            )
        
        if not action_taken and penalty != "warn":
            await message.answer(
                f"🚨 {Fonts.mono_upper(f'User reached {limit} warnings')}\n{Fonts.mono_upper('Bot needs admin permission')}"
            )

# Remove single warning handler
@dp.callback_query(lambda c: c.data.startswith("remove_warn_"))
async def remove_warn_handler(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[2])
    
    # Check if caller is admin
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
                
                kb = InlineKeyboardBuilder()
                if new_count > 0:
                    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{user_id}")
                kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{user_id}")
                
                await call.message.edit_text(
                    f"⚠ {Fonts.outline('Warning removed')}\n<b>Warnings remaining: {new_count}</b>",
                    reply_markup=kb.as_markup()
                )
                await call.answer("✅ Warning removed!")
            else:
                await call.answer("No warnings to remove!", show_alert=True)


# Reset all warnings handler
@dp.callback_query(lambda c: c.data.startswith("reset_warn_"))
async def reset_warn_handler(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[2])
    
    chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await call.answer("❌ Only admins can reset warnings!", show_alert=True)
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", 
                        (call.message.chat.id, user_id))
        await db.commit()
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Warnings Reset", callback_data="noop")
        
        await call.message.edit_text(
            f"✅ {Fonts.bold_script('All warnings reset')}\n{Fonts.typewriter(f'For user {user_id}')}",
            reply_markup=kb.as_markup()
        )
        await call.answer("✅ All warnings reset!")

@dp.callback_query(lambda c: c.data == "noop")
async def noop_handler(call: types.CallbackQuery):
    await call.answer()

# Register settings handlers
register_settings_handlers(dp, bot)

# Register NSFW detection handlers
nsfw_detector = NSFWDetector(openai_api_key=OPENAI_API_KEY)
register_nsfw_handlers(dp, bot, nsfw_detector)

# Monitor new chat members for NSFW profile content
@dp.chat_member()
async def monitor_new_members(chat_member: types.ChatMemberUpdated):
    """Check new members' profiles for NSFW content"""
    if chat_member.chat.type not in ["group", "supergroup"]:
        return
    
    # Only check when user joins (status changed to member)
    if chat_member.new_chat_member.status == "member" and chat_member.old_chat_member.status != "member":
        await nsfw_detector.check_user_profile(chat_member, bot, LOG_CHANNEL_ID)

# Admin commands for NSFW word management
@dp.message(Command("addword"))
async def add_nsfw_word(message: types.Message):
    """Add NSFW word (admin only)"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer(Fonts.mono_upper("❌ Only admins can use this command"))
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(Fonts.mono_upper("Usage: /addword word"))
        return
    
    word = parts[1].strip()
    if nsfw_detector.add_word(word):
        await message.answer(Fonts.mono_upper(f"✅ Added NSFW word: {word}"))
    else:
        await message.answer(Fonts.mono_upper(f"⚠️ Word already exists: {word}"))

@dp.message(Command("removeword"))
async def remove_nsfw_word(message: types.Message):
    """Remove NSFW word (admin only)"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer(Fonts.mono_upper("❌ Only admins can use this command"))
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(Fonts.mono_upper("Usage: /removeword word"))
        return
    
    word = parts[1].strip()
    if nsfw_detector.remove_word(word):
        await message.answer(Fonts.mono_upper(f"❌ Removed NSFW word: {word}"))
    else:
        await message.answer(Fonts.mono_upper("⚠️ Word not found"))

@dp.message(Command("words"))
async def list_nsfw_words(message: types.Message):
    """List all NSFW words (admin only)"""
    if message.chat.type not in ["group", "supergroup"]:
        return
    
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer(Fonts.mono_upper("❌ Only admins can use this command"))
        return
    
    words_list = "\n".join([f"• {word}" for word in nsfw_detector.nsfw_keywords])
    await message.answer(
        Fonts.mono_upper(f"📋 NSFW Words List ({len(nsfw_detector.nsfw_keywords)} words):\n\n{words_list}")
    )

@dp.message(Command("warns"))
async def check_user_warns(message: types.Message):
    """Check user's warnings"""
    if not message.from_user:
        return
    
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute(
            "SELECT warning_count FROM warnings WHERE chat_id=? AND user_id=?",
            (message.chat.id, message.from_user.id)
        ) as cur:
            row = await cur.fetchone()
            count = row[0] if row else 0
    
    status = "At Risk" if count > 0 else "Clean"
    await message.answer(
        f"⚠️ {Fonts.mono_upper('Your Warnings')}\n"
        f"{Fonts.mono_upper(f'Current: {count}/3')}\n"
        f"{Fonts.mono_upper(f'Status: {status}')}"
    )

# Main function
async def main():
    await init_db()
    print("✅ Bio Guard Bot started with font styling!")
    ai_status = "Enabled" if OPENAI_API_KEY else "Disabled"
    print(f"🛡️ Features: Bio Detection + Edit Message Deletion + NSFW Detection (AI: {ai_status})")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
