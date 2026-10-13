import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import (
    FloodWait, UserAdminInvalid, ChatAdminRequired,
    UserNotParticipant, RPCError
)
from config import API_ID, API_HASH, BOT_TOKEN, SUDO_USERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client(
    "banbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS

async def ban_member(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        await client.ban_chat_member(chat_id, user_id)
        return True
    except FloodWait as e:
        logger.warning(f"FloodWait: sleeping {e.value}s")
        await asyncio.sleep(e.value)
        return await ban_member(client, chat_id, user_id)
    except (UserAdminInvalid, ChatAdminRequired):
        return False
    except RPCError as e:
        logger.error(f"RPCError banning {user_id}: {e}")
        return False

@app.on_message(filters.command("banall") & filters.group)
async def banall_handler(client: Client, message: Message):
    if not is_sudo(message.from_user.id):
        await message.reply("❌ Tu sudo nahi hai bhai.")
        return

    chat_id = message.chat.id

    # Check bot admin status
    bot_member = await client.get_chat_member(chat_id, "me")
    if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
        await message.reply("❌ Mujhe ban permission chahiye pehle.")
        return

    status_msg = await message.reply("⚡ Ban-All shuru ho raha hai... sab gaye!")

    banned = 0
    failed = 0
    skipped = 0

    async for member in client.get_chat_members(chat_id):
        user_id = member.user.id

        # Skip bots, sudo users, and the bot itself
        if member.user.is_bot:
            skipped += 1
            continue
        if user_id in SUDO_USERS:
            skipped += 1
            continue
        if member.status in ("administrator", "creator"):
            skipped += 1
            continue

        success = await ban_member(client, chat_id, user_id)
        if success:
            banned += 1
        else:
            failed += 1

        # Progress update har 20 ban pe
        if (banned + failed) % 20 == 0:
            try:
                await status_msg.edit(
                    f"⚡ Progress: {banned} banned | {failed} failed | {skipped} skipped"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)  # Rate limit se bachne ke liye

    await status_msg.edit(
        f"✅ **Ban-All Complete!**\n"
        f"├ Banned: `{banned}`\n"
        f"├ Failed: `{failed}`\n"
        f"└ Skipped: `{skipped}` (admins/bots/sudo)"
    )

@app.on_message(filters.command("unbanall") & filters.group)
async def unbanall_handler(client: Client, message: Message):
    if not is_sudo(message.from_user.id):
        await message.reply("❌ Tu sudo nahi hai bhai.")
        return

    chat_id = message.chat.id
    status_msg = await message.reply("🔓 Unban-All shuru...")

    unbanned = 0
    failed = 0

    async for member in client.get_chat_members(chat_id, filter="banned"):
        user_id = member.user.id
        try:
            await client.unban_chat_member(chat_id, user_id)
            unbanned += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await client.unban_chat_member(chat_id, user_id)
                unbanned += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1

        await asyncio.sleep(0.05)

    await status_msg.edit(
        f"✅ **Unban-All Complete!**\n"
        f"├ Unbanned: `{unbanned}`\n"
        f"└ Failed: `{failed}`"
    )

@app.on_message(filters.command("muteall") & filters.group)
async def muteall_handler(client: Client, message: Message):
    if not is_sudo(message.from_user.id):
        await message.reply("❌ Tu sudo nahi hai.")
        return

    chat_id = message.chat.id
    status_msg = await message.reply("🔇 Mute-All shuru...")

    muted = 0
    failed = 0

    mute_perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    async for member in client.get_chat_members(chat_id):
        user_id = member.user.id
        if member.user.is_bot or user_id in SUDO_USERS:
            continue
        if member.status in ("administrator", "creator"):
            continue

        try:
            await client.restrict_chat_member(chat_id, user_id, mute_perms)
            muted += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            failed += 1

        await asyncio.sleep(0.05)

    await status_msg.edit(
        f"✅ **Mute-All Complete!**\n"
        f"├ Muted: `{muted}`\n"
        f"└ Failed: `{failed}`"
    )

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply(
        "⚡ **Ban-All Bot — VPS Ready**\n\n"
        "Commands:\n"
        "`/banall` — Sab members ko ban karo\n"
        "`/unbanall` — Sab ko unban karo\n"
        "`/muteall` — Sab ko mute karo\n\n"
        "Bot ko group admin + ban permission chahiye."
    )

if __name__ == "__main__":
    logger.info("Bot live ho gaya, baby. 6767.")
    app.run()