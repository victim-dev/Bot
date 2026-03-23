# modules/alive.py

import os
import sys
import time
import asyncio
import zipfile
import traceback
import subprocess
import platform
import shutil
import psutil
from pathlib import Path
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import header, separator

__MODULE__ = "alive"

START_TIME = time.time()


# ─────────────────────────────────────────────
async def edit(msg, text):
    try:
        await msg.edit(text)
    except:
        await msg.reply(text)


# ─────────────────────────────────────────────
# PRO ALIVE PANEL
async def alive(client, message):
    # ─── Ping ───
    start = time.time()
    await client.get_me()
    ping = int((time.time() - start) * 1000)

    # ─── Uptime ───
    uptime = int(time.time() - START_TIME)
    hrs, rem = divmod(uptime, 3600)
    mins, secs = divmod(rem, 60)
    uptime_str = f"{hrs}h {mins}m {secs}s"

    # ─── Modules ───
    modules_dir = Path("modules")
    total = len([f for f in modules_dir.glob("*.py") if not f.name.startswith("_")])
    failed = 0

    # ─── RAM / CPU ───
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=0.5)

    # ─── Disk ───
    disk = shutil.disk_usage("/")
    disk_used = int(disk.used / (1024**3))
    disk_total = int(disk.total / (1024**3))

    # ─── Panel ───
    text = (
        f"{header('System')}\n"
        f"{separator()}\n"
        f"[✓] ᴀʟᴘʜᴀ ʙᴏᴏᴛᴇᴅ\n"
        f"[✓] ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ\n\n"

        f"[⚡] ᴘɪɴɢ: {ping} ᴍs\n"
        f"[⏳] ᴜᴘᴛɪᴍᴇ: {uptime_str}\n\n"

        f"[📦] ᴍᴏᴅᴜʟᴇs: {total}\n"
        f"[✗] ꜰᴀɪʟᴇᴅ: {failed}\n\n"

        f"[🧠] ʀᴀᴍ: {ram}%\n"
        f"[⚙️] ᴄᴘᴜ: {cpu}%\n"
        f"[💾] ᴅɪsᴋ: {disk_used}/{disk_total} GB\n"

        f"{separator()}\n"
        f"✦ ᴘʀᴏ ᴘᴀɴᴇʟ ✦"
    )

    await edit(message, text)


# ─────────────────────────────────────────────
# FILE LIST
async def ls(client, message):
    files = "\n".join(os.listdir("."))[:4000]
    await edit(message, f"<code>{files}</code>")


# ─────────────────────────────────────────────
# TREE
async def tree(client, message):
    out = []
    for root, dirs, files in os.walk("."):
        level = root.replace(".", "").count(os.sep)
        indent = " " * 2 * level
        out.append(f"{indent}{os.path.basename(root)}/")
        for f in files:
            out.append(f"{indent}  {f}")
    await edit(message, f"<code>{chr(10).join(out)[:4000]}</code>")


# ─────────────────────────────────────────────
# BACKUP
async def backup(client, message):
    zip_name = "backup.zip"
    await message.edit("📦 Zipping...")

    with zipfile.ZipFile(zip_name, "w") as z:
        for root, _, files in os.walk("."):
            for f in files:
                if "session" in f:
                    continue
                z.write(os.path.join(root, f))

    await message.reply_document(zip_name)
    os.remove(zip_name)


# ─────────────────────────────────────────────
# SHELL
async def shell(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage: .sh <cmd>")

    cmd = " ".join(message.command[1:])
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate()
    text = (out + err).decode()[:4000]

    await edit(message, f"<code>{text}</code>")


# ─────────────────────────────────────────────
# PIP INSTALL
async def pip_install(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage: .pip <package>")

    pkg = message.command[1]
    await message.edit(f"📦 Installing {pkg}...")

    proc = subprocess.Popen(f"pip install {pkg}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    await edit(message, f"<code>{(out+err).decode()[:4000]}</code>")


# ─────────────────────────────────────────────
# SYSTEM INFO
async def sysinfo(client, message):
    text = f"""
🖥 OS: {platform.system()}
⚙️ Python: {platform.python_version()}
📦 Files: {len(os.listdir('.'))}
"""
    await edit(message, f"<code>{text}</code>")


# ─────────────────────────────────────────────
# RESTART
async def restart(client, message):
    await message.edit("🔄 Restarting...")
    os.execv(sys.executable, ["python"] + sys.argv)


# ─────────────────────────────────────────────
# EVAL
async def eval_code(client, message):
    if len(message.command) < 2:
        return await message.edit("Usage: .eval <code>")

    code = " ".join(message.command[1:])

    try:
        result = eval(code)
        await edit(message, f"<code>{result}</code>")
    except Exception:
        await edit(message, f"<code>{traceback.format_exc()}</code>")


# ─────────────────────────────────────────────
def register(app):
    app.add_handler(MessageHandler(alive, filters.command("alive", ".") & filters.me))
    app.add_handler(MessageHandler(ls, filters.command("ls", ".") & filters.me))
    app.add_handler(MessageHandler(tree, filters.command("tree", ".") & filters.me))
    app.add_handler(MessageHandler(backup, filters.command("backup", ".") & filters.me))
    app.add_handler(MessageHandler(shell, filters.command("sh", ".") & filters.me))
    app.add_handler(MessageHandler(pip_install, filters.command("pip", ".") & filters.me))
    app.add_handler(MessageHandler(sysinfo, filters.command("sys", ".") & filters.me))
    app.add_handler(MessageHandler(restart, filters.command("restart", ".") & filters.me))
    app.add_handler(MessageHandler(eval_code, filters.command("eval", ".") & filters.me))

    help_dict[__MODULE__] = {
        "alive": "Show pro system panel",
        "ls": "List files",
        "tree": "Directory tree",
        "backup": "Zip project",
        "sh": "Run shell command",
        "pip": "Install pip package",
        "sys": "System info",
        "restart": "Restart bot",
        "eval": "Run python code"
    }