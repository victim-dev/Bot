
# modules/ask.py

import os
import asyncio
import tempfile
import smtplib
from email.message import EmailMessage

from openai import OpenAI
from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict

__MODULE__ = "ask"

# ================= AI ================= #

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

GMAIL = os.getenv("GMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ================= MEMORY ================= #

chat_memory = {}  # {user_id: [messages]}


def get_memory(user_id):
    return chat_memory.setdefault(user_id, [])


def reset_memory(user_id):
    chat_memory[user_id] = []


# ================= MODES ================= #

MODES = {
    "chat": "You are a helpful AI assistant.",
    "code": "You are an expert programmer. Return clean working code.",
    "explain": "Explain step by step simply.",
    "short": "Give short direct answers."
}


# ================= GMAIL BACKUP ================= #

def backup_to_gmail(user_id, content):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"AI_MEMORY:{user_id}"
        msg["From"] = GMAIL
        msg["To"] = GMAIL
        msg.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL, APP_PASSWORD)
            smtp.send_message(msg)
    except:
        pass


# ================= AI ================= #

async def ask_ai(user_id, prompt, mode="chat"):
    def run():
        memory = get_memory(user_id)

        system = MODES.get(mode, MODES["chat"])

        messages = [{"role": "system", "content": system}]
        messages += memory[-10:]
        messages.append({"role": "user", "content": prompt})

        res = client.chat.completions.create(
            model="minimaxai/minimax-m2.5",
            messages=messages,
            temperature=0.6,
            top_p=0.95,
            max_tokens=4096,
        )

        reply = res.choices[0].message.content

        # store memory
        memory.append({"role": "user", "content": prompt})
        memory.append({"role": "assistant", "content": reply})

        # backup important chats
        if len(prompt) > 50:
            backup_to_gmail(user_id, prompt + "\n\n" + reply)

        return reply

    return await asyncio.to_thread(run)


# ================= OUTPUT ================= #

async def send_output(client, message, content):
    if len(content) < 3500:
        return await message.edit(content)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content.encode())
        path = f.name

    await message.delete()
    await client.send_document(message.chat.id, path, caption="AI Response")
    os.remove(path)


# ================= COMMAND ================= #

async def ask_command(client, message):
    user_id = message.from_user.id

    if len(message.command) < 2 and not message.reply_to_message:
        return await message.edit("Usage: .ask [mode] question")

    parts = message.text.split(None, 2)

    if len(parts) > 2 and parts[1] in MODES:
        mode = parts[1]
        prompt = parts[2]
    else:
        mode = "chat"
        prompt = message.text.split(None, 1)[1] if len(message.command) > 1 else None

    if message.reply_to_message:
        prompt = message.reply_to_message.text

    if not prompt:
        return await message.edit("No input")

    await message.edit(f"Thinking ({mode})...")

    result = await ask_ai(user_id, prompt, mode)
    await send_output(client, message, result)


# ================= RESET ================= #

async def reset_command(client, message):
    reset_memory(message.from_user.id)
    await message.edit("Memory cleared")


# ================= REGISTER ================= #

def register(app):
    f = filters.user(app.owner_id)

    app.add_handler(MessageHandler(ask_command, filters.command("ask", ".") & f))
    app.add_handler(MessageHandler(reset_command, filters.command("resetai", ".") & f))

    help_dict[__MODULE__] = {
        "ask": "AI chat with session memory + Gmail backup",
        "resetai": "Clear session memory"
    }