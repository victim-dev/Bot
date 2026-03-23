# modules/help.py
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from utils.style import format_main_help, format_module_help, format_error, safe_edit

__MODULE__ = "help"

# Global dictionary that other modules will populate
help_dict = {}

async def help_command(client, message):
    """Display help for all modules or a specific module."""
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        # Main help – list all modules
        text = format_main_help(list(help_dict.keys()))
        await safe_edit(message, text)
    else:
        module_name = args[0].lower()
        if module_name in help_dict:
            # Module-specific help
            text = format_module_help(module_name, help_dict[module_name])
            await safe_edit(message, text)
        else:
            await safe_edit(message, format_error(f"Module '{module_name}' not found"))

def register(app):
    app.add_handler(MessageHandler(help_command, filters.command("help", prefixes=".") & filters.user(app.owner_id)))