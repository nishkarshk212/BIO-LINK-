"""
Settings Panel Module for Bio Guard Bot
Handles all settings-related functionality with modern UI
"""

import aiosqlite
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from font import Fonts


class SettingsPanel:
    """Modern settings panel with clean UI"""
    
    @staticmethod
    async def get_settings(chat_id):
        """Retrieve settings from database"""
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("""
                SELECT warn_limit, penalty, apply_to, edit_checker, 
                       bio_apply_to, bio_penalty, edit_apply_to, edit_penalty,
                       bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty,
                       nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages
                FROM settings WHERE chat_id = ?
            """, (chat_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    # Create default settings
                    await db.execute("""
                        INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker,
                                            bio_apply_to, bio_penalty, edit_apply_to, edit_penalty,
                                            bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty,
                                            nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (chat_id, 3, "mute", "members", 1, "members", "mute", "members", "mute", 1, 1, "members", "mute", 1, 1, 1, 1))
                    await db.commit()
                    return (3, "mute", "members", 1, "members", "mute", "members", "mute", 1, 1, "members", "mute", 1, 1, 1, 1)
                return row
    
    @staticmethod
    def build_main_menu(limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, 
                       edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, 
                       nsfw_apply_to, nsfw_penalty):
        """Build main settings menu - Only configure buttons"""
        kb = InlineKeyboardBuilder()
        
        # Layer 1: Configure Buttons (Column layout for better visibility)
        kb.button(text="BIO ❂ Cᴏɴғɪɢᴜʀᴇ", callback_data="bio_settings_menu")
        kb.button(text="EDIT ❂ Cᴏɴғɪɢᴜʀᴇ", callback_data="edit_settings_menu")
        kb.button(text="NSFW ❂ Cᴏɴғɪɢᴜʀᴇ", callback_data="nsfw_settings_menu")
        
        # Layer 2: Revert & Close
        kb.button(text="🔄 Rᴇᴠᴇʀᴛ Sᴇᴛᴛɪɴɢs", callback_data="revert_settings")
        kb.button(text="━━━━━━━━━━━━━━━", callback_data="noop")
        kb.button(text="✓ Cʟᴏsᴇ", callback_data="save_and_close")
        
        kb.adjust(1)  # Single column layout for better visibility
        return kb
    
    @staticmethod
    def build_bio_settings_menu(bio_apply_to, bio_penalty, bio_checker_enabled):
        """Build Bio Checker settings submenu"""
        kb = InlineKeyboardBuilder()
        
        # Status indicator
        status = "🟢 Aᴄᴛɪᴠᴇ" if bio_checker_enabled == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        kb.button(text=f"🔍 Bɪᴏ Cʜᴇᴄᴋᴇʀ: {status}", callback_data="noop")
        
        # Toggle button
        toggle_text = "❌ Dɪsᴀʙʟᴇ" if bio_checker_enabled == 1 else "✅ Eɴᴀʙʟᴇ"
        kb.button(text=toggle_text, callback_data="toggle_bio_checker")
        
        # Settings
        kb.button(text=f"👥 Aᴘᴘʟʏ Tᴏ: {bio_apply_to.title()}", callback_data="bio_apply_to")
        kb.button(text=f"⚡ Pᴇɴᴀʟᴛʏ: {bio_penalty.upper()}", callback_data="bio_penalty")
        
        # Back button
        kb.button(text="━━━━━━━━━━━━━━━", callback_data="noop")
        kb.button(text="↩️ Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ", callback_data="back_to_settings")
        
        kb.adjust(1)
        return kb
    
    @staticmethod
    def build_edit_settings_menu(edit_apply_to, edit_penalty, edit_checker):
        """Build Edit Checker settings submenu"""
        kb = InlineKeyboardBuilder()
        
        # Status indicator
        status = "🟢 Aᴄᴛɪᴠᴇ" if edit_checker == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        kb.button(text=f"✏️ Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ: {status}", callback_data="noop")
        
        # Toggle button
        toggle_text = "❌ Dɪsᴀʙʟᴇ" if edit_checker == 1 else "✅ Eɴᴀʙʟᴇ"
        kb.button(text=toggle_text, callback_data="toggle_edit_checker")
        
        # Settings
        kb.button(text=f"👥 Aᴘᴘʟʏ Tᴏ: {edit_apply_to.title()}", callback_data="edit_apply_to")
        kb.button(text=f"⚡ Pᴇɴᴀʟᴛʏ: {edit_penalty.upper()}", callback_data="edit_penalty")
        
        # Back button
        kb.button(text="━━━━━━━━━━━━━━━", callback_data="noop")
        kb.button(text="↩️ Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ", callback_data="back_to_settings")
        
        kb.adjust(1)
        return kb
    
    @staticmethod
    def build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled, 
                                nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages):
        """Build NSFW Checker settings submenu"""
        kb = InlineKeyboardBuilder()
        
        # Status indicator
        status = "🟢 Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        kb.button(text=f"🚫 NSFW Cʜᴇᴄᴋᴇʀ: {status}", callback_data="noop")
        
        # Toggle button
        toggle_text = "❌ Dɪsᴀʙʟᴇ" if nsfw_checker_enabled == 1 else "✅ Eɴᴀʙʟᴇ"
        kb.button(text=toggle_text, callback_data="toggle_nsfw_checker")
        
        # Detection toggles
        name_status = "✅" if nsfw_check_name == 1 else "❌"
        username_status = "✅" if nsfw_check_username == 1 else "❌"
        bio_status = "✅" if nsfw_check_bio == 1 else "❌"
        message_status = "✅" if nsfw_check_messages == 1 else "❌"
        
        kb.button(text=f"👤 Cʜᴇᴄᴋ Nᴀᴍᴇ: {name_status}", callback_data="toggle_nsfw_check_name")
        kb.button(text=f"🆔 Cʜᴇᴄᴋ Usᴇʀɴᴀᴍᴇ: {username_status}", callback_data="toggle_nsfw_check_username")
        kb.button(text=f"📝 Cʜᴇᴄᴋ Bɪᴏ: {bio_status}", callback_data="toggle_nsfw_check_bio")
        kb.button(text=f"💬 Cʜᴇᴄᴋ Mᴇssᴀɢᴇs: {message_status}", callback_data="toggle_nsfw_check_messages")
        
        # Settings
        kb.button(text=f"👥 Aᴘᴘʟʏ Tᴏ: {nsfw_apply_to.title()}", callback_data="nsfw_apply_to")
        kb.button(text=f"⚡ Pᴇɴᴀʟᴛʏ: {nsfw_penalty.upper()}", callback_data="nsfw_penalty")
        
        # Back button
        kb.button(text="━━━━━━━━━━━━━━━", callback_data="noop")
        kb.button(text="↩️ Bᴀᴄᴋ ᴛᴏ Mᴀɪɴ", callback_data="back_to_settings")
        
        kb.adjust(1)
        return kb
    
    @staticmethod
    def build_status_message(bio_checker_enabled, edit_checker, nsfw_checker_enabled):
        """Build status description message"""
        title = Fonts.mono_upper("Bɪᴏ Gᴜᴀʀᴅ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ")
        
        bio_status = "🟢 Aᴄᴛɪᴠᴇ" if bio_checker_enabled == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        edit_status = "🟢 Aᴄᴛɪᴠᴇ" if edit_checker == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        nsfw_status = "🟢 Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "🔴 Iɴᴀᴄᴛɪᴠᴇ"
        
        msg = f"🛡️ <b>{title}</b>\n\n"
        msg += f"🔍 Bɪᴏ Lɪɴᴋ Dᴇᴛᴇᴄᴛᴏʀ: {bio_status}\n"
        msg += f"✏️ Mᴇssᴀɢᴇ Eᴅɪᴛ Gᴜᴀʀᴅ: {edit_status}\n"
        msg += f"🚫 NSFW Cᴏɴᴛᴇɴᴛ Fɪʟᴛᴇʀ: {nsfw_status}"
        
        return msg
    
    @staticmethod
    async def show_settings(call_or_message, chat_id, is_callback=True):
        """Display settings panel"""
        settings = await SettingsPanel.get_settings(chat_id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        
        kb = SettingsPanel.build_main_menu(limit, penalty, apply_to, edit_checker, 
                                          bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, 
                                          bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty)
        msg = SettingsPanel.build_status_message(bio_checker_enabled, edit_checker, nsfw_checker_enabled)
        
        if is_callback:
            try:
                await call_or_message.message.edit_text(msg, reply_markup=kb.as_markup())
            except Exception:
                # If editing fails (e.g., photo message), delete and send new
                try:
                    await call_or_message.message.delete()
                except:
                    pass
                await call_or_message.message.answer(msg, reply_markup=kb.as_markup())
            await call_or_message.answer()
        else:
            await call_or_message.reply(msg, reply_markup=kb.as_markup())
    
    @staticmethod
    async def toggle_bio_checker(call):
        """Toggle bio checker on/off"""
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT bio_checker_enabled FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET bio_checker_enabled=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Bɪᴏ Cʜᴇᴄᴋᴇʀ {status}")
                else:
                    await call.answer("✅ Bɪᴏ Cʜᴇᴄᴋᴇʀ Eɴᴀʙʟᴇᴅ")
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    @staticmethod
    async def toggle_edit_checker(call):
        """Toggle edit checker on/off"""
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT edit_checker FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET edit_checker=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ {status}")
                else:
                    await call.answer("✅ Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ Eɴᴀʙʟᴇᴅ")
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    @staticmethod
    async def toggle_nsfw_checker(call):
        """Toggle NSFW checker on/off"""
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT nsfw_checker_enabled FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET nsfw_checker_enabled=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ NSFW Cʜᴇᴄᴋᴇʀ {status}")
                else:
                    await call.answer("✅ NSFW Cʜᴇᴄᴋᴇʀ Eɴᴀʙʟᴇᴅ")
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    @staticmethod
    async def revert_settings(chat_id):
        """Reset all settings to default values"""
        async with aiosqlite.connect("bio_guard.db") as db:
            await db.execute("""
                UPDATE settings SET 
                    warn_limit=?, penalty=?, apply_to=?, edit_checker=?,
                    bio_apply_to=?, bio_penalty=?, edit_apply_to=?, edit_penalty=?,
                    bio_checker_enabled=?, nsfw_checker_enabled=?, nsfw_apply_to=?, nsfw_penalty=?,
                    nsfw_check_name=?, nsfw_check_username=?, nsfw_check_bio=?, nsfw_check_messages=?
                WHERE chat_id=?
            """, (3, "mute", "members", 1, "members", "mute", "members", "mute", 1, 1, "members", "mute", 1, 1, 1, 1, chat_id))
            await db.commit()
    
    @staticmethod
    async def update_setting(field, value, call):
        """Update a specific setting field"""
        async with aiosqlite.connect("bio_guard.db") as db:
            await db.execute(f"UPDATE settings SET {field}=? WHERE chat_id=?", 
                           (value, call.message.chat.id))
            await db.commit()
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)


# Callback handlers for settings
def register_settings_handlers(dp, bot):
    """Register all settings-related callback handlers"""
    
    @dp.callback_query(lambda c: c.data == "open_settings_menu")
    async def open_settings_callback(call: types.CallbackQuery):
        """Handle settings button click"""
        # Check if in a group chat
        if call.message.chat.type not in ["group", "supergroup"]:
            await call.answer("Sᴇᴛᴛɪɴɢs ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴀᴄᴄᴇssᴇᴅ ɪɴ ɢʀᴏᴜᴘs!", show_alert=True)
            return
        
        # Check admin permissions
        chat_member = await bot.get_chat_member(call.message.chat.id, call.from_user.id)
        if chat_member.status not in ["creator", "administrator"]:
            await call.answer("Oɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴀᴄᴄᴇss sᴇᴛᴛɪɴɢs!", show_alert=True)
            return
        
        # Check if admin has ban permission
        if chat_member.status == "administrator":
            if not chat_member.can_restrict_members:
                await call.answer("Yᴏᴜ ɴᴇᴇᴅ ʙᴀɴ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴀᴄᴄᴇss sᴇᴛᴛɪɴɢs!", show_alert=True)
                return
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    @dp.callback_query(lambda c: c.data == "toggle_bio_checker")
    async def toggle_bio_handler(call: types.CallbackQuery):
        await SettingsPanel.toggle_bio_checker(call)
    
    @dp.callback_query(lambda c: c.data == "toggle_edit_checker")
    async def toggle_edit_handler(call: types.CallbackQuery):
        await SettingsPanel.toggle_edit_checker(call)
    
    @dp.callback_query(lambda c: c.data == "save_and_close")
    async def close_settings_handler(call: types.CallbackQuery):
        await call.message.delete()
        await call.answer("✅ Sᴇᴛᴛɪɴɢs sᴀᴠᴇᴅ!")
    
    @dp.callback_query(lambda c: c.data == "noop")
    async def noop_handler(call: types.CallbackQuery):
        await call.answer()
    
    # Bio Settings Menu Handler
    @dp.callback_query(lambda c: c.data == "bio_settings_menu")
    async def bio_settings_menu_handler(call: types.CallbackQuery):
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        
        kb = SettingsPanel.build_bio_settings_menu(bio_apply_to, bio_penalty, bio_checker_enabled)
        
        status = "Aᴄᴛɪᴠᴇ" if bio_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🔍 <b>Bɪᴏ Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
        await call.answer()
    
    # Edit Settings Menu Handler
    @dp.callback_query(lambda c: c.data == "edit_settings_menu")
    async def edit_settings_menu_handler(call: types.CallbackQuery):
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        
        kb = SettingsPanel.build_edit_settings_menu(edit_apply_to, edit_penalty, edit_checker)
        
        status = "Aᴄᴛɪᴠᴇ" if edit_checker == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"✏️ <b>Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
        await call.answer()
    
    # NSFW Settings Menu Handler
    @dp.callback_query(lambda c: c.data == "nsfw_settings_menu")
    async def nsfw_settings_menu_handler(call: types.CallbackQuery):
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        
        kb = SettingsPanel.build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled,
                                                   nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages)
        
        status = "Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🚫 <b>NSFW Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
        await call.answer()
    
    # Warn Limit Handlers
    @dp.callback_query(lambda c: c.data == "change_limit")
    async def change_limit_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        kb.button(text="➖ Dᴇᴄʀᴇᴀsᴇ", callback_data="limit_down")
        kb.button(text="➕ Iɴᴄʀᴇᴀsᴇ", callback_data="limit_up")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(2)
        
        await call.message.edit_text("⚠️ Aᴅᴊᴜsᴛ Wᴀʀɴ Lɪᴍɪᴛ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data == "limit_up")
    async def limit_up_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT warn_limit FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    new_limit = min(row[0] + 1, 10)
                    await db.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", 
                                   (new_limit, call.message.chat.id))
                    await db.commit()
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
        await call.answer("✅ Wᴀʀɴ ʟɪᴍɪᴛ ɪɴᴄʀᴇᴀsᴇᴅ")
    
    @dp.callback_query(lambda c: c.data == "limit_down")
    async def limit_down_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT warn_limit FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    new_limit = max(row[0] - 1, 1)
                    await db.execute("UPDATE settings SET warn_limit=? WHERE chat_id=?", 
                                   (new_limit, call.message.chat.id))
                    await db.commit()
        
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
        await call.answer("✅ Wᴀʀɴ ʟɪᴍɪᴛ ᴅᴇᴄʀᴇᴀsᴇᴅ")
    
    # Penalty Handlers
    @dp.callback_query(lambda c: c.data == "change_penalty")
    async def change_penalty_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        for p in ["mute", "kick", "ban"]:
            kb.button(text=p.upper(), callback_data=f"set_penalty_{p}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("🎯 Sᴇʟᴇᴄᴛ Dᴇғᴀᴜʟᴛ Pᴇɴᴀʟᴛʏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_penalty_"))
    async def set_penalty_handler(call: types.CallbackQuery):
        penalty = call.data.split("_")[2]
        await SettingsPanel.update_setting("penalty", penalty, call)
        await call.answer(f"✅ Pᴇɴᴀʟᴛʏ sᴇᴛ ᴛᴏ {penalty.upper()}")
    
    # Apply To Handler
    @dp.callback_query(lambda c: c.data == "change_apply")
    async def change_apply_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        options = [
            ("members", "Mᴇᴍʙᴇʀs Oɴʟʏ"),
            ("admins", "Aᴅᴍɪɴs Oɴʟʏ"),
            ("members_and_admins", "Mᴇᴍʙᴇʀs & Aᴅᴍɪɴs"),
            ("everyone", "Eᴠᴇʀʏᴏɴᴇ")
        ]
        for value, label in options:
            kb.button(text=label, callback_data=f"set_apply_{value}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("👤 Aᴘᴘʟʏ Sᴇᴛᴛɪɴɢs Tᴏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_apply_"))
    async def set_apply_handler(call: types.CallbackQuery):
        apply_to = call.data.split("_")[2]
        await SettingsPanel.update_setting("apply_to", apply_to, call)
        await call.answer(f"✅ Aᴘᴘʟʏ ᴛᴏ: {apply_to.replace('_', ' ').title()}")
    
    # Bio Apply To Handler
    @dp.callback_query(lambda c: c.data == "bio_apply_to")
    async def bio_apply_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        options = [
            ("members", "Mᴇᴍʙᴇʀs Oɴʟʏ"),
            ("everyone", "Eᴠᴇʀʏᴏɴᴇ")
        ]
        for value, label in options:
            kb.button(text=label, callback_data=f"set_bio_apply_{value}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("👥 Bɪᴏ Cʜᴇᴄᴋᴇʀ - Aᴘᴘʟʏ Tᴏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_bio_apply_"))
    async def set_bio_apply_handler(call: types.CallbackQuery):
        apply_to = call.data.split("_")[3]
        await SettingsPanel.update_setting("bio_apply_to", apply_to, call)
        await call.answer(f"✅ Bɪᴏ ᴀᴘᴘʟʏ ᴛᴏ: {apply_to.replace('_', ' ').title()}")
    
    # Bio Penalty Handler
    @dp.callback_query(lambda c: c.data == "bio_penalty")
    async def bio_penalty_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        for p in ["warn", "mute", "kick", "ban"]:
            kb.button(text=p.upper(), callback_data=f"set_bio_penalty_{p}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("⚡ Bɪᴏ Cʜᴇᴄᴋᴇʀ - Pᴇɴᴀʟᴛʏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_bio_penalty_"))
    async def set_bio_penalty_handler(call: types.CallbackQuery):
        penalty = call.data.split("_")[3]
        await SettingsPanel.update_setting("bio_penalty", penalty, call)
        await call.answer(f"✅ Bɪᴏ ᴘᴇɴᴀʟᴛʏ: {penalty.upper()}")
    
    # Edit Apply To Handler
    @dp.callback_query(lambda c: c.data == "edit_apply_to")
    async def edit_apply_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        options = [
            ("members", "Mᴇᴍʙᴇʀs Oɴʟʏ"),
            ("everyone", "Eᴠᴇʀʏᴏɴᴇ")
        ]
        for value, label in options:
            kb.button(text=label, callback_data=f"set_edit_apply_{value}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("👥 Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ - Aᴘᴘʟʏ Tᴏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_edit_apply_"))
    async def set_edit_apply_handler(call: types.CallbackQuery):
        apply_to = call.data.split("_")[3]
        await SettingsPanel.update_setting("edit_apply_to", apply_to, call)
        await call.answer(f"✅ Eᴅɪᴛ ᴀᴘᴘʟʏ ᴛᴏ: {apply_to.replace('_', ' ').title()}")
    
    # Edit Penalty Handler
    @dp.callback_query(lambda c: c.data == "edit_penalty")
    async def edit_penalty_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        for p in ["warn", "mute", "kick", "ban"]:
            kb.button(text=p.upper(), callback_data=f"set_edit_penalty_{p}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("⚡ Eᴅɪᴛ Cʜᴇᴄᴋᴇʀ - Pᴇɴᴀʟᴛʏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_edit_penalty_"))
    async def set_edit_penalty_handler(call: types.CallbackQuery):
        penalty = call.data.split("_")[3]
        await SettingsPanel.update_setting("edit_penalty", penalty, call)
        await call.answer(f"✅ Eᴅɪᴛ ᴘᴇɴᴀʟᴛʏ: {penalty.upper()}")
    
    # NSFW Toggle Handler
    @dp.callback_query(lambda c: c.data == "toggle_nsfw_checker")
    async def toggle_nsfw_handler(call: types.CallbackQuery):
        await SettingsPanel.toggle_nsfw_checker(call)
    
    # NSFW Apply To Handler
    @dp.callback_query(lambda c: c.data == "nsfw_apply_to")
    async def nsfw_apply_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        options = [
            ("members", "Mᴇᴍʙᴇʀs Oɴʟʏ"),
            ("everyone", "Eᴠᴇʀʏᴏɴᴇ")
        ]
        for value, label in options:
            kb.button(text=label, callback_data=f"set_nsfw_apply_{value}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("👥 NSFW Cʜᴇᴄᴋᴇʀ - Aᴘᴘʟʏ Tᴏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_nsfw_apply_"))
    async def set_nsfw_apply_handler(call: types.CallbackQuery):
        apply_to = call.data.split("_")[3]
        await SettingsPanel.update_setting("nsfw_apply_to", apply_to, call)
        await call.answer(f"✅ NSFW ᴀᴘᴘʟʏ ᴛᴏ: {apply_to.replace('_', ' ').title()}")
    
    # NSFW Penalty Handler
    @dp.callback_query(lambda c: c.data == "nsfw_penalty")
    async def nsfw_penalty_handler(call: types.CallbackQuery):
        kb = InlineKeyboardBuilder()
        for p in ["warn", "mute", "kick", "ban"]:
            kb.button(text=p.upper(), callback_data=f"set_nsfw_penalty_{p}")
        kb.button(text="↩️ Bᴀᴄᴋ", callback_data="back_to_settings")
        kb.adjust(1)
        
        await call.message.edit_text("⚡ NSFW Cʜᴇᴄᴋᴇʀ - Pᴇɴᴀʟᴛʏ:", reply_markup=kb.as_markup())
        await call.answer()
    
    @dp.callback_query(lambda c: c.data.startswith("set_nsfw_penalty_"))
    async def set_nsfw_penalty_handler(call: types.CallbackQuery):
        penalty = call.data.split("_")[3]
        await SettingsPanel.update_setting("nsfw_penalty", penalty, call)
        await call.answer(f"✅ NSFW ᴘᴇɴᴀʟᴛʏ: {penalty.upper()}")
    
    @dp.callback_query(lambda c: c.data == "back_to_settings")
    async def back_to_settings_handler(call: types.CallbackQuery):
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    @dp.callback_query(lambda c: c.data == "revert_settings")
    async def revert_settings_handler(call: types.CallbackQuery):
        """Handle revert settings button click"""
        await SettingsPanel.revert_settings(call.message.chat.id)
        await call.answer("✅ Aʟʟ sᴇᴛᴛɪɴɢs ʀᴇᴠᴇʀᴛᴇᴅ ᴛᴏ ᴅᴇғᴀᴜʟᴛs!")
        await SettingsPanel.show_settings(call, call.message.chat.id, is_callback=True)
    
    # NSFW Check Name Toggle
    @dp.callback_query(lambda c: c.data == "toggle_nsfw_check_name")
    async def toggle_nsfw_check_name_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT nsfw_check_name FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET nsfw_check_name=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Nᴀᴍᴇ ᴄʜᴇᴄᴋ {status}")
        
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        kb = SettingsPanel.build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled,
                                                   nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages)
        status = "Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🚫 <b>NSFW Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
    
    # NSFW Check Username Toggle
    @dp.callback_query(lambda c: c.data == "toggle_nsfw_check_username")
    async def toggle_nsfw_check_username_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT nsfw_check_username FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET nsfw_check_username=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Usᴇʀɴᴀᴍᴇ ᴄʜᴇᴄᴋ {status}")
        
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        kb = SettingsPanel.build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled,
                                                   nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages)
        status = "Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🚫 <b>NSFW Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
    
    # NSFW Check Bio Toggle
    @dp.callback_query(lambda c: c.data == "toggle_nsfw_check_bio")
    async def toggle_nsfw_check_bio_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT nsfw_check_bio FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET nsfw_check_bio=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Bɪᴏ ᴄʜᴇᴄᴋ {status}")
        
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        kb = SettingsPanel.build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled,
                                                   nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages)
        status = "Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🚫 <b>NSFW Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
    
    # NSFW Check Messages Toggle
    @dp.callback_query(lambda c: c.data == "toggle_nsfw_check_messages")
    async def toggle_nsfw_check_messages_handler(call: types.CallbackQuery):
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("SELECT nsfw_check_messages FROM settings WHERE chat_id = ?", 
                                (call.message.chat.id,)) as cur:
                row = await cur.fetchone()
                if row:
                    current = row[0]
                    new_value = 0 if current == 1 else 1
                    await db.execute("UPDATE settings SET nsfw_check_messages=? WHERE chat_id=?", 
                                   (new_value, call.message.chat.id))
                    await db.commit()
                    status = "Eɴᴀʙʟᴇᴅ" if new_value == 1 else "Dɪsᴀʙʟᴇᴅ"
                    await call.answer(f"✅ Mᴇssᴀɢᴇ ᴄʜᴇᴄᴋ {status}")
        
        settings = await SettingsPanel.get_settings(call.message.chat.id)
        limit, penalty, apply_to, edit_checker, bio_apply_to, bio_penalty, edit_apply_to, edit_penalty, bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = settings
        kb = SettingsPanel.build_nsfw_settings_menu(nsfw_apply_to, nsfw_penalty, nsfw_checker_enabled,
                                                   nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages)
        status = "Aᴄᴛɪᴠᴇ" if nsfw_checker_enabled == 1 else "Iɴᴀᴄᴛɪᴠᴇ"
        msg = f"🚫 <b>NSFW Cʜᴇᴄᴋᴇʀ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: {status}"
        await call.message.edit_text(msg, reply_markup=kb.as_markup())
