import asyncio
import re
import random
import string
import time
import json
import requests
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from modules.help import help_dict
from utils.style import format_success, format_error, header, separator

__MODULE__ = "account_checker"

# ──────────────────────────────────────────────────────────────
# AOL checker
# ──────────────────────────────────────────────────────────────
WEB_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def _aol_available_sync(username: str) -> bool:
    """Synchronous AOL check."""
    time.sleep(random.uniform(0.3, 1.0))
    s = requests.Session()

    create_url = 'https://login.aol.com/account/create?specId=yidregsimplified&done=https%3A%2F%2Fapi.login.aol.com%2Foauth2%2Fauthorize%3Factivity%3Dheader-signin%26client_id%3Ddj0yJmk9VlN3cDhpNm1Id0szJmQ9WVdrOVdtRm1aMVU1Tm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1mYQ--%26language%3Dtr-TR%26nonce%3DespCiEVdB33iuFGue3kB74NAbyy3wQWj%26pspid%3D1197806870%26redirect_uri%3Dhttps%253A%252F%252Foidc.mail.aol.com%252Fcallback%26response_type%3Dcode%26scope%3Dmail-r%2520ycal-w%2520openid%2520openid2%2520mail-w%2520mail-x%2520sdps-r%2520msgr-w%26src%3Dmail%26state%3DeyJhbGciOiJSUzI1NiIsImtpZCI6IjZmZjk0Y2RhZDExZTdjM2FjMDhkYzllYzNjNDQ4NDRiODdlMzY0ZjcifQ.eyJyZWRpcmVjdFVyaSI6Imh0dHBzOi8vbWFpbC5hb2wuY29tL2QifQ.JMX40ZssLtCMlaqAOZYFU6Tz6rggXd8IYA-lVO2jkmWcFPGEJ3tTkOj7qGkKjtTLXofPUFFQ6Uzih1pYCkh_fgS1zD8X5Ge3c0oSKTchP4AdNmsEetEyDMoUijvOWJVVbDe0byUHYQzCmE7F-o2187M5fpzxgGEV6U-7Xm4ywaA'

    headers = {
        'authority': 'login.aol.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'user-agent': random.choice(WEB_USER_AGENTS),
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    r1 = s.get(create_url, headers=headers)
    if r1.status_code != 200:
        return False

    specId_match = re.search(r'name="specId"\s+value="([^"]+)"', r1.text)
    acrumb_match = re.search(r'name="acrumb"\s+value="([^"]+)"', r1.text)
    sessionIndex_match = re.search(r'name="sessionIndex"\s+value="([^"]+)"', r1.text)

    if not (specId_match and acrumb_match and sessionIndex_match):
        return False

    specId = specId_match.group(1)
    acrumb = acrumb_match.group(1)
    sessionIndex = sessionIndex_match.group(1)

    validate_url = f'https://login.aol.com/account/create/validate?specId={specId}&done=https%3A%2F%2Fapi.login.aol.com%2Foauth2%2Fauthorize%3Factivity%3Dheader-signin%26client_id%3Ddj0yJmk9VlN3cDhpNm1Id0szJmQ9WVdrOVdtRm1aMVU1Tm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1mYQ--%26language%3Dtr-TR%26nonce%3DespCiEVdB33iuFGue3kB74NAbyy3wQWj%26pspid%3D1197806870%26redirect_uri%3Dhttps%253A%252F%252Foidc.mail.aol.com%252Fcallback%26response_type%3Dcode%26scope%3Dmail-r%2520ycal-w%2520openid%2520openid2%2520mail-w%2520mail-x%2520sdps-r%2520msgr-w%26src%3Dmail%26state%3DeyJhbGciOiJSUzI1NiIsImtpZCI6IjZmZjk0Y2RhZDExZTdjM2FjMDhkYzllYzNjNDQ4NDRiODdlMzY0ZjcifQ.eyJyZWRpcmVjdFVyaSI6Imh0dHBzOi8vbWFpbC5hb2wuY29tL2QifQ.JMX40ZssLtCMlaqAOZYFU6Tz6rggXd8IYA-lVO2jkmWcFPGEJ3tTkOj7qGkKjtTLXofPUFFQ6Uzih1pYCkh_fgS1zD8X5Ge3c0oSKTchP4AdNmsEetEyDMoUijvOWJVVbDe0byUHYQzCmE7F-o2187M5fpzxgGEV6U-7Xm4ywaA'

    data = {
        'specId': specId,
        'acrumb': acrumb,
        'sessionIndex': sessionIndex,
        'userId': username,
        'validateField': 'userId'
    }

    headers2 = {
        'authority': 'login.aol.com',
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://login.aol.com',
        'referer': create_url,
        'user-agent': random.choice(WEB_USER_AGENTS),
        'x-requested-with': 'XMLHttpRequest',
    }

    r2 = s.post(validate_url, headers=headers2, data=data)

    if r2.status_code != 200:
        return False

    try:
        json_resp = r2.json()
        user_field = json_resp.get('fields', {}).get('userId', {})
        if 'error' in user_field:
            error_id = user_field['error'].get('id')
            if error_id in ["IDENTIFIER_EXISTS", "IDENTIFIER_NOT_AVAILABLE", "RESERVED_WORD_PRESENT"]:
                return False
            else:
                return False
        else:
            return True
    except Exception:
        # fallback
        if '"errors":[]' in r2.text or 'IDENTIFIER_AVAILABLE' in r2.text:
            return True
        return False

async def aol_available(username: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _aol_available_sync, username)

# ──────────────────────────────────────────────────────────────
# Instagram checker
# ──────────────────────────────────────────────────────────────
IG_USER_AGENTS = [
    "Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546B; a54x; exynos1380; en_US; 465123678)",
    "Instagram 319.0.0.30.121 Android (31/12; 440dpi; 1080x2400; xiaomi; M2101K6G; sweet; qcom; en_GB; 454782345)",
]

def _instagram_check_sync(username_or_email: str) -> str | None:
    """Returns masked contact point if account exists, else None."""
    headers = {
        "user-agent": random.choice(IG_USER_AGENTS),
        "x-ig-app-id": "936619743392459",
        "x-requested-with": "XMLHttpRequest",
        "x-instagram-ajax": "1032099486",
        "x-csrftoken": "missing",
        "x-asbd-id": "359341",
        "origin": "https://www.instagram.com",
        "referer": "https://www.instagram.com/accounts/password/reset/",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
    }

    try:
        import httpx
        client = httpx.Client(http2=True, headers=headers)
        r = client.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data={"email_or_username": username_or_email}
        )
        client.close()
    except ImportError:
        # Fallback to requests
        r = requests.post(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data={"email_or_username": username_or_email},
            headers=headers
        )

    if r.status_code != 200:
        return None

    try:
        data = r.json()
        if data.get("status") != "ok":
            return None
        contact = data.get('contact_point') or data.get('masked_email')
        if contact and '@' in contact:
            return contact
        return None
    except Exception:
        return None

async def instagram_check(username_or_email: str) -> str | None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _instagram_check_sync, username_or_email)

# ──────────────────────────────────────────────────────────────
# Gmail checker (with token refresh)
# ──────────────────────────────────────────────────────────────
_tl_cache = None
_host_cache = None

def _random_user_agent():
    chrome_versions = ['120.0.0.0', '119.0.0.0', '118.0.0.0']
    platform = random.choice(['Windows NT 10.0; Win64; x64', 'Macintosh; Intel Mac OS X 10_15_7', 'X11; Linux x86_64'])
    return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"

def _generate_tl_sync():
    global _tl_cache, _host_cache
    chars = 'abcdefghijklmnopqrstuvwxyz'
    n1 = ''.join(random.choices(chars, k=random.randrange(6,9)))
    n2 = ''.join(random.choices(chars, k=random.randrange(3,9)))
    host = ''.join(random.choices(chars, k=random.randrange(15,30)))

    headers = {
        "accept": "*/*",
        "accept-language": "ar-IQ,ar;q=0.9,en-IQ;q=0.8,en;q=0.7,en-US;q=0.6",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "google-accounts-xsrf": "1",
        "sec-ch-ua": '"Not)A;Brand";v="24", "Chromium";v="116"',
        "sec-ch-ua-arch": '""',
        "sec-ch-ua-bitness": '""',
        "sec-ch-ua-full-version": '"116.0.5845.72"',
        "sec-ch-ua-full-version-list": '"Not)A;Brand";v="24.0.0.0", "Chromium";v="116.0.5845.72"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-model": '"ANY-LX2"',
        "sec-ch-ua-platform": '"Android"',
        "sec-ch-ua-platform-version": '"13.0.0"',
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-chrome-connected": "source=Chrome,eligible_for_consistency=true",
        "x-client-data": "CJjbygE=",
        "x-same-domain": "1",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        'user-agent': _random_user_agent(),
    }

    res1 = requests.get(
        'https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin&hl=en-GB',
        headers=headers
    )
    match = re.search(r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', res1.text)
    if not match:
        raise Exception("Failed to extract TL token")
    tok = match.group(2)

    cookies = {'__Host-GAPS': host}

    headers2 = {
        'authority': 'accounts.google.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'google-accounts-xsrf': '1',
        'origin': 'https://accounts.google.com',
        'referer': 'https://accounts.google.com/signup/v2/createaccount?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&parent_directed=true&theme=mn&ddm=0&flowName=GlifWebSignIn&flowEntry=SignUp',
        'user-agent': _random_user_agent(),
    }

    data = {
        'f.req': f'["{tok}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
        'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
    }

    response = requests.post(
        'https://accounts.google.com/_/signup/validatepersonaldetails',
        cookies=cookies,
        headers=headers2,
        data=data,
    )

    tl_match = re.search(r'",null,"([^"]+)"', response.text)
    if not tl_match:
        raise Exception("Failed to extract TL from validation response")
    tl = tl_match.group(1)
    host = response.cookies.get_dict().get('__Host-GAPS', host)

    _tl_cache = tl
    _host_cache = host
    return tl, host

def _check_gmail_sync(username: str) -> bool:
    global _tl_cache, _host_cache
    if not _tl_cache or not _host_cache:
        try:
            _generate_tl_sync()
        except Exception as e:
            return False

    tl = _tl_cache
    host = _host_cache
    cookies = {'__Host-GAPS': host}

    headers = {
        'authority': 'accounts.google.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'google-accounts-xsrf': '1',
        'origin': 'https://accounts.google.com',
        'referer': f'https://accounts.google.com/signup/v2/createusername?service=mail&continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&parent_directed=true&theme=mn&ddm=0&flowName=GlifWebSignIn&flowEntry=SignUp&TL={tl}',
        'user-agent': _random_user_agent(),
    }

    params = {'TL': tl}
    data = (
        f'continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&ddm=0&flowEntry=SignUp&service=mail&theme=mn'
        f'&f.req=%5B%22TL%3A{tl}%22%2C%22{username}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D'
        '&azt=AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig%3A1712322460888&cookiesDisabled=false'
        '&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22'
        '%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D'
        '&gmscoreversion=undefined&flowName=GlifWebSignIn&'
    )

    try:
        response = requests.post(
            'https://accounts.google.com/_/signup/usernameavailability',
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
            timeout=10
        )
        if '"er",null,null,null,null,400' in response.text:
            # token expired, refresh and retry
            _generate_tl_sync()
            return _check_gmail_sync(username)

        return '"gf.uar",1' in response.text
    except Exception:
        return False

async def gmail_available(username: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _check_gmail_sync, username)

# ──────────────────────────────────────────────────────────────
# Command handlers
# ──────────────────────────────────────────────────────────────
async def check_aol(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: .checkaol <username>"))
    username = args[0].lower()
    msg = await message.edit(f"Checking AOL username `{username}`...")
    available = await aol_available(username)
    result = "AVAILABLE" if available else "TAKEN"
    await msg.edit(f"**AOL Check**\nUsername: `{username}`\nResult: **{result}**")

async def check_ig(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: .checkig <username/email>"))
    query = args[0]
    msg = await message.edit(f"Checking Instagram account `{query}`...")
    contact = await instagram_check(query)
    if contact:
        await msg.edit(f"**Instagram Check**\nAccount `{query}` exists.\nContact: `{contact}`")
    else:
        await msg.edit(f"**Instagram Check**\nAccount `{query}` does NOT exist or could not be verified.")

async def check_gmail(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: .checkgmail <username>"))
    username = args[0].lower()
    msg = await message.edit(f"Checking Gmail username `{username}`...")
    available = await gmail_available(username)
    result = "AVAILABLE" if available else "TAKEN"
    await msg.edit(f"**Gmail Check**\nUsername: `{username}`@gmail.com\nResult: **{result}**")

async def check_all(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    if not args:
        return await message.edit(format_error("Usage: .checkall <username>"))
    username = args[0].lower()
    msg = await message.edit(f"Checking all services for `{username}`...")
    aol = await aol_available(username)
    ig_contact = await instagram_check(username)
    gmail = await gmail_available(username)

    text = f"{header('Account Check')}\n{separator()}\n"
    text += f"AOL: **{'AVAILABLE' if aol else 'TAKEN'}**\n"
    if ig_contact:
        text += f"Instagram: **EXISTS** (`{ig_contact}`)\n"
    else:
        text += f"Instagram: **DOES NOT EXIST** (or not verifiable)\n"
    text += f"Gmail: **{'AVAILABLE' if gmail else 'TAKEN'}**\n"
    text += separator()
    await msg.edit(text)

def register(app):
    app.add_handler(MessageHandler(check_aol, filters.command("checkaol", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(check_ig, filters.command("checkig", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(check_gmail, filters.command("checkgmail", prefixes=".") & filters.me))
    app.add_handler(MessageHandler(check_all, filters.command("checkall", prefixes=".") & filters.me))
    help_dict[__MODULE__] = {
        "checkaol <username>": "Check if an AOL username is available.",
        "checkig <username/email>": "Check if an Instagram account exists (returns masked contact).",
        "checkgmail <username>": "Check if a Gmail address is available.",
        "checkall <username>": "Check all three services at once."
    }