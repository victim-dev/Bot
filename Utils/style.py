# utils/style.py
# Central styling for all modules – now using Markdown

HEADER_SYMBOL = "✦"
FOOTER_SYMBOL = "⌬"
LINE_CHAR = "━"
LINE_LENGTH = 25
FONT_STYLE = "smallcaps"  # "smallcaps", "upper", "normal"
LOADING_CHARS = ["|", "/", "-", "\\"]

def fancy(text: str, style: str = None) -> str:
    style = style or FONT_STYLE
    if style == "upper":
        return text.upper()
    if style == "smallcaps":
        smallcaps = str.maketrans(
            "abcdefghijklmnopqrstuvwxyz",
            "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
        )
        return text.translate(smallcaps)
    return text

def separator() -> str:
    # Use code block to preserve monospaced line
    return f"`{LINE_CHAR * LINE_LENGTH}`"

def header(text: str, symbol: str = HEADER_SYMBOL) -> str:
    return f"**{symbol} {fancy(text)} {symbol}**"

def footer(text: str, symbol: str = FOOTER_SYMBOL) -> str:
    return f"_{symbol} {fancy(text)}_"

def format_success(text: str) -> str:
    return f"{header('✓')} {text}"

def format_error(text: str) -> str:
    return f"{header('✗')} **{text}**"

def format_main_help(modules: list) -> str:
    lines = [
        header("Help Panel"),
        separator(),
        "📦 **Available modules:**\n"
    ]
    for mod in sorted(modules):
        lines.append(f"➤ `{mod}`")
    lines.extend([
        "",
        separator(),
        footer("Use .help <module> for details")
    ])
    return "\n".join(lines)

def format_module_help(module_name: str, commands: dict) -> str:
    lines = [
        header(f"Module: {module_name}"),
        separator(),
        ""
    ]
    for cmd, desc in commands.items():
        lines.append(f"⚡ `.{cmd}`\n   ➜ {desc}\n")
    lines.append(separator())
    return "\n".join(lines)

async def safe_edit(message, text):
    try:
        await message.edit(text, parse_mode='Markdown')
    except Exception:
        await message.reply(text, parse_mode='Markdown')
        await message.delete()