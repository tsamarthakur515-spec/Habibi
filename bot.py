# bot.py — Habibi BanBot v3 | Custom Prefix: /bakchodi
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserAdminInvalid, ChatAdminRequired, RPCError
from config import API_ID, API_HASH, BOT_TOKEN, SUDO_USERS, CMD_PREFIX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client(
    "banbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ─────────────────────────────────────────
#  CUSTOM PREFIX FILTER
# ─────────────────────────────────────────

def bakchodi_cmd(*commands):
    """
    Custom filter — sirf /bakchodi_COMMAND pe respond karta hai.
    /start, /help, /banall = ignore
    /bakchodi_banall = chalega
    """
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        text = message.text.strip()
        for cmd in flt.commands:
            full_cmd = f"/{CMD_PREFIX}_{cmd}"
            full_cmd_at = f"/{CMD_PREFIX}_{cmd}@"
            if text == full_cmd or text.startswith(full_cmd + " ") or text.startswith(full_cmd_at):
                return True
        return False

    return filters.create(func, commands=list(commands))

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def is_sudo(uid: int) -> bool:
    return uid in SUDO_USERS

def progress_bar(done: int, total: int, length: int = 12) -> str:
    if total == 0:
        return "░" * length
    filled = int(length * done / total)
    return "█" * filled + "░" * (length - filled)

async def safe_ban(client, chat_id, user_id):
    for _ in range(3):
        try:
            await client.ban_chat_member(chat_id, user_id)
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserAdminInvalid, ChatAdminRequired):
            return False
        except RPCError:
            await asyncio.sleep(0.3)
    return False

async def safe_unban(client, chat_id, user_id):
    for _ in range(3):
        try:
            await client.unban_chat_member(chat_id, user_id)
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except RPCError:
            await asyncio.sleep(0.3)
    return False

async def safe_mute(client, chat_id, user_id):
    perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_invite_users=False
    )
    for _ in range(3):
        try:
            await client.restrict_chat_member(chat_id, user_id, perms)
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except RPCError:
            await asyncio.sleep(0.3)
    return False

async def safe_kick(client, chat_id, user_id):
    try:
        await client.ban_chat_member(chat_id, user_id)
        await asyncio.sleep(0.1)
        await client.unban_chat_member(chat_id, user_id)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return False
    except Exception:
        return False

# ─────────────────────────────────────────
#  BATCH ENGINE
# ─────────────────────────────────────────

async def batch_action(client, chat_id, user_ids, action_fn, status_msg, action_name, emoji):
    total = len(user_ids)
    done = 0
    success = 0
    failed = 0
    BATCH_SIZE = 8

    async def worker(uid):
        nonlocal done, success, failed
        result = await action_fn(client, chat_id, uid)
        done += 1
        if result:
            success += 1
        else:
            failed += 1

    for i in range(0, total, BATCH_SIZE):
        batch = user_ids[i:i + BATCH_SIZE]
        await asyncio.gather(*[worker(uid) for uid in batch])

        if done % 15 < BATCH_SIZE or done >= total:
            bar = progress_bar(done, total)
            pct = int(100 * done / total) if total else 100
            try:
                await status_msg.edit(
                    f"{emoji} **{action_name} — Running**\n"
                    f"┌ Progress : `{bar}` {pct}%\n"
                    f"├ ✅ Success : `{success}`\n"
                    f"├ ❌ Failed  : `{failed}`\n"
                    f"└ 📊 Total   : `{done}/{total}`"
                )
            except Exception:
                pass

        await asyncio.sleep(0.08)

    return success, failed

async def collect_members(client, chat_id):
    members = []
    async for m in client.get_chat_members(chat_id):
        if m.user.is_bot:
            continue
        if m.user.id in SUDO_USERS:
            continue
        if m.status in ("administrator", "creator"):
            continue
        members.append(m.user.id)
    return members

async def collect_banned(client, chat_id):
    members = []
    async for m in client.get_chat_members(chat_id, filter="banned"):
        members.append(m.user.id)
    return members

# ─────────────────────────────────────────
#  COMMANDS — sirf /bakchodi_X pe chalte hain
# ─────────────────────────────────────────

@app.on_message(bakchodi_cmd("menu", "start", "help"))
async def menu_cmd(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔨 Ban-All", callback_data="info_ban"),
            InlineKeyboardButton("🔓 Unban-All", callback_data="info_unban")
        ],
        [
            InlineKeyboardButton("🔇 Mute-All", callback_data="info_mute"),
            InlineKeyboardButton("👟 Kick-All", callback_data="info_kick")
        ],
        [InlineKeyboardButton("📊 Stats", callback_data="info_stats")]
    ])

    await message.reply(
        f"⚡ **Habibi BanBot v3**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Prefix: `/{CMD_PREFIX}_COMMAND`\n\n"
        f"**Commands:**\n"
        f"`/{CMD_PREFIX}_banall` — Sab ko ban karo\n"
        f"`/{CMD_PREFIX}_unbanall` — Sab ko unban karo\n"
        f"`/{CMD_PREFIX}_muteall` — Sab ko mute karo\n"
        f"`/{CMD_PREFIX}_kickall` — Sab ko kick karo\n"
        f"`/{CMD_PREFIX}_stats` — Group stats\n"
        f"`/{CMD_PREFIX}_menu` — Yeh menu\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_/start aur /help ignore kiye jaate hain._",
        reply_markup=keyboard
    )

@app.on_message(bakchodi_cmd("banall") & filters.group)
async def banall_cmd(client, message: Message):
    if not is_sudo(message.from_user.id):
        return await message.reply("🚫 **Access Denied**")

    bot_me = await client.get_chat_member(message.chat.id, "me")
    if not getattr(bot_me.privileges, "can_restrict_members", False):
        return await message.reply("⚠️ Mujhe ban rights chahiye pehle.")

    status = await message.reply("⚡ **BAN-ALL INITIATED**\n└ Members collect ho rahe hain...")
    user_ids = await collect_members(client, message.chat.id)

    if not user_ids:
        return await status.edit("✅ Koi bannable member nahi mila.")

    s, f = await batch_action(client, message.chat.id, user_ids, safe_ban, status, "BAN-ALL", "🔨")

    await status.edit(
        f"🔨 **BAN-ALL — COMPLETE**\n"
        f"┌ ✅ Banned : `{s}`\n"
        f"├ ❌ Failed : `{f}`\n"
        f"└ 👥 Total  : `{s + f}`\n\n"
        f"_By_ {message.from_user.mention}"
    )

@app.on_message(bakchodi_cmd("unbanall") & filters.group)
async def unbanall_cmd(client, message: Message):
    if not is_sudo(message.from_user.id):
        return await message.reply("🚫 **Access Denied**")

    status = await message.reply("🔓 **UNBAN-ALL INITIATED**\n└ List fetch ho rahi hai...")
    user_ids = await collect_banned(client, message.chat.id)

    if not user_ids:
        return await status.edit("✅ Koi banned member nahi hai.")

    s, f = await batch_action(client, message.chat.id, user_ids, safe_unban, status, "UNBAN-ALL", "🔓")

    await status.edit(
        f"🔓 **UNBAN-ALL — COMPLETE**\n"
        f"┌ ✅ Unbanned : `{s}`\n"
        f"├ ❌ Failed   : `{f}`\n"
        f"└ 👥 Total    : `{s + f}`\n\n"
        f"_By_ {message.from_user.mention}"
    )

@app.on_message(bakchodi_cmd("muteall") & filters.group)
async def muteall_cmd(client, message: Message):
    if not is_sudo(message.from_user.id):
        return await message.reply("🚫 **Access Denied**")

    status = await message.reply("🔇 **MUTE-ALL INITIATED**\n└ Members collect ho rahe hain...")
    user_ids = await collect_members(client, message.chat.id)

    if not user_ids:
        return await status.edit("✅ Koi muteable member nahi mila.")

    s, f = await batch_action(client, message.chat.id, user_ids, safe_mute, status, "MUTE-ALL", "🔇")

    await status.edit(
        f"🔇 **MUTE-ALL — COMPLETE**\n"
        f"┌ ✅ Muted  : `{s}`\n"
        f"├ ❌ Failed : `{f}`\n"
        f"└ 👥 Total  : `{s + f}`\n\n"
        f"_By_ {message.from_user.mention}"
    )

@app.on_message(bakchodi_cmd("kickall") & filters.group)
async def kickall_cmd(client, message: Message):
    if not is_sudo(message.from_user.id):
        return await message.reply("🚫 **Access Denied**")

    status = await message.reply("👟 **KICK-ALL INITIATED**\n└ Members collect ho rahe hain...")
    user_ids = await collect_members(client, message.chat.id)

    if not user_ids:
        return await status.edit("✅ Koi kickable member nahi mila.")

    s, f = await batch_action(client, message.chat.id, user_ids, safe_kick, status, "KICK-ALL", "👟")

    await status.edit(
        f"👟 **KICK-ALL — COMPLETE**\n"
        f"┌ ✅ Kicked : `{s}`\n"
        f"├ ❌ Failed : `{f}`\n"
        f"└ 👥 Total  : `{s + f}`\n\n"
        f"_By_ {message.from_user.mention}"
    )

@app.on_message(bakchodi_cmd("stats") & filters.group)
async def stats_cmd(client, message: Message):
    chat = await client.get_chat(message.chat.id)
    total = chat.members_count

    admins = 0
    async for _ in client.get_chat_members(message.chat.id, filter="administrators"):
        admins += 1

    bots = 0
    async for m in client.get_chat_members(message.chat.id):
        if m.user.is_bot:
            bots += 1

    await message.reply(
        f"📊 **Group Stats — {chat.title}**\n"
        f"┌ 👥 Total Members : `{total}`\n"
        f"├ 🛡️ Admins        : `{admins}`\n"
        f"├ 🤖 Bots          : `{bots}`\n"
        f"└ 👤 Users         : `{total - admins - bots}`"
    )

# ─────────────────────────────────────────
#  CALLBACK
# ─────────────────────────────────────────

@app.on_callback_query()
async def cb_handler(client, query):
    info = {
        "info_ban":   f"🔨 /{CMD_PREFIX}_banall — Sab members ko ban. Admins + Sudo safe.",
        "info_unban": f"🔓 /{CMD_PREFIX}_unbanall — Sare banned members unban.",
        "info_mute":  f"🔇 /{CMD_PREFIX}_muteall — Sabko mute. Admins safe.",
        "info_kick":  f"👟 /{CMD_PREFIX}_kickall — Sabko kick (rejoin allowed).",
        "info_stats": f"📊 /{CMD_PREFIX}_stats — Group members breakdown.",
    }
    await query.answer(info.get(query.data, "—"), show_alert=True)

# ─────────────────────────────────────────
#  LAUNCH
# ─────────────────────────────────────────

if __name__ == "__main__":
    logger.info(f"⚡ Habibi BanBot v3 — Prefix: /{CMD_PREFIX}_COMMAND | 6767")
    app.run()