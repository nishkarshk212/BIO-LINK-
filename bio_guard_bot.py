import re
import asyncio
import aiosqlite
import os
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
BOT_NAME = "Bio Guard Bot"

# Database initialization
async def init_db():
    async with aiosqlite.connect("bio_guard.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            chat_id INTEGER PRIMARY KEY,
            warn_limit INTEGER DEFAULT 3,
            penalty TEXT DEFAULT 'mute',
            apply_to TEXT DEFAULT 'members'
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            chat_id INTEGER,
            user_id INTEGER,
            count INTEGER,
            PRIMARY KEY (chat_id, user_id)
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
        kb.button(text="✚ Add To Group", url=f"https://t.me/{bot_username}?startgroup=true")
    except Exception:
        kb.button(text="✚ Add To Group", url="https://t.me/your_bot_username?startgroup=true")
    
    kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
    kb.adjust(2)
    
    await message.answer(
        f"🔗 <b>{BOT_NAME}</b>🔒\n"
        f"👋 Hello! <b>{message.from_user.first_name}</b> I am an Automatic Bio Link Checker Bot.\n\n"
        f"🚫 I Detect And Restrict Users With Links In Their Bio.\n\n"
        f"🛡 Perfect For:\n"
        f"• Secure Groups\n"
        f"• Anti-Spam Control\n"
        f"• Clean Communities\n\n"
        f"⚡ How To Use:\n"
        f"1️⃣ Add Me To Your Group\n"
        f"2️⃣ Give Me Admin Permission\n"
        f"3️⃣ Enjoy Automatic Protection🔥\n\n"
        f"🔒 I Keep Your Group Safe From Link Spammers!",
        reply_markup=kb.as_markup()
    )

# Settings command
@dp.message(Command("settings"))
async def open_settings(message: types.Message):
    # Settings accessible everywhere with improved interface
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
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await message.reply("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())

# Bio checking logic - Improved link detection
bio_pattern = re.compile(r"(https?://|t\.me/|@\w+|telegram\.me/|t\.me/joinchat/|t\.me/\+|telegram\.dog/)", re.IGNORECASE)

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

# Monitor all messages
@dp.message()
async def monitor(message: types.Message):
    await check_bio(message)

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
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to = row
            else:
                limit, penalty, apply_to = 3, "mute", "members"
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    kb.button(text="✔︎ & Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer(f"✅ Penalty set to {penalty}")

# Helper function to refresh settings menu
async def refresh_settings_menu(call, new_limit=None, new_penalty=None, new_apply_to=None):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to = row
            else:
                limit, penalty, apply_to = 3, "mute", "members"
    
    # Use new values if provided
    if new_limit is not None:
        limit = new_limit
    if new_penalty is not None:
        penalty = new_penalty
    if new_apply_to is not None:
        apply_to = new_apply_to
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(lambda c: c.data == "change_apply")
async def change_apply_callback(call: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    # Custom apply options with symbols
    kb.button(text="♟ Apply on: Members", callback_data="apply_members")
    kb.button(text="♝ Apply on: Admins", callback_data="apply_admins")
    kb.button(text="👥 Apply on: Members & Admins", callback_data="apply_both")
    kb.button(text="🌍 Apply on: Everyone", callback_data="apply_everyone")
    kb.button(text="↩︎ Back", callback_data="back_to_settings")
    kb.adjust(1)
    
    await call.message.edit_text("👥 Apply Settings:", reply_markup=kb.as_markup())
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

@dp.callback_query(lambda c: c.data == "open_settings_here")
async def open_settings_here_callback(call: types.CallbackQuery):
    # Open settings directly in the group
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if not row:
                await db.execute("INSERT INTO settings (chat_id, warn_limit, penalty, apply_to) VALUES (?, ?, ?, ?)", 
                               (call.message.chat.id, 3, "mute", "members"))
                await db.commit()
                row = (3, "mute", "members")
    
    limit, penalty, apply_to = row
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
    kb.button(text="✔︎ Close", callback_data="save_and_close")
    kb.adjust(2)
    
    await call.message.edit_text("⚙ <b>Bio Guard Settings</b>", reply_markup=kb.as_markup())
    await call.answer("✅ Settings opened here")

@dp.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings_callback(call: types.CallbackQuery):
    async with aiosqlite.connect("bio_guard.db") as db:
        async with db.execute("SELECT warn_limit, penalty, apply_to FROM settings WHERE chat_id = ?", (call.message.chat.id,)) as cur:
            row = await cur.fetchone()
            if row:
                limit, penalty, apply_to = row
            else:
                limit, penalty, apply_to = 3, "mute", "members"
    
    kb = InlineKeyboardBuilder()
    kb.button(text=f"⚠ Warn Limit: {limit}", callback_data="change_limit")
    kb.button(text=f"🚨 Penalty: {penalty}", callback_data="change_penalty")
    kb.button(text=f"👥 Apply To: {apply_to}", callback_data="change_apply")
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
