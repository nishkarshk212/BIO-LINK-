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
    kb = InlineKeyboardBuilder()
    try:
        bot_username = (await bot.get_me()).username
        kb.button(text="✚ Add To Group", url=f"https://t.me/{bot_username}?startgroup=true")
    except Exception:
        kb.button(text="✚ Add To Group", url="https://t.me/your_bot_username?startgroup=true")
    
    kb.button(text="♛ Owner", url="https://t.me/Jayden_212")
    kb.adjust(1)
    
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
    if not message.chat.type == "private":
        await message.reply("❌ Settings only available in private chat.")
        return
    
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
    kb.adjust(1)
    
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

# Monitor all messages
@dp.message()
async def monitor(message: types.Message):
    await check_bio(message)

# Callback handlers
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