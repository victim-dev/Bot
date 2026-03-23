# modules/spam.py
import asyncio
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import format_error, format_success

__MODULE__ = "spam"

MAX_SPAM = 50

async def _spam_base(client, message, delay):
    """Core spam logic."""
    if len(message.command) < 2:
        return await message.edit(format_error("Usage: .spam [count] [text] (or reply)"))
    try:
        count = int(message.command[1])
    except ValueError:
        return await message.edit(format_error("Count must be a number."))
    if count < 1 or count > MAX_SPAM:
        return await message.edit(format_error(f"Count must be between 1 and {MAX_SPAM}."))
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if not text:
            return await message.edit(format_error("Replied message has no text."))
    else:
        if len(message.command) < 3:
            return await message.edit(format_error("Please provide text to spam."))
        text = " ".join(message.command[2:])
    await message.delete()
    for _ in range(count):
        await client.send_message(message.chat.id, text)
        await asyncio.sleep(delay)

async def spam_command(client, message):
    await _spam_base(client, message, 0.3)

async def fastspam_command(client, message):
    await _spam_base(client, message, 0)

async def slowspam_command(client, message):
    await _spam_base(client, message, 0.9)

async def statspam_command(client, message):
    if len(message.command) < 2:
        return await message.edit(format_error("Usage: .statspam [count] [text] (or reply)"))
    try:
        count = int(message.command[1])
    except ValueError:
        return await message.edit(format_error("Count must be a number."))
    if count < 1 or count > MAX_SPAM:
        return await message.edit(format_error(f"Count must be between 1 and {MAX_SPAM}."))
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
        if not text:
            return await message.edit(format_error("Replied message has no text."))
    else:
        if len(message.command) < 3:
            return await message.edit(format_error("Please provide text to spam."))
        text = " ".join(message.command[2:])
    await message.delete()
    for _ in range(count):
        sent = await client.send_message(message.chat.id, text)
        await asyncio.sleep(0.1)
        await sent.delete()

def register(app):
    app.add_handler(MessageHandler(spam_command, filters.command("spam", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(fastspam_command, filters.command("fastspam", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(slowspam_command, filters.command("slowspam", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(statspam_command, filters.command("statspam", prefixes=".") & filters.me))
    help_dict[__MODULE__] = {
        "spam [count] [text]": "Spam with 0.3s delay (max 50).",
        "fastspam [count] [text]": "Spam without delay (max 50).",
        "slowspam [count] [text]": "Spam with 0.9s delay (max 50).",
        "statspam [count] [text]": "Spam and delete each message (max 50)."
    }