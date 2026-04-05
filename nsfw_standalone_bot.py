"""
Advanced NSFW Text Detection Bot
Features:
- Keyword-based detection with customizable word list
- AI-powered content moderation using OpenAI
- Warning system with auto-mute
- Admin commands to manage NSFW words
- Logging channel support
"""

import json
import os
import re
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("NSFW_BOT_TOKEN", "your_bot_token")
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LOG_CHANNEL_STR = os.getenv("LOG_CHANNEL", "")
LOG_CHANNEL = int(LOG_CHANNEL_STR) if LOG_CHANNEL_STR else None

WARN_LIMIT = 3
MUTE_TIME = 600  # 10 minutes in seconds

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class NSFWDetector:
    """NSFW Content Detection System"""
    
    def __init__(self):
        self.words_file = "nsfw_words.json"
        self.warnings_file = "warnings.json"
        self.nsfw_words = self.load_words()
        self.warnings = self.load_warnings()
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ OpenAI moderation enabled")
            except ImportError:
                print("⚠️ OpenAI library not installed. Install with: pip install openai")
    
    def load_words(self):
        """Load NSFW words from JSON file"""
        try:
            if os.path.exists(self.words_file):
                with open(self.words_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading words: {e}")
        
        # Default NSFW words
        default_words = [
            "sex", "porn", "xxx", "nude", "fuck", "boobs", "dick", "pussy",
            "hentai", "rape", "cum", "blowjob", "ass", "bitch", "chut",
            "lund", "randi", "chutiya", "bastard", "slut", "whore"
        ]
        self.save_words(default_words)
        return default_words
    
    def save_words(self, words):
        """Save NSFW words to JSON file"""
        try:
            with open(self.words_file, "w", encoding="utf-8") as f:
                json.dump(words, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving words: {e}")
    
    def load_warnings(self):
        """Load warnings from JSON file"""
        try:
            if os.path.exists(self.warnings_file):
                with open(self.warnings_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading warnings: {e}")
        return {}
    
    def save_warnings(self, data):
        """Save warnings to JSON file"""
        try:
            with open(self.warnings_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving warnings: {e}")
    
    def is_nsfw_keyword(self, text):
        """Check text for NSFW keywords using regex"""
        if not text:
            return False
        
        text_lower = text.lower()
        for word in self.nsfw_words:
            # Use word boundary matching to avoid false positives
            pattern = rf"\b{re.escape(word)}\b"
            if re.search(pattern, text_lower):
                return True
        return False
    
    async def is_nsfw_ai(self, text):
        """Check text using OpenAI moderation API"""
        if not self.openai_client or not text:
            return False
        
        try:
            response = self.openai_client.moderations.create(
                model="omni-moderation-latest",
                input=text
            )
            
            result = response.results[0]
            
            # Check if content is flagged
            if result.flagged:
                return True
            
            # Check specific categories
            if result.categories.sexual or result.categories.sexual_minors:
                return True
            
            return False
        except Exception as e:
            print(f"OpenAI moderation error: {e}")
            return False
    
    async def check_message(self, message: types.Message):
        """Main message checking function"""
        if message.chat.type not in ["group", "supergroup"]:
            return
        
        text = message.text or message.caption or ""
        
        if not text:
            return
        
        # Check using both methods
        keyword_detected = self.is_nsfw_keyword(text)
        ai_detected = await self.is_nsfw_ai(text) if OPENAI_API_KEY else False
        
        if not (keyword_detected or ai_detected):
            return
        
        print(f"🚫 NSFW detected from user {message.from_user.id} in chat {message.chat.id}")
        
        # Delete the NSFW message immediately
        try:
            await message.delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")
            return
        
        # Update warnings
        user_id = str(message.from_user.id)
        self.warnings[user_id] = self.warnings.get(user_id, 0) + 1
        self.save_warnings(self.warnings)
        
        warn_count = self.warnings[user_id]
        
        # Send warning message
        detection_method = "AI + Keywords" if ai_detected and keyword_detected else ("AI" if ai_detected else "Keywords")
        warning_msg = await message.answer(
            f"🚫 <b>NSFW Content Detected!</b>\n"
            f"Method: {detection_method}\n"
            f"⚠️ Warning: {warn_count}/{WARN_LIMIT}"
        )
        
        # Log to channel
        if LOG_CHANNEL:
            try:
                log_text = (
                    f"🚨 <b>NSFW Detected</b>\n"
                    f"User: {message.from_user.mention} (<code>{message.from_user.id}</code>)\n"
                    f"Chat: {message.chat.title} (<code>{message.chat.id}</code>)\n"
                    f"Text: <code>{text[:200]}</code>\n"
                    f"Warnings: {warn_count}/{WARN_LIMIT}\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await bot.send_message(LOG_CHANNEL, log_text)
            except Exception as e:
                print(f"Failed to send log: {e}")
        
        # Apply penalty if warning limit reached
        if warn_count >= WARN_LIMIT:
            try:
                await message.chat.restrict_member(
                    message.from_user.id,
                    ChatPermissions(),
                    until_date=int(asyncio.get_event_loop().time()) + MUTE_TIME
                )
                
                await message.answer(
                    f"🔇 User muted for {MUTE_TIME//60} minutes due to NSFW content"
                )
                
                # Reset warnings after mute
                self.warnings[user_id] = 0
                self.save_warnings(self.warnings)
                
            except Exception as e:
                print(f"Failed to mute user: {e}")
        
        # Auto-delete warning after 30 seconds
        asyncio.create_task(self.auto_delete_warning(warning_msg))
    
    async def auto_delete_warning(self, message):
        """Delete warning message after 30 seconds"""
        await asyncio.sleep(30)
        try:
            await message.delete()
        except:
            pass


# Initialize detector
detector = NSFWDetector()


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Start command handler"""
    welcome_text = (
        "🤖 <b>NSFW Text Protection Bot</b>\n\n"
        "I detect and remove NSFW messages automatically.\n\n"
        "<b>Features:</b>\n"
        "• Keyword-based detection\n"
        "• AI-powered moderation (optional)\n"
        "• Warning system with auto-mute\n"
        "• Customizable word list\n\n"
        "<b>Admin Commands:</b>\n"
        "• /addword - Add NSFW word\n"
        "• /removeword - Remove NSFW word\n"
        "• /words - List all NSFW words\n"
        "• /warns - Check your warnings\n"
        "• /resetwarns - Reset all warnings"
    )
    await message.answer(welcome_text)


@dp.message(Command("addword"))
async def add_word(message: types.Message):
    """Add NSFW word (admin only)"""
    if not message.from_user or message.chat.type == "private":
        return
    
    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("❌ Only admins can use this command")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /addword word")
        return
    
    word = parts[1].lower().strip()
    
    if word in detector.nsfw_words:
        await message.answer(f"⚠️ Word already exists: {word}")
        return
    
    detector.nsfw_words.append(word)
    detector.save_words(detector.nsfw_words)
    
    await message.answer(f"✅ Added NSFW word: <code>{word}</code>")


@dp.message(Command("removeword"))
async def remove_word(message: types.Message):
    """Remove NSFW word (admin only)"""
    if not message.from_user or message.chat.type == "private":
        return
    
    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("❌ Only admins can use this command")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /removeword word")
        return
    
    word = parts[1].lower().strip()
    
    if word in detector.nsfw_words:
        detector.nsfw_words.remove(word)
        detector.save_words(detector.nsfw_words)
        await message.answer(f"❌ Removed NSFW word: <code>{word}</code>")
    else:
        await message.answer("⚠️ Word not found in NSFW list")


@dp.message(Command("words"))
async def list_words(message: types.Message):
    """List all NSFW words (admin only)"""
    if not message.from_user or message.chat.type == "private":
        return
    
    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("❌ Only admins can use this command")
        return
    
    words_list = "\n".join([f"• {word}" for word in detector.nsfw_words])
    await message.answer(
        f"📋 <b>NSFW Words List</b> ({len(detector.nsfw_words)} words):\n\n"
        f"{words_list}"
    )


@dp.message(Command("warns"))
async def check_warns(message: types.Message):
    """Check user's warnings"""
    if not message.from_user:
        return
    
    user_id = str(message.from_user.id)
    count = detector.warnings.get(user_id, 0)
    
    await message.answer(
        f"⚠️ <b>Your Warnings</b>\n"
        f"Current: {count}/{WARN_LIMIT}\n"
        f"Status: {'⚠️ At Risk' if count > 0 else '✅ Clean'}"
    )


@dp.message(Command("resetwarns"))
async def reset_warns(message: types.Message):
    """Reset all warnings (admin only)"""
    if not message.from_user or message.chat.type == "private":
        return
    
    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("❌ Only admins can use this command")
        return
    
    detector.warnings = {}
    detector.save_warnings(detector.warnings)
    
    await message.answer("✅ All warnings have been reset")


@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    """Show bot statistics (admin only)"""
    if not message.from_user or message.chat.type == "private":
        return
    
    # Check if user is admin
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        await message.answer("❌ Only admins can use this command")
        return
    
    total_users_warned = len(detector.warnings)
    total_warnings = sum(detector.warnings.values())
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"Total NSFW Words: {len(detector.nsfw_words)}\n"
        f"Users Warned: {total_users_warned}\n"
        f"Total Warnings Issued: {total_warnings}\n"
        f"Warning Limit: {WARN_LIMIT}\n"
        f"Mute Duration: {MUTE_TIME//60} minutes\n"
        f"AI Moderation: {'✅ Enabled' if OPENAI_API_KEY else '❌ Disabled'}"
    )
    
    await message.answer(stats_text)


@dp.message()
async def message_handler(message: types.Message):
    """Handle all messages for NSFW detection"""
    if message.chat.type in ["group", "supergroup"]:
        await detector.check_message(message)


async def main():
    """Main function to start the bot"""
    print("🛡️ NSFW Detection Bot Starting...")
    print(f"📝 Loaded {len(detector.nsfw_words)} NSFW words")
    print(f"⚠️ Warning limit: {WARN_LIMIT}")
    print(f"🔇 Mute duration: {MUTE_TIME//60} minutes")
    print(f"🤖 AI Moderation: {'Enabled' if OPENAI_API_KEY else 'Disabled'}")
    print("="*50)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
