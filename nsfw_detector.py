"""
NSFW Content Detection Module for Bio Guard Bot
Detects and handles NSFW/inappropriate text content in messages
Supports both keyword-based and AI-powered detection with advanced text normalization
"""

import re
import json
import os
import asyncio
import unicodedata
import aiosqlite
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from font import Fonts

# Try to import OpenAI (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class NSFWDetector:
    """Detects and handles NSFW text content in messages"""
    
    # Default NSFW keywords
    DEFAULT_KEYWORDS = [
        "sex", "porn", "xxx", "nude", "fuck", "boobs", "dick", "pussy",
        "hentai", "rape", "cum", "blowjob", "ass", "bitch", "chut",
        "lund", "randi", "chutiya", "bastard", "slut", "whore",
        "kill", "murder", "blood", "gore",
        "cocaine", "heroin", "meth", "lsd"
    ]
    
    def __init__(self, openai_api_key=""):
        self.openai_client = None
        self.ai_enabled = False
        
        if openai_api_key and OPENAI_AVAILABLE:
            try:
                # Check if it's an OpenAI key (starts with sk-) or Groq key (starts with gsk_)
                if openai_api_key.startswith("sk-"):
                    self.openai_client = OpenAI(api_key=openai_api_key)
                    print("✅ OpenAI moderation enabled")
                    self.ai_enabled = True
                elif openai_api_key.startswith("gsk_"):
                    print("⚠️ Groq API key detected - AI moderation not supported, using keyword detection only")
                else:
                    print("⚠️ Unknown API key format - using keyword detection only")
            except Exception as e:
                print(f"⚠️ OpenAI initialization failed: {e}")
        
        # Load custom words from file
        self.custom_words_file = "nsfw_words.json"
        self.nsfw_keywords = self.load_custom_words()
        
        # Regex patterns for obfuscated text detection
        self.regex_patterns = [
            r"s\s*e\s*x",
            r"k\s*i\s*l\s*l",
            r"p\s*o\s*r\s*n",
            r"d\s*r\s*u\s*g",
            r"r\s*a\s*p\s*e",
            r"n\s*u\s*d\s*e",
            r"f\s*u\s*c\s*k",
            r"s\s*h\s*i\s*t",
            r"b\s*i\s*t\s*c\s*h",
            r"a\s*s\s*s",
            r"d\s*i\s*c\s*k",
            r"c\s*u\s*m"
        ]
    
    def load_custom_words(self):
        """Load custom NSFW words from JSON file"""
        try:
            if os.path.exists(self.custom_words_file):
                with open(self.custom_words_file, "r", encoding="utf-8") as f:
                    words = json.load(f)
                    print(f"📝 Loaded {len(words)} custom NSFW words")
                    return words
        except Exception as e:
            print(f"Error loading custom words: {e}")
        
        # Use default words if file doesn't exist
        self.save_custom_words(self.DEFAULT_KEYWORDS)
        return self.DEFAULT_KEYWORDS.copy()
    
    def save_custom_words(self, words):
        """Save custom NSFW words to JSON file"""
        try:
            with open(self.custom_words_file, "w", encoding="utf-8") as f:
                json.dump(words, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving custom words: {e}")
    
    def add_word(self, word):
        """Add a new NSFW word"""
        word_lower = word.lower().strip()
        if word_lower not in self.nsfw_keywords:
            self.nsfw_keywords.append(word_lower)
            self.save_custom_words(self.nsfw_keywords)
            return True
        return False
    
    def remove_word(self, word):
        """Remove an NSFW word"""
        word_lower = word.lower().strip()
        if word_lower in self.nsfw_keywords:
            self.nsfw_keywords.remove(word_lower)
            self.save_custom_words(self.nsfw_keywords)
            return True
        return False
    
    @staticmethod
    def normalize_text(text):
        """Normalize text to bypass Unicode/font obfuscation"""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove spaces between letters (e.g., "s e x" -> "sex")
        text = re.sub(r'(\w)\s+(\w)', r'\1\2', text)
        
        # Remove symbols and special characters
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        
        # Normalize Unicode fonts (e.g., fancy fonts to normal)
        text = unicodedata.normalize('NFKD', text)
        
        # Remove combining characters (accents, diacritics)
        text = ''.join(
            c for c in unicodedata.normalize('NFKD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        return text
    
    def regex_check(self, text):
        """Check text using regex patterns for obfuscated words"""
        if not text:
            return False
        
        clean_text = self.normalize_text(text)
        
        for pattern in self.regex_patterns:
            if re.search(pattern, clean_text):
                return True
        
        return False
    
    def contains_nsfw_keyword(self, text):
        """Check if text contains NSFW keywords using regex with normalization"""
        if not text:
            return False
        
        # Normalize text first to bypass obfuscation
        clean_text = self.normalize_text(text)
        text_lower = clean_text.lower()
        
        for keyword in self.nsfw_keywords:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, text_lower):
                return True
        return False
    
    async def contains_nsfw_ai(self, text):
        """Check text using OpenAI moderation API with detailed category detection"""
        if not self.openai_client or not text:
            return False, None
        
        try:
            response = self.openai_client.moderations.create(
                model="omni-moderation-latest",
                input=text
            )
            
            result = response.results[0]
            categories = result.categories
            
            # Check all harmful categories
            is_harmful = (
                result.flagged
                or categories.sexual
                or categories.sexual_minors
                or categories.violence
                or categories.violence_graphic
                or categories.hate
                or categories.harassment
                or categories.self_harm
                or categories.illicit
                or categories.illicit_violent
            )
            
            if is_harmful:
                # Return detailed category information
                category_details = {
                    'sexual': categories.sexual,
                    'sexual_minors': categories.sexual_minors,
                    'violence': categories.violence,
                    'violence_graphic': categories.violence_graphic,
                    'hate': categories.hate,
                    'harassment': categories.harassment,
                    'self_harm': categories.self_harm,
                    'illicit': categories.illicit,
                    'illicit_violent': categories.illicit_violent
                }
                return True, category_details
            
            return False, None
        except Exception as e:
            print(f"OpenAI moderation error: {e}")
            return False, None
    
    async def contains_nsfw(self, text):
        """Check if text contains NSFW content (keyword + regex + AI)"""
        keyword_detected = self.contains_nsfw_keyword(text)
        regex_detected = self.regex_check(text)
        ai_detected, category_details = await self.contains_nsfw_ai(text) if self.openai_client else (False, None)
        
        return (keyword_detected or regex_detected or ai_detected), category_details
    
    async def check_message(self, message: types.Message, bot, log_channel_id=""):
        """Check a message for NSFW content"""
        if message.chat.type not in ["group", "supergroup"]:
            return
        
        # Get message text
        text = message.text or message.caption or ""
        
        nsfw_detected, category_details = await self.contains_nsfw(text)
        
        if not nsfw_detected:
            return
        
        print(f"🚫 NSFW content detected from user {message.from_user.id}")
        
        # Send detailed log to log channel if configured
        if log_channel_id and category_details:
            try:
                log_msg = f"""
🚨 <b>Harmful Text Detected</b>

👤 <b>User:</b> {message.from_user.mention(html=True)} (ID: <code>{message.from_user.id}</code>)
💬 <b>Message:</b> {text[:500]}

📊 <b>AI Detection Categories:</b>
• Sexual: {category_details['sexual']}
• Violence: {category_details['violence']}
• Hate: {category_details['hate']}
• Harassment: {category_details['harassment']}
• Self-harm: {category_details['self_harm']}
• Drugs/Illicit: {category_details['illicit']}
"""
                await bot.send_message(log_channel_id, log_msg)
            except Exception as e:
                print(f"Failed to send log: {e}")
        
        # Get settings
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("""
                SELECT warn_limit, penalty, apply_to, nsfw_checker_enabled,
                       nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages
                FROM settings WHERE chat_id = ?
            """, (message.chat.id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    # Create default settings with NSFW columns
                    await db.execute("""
                        INSERT INTO settings (chat_id, warn_limit, penalty, apply_to, edit_checker,
                                            bio_apply_to, bio_penalty, edit_apply_to, edit_penalty,
                                            bio_checker_enabled, nsfw_checker_enabled, nsfw_apply_to, nsfw_penalty,
                                            nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (message.chat.id, 3, "mute", "members", 1, "members", "mute", "members", "mute", 1, 1, "members", "mute", 1, 1, 1, 1))
                    await db.commit()
                    limit, penalty, apply_to, nsfw_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = 3, "mute", "members", 1, "members", "mute", 1, 1, 1, 1
                else:
                    # Handle case where NSFW columns might not exist yet
                    if len(row) == 10:
                        limit, penalty, apply_to, nsfw_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = row
                    elif len(row) == 9:
                        limit, penalty, apply_to, nsfw_enabled, nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio = row
                        nsfw_check_messages = 1
                    elif len(row) == 6:
                        # Old schema without new NSFW columns
                        limit, penalty, apply_to, nsfw_enabled, nsfw_apply_to, nsfw_penalty = row
                        nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = 1, 1, 1, 1
                    else:
                        # Very old schema
                        limit, penalty, apply_to, nsfw_enabled = row[0], row[1], row[2], 1
                        nsfw_apply_to, nsfw_penalty = "members", "mute"
                        nsfw_check_name, nsfw_check_username, nsfw_check_bio, nsfw_check_messages = 1, 1, 1, 1
        
        # Check if NSFW checker is enabled
        if nsfw_enabled == 0:
            return
        
        # Check if message scanning is enabled
        if nsfw_check_messages == 0:
            return
        
        # Check if user should be affected based on nsfw_apply_to setting
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        user_status = chat_member.status
        
        should_apply = False
        
        if nsfw_apply_to == "members":
            if user_status in ["member", "left"]:
                should_apply = True
        elif nsfw_apply_to == "admins":
            if user_status in ["administrator", "creator"]:
                should_apply = True
        elif nsfw_apply_to == "members_and_admins":
            if user_status in ["member", "administrator", "creator"]:
                should_apply = True
        elif nsfw_apply_to == "everyone":
            should_apply = True
        
        if not should_apply:
            return
        
        # Increment warning count
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
        
        # Show warning message (only buttons if penalty is not "warn")
        kb = InlineKeyboardBuilder()
        if nsfw_penalty != "warn":
            kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{message.from_user.id}")
            kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{message.from_user.id}")
            kb.adjust(2)
        
        warning_text = Fonts.mono_upper("NSFW content detected!")
        warning_msg = await message.reply(
            f"🚫 {warning_text}\n{Fonts.mono_upper('Inappropriate content is not allowed')}",
            reply_markup=kb.as_markup() if nsfw_penalty != "warn" else None
        )
        
        # Delete the NSFW message immediately
        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete NSFW message: {e}")
        
        # Delete warning after 30 seconds
        async def delete_warning():
            await asyncio.sleep(30)
            try:
                await warning_msg.delete()
            except:
                pass
        
        asyncio.create_task(delete_warning())
        
        # Apply penalty if warning limit reached
        if count >= limit:
            bot_member = await bot.get_chat_member(message.chat.id, bot.id)
            penalty_kb = InlineKeyboardBuilder()
            penalty_kb.adjust(1)
            action_taken = False
            
            if nsfw_penalty == "warn":
                action_taken = True
                # Don't send warning message when penalty is warn
                # Just increment the warning count silently
            elif nsfw_penalty == "mute" and bot_member.can_restrict_members:
                await bot.restrict_chat_member(message.chat.id, message.from_user.id, 
                                             permissions=types.ChatPermissions(can_send_messages=False))
                penalty_kb.button(text="✅ Unmute User", callback_data=f"unmute_{message.from_user.id}")
                action_taken = True
                penalty_text = Fonts.mono_upper("Muted!")
                await message.answer(
                    f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                    reply_markup=penalty_kb.as_markup()
                )
            elif nsfw_penalty == "kick" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                await bot.unban_chat_member(message.chat.id, message.from_user.id)
                penalty_kb.button(text="🔄 Re-add User", callback_data=f"readd_{message.from_user.id}")
                action_taken = True
                penalty_text = Fonts.mono_upper("Kicked!")
                await message.answer(
                    f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                    reply_markup=penalty_kb.as_markup()
                )
            elif nsfw_penalty == "ban" and bot_member.can_restrict_members:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                penalty_kb.button(text="🔓 Unban User", callback_data=f"unban_{message.from_user.id}")
                action_taken = True
                penalty_text = Fonts.mono_upper("Banned!")
                await message.answer(
                    f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                    reply_markup=penalty_kb.as_markup()
                )
            
            if not action_taken and nsfw_penalty != "warn":
                await message.answer(
                    f"🚨 {Fonts.mono_upper(f'User reached {limit} warnings')}\n{Fonts.mono_upper('Bot needs admin permission')}"
                )
    
    async def check_user_profile(self, chat_member: types.ChatMemberUpdated, bot, log_channel_id=""):
        """Check user's name, username, and bio for NSFW content when they join"""
        if chat_member.chat.type not in ["group", "supergroup"]:
            return
        
        # Get the new member
        user = chat_member.new_chat_member.user
        
        # Get settings
        async with aiosqlite.connect("bio_guard.db") as db:
            async with db.execute("""
                SELECT warn_limit, penalty, apply_to, nsfw_checker_enabled,
                       nsfw_apply_to, nsfw_penalty, nsfw_check_name, nsfw_check_username, nsfw_check_bio
                FROM settings WHERE chat_id = ?
            """, (chat_member.chat.id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return
                
                limit, penalty, apply_to, nsfw_enabled, nsfw_apply_to, nsfw_penalty = row[0], row[1], row[2], row[3], row[4], row[5]
                nsfw_check_name = row[6] if len(row) > 6 else 1
                nsfw_check_username = row[7] if len(row) > 7 else 1
                nsfw_check_bio = row[8] if len(row) > 8 else 1
        
        # Check if NSFW checker is enabled
        if nsfw_enabled == 0:
            return
        
        # Collect texts to check based on settings
        texts_to_check = []
        
        if nsfw_check_name == 1 and user.first_name:
            texts_to_check.append(("name", user.first_name))
        
        if nsfw_check_username == 1 and user.username:
            texts_to_check.append(("username", f"@{user.username}"))
        
        # Get user bio from get_chat
        if nsfw_check_bio == 1:
            try:
                chat_full = await bot.get_chat(user.id)
                if chat_full.description:  # Bio is stored in description for users
                    texts_to_check.append(("bio", chat_full.description))
            except Exception as e:
                print(f"Could not fetch user bio: {e}")
        
        # Check each text for NSFW content
        for text_type, text in texts_to_check:
            nsfw_detected, category_details = await self.contains_nsfw(text)
            if nsfw_detected:
                print(f"🚫 NSFW {text_type} detected for user {user.id}: {text}")
                
                # Send detailed log to log channel if configured
                if log_channel_id and category_details:
                    try:
                        log_msg = f"""
🚨 <b>Harmful Profile Detected</b>

👤 <b>User:</b> {user.mention(html=True)} (ID: <code>{user.id}</code>)
🆔 <b>Username:</b> @{user.username or 'None'}
📝 <b>{text_type.title()}:</b> {text[:500]}

📊 <b>AI Detection Categories:</b>
• Sexual: {category_details['sexual']}
• Violence: {category_details['violence']}
• Hate: {category_details['hate']}
• Harassment: {category_details['harassment']}
• Self-harm: {category_details['self_harm']}
• Drugs/Illicit: {category_details['illicit']}
"""
                        await bot.send_message(log_channel_id, log_msg)
                    except Exception as e:
                        print(f"Failed to send log: {e}")
                
                # Check if user should be affected based on nsfw_apply_to setting
                user_status = chat_member.new_chat_member.status
                
                should_apply = False
                
                if nsfw_apply_to == "members":
                    if user_status in ["member", "left"]:
                        should_apply = True
                elif nsfw_apply_to == "admins":
                    if user_status in ["administrator", "creator"]:
                        should_apply = True
                elif nsfw_apply_to == "members_and_admins":
                    if user_status in ["member", "administrator", "creator"]:
                        should_apply = True
                elif nsfw_apply_to == "everyone":
                    should_apply = True
                
                if not should_apply:
                    continue
                
                # Increment warning count
                async with aiosqlite.connect("bio_guard.db") as db:
                    async with db.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", 
                                        (chat_member.chat.id, user.id)) as cur:
                        row = await cur.fetchone()
                        if row:
                            count = row[0] + 1
                            await db.execute("UPDATE warns SET count=? WHERE chat_id=? AND user_id=?", 
                                           (count, chat_member.chat.id, user.id))
                        else:
                            count = 1
                            await db.execute("INSERT INTO warns VALUES (?, ?, ?)", 
                                           (chat_member.chat.id, user.id, count))
                    await db.commit()
                
                # Show warning message
                kb = InlineKeyboardBuilder()
                if nsfw_penalty != "warn":
                    kb.button(text="ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ ✖︎", callback_data=f"remove_warn_{user.id}")
                    kb.button(text="ʀᴇꜱᴇᴛ ᴡᴀʀɴ ✖︎", callback_data=f"reset_warn_{user.id}")
                    kb.adjust(2)
                
                warning_text = Fonts.mono_upper(f"NSFW {text_type} detected!")
                warning_msg = await chat_member.chat.send_message(
                    f"🚫 {warning_text}\n{Fonts.mono_upper(f'Inappropriate {text_type} is not allowed')}",
                    reply_markup=kb.as_markup() if nsfw_penalty != "warn" else None
                )
                
                # Delete warning after 30 seconds
                async def delete_warning():
                    await asyncio.sleep(30)
                    try:
                        await warning_msg.delete()
                    except:
                        pass
                
                asyncio.create_task(delete_warning())
                
                # Apply penalty if warning limit reached
                if count >= limit:
                    bot_member = await bot.get_chat_member(chat_member.chat.id, bot.id)
                    penalty_kb = InlineKeyboardBuilder()
                    penalty_kb.adjust(1)
                    action_taken = False
                    
                    if nsfw_penalty == "warn":
                        action_taken = True
                        # Don't send warning message when penalty is warn
                        # Just increment the warning count silently
                    elif nsfw_penalty == "mute" and bot_member.can_restrict_members:
                        await bot.restrict_chat_member(chat_member.chat.id, user.id, 
                                                     permissions=types.ChatPermissions(can_send_messages=False))
                        penalty_kb.button(text="✅ Unmute User", callback_data=f"unmute_{user.id}")
                        action_taken = True
                        penalty_text = Fonts.mono_upper("Muted!")
                        await chat_member.chat.send_message(
                            f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                            reply_markup=penalty_kb.as_markup()
                        )
                    elif nsfw_penalty == "kick" and bot_member.can_restrict_members:
                        await bot.ban_chat_member(chat_member.chat.id, user.id)
                        await bot.unban_chat_member(chat_member.chat.id, user.id)
                        penalty_kb.button(text="🔄 Re-add User", callback_data=f"readd_{user.id}")
                        action_taken = True
                        penalty_text = Fonts.mono_upper("Kicked!")
                        await chat_member.chat.send_message(
                            f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                            reply_markup=penalty_kb.as_markup()
                        )
                    elif nsfw_penalty == "ban" and bot_member.can_restrict_members:
                        await bot.ban_chat_member(chat_member.chat.id, user.id)
                        penalty_kb.button(text="🔓 Unban User", callback_data=f"unban_{user.id}")
                        action_taken = True
                        penalty_text = Fonts.mono_upper("Banned!")
                        await chat_member.chat.send_message(
                            f"⚠️ {penalty_text} {Fonts.mono_upper(f'Warning limit ({count}/{limit})')}",
                            reply_markup=penalty_kb.as_markup()
                        )
                    
                    if not action_taken and nsfw_penalty != "warn":
                        await chat_member.chat.send_message(
                            f"🚨 {Fonts.mono_upper(f'User reached {limit} warnings')}\n{Fonts.mono_upper('Bot needs admin permission')}"
                        )
                    
                    break  # Only apply penalty once per join


def register_nsfw_handlers(dp, bot, nsfw_detector_instance):
    """Register NSFW detection handlers - now handled in main monitor"""
    # NSFW checking is now integrated into the main message handler
    pass
