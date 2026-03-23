import io
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import header, separator, footer

__MODULE__ = "command_list"

async def list_all_commands(client, message):
    """List every command from all modules with descriptions."""
    if not help_dict:
        await message.edit("No modules loaded.")
        return

    lines = []
    # Sort module names
    for mod_name in sorted(help_dict.keys()):
        commands = help_dict[mod_name]
        lines.append(f"<b>✦ Module: {mod_name} ✦</b>")
        lines.append(separator())
        for cmd, desc in commands.items():
            lines.append(f"⚡ <code>.{cmd}</code>")
            lines.append(f"   ➜ {desc}\n")
        lines.append("")  # blank line between modules

    # Join all lines
    full_text = "\n".join(lines)

    # Check length (Telegram limit ~ 4096)
    if len(full_text) > 4000:
        # Send as file
        bio = io.BytesIO(full_text.encode())
        bio.name = "all_commands.txt"
        await message.reply_document(bio, caption="All commands (too long for a single message)")
        await message.delete()
    else:
        await message.edit(full_text)

def register(app):
    app.add_handler(MessageHandler(list_all_commands, filters.command("allcommands", prefixes=".") & filters.me))
    help_dict[__MODULE__] = {
        "allcommands": "List every command from all loaded modules with descriptions."
    }