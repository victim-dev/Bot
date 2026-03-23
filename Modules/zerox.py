# modules/zerox.py

import os
import tempfile
import base64
import smtplib
import mimetypes
from email.message import EmailMessage
from dotenv import load_dotenv

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.raw import functions

from utils.mongo import mset, mget, mkeys, mdelete, store_col
from modules.help import help_dict
from utils.style import format_success, format_error, safe_edit

load_dotenv()

GMAIL = os.getenv("GMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

__MODULE__ = "zerox"

# ================= GMAIL ================= #

async def send_to_gmail(subject, file_path=None, text=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL
    msg["To"] = GMAIL

    msg.set_content(text or "Stored via bot")

    if file_path:
        mime, _ = mimetypes.guess_type(file_path)
        maintype, subtype = (mime.split("/") if mime else ("application", "octet-stream"))

        with open(file_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(file_path)
            )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(msg)

# ================= MODE ================= #

async def get_mode():
    data = await mget(store_col, "config_mode")
    return data.get("mode", "both") if data else "both"

async def setmode_command(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage: .setmode mongo/cloud/both")

    mode = message.command[1].lower()

    if mode not in ["mongo", "cloud", "both"]:
        return await message.edit("Invalid mode")

    await mset(store_col, "config_mode", {"mode": mode})
    await message.edit(f"Mode → {mode}")

async def mode_command(client, message):
    mode = await get_mode()
    await message.edit(f"Mode → {mode}")

# ================= PROFILE ================= #

async def save_current_profile(client, key="original"):
    me = await client.get_me()

    full = await client.invoke(
        functions.users.GetFullUser(id=await client.resolve_peer(me.id))
    )

    photo_bytes = None
    async for photo in client.get_chat_photos("me"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            await client.download_media(photo.file_id, tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            photo_bytes = base64.b64encode(f.read()).decode()

        os.remove(tmp_path)
        break

    data = {
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "bio": full.full_user.about or "",
        "photo": photo_bytes
    }

    await mset(store_col, f"profile_{key}", data)

async def load_profile(client, data):
    await client.update_profile(
        first_name=data["first_name"],
        last_name=data["last_name"],
        bio=data["bio"]
    )

    current = [p async for p in client.get_chat_photos("me")]
    if current:
        await client.delete_profile_photos([p.file_id for p in current])

    if data.get("photo"):
        photo_bytes = base64.b64decode(data["photo"])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(photo_bytes)
            tmp_path = tmp.name

        await client.set_profile_photo(photo=tmp_path)
        os.remove(tmp_path)

# ================= PROFILE COMMANDS ================= #

async def saveop_command(client, message):
    slot = message.command[1] if len(message.command) > 1 else "original"
    await save_current_profile(client, slot)
    await safe_edit(message, format_success(f"Saved → {slot}"))

async def loadop_command(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, format_error("Usage"))

    data = await mget(store_col, f"profile_{message.command[1]}")
    if not data:
        return await safe_edit(message, format_error("Empty"))

    await load_profile(client, data)
    await safe_edit(message, format_success("Loaded"))

async def zerox_command(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target and len(message.command) > 1:
        target = await client.get_users(message.command[1])
    if not target:
        return await safe_edit(message, format_error("Reply/user"))

    if not await mget(store_col, "profile_original"):
        await save_current_profile(client, "original")

    full = await client.invoke(
        functions.users.GetFullUser(id=await client.resolve_peer(target.id))
    )

    await client.update_profile(
        first_name=target.first_name or "",
        last_name=target.last_name or "",
        bio=full.full_user.about or ""
    )

    current = [p async for p in client.get_chat_photos("me")]
    if current:
        await client.delete_profile_photos([p.file_id for p in current])

    async for photo in client.get_chat_photos(target.id):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            await client.download_media(photo.file_id, tmp.name)
            await client.set_profile_photo(photo=tmp.name)
            os.remove(tmp.name)
        break

    await safe_edit(message, format_success("Cloned"))

async def revert_command(client, message):
    data = await mget(store_col, "profile_original")
    if not data:
        return await safe_edit(message, format_error("No backup"))

    await load_profile(client, data)
    await safe_edit(message, format_success("Reverted"))

async def swapdp_command(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        return await message.edit("Reply")

    await save_current_profile(client, "swap")

    async for photo in client.get_chat_photos(target.id):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            await client.download_media(photo.file_id, tmp.name)
            await client.set_profile_photo(photo=tmp.name)
            os.remove(tmp.name)
        break

    await message.edit("Swapped")

async def swapback_command(client, message):
    data = await mget(store_col, "profile_swap")
    if not data:
        return await message.edit("No backup")

    await load_profile(client, data)
    await message.edit("Restored")

# ================= STEAL ================= #

async def steal_command(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        return await message.edit("Reply")

    async for photo in client.get_chat_photos(target.id):
        await client.send_photo("me", photo.file_id)
        break

    await message.edit("Saved")

async def stealall_command(client, message):
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        return await message.edit("Reply")

    count = 0
    async for photo in client.get_chat_photos(target.id):
        await client.send_photo("me", photo.file_id)
        count += 1

    await message.edit(f"{count} saved")

# ================= STORE ================= #

async def store_command(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage")

    name = message.command[1]
    msg = message.reply_to_message

    if not msg:
        return await message.edit("Reply required")

    mode = await get_mode()
    await message.edit(f"Saving ({mode})...")

    data = {"_id": name, "type": None, "file_id": None, "text": None}

    try:
        if msg.text or msg.caption:
            text = msg.text or msg.caption
            data["type"] = "text"
            data["text"] = text

            if mode in ["cloud", "both"]:
                await send_to_gmail(f"STORE:{name}", text=text)

        else:
            file_path = await client.download_media(msg)

            data["type"] = "file"
            data["file_id"] = (
                msg.document.file_id if msg.document else
                msg.photo.file_id if msg.photo else
                msg.video.file_id if msg.video else None
            )

            if mode in ["cloud", "both"]:
                await send_to_gmail(f"STORE:{name}", file_path=file_path)

            if os.path.exists(file_path):
                os.remove(file_path)

        if mode in ["mongo", "both"]:
            await mset(store_col, name, data)

        await message.edit(f"Saved → {mode} ✅")

    except Exception as e:
        await message.edit(str(e))

async def get_command(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage")

    data = await mget(store_col, message.command[1])
    if not data:
        return await message.edit("Not found")

    if data["type"] == "text":
        await message.edit(data["text"])
    else:
        await client.send_cached_media(message.chat.id, data["file_id"])

async def storelist_command(client, message):
    keys = await mkeys(store_col)
    if not keys:
        return await message.edit("Empty")

    await message.edit("📦\n" + "\n".join(keys))

async def delstore_command(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage")

    await mdelete(store_col, message.command[1])
    await message.edit("Deleted")

# ================= REGISTER ================= #

def register(app):
    f = filters.user(app.owner_id)

    cmds = [
        ("saveop", saveop_command),
        ("loadop", loadop_command),
        ("zerox", zerox_command),
        ("revert", revert_command),
        ("swapdp", swapdp_command),
        ("swapback", swapback_command),
        ("steal", steal_command),
        ("stealall", stealall_command),
        ("store", store_command),
        ("get", get_command),
        ("storelist", storelist_command),
        ("delstore", delstore_command),
        ("setmode", setmode_command),
        ("mode", mode_command),
    ]

    for cmd, func in cmds:
        app.add_handler(MessageHandler(func, filters.command(cmd, ".") & f))

    help_dict[__MODULE__] = {
            "saveop [slot]": "Save current profile to a slot (default: 'original')",
            "loadop [slot]": "Load a saved profile from a slot",
            "zerox [username/reply]": "Copy full profile (name, bio, photo) – auto‑backup",
            "revert": "Restore the original profile",
            "swapdp [reply]": "Swap your profile photo with target's (temporary)",
            "swapback": "Restore your profile photo after swap",
            "steal [reply]": "Send one profile photo of target to saved messages",
            "stealall [reply]": "Send all profile photos of target to saved messages",                            "store <name>": "Save text/media with a name (MongoDB + optional Gmail)",
            "get <name>": "Retrieve stored item",
            "storelist": "List all stored item names",             "delstore <name>": "Delete stored item",
            "setmode <mongo/cloud/both>": "Set storage backend (MongoDB, Gmail, or both)",
            "mode": "Show current storage mode" }