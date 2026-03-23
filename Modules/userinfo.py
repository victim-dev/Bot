# modules/userinfo.py
import os
import tempfile
import asyncio
import re
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.raw import functions
from modules.help import help_dict
from utils.style import format_success, format_error, safe_edit, header, separator

__MODULE__ = "userinfo"

# ==================== Helper for SangMata ====================
async def _get_bot_response(client, bot_username, text, timeout=10):
    """Send a message to a bot and wait for its response."""
    last_msg_id = None
    async for msg in client.get_chat_history(bot_username, limit=1):
        last_msg_id = msg.id
    await client.send_message(bot_username, text)
    start = asyncio.get_event_loop().time()
    while True:
        async for msg in client.get_chat_history(bot_username, limit=10):
            if msg.from_user and msg.from_user.username == bot_username.lstrip('@'):
                if last_msg_id is None or msg.id > last_msg_id:
                    return msg.text
        if asyncio.get_event_loop().time() - start > timeout:
            raise TimeoutError("Bot did not respond in time")
        await asyncio.sleep(0.5)

def _parse_sangamata(text, only_usernames=False):
    """Extract name/username history from SangMata bot reply."""
    lines = text.splitlines()
    names = []
    usernames = []
    section = None
    for line in lines:
        if "Name History" in line:
            section = "names"
            continue
        elif "Username History" in line:
            section = "usernames"
            continue

        if not line.strip() or "-----" in line or "History:" in line:
            continue

        clean = re.sub(r'^[•\-]\s*', '', line).strip()
        if not clean:
            continue

        if section == "names" and not only_usernames:
            names.append(clean)
        elif section == "usernames":
            usernames.append(clean)

    parts = []
    if names:
        parts.append("<b>Name History</b>")
        for name in names:
            parts.append(f"• {name}")

    if usernames:
        parts.append("<b>Username History</b>")
        for username in usernames:
            parts.append(f"• {username}")

    if not parts:
        return "No records found."

    return "\n".join(parts)

# ==================== .id command ===================="}
async def id_command(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if not user:
            return await safe_edit(message, format_error("Cannot identify user."))
        text = f"<b>User ID of {user.first_name}:</b> <code>{user.id}</code>"
    else:
        user = message.from_user
        text = f"<b>Your user ID:</b> <code>{user.id}</code>"
    if message.chat.type != "private":
        text += f"\n<b>Chat ID:</b> <code>{message.chat.id}</code>"
    await safe_edit(message, text)

# ==================== .info command ====================
async def info_command(client, message):
    # Determine target user
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if not user:
            return await safe_edit(message, format_error("Cannot identify user."))
    elif len(message.command) > 1:
        try:
            user = await client.get_users(message.command[1])
        except Exception as e:
            return await safe_edit(message, format_error(f"User not found: {e}"))
    else:
        user = message.from_user

    # Get full user info (bio, common chats)
    try:
        full = await client.invoke(
            functions.users.GetFullUser(id=await client.resolve_peer(user.id))
        )
    except Exception as e:
        return await safe_edit(message, format_error(f"Error fetching user info: {e}"))

    # Basic user data
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "None"
    user_id = user.id
    bio = full.full_user.about or "No bio"
    common_chats = full.full_user.common_chats_count
    is_bot = user.is_bot

    # Profile photos count
    photo_count = 0
    photos = []
    async for photo in client.get_chat_photos(user.id, limit=0):
        photo_count += 1
    # Get the first photo (if any) to send
    first_photo = None
    async for photo in client.get_chat_photos(user.id, limit=1):
        first_photo = photo
        break

    # Build text info
    text = (
        f"{header('User Info')}\n"
        f"{separator()}\n"
        f"First Name: {first_name}\n"
        f"Last Name: {last_name}\n"
        f"Username: {username}\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Bot: {'Yes' if is_bot else 'No'}\n"
        f"Bio: {bio}\n"
        f"Common Chats: {common_chats}\n"
        f"Profile Photos: {photo_count}\n"
        f"{separator()}"
    )

    # If there's a profile photo, send it with the caption
    if first_photo:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
            await client.download_media(first_photo.file_id, file_name=tmp_path)
        await message.reply_photo(tmp_path, caption=text)
        os.unlink(tmp_path)
        await message.delete()
    else:
        await message.edit(text)

# ==================== .sang command ====================
async def sang_command(client, message):
    """Get name/username history of a user using SangMata bot."""
    args = message.command[1:] if len(message.command) > 1 else []
    only_usernames = False
    if args and args[0] in ("u", "-u", "--username"):
        only_usernames = True
        args.pop(0)
    # Determine target
    if args:
        try:
            target = await client.get_users(args[0])
        except Exception:
            return await safe_edit(message, format_error("User not found."))
    elif message.reply_to_message:
        target = message.reply_to_message.from_user
        if not target:
            return await safe_edit(message, format_error("Cannot identify user."))
    else:
        return await safe_edit(message, format_error("Usage: .sang [u] <username/id> or reply to a user."))

    await safe_edit(message, "Fetching history...")
    try:
        response = await _get_bot_response(client, "@SangMata_beta_bot", str(target.id), timeout=15)
    except TimeoutError:
        return await safe_edit(message, format_error("SangMata bot did not respond in time."))
    except Exception as e:
        return await safe_edit(message, format_error(f"Error: {e}"))

    parsed = _parse_sangamata(response, only_usernames)

    display_name = target.first_name or "Unknown"
    username_display = f"@{target.username}" if getattr(target, 'username', None) else "No username"

    output = (
        f"{header('SangMata History')}\n"
        f"{separator()}\n"
        f"<b>User:</b> {display_name} ({username_display})\n"
        f"<b>ID:</b> <code>{target.id}</code>\n"
        f"{separator()}\n"
        f"{parsed}"
    )

    await safe_edit(message, output)

# ==================== Register handlers ====================
def register(app):
    app.add_handler(MessageHandler(id_command, filters.command("id", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(info_command, filters.command("info", prefixes=".") & filters.user(app.owner_id)))
    app.add_handler(MessageHandler(sang_command, filters.command("sang", prefixes=".") & filters.user(app.owner_id)))
    help_dict[__MODULE__] = {
        "id [reply]": "Get user ID (and chat ID if in group)",
        "info [username/reply]": "Get detailed user information (ID, bio, profile photo, etc.)",
        "sang [u] <user/reply>": "Get name/username history from SangMata (use 'u' for usernames only)"
    }