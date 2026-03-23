# modules/admin.py
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions
from modules.help import help_dict
from utils.style import format_success, format_error, safe_edit

__MODULE__ = "admin"

async def ban_user(client, message):
    if not message.reply_to_message:
        return await safe_edit(message, format_error("Reply to a user to ban them."))
    user = message.reply_to_message.from_user
    if not user:
        return await safe_edit(message, format_error("Cannot identify user."))
    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await safe_edit(message, format_success(f"{user.first_name} banned."))
    except Exception as e:
        await safe_edit(message, format_error(f"Error: {e}"))

async def kick_user(client, message):
    if not message.reply_to_message:
        return await safe_edit(message, format_error("Reply to a user to kick them."))
    user = message.reply_to_message.from_user
    if not user:
        return await safe_edit(message, format_error("Cannot identify user."))
    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await safe_edit(message, format_success(f"{user.first_name} kicked."))
    except Exception as e:
        await safe_edit(message, format_error(f"Error: {e}"))

async def mute_user(client, message):
    if not message.reply_to_message:
        return await message.edit(format_error("Reply to a user to mute them."))
    user = message.reply_to_message.from_user
    if not user:
        return await message.edit(format_error("Cannot identify user."))
    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=False)
        )
        await safe_edit(message, format_success(f"{user.first_name} muted."))
    except Exception as e:
        await safe_edit(message, format_error(f"Error: {e}"))

async def unmute_user(client, message):
    if not message.reply_to_message:
        return await message.edit(format_error("Reply to a user to unmute them."))
    user = message.reply_to_message.from_user
    if not user:
        return await message.edit(format_error("Cannot identify user."))
    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=True)
        )
        await safe_edit(message, format_success(f"{user.first_name} unmuted."))
    except Exception as e:
        await safe_edit(message, format_error(f"Error: {e}"))

def register(app):
    app.add_handler(MessageHandler(ban_user, filters.command("ban", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(kick_user, filters.command("kick", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(mute_user, filters.command("mute", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(unmute_user, filters.command("unmute", prefixes=".") & filters.user(app.owner_id)))
    help_dict[__MODULE__] = {
        "ban [reply]": "Ban a user",
        "kick [reply]": "Kick a user",
        "mute [reply]": "Mute a user",
        "unmute [reply]": "Unmute a user"
    }