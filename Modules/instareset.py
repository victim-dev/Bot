import os
import random
import string
import uuid
import asyncio
import requests
from datetime import datetime
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import format_success, format_error, header, separator

__MODULE__ = "instareset"

# ──────────────────────────────────────────────────────────────
# Helper functions (synchronous, will be run in thread)
# ──────────────────────────────────────────────────────────────
def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:Random@{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    """Get username from user ID."""
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = requests.get(url, headers=headers)
        return r.json()["user"]["username"]
    except Exception:
        return None

def reset_instagram_password_sync(reset_link):
    """Synchronous reset attempt, returns dict with result."""
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        # Extract uidb36 and token from link
        parts = reset_link.split("uidb36=")[1].split("&token=")
        uidb36 = parts[0]
        token = parts[1].split(":")[0]

        # Step 1: password reset request
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r = requests.post(url, headers=make_headers(user_agent=USER_AGENT), data=data)

        if "user_id" not in r.text:
            return {"success": False, "error": f"Reset request failed: {r.text[:200]}"}

        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        # Step 2: challenge navigation
        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        r2 = requests.post(url2, headers=make_headers(mid, USER_AGENT), data=data2).text

        # Extract challenge_context_final from r2
        import re
        match = re.search(r'\(bk\.action\.i64\.Const, {cni}), "([^"]+)"'.replace("{cni}", str(cni)), r2)
        if not match:
            return {"success": False, "error": "Failed to extract challenge context."}
        challenge_context_final = match.group(1)

        # Step 3: set new password
        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        requests.post(url2, headers=make_headers(mid, USER_AGENT), json=data3)
        new_password = PASSWORD.split(":")[-1]

        username = id_user(user_id)
        return {
            "success": True,
            "username": username,
            "password": new_password
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def reset_instagram_password(reset_link):
    """Async wrapper."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, reset_instagram_password_sync, reset_link)

# ──────────────────────────────────────────────────────────────
# Command handler
# ──────────────────────────────────────────────────────────────
async def instareset_command(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: .instareset <reset_link>"))
    reset_link = args[0]
    if not reset_link.startswith("https://") or "uidb36=" not in reset_link:
        return await message.edit(format_error("Invalid reset link. Must be a valid Instagram password reset URL."))

    msg = await message.edit(f"{header('Instagram Password Reset')}\n{separator()}\nProcessing...")
    result = await reset_instagram_password(reset_link)

    if result.get("success"):
        text = (
            f"{header('Success')}\n{separator()}\n"
            f"Username: <code>{result['username']}</code>\n"
            f"New Password: <code>{result['password']}</code>\n"
            f"{separator()}"
        )
        await msg.edit(text)
    else:
        error_msg = result.get("error", "Unknown error")
        await msg.edit(format_error(f"Reset failed: {error_msg}"))

def register(app):
    app.add_handler(MessageHandler(instareset_command, filters.command("instareset", prefixes=".") & filters.me))
    help_dict[__MODULE__] = {
        "instareset <reset_link>": "Attempt to reset an Instagram account password using a valid reset link."
    }