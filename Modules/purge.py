# modules/purge.py
import asyncio
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import format_success, format_error, safe_edit

__MODULE__ = "purge"

async def del_msg(client, message):
    """Delete a single replied message."""
    if not message.reply_to_message:
        return await safe_edit(message, format_error("Reply to a message to delete it."))
    target = message.reply_to_message
    # Check permissions
    try:
        # Try to delete normally
        await target.delete()
        await message.delete()
    except Exception:
        # If failed, check if target is from ourselves (owner) and try to delete via own message delete
        if target.from_user and target.from_user.id == (await client.get_me()).id:
            # This message is from us, we can delete it even without admin
            await target.delete()
            await message.delete()
        else:
            # Not our message and we lack permissions
            await safe_edit(message, format_error("I don't have permission to delete that message."))
            return

async def purge(client, message):
    """Delete all messages from the replied message to the latest."""
    if not message.reply_to_message:
        return await safe_edit(message, format_error("Reply to a message to purge from there."))
    start_id = message.reply_to_message.id
    end_id = message.id
    total = end_id - start_id + 1
    if total <= 1:
        return await safe_edit(message, format_error("No messages to purge."))
    await safe_edit(message, format_success(f"Purging {total} messages..."))
    chunk = []
    async for msg in client.get_chat_history(message.chat.id, limit=total):
        if msg.id < start_id:
            break
        chunk.append(msg.id)
        if len(chunk) >= 100:
            await client.delete_messages(message.chat.id, chunk)
            chunk.clear()
            await asyncio.sleep(1)
    if chunk:
        await client.delete_messages(message.chat.id, chunk)
    await message.delete()

async def delme(client, message):
    """Delete only your own messages from the replied message to the latest."""
    if not message.reply_to_message:
        return await safe_edit(message, format_error("Reply to a message to delete your messages from there."))
    start_id = message.reply_to_message.id
    end_id = message.id
    total = end_id - start_id + 1
    if total <= 1:
        return await safe_edit(message, format_error("No messages to delete."))
    await safe_edit(message, "Scanning your messages...")
    my_msg_ids = []
    async for msg in client.get_chat_history(message.chat.id, limit=total):
        if msg.id < start_id:
            break
        if msg.outgoing:
            my_msg_ids.append(msg.id)
    if not my_msg_ids:
        return await safe_edit(message, format_error("No messages from you found in that range."))
    count = len(my_msg_ids)
    await safe_edit(message, format_success(f"Deleting {count} of your messages..."))
    chunk = []
    for msg_id in my_msg_ids:
        chunk.append(msg_id)
        if len(chunk) >= 100:
            await client.delete_messages(message.chat.id, chunk)
            chunk.clear()
            await asyncio.sleep(1)
    if chunk:
        await client.delete_messages(message.chat.id, chunk)
    await message.delete()

async def allme(client, message):
    """Delete ALL your messages in this chat."""
    if len(message.command) == 1 or (len(message.command) > 1 and message.command[1].lower() != "confirm"):
        return await safe_edit(message,
            f"{format_error('⚠️ WARNING: This will delete ALL messages you ever sent in this chat.')}\n"
            "This action cannot be undone.\n\n"
            f"To confirm, type: <code>.allme confirm</code>"
        )
    chat_id = message.chat.id
    msg = await safe_edit(message, "Scanning chat for your messages...")
    my_msg_ids = []
    total_found = 0
    last_id = None
    while True:
        async for m in client.get_chat_history(chat_id, limit=100, offset_id=last_id):
            if m.outgoing:
                my_msg_ids.append(m.id)
            last_id = m.id
        if len(my_msg_ids) == total_found:
            break
        total_found = len(my_msg_ids)
        await safe_edit(msg, f"Scanning... Found {total_found} messages so far.")
        await asyncio.sleep(0.5)
    if not my_msg_ids:
        return await safe_edit(msg, format_error("No messages from you found."))
    await safe_edit(msg, format_success(f"Found {len(my_msg_ids)} messages. Deleting..."))
    chunk = []
    for msg_id in my_msg_ids:
        chunk.append(msg_id)
        if len(chunk) >= 100:
            await client.delete_messages(chat_id, chunk)
            chunk.clear()
            await asyncio.sleep(1)
    if chunk:
        await client.delete_messages(chat_id, chunk)
    await message.delete()
    await client.send_message(chat_id, format_success(f"Deleted all {len(my_msg_ids)} of your messages."))

async def delme_date(client, message):
    """Delete your messages from a specific date onward."""
    args = message.command[1:] if len(message.command) > 1 else []
    if not args or args[0].lower() != "from":
        return await safe_edit(message, format_error("Usage: .delme from <date> [optional: to <date>]\nExamples: .delme from 2024-03-01, .delme from 9 Dec"))
    date_str = args[1] if len(args) > 1 else None
    if not date_str:
        return await safe_edit(message, format_error("Please provide a date."))
    # Parse date
    try:
        date = date_parser.parse(date_str, fuzzy=True)
    except Exception:
        return await safe_edit(message, format_error("Could not parse date. Use formats like '2024-03-01', '1 March', '9 Dec'."))
    # If a second date is given (to), parse it
    to_date = None
    if len(args) >= 4 and args[2].lower() == "to":
        to_date_str = args[3]
        try:
            to_date = date_parser.parse(to_date_str, fuzzy=True)
        except Exception:
            return await safe_edit(message, format_error("Could not parse 'to' date."))
    # Start scanning messages
    msg = await safe_edit(message, f"Scanning your messages from {date.strftime('%Y-%m-%d')}...")
    my_msg_ids = []
    total_found = 0
    last_id = None
    while True:
        async for m in client.get_chat_history(message.chat.id, limit=100, offset_id=last_id):
            if not m.outgoing:
                last_id = m.id
                continue
            if m.date.date() < date.date():
                # Stop scanning if we go earlier than start date
                break
            if to_date and m.date.date() > to_date.date():
                last_id = m.id
                continue
            my_msg_ids.append(m.id)
            last_id = m.id
        # If we broke because we hit messages before date, break outer loop
        if last_id is not None and (await client.get_messages(message.chat.id, last_id)).date.date() < date.date():
            break
        if len(my_msg_ids) == total_found:
            break
        total_found = len(my_msg_ids)
        await msg.edit(f"Scanning... Found {total_found} messages so far.")
        await asyncio.sleep(0.5)
    if not my_msg_ids:
        return await msg.edit(format_error("No messages from you found in the given period."))
    await msg.edit(format_success(f"Found {len(my_msg_ids)} messages. Deleting..."))
    chunk = []
    for msg_id in my_msg_ids:
        chunk.append(msg_id)
        if len(chunk) >= 100:
            await client.delete_messages(message.chat.id, chunk)
            chunk.clear()
            await asyncio.sleep(1)
    if chunk:
        await client.delete_messages(message.chat.id, chunk)
    await message.delete()

def register(app):
    app.add_handler(MessageHandler(del_msg, filters.command("del", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(purge, filters.command("purge", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(delme, filters.command("delme", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(allme, filters.command("allme", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(delme_date, filters.command("delme from", prefixes=".") & filters.user(app.owner_id)))
    help_dict[__MODULE__] = {
        "del [reply]": "Delete the replied message (if bot has permission).",
        "purge [reply]": "Delete all messages from the replied message to the latest.",
        "delme [reply]": "Delete only your own messages from the replied message to the latest.",
        "allme [confirm]": "Delete ALL your messages in this chat.",
        "delme from <date> [to <date>]": "Delete your messages from a specific date onward (optional end date)."
    }