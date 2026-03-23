# bot.py
import os
import asyncio
import logging
import importlib
from pathlib import Path

# ─── Load environment variables from .env file ───
from dotenv import load_dotenv
load_dotenv()  # this reads .env in the current directory

from pyrogram import Client, idle
from pyrogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Environment variables (fallbacks for convenience) ───
API_ID = int(os.getenv("API_ID", 0))          # get from .env or set default
API_HASH = os.getenv("API_HASH", "")
MONGO_URI = os.getenv("MONGO_URI", "")        # optional MongoDB connection string

# ─── Check required values ───
if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set in .env file")

MODULES = {}

async def load_modules(client):
    modules_dir = Path("modules")
    modules_dir.mkdir(exist_ok=True)

    for file in modules_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue
        module_name = file.stem
        try:
            module = importlib.import_module(f"modules.{module_name}")
            if hasattr(module, "register"):
                module.register(client)
            MODULES[module_name] = module
            logger.info(f"Loaded: {module_name}")
        except Exception as e:
            logger.error(f"Failed {module_name}: {e}")

async def main():
    client = Client(
        "my_userbot",
        api_id=API_ID,
        api_hash=API_HASH,
        parse_mode=ParseMode.HTML,
        workdir="."
    )

    await client.start()
    logger.info("Userbot started!")

    # Store owner ID for modules that need it
    me = await client.get_me()
    client.owner_id = me.id
    logger.info(f"Owner ID: {client.owner_id}")

    await load_modules(client)

    await idle()

    await client.stop()

if __name__ == "__main__":
    import os   # needed for os.getenv
    asyncio.run(main())