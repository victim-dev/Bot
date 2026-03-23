# modules/deobf.py

import base64
import codecs
import zlib
import gzip
import bz2
import lzma
import asyncio
import os
import tempfile

from openai import OpenAI
from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict

__MODULE__ = "deobf"

# ================= AI ================= #

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


async def ai_clean(code: str, mode="clean"):
    def run():
        prompt = (
            f"You are a Python reverse engineering expert.\n"
            f"Clean and deobfuscate this code:\n{code}"
            if mode == "clean"
            else f"You are an advanced reverse engineer.\n"
                 f"Fully deobfuscate, simplify and reconstruct logic:\n{code}"
        )

        res = client.chat.completions.create(
            model="minimaxai/minimax-m2.5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            top_p=0.95,
            max_tokens=4096,
        )

        return res.choices[0].message.content

    return await asyncio.to_thread(run)


# ================= SAFE DECODERS ================= #

def safe(fn):
    def wrap(d):
        try:
            return fn(d)
        except:
            return None
    return wrap


@safe
def b64(d): return base64.b64decode(d)
@safe
def b32(d): return base64.b32decode(d)
@safe
def b16(d): return base64.b16decode(d)
@safe
def b85(d): return base64.b85decode(d)
@safe
def a85(d): return base64.a85decode(d)
@safe
def hex_d(d): return bytes.fromhex(d.decode())
@safe
def rot13(d): return codecs.decode(d.decode(), "rot_13").encode()
@safe
def uni(d): return codecs.decode(d.decode(), "unicode_escape").encode()
@safe
def raw_uni(d): return codecs.decode(d.decode(), "raw_unicode_escape").encode()
@safe
def zlib_d(d): return zlib.decompress(d)
@safe
def gzip_d(d): return gzip.decompress(d)
@safe
def bz2_d(d): return bz2.decompress(d)
@safe
def lzma_d(d): return lzma.decompress(d)


DECODERS = [
    ("base64", b64),
    ("base32", b32),
    ("base16", b16),
    ("base85", b85),
    ("ascii85", a85),
    ("hex", hex_d),
    ("rot13", rot13),
    ("unicode_escape", uni),
    ("raw_unicode_escape", raw_uni),
    ("zlib", zlib_d),
    ("gzip", gzip_d),
    ("bz2", bz2_d),
    ("lzma", lzma_d),
]


# ================= CORE ================= #

def smart_decode(data, depth=15):
    steps = []
    current = data

    for _ in range(depth):
        for name, fn in DECODERS:
            result = fn(current)
            if result and result != current:
                current = result
                steps.append(name)
                break
        else:
            break

    return current, steps


# ================= OUTPUT ================= #

async def send_output(client, message, content: str):
    if len(content) < 3500:
        return await message.edit(f"```{content}```")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(content.encode())
        path = f.name

    await message.delete()
    await client.send_document(
        message.chat.id,
        path,
        caption="Deobfuscated Output"
    )

    os.remove(path)


# ================= INPUT ================= #

async def get_input(client, message):
    msg = message.reply_to_message

    if not msg:
        return None

    if msg.text:
        return msg.text.encode()

    if msg.document:
        path = await client.download_media(msg)
        with open(path, "rb") as f:
            return f.read()

    return None


# ================= COMMANDS ================= #

async def deobf_command(client, message):
    raw = await get_input(client, message)
    if not raw:
        return await message.edit("Reply to text/file")

    await message.edit("Decoding...")

    decoded, steps = smart_decode(raw)

    try:
        final = decoded.decode()
    except:
        final = str(decoded)

    await send_output(client, message, final)


async def deobfai_command(client, message):
    raw = await get_input(client, message)
    if not raw:
        return await message.edit("Reply to text/file")

    await message.edit("Decoding + AI...")

    decoded, _ = smart_decode(raw)

    try:
        decoded = decoded.decode()
    except:
        decoded = str(decoded)

    result = await ai_clean(decoded, "clean")

    await send_output(client, message, result)


async def deobfdeep_command(client, message):
    raw = await get_input(client, message)
    if not raw:
        return await message.edit("Reply to text/file")

    await message.edit("Deep analysis...")

    decoded, _ = smart_decode(raw)

    try:
        decoded = decoded.decode()
    except:
        decoded = str(decoded)

    result = await ai_clean(decoded, "deep")

    await send_output(client, message, result)


# ================= REGISTER ================= #

def register(app):
    f = filters.user(app.owner_id)

    cmds = [
        ("deobf", deobf_command),
        ("deobfai", deobfai_command),
        ("deobfdeep", deobfdeep_command),
    ]

    for cmd, func in cmds:
        app.add_handler(MessageHandler(func, filters.command(cmd, ".") & f))

    help_dict[__MODULE__] = {
        "deobf": "Decode obfuscated text/file",
        "deobfai": "Decode + AI clean",
        "deobfdeep": "Deep AI deobfuscation"
    }