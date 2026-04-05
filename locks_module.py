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
            # Check if sticker is allowlisted
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
                # Check if URL is allowlisted
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
            # Check if command is allowlisted
            command = message.text.split()[0][1:]  # Remove the /
            if f"/{command}" not in allowlist and command not in allowlist:
                should_delete = True
        
        # Emoji lock
        elif lock_type == "emoji":
            text = message.text or ""
            import emoji
            if any(char in emoji.EMOJI_DATA for char in text):
                should_delete = True
        
        if should_delete:
            try:
                await message.delete()
                
                # Send warning if enabled
                if warn_enabled:
                    warning = await message.reply(
                        f"⚠️ This type of message is locked in this group.",
                        reply_to_message_id=message.message_id if hasattr(message, 'message_id') else None
                    )
                    asyncio.create_task(delete_after_delay(warning, 30))
                
                await log_activity("lock_trigger", message.from_user.id if message.from_user else 0,
                                 message.from_user.username if message.from_user else "Unknown",
                                 message.chat.id, message.chat.title, f"Deleted locked content: {lock_type}")
            except Exception as e:
                print(f"Error deleting locked content: {e}")
            break  # Only delete once

async def delete_after_delay(message, delay):
    """Delete message after delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
