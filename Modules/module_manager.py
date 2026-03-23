import os
import sys
import asyncio
import aiohttp
import importlib
import traceback
from pathlib import Path
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import format_success, format_error, header, separator, footer

__MODULE__ = "module_manager"

MODULES_DIR = Path("modules")

async def _edit_safe(message, text):
    try:
        await message.edit(text)
    except Exception:
        await message.reply(text)
        await message.delete()

async def _restart_bot():
    print("🔄 Restarting bot...")
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def _restart_after(message):
    await message.edit(format_success("✅ Module updated. Restarting bot..."))
    await _restart_bot()

async def upload_module(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    url = None
    if args:
        url = args[0]

    reply = message.reply_to_message
    if reply and reply.document and reply.document.file_name.endswith(".py"):
        await message.edit(f"📥 Downloading `{reply.document.file_name}`...")
        file_path = await reply.download()
        if not file_path:
            return await message.edit(format_error("Failed to download file."))
        dest = MODULES_DIR / reply.document.file_name
        os.rename(file_path, dest)
        await message.edit(format_success(f"✅ Module `{reply.document.file_name}` saved to `modules/`."))
        await _restart_after(message)
        return

    if url:
        if not (url.endswith(".py") or "raw.githubusercontent.com" in url or "pastebin" in url):
            return await message.edit(format_error("URL does not appear to be a raw Python file."))
        await message.edit(f"📥 Downloading from URL...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await message.edit(format_error(f"Failed to fetch URL (status {resp.status})."))
                    content = await resp.text()
            except Exception as e:
                return await message.edit(format_error(f"Error downloading: {e}"))
        filename = None
        if len(args) > 1:
            filename = args[1]
        else:
            filename = url.split("/")[-1]
            if not filename.endswith(".py"):
                filename = "module.py"
        dest = MODULES_DIR / filename
        dest.write_text(content, encoding="utf-8")
        await message.edit(format_success(f"✅ Module `{filename}` saved to `modules/`."))
        await _restart_after(message)
        return

    await message.edit(format_error("Usage: `.uploadmodule <reply to .py file>` or `.uploadmodule <raw_url> [filename.py]`"))

async def unload_module(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: `.unloadmodule <module_name>` (without .py)"))
    module_name = args[0]
    if not module_name.endswith(".py"):
        module_name += ".py"
    file_path = MODULES_DIR / module_name
    if not file_path.exists():
        return await message.edit(format_error(f"Module `{module_name}` not found."))
    critical = ["help.py", "alive.py", "module_manager.py"]
    if module_name in critical:
        return await message.edit(format_error(f"Cannot delete built‑in module `{module_name}`."))
    try:
        os.remove(file_path)
        if module_name[:-3] in sys.modules:
            del sys.modules[module_name[:-3]]
        await message.edit(format_success(f"🗑️ Module `{module_name}` deleted."))
        await _restart_after(message)
    except Exception as e:
        await message.edit(format_error(f"Error deleting: {e}"))

async def list_modules(client, message):
    try:
        files = [f.name for f in MODULES_DIR.glob("*.py") if not f.name.startswith("_")]
        if not files:
            return await message.edit("No modules found.")
        loaded = [m for m in sys.modules if m.startswith("modules.")]
        loaded_names = [m.split(".")[-1] + ".py" for m in loaded]
        text = f"{header('Modules')}\n{separator()}\n"
        for f in sorted(files):
            if f in loaded_names:
                text += f"🟢 `{f}` (loaded)\n"
            else:
                text += f"⚪ `{f}` (not loaded)\n"
        text += f"{separator()}\n{footer('Use .uploadmodule / .unloadmodule')}"
        await message.edit(text)
    except Exception as e:
        await message.edit(format_error(f"Error: {e}"))

def register(app):
    app.add_handler(MessageHandler(upload_module, filters.command("uploadmodule", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(unload_module, filters.command("unloadmodule", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(list_modules, filters.command("listmodules", prefixes=".") & filters.me))
    help_dict[__MODULE__] = {
        "uploadmodule [url] [filename]": "Upload a .py file from reply or URL to modules/ (bot restarts)",
        "unloadmodule <module_name>": "Delete a module from modules/ (without .py) (bot restarts)",
        "listmodules": "List all modules in modules/ folder (mark loaded)"
    }
