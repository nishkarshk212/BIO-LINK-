import re
import asyncio
import aiosqlite
import os
from datetime import datetime
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

# Owner username
OWNER_USERNAME = "Jayden_212"

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
    kb = InlineKeyboardBuilder()
    try:
        bot_username = (await bot.get_me()).username
        kb.button(text="✚ Add To Group", url=f"https://t.me/{bot_username}?startgroup=true")
    except Exception:
        kb.button(text="✚ Add To Group", url="https://t.me/your_bot_username?startgroup=true")
    
    kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
    kb.adjust(2)  # Make it consistent with 2 columns like in bio_guard_bot.py
    
    bot_username = "your_bot_username"
    try:
        bot_username = (await bot.get_me()).username
    except Exception:
        pass

    await message.answer(
        f"๏ ᴛʜɪs ɪs <a href='https://t.me/{bot_username}'>{BOT_NAME}</a>\n\n"
        f"➻ ᴀ ᴘᴏᴡᴇʀғᴜʟ sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ ᴅᴇsɪɢɴᴇᴅ ᴛᴏ ᴘʀᴏᴛᴇᴄᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ\n"
        f"ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ ᴍᴇ ᴀᴅᴍɪɴ & ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ ʀɪɢʜᴛ ɪ sᴛᴀʀᴛ ᴘʀᴏᴛᴇᴄᴛɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ\n"
        f"➻ ɢɪᴠᴇ ᴍᴇ ᴀ ᴄʜᴀɴᴄᴇ ʜᴀɴᴅʟᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ.\n"
        f"➻ ᴊᴏɪɴ sᴜᴘᴘᴏʀᴛ ғᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇs.🥂",
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

# Settings command
@dp.message(Command("settings"))
async def open_settings(message: types.Message):
    if not message.chat.type == "private":
        await message.reply("❌ Settings only available in private chat.")
        return
    
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
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"ᴇᴅɪᴛ ᴄʜᴇᴄᴋᴇʀ ✎ : {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Apply on: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ & Close", callback_data="save_and_close")
    kb.adjust(2)  # Make it consistent with 2 columns
    
    await message.reply("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())

# Bio checking logic
bio_pattern = re.compile(r"(https?://|t\.me/|@\w+)", re.IGNORECASE)

async def check_bio(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    user = await bot.get_chat(message.from_user.id)
    bio = user.bio or ""

    if not bio_pattern.search(bio):
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

    # Send warning
    warning_msg = await message.reply(
        f"⚠ Warning {count}/{limit} | ID: <code>{message.from_user.id}</code>\n"
        f"Reason: Bio contains link."
    )
    
    # Auto-delete warning after 1 minute
    async def delete_warning():
        await asyncio.sleep(60)
        try:
            await warning_msg.delete()
        except:
            pass
    
    asyncio.create_task(delete_warning())

    # Apply penalty if limit reached
    if count >= limit:
        bot_member = await bot.get_chat_member(message.chat.id, bot.id)
        kb = InlineKeyboardBuilder()
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
        else:
            action_msg = await message.reply(
                f"🚨 <b>User {message.from_user.id}</b> reached {limit} warnings but bot doesn't have permission to {penalty}."
            )
        
        async def delete_action():
            await asyncio.sleep(60)
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
                    await message.reply(f"🚫 <b>ɢʟᴏʙᴀʟ ʙᴀɴ ᴅᴇᴛᴇᴄᴛᴇᴅ</b>\n\n👤 ᴜsᴇʀ: {message.from_user.id}\n📝 ʀᴇᴀsᴏɴ: {reason}\n\n<i>ᴛʜɪs ᴜsᴇʀ ʜᴀs ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.</i>")
                    return True
                except Exception as e:
                    print(f"Error auto-banning globally banned user: {e}")
    return False

# Monitor all messages
@dp.message()
async def monitor(message: types.Message):
    if await check_global_ban(message):
        return
    await check_bio(message)

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
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    
    edit_status = "ON ✅" if edit_checker == 1 else "OFF ❌"
    kb.button(text=f"ᴇᴅɪᴛ ᴄʜᴇᴄᴋᴇʀ ✎ : {edit_status}", callback_data="toggle_edit_checker")
    kb.button(text=f"✎ Apply on: {edit_apply_to}", callback_data="change_edit_apply")
    
    kb.button(text="✔︎ & Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer()

# Callback handlers for settings
@dp.callback_query(lambda c: c.data == "change_limit")
async def change_limit_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for limit in [1, 2, 3, 5, 10]:
        kb.button(text=f"{limit} Warnings", callback_data=f"set_limit_{limit}")
    kb.button(text="⬅ Back", callback_data="back_to_settings")
    kb.adjust(2)
    
    await call.message.edit_text("⚠ Select Warn Limit:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("set_limit_"))
async def set_limit_callback(call: types.CallbackQuery):
    limit = int(call.data.split("_")[2])
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", (limit, call.message.chat.id))
        await db.commit()
    
    # Refresh settings menu
    await refresh_settings_menu(call, new_limit=limit)
    await call.answer(f"✅ Warn limit set to {limit}")

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
    await refresh_settings_menu(call, new_penalty=penalty)
    await call.answer(f"✅ Penalty set to {penalty}")

@dp.callback_query(lambda c: c.data == "change_apply")
async def change_apply_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    options = ["members", "admins", "everyone"]
    for option in options:
        kb.button(text=option.capitalize(), callback_data=f"set_apply_{option}")
    kb.button(text="⬅ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("👥 Apply To:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data.startswith("set_apply_"))
async def set_apply_callback(call: types.CallbackQuery):
    apply_to = call.data.split("_")[2]
    
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET apply_to=? WHERE chat_id=?", (apply_to, call.message.chat.id))
        await db.commit()
    
    # Refresh settings menu
    await refresh_settings_menu(call, new_apply_to=apply_to)
    await call.answer(f"✅ Apply to set to {apply_to}")

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
                await refresh_settings_menu(call, new_edit_checker=new_status)
                status_text = "Enabled" if new_status == 1 else "Disabled"
                await call.answer(f"✅ Edit Checker {status_text}")
            else:
                await refresh_settings_menu(call, new_edit_checker=1)
                await call.answer("✅ Edit Checker Enabled")

@dp.callback_query(lambda c: c.data == "change_edit_apply")
async def change_edit_apply_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="♟ Apply on: Members", callback_data="edit_apply_members")
    kb.button(text="♝ Apply on: Admins", callback_data="edit_apply_admins")
    kb.button(text="🌍 Apply on: Everyone", callback_data="edit_apply_everyone")
    kb.button(text="↩︎ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("👥 Edit Checker Apply Settings:", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "edit_apply_members")
async def edit_apply_members_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("members", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, new_edit_apply_to="members")
    await call.answer("✅ Edit Apply to: Members")

@dp.callback_query(lambda c: c.data == "edit_apply_admins")
async def edit_apply_admins_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("admins", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, new_edit_apply_to="admins")
    await call.answer("✅ Edit Apply to: Admins")

@dp.callback_query(lambda c: c.data == "edit_apply_everyone")
async def edit_apply_everyone_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("UPDATE settings SET edit_apply_to=? WHERE chat_id=?", ("everyone", call.message.chat.id))
        await db.commit()
    await refresh_settings_menu(call, new_edit_apply_to="everyone")
    await call.answer("✅ Edit Apply to: Everyone")

@dp.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings_callback(call: types.CallbackQuery):
    await refresh_settings_menu(call)

@dp.callback_query(lambda c: c.data == "save_and_close")
async def save_and_close_callback(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer("✅ Settings saved and closed!")
@dp.callback_query(lambda c: c.data.startswith("unmute_"))
async def unmute_user(call: types.CallbackQuery):
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
    user_id = int(call.data.split("_")[1])
    try:
        await bot.unban_chat_member(chat_id=call.message.chat.id, user_id=user_id)
        await call.answer(f"🔓 User {user_id} unbanned successfully!")
        await call.message.delete()
    except Exception as e:
        await call.answer(f"Error unbanning user: {str(e)}", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("readd_"))
async def readd_user(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    try:
        await bot.unban_chat_member(chat_id=call.message.chat.id, user_id=user_id)
        await call.answer(f"🔄 User {user_id} can be re-added to the group!")
        await call.message.delete()
    except Exception as e:
        await call.answer(f"Error re-adding user: {str(e)}", show_alert=True)

# Main function
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())