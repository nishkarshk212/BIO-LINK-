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
