from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import subprocess
import psutil
import asyncio

# =============================== #
#        Configuration             #
# =============================== #

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ALLOWED_USER_ID = ALLOWED_YUSER_TELEGRAM_ID # [ 6797995190, 349687907 ]
CHAT_ID = "CHAT_ID"  # Replace with your Telegram ID

# Safe allowed shell commands
ALLOWED_COMMANDS = {
    "uptime": "uptime",
    "disk": "df -h",
    "memory": "free -h",
    "cpu": "top -bn1 | head -10",
    "services": "systemctl list-units --type=service --state=running | head -20",
    "restart_nginx": "sudo systemctl restart nginx",
    "restart_docker": "sudo systemctl restart docker",
}

# Services to monitor
MONITOR_SERVICES = ["nginx", "docker", "sshd"]

# Thresholds
CPU_THRESHOLD = 80
MEM_THRESHOLD = 85

# Alert interval (in seconds)
ALERT_INTERVAL = 300  # 5 minutes

# =============================== #
#        Helper Functions          #
# =============================== #

async def is_authorized(update: Update):
    """Ensure only authorized Telegram user can interact."""
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 Unauthorized user.")
        return False
    return True

async def run_shell_command(command: str):
    """Execute safe shell command."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True, timeout=10)
        return output.strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip()
    except Exception as e:
        return f"⚙️ Exception: {str(e)}"

# =============================== #
#        Command Handlers          #
# =============================== #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List available commands."""
    if not await is_authorized(update):
        return

    msg = (
        "🤖 *System Monitor Bot Active!*\n\n"
        "Available commands:\n"
        + "\n".join(f"/{cmd}" for cmd in ALLOWED_COMMANDS.keys())
        + "\n/status — check service statuses"
        + "\n/alert — check CPU & memory usage"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def run_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute safe whitelisted commands."""
    if not await is_authorized(update):
        return

    command_name = update.message.text.strip().replace("/", "")
    if command_name not in ALLOWED_COMMANDS:
        await update.message.reply_text("⚠️ Command not allowed.")
        return

    output = await run_shell_command(ALLOWED_COMMANDS[command_name])
    await update.message.reply_text(f"🖥️ Output:\n{output[:4000]}")

async def service_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check the status of specific services."""
    if not await is_authorized(update):
        return

    msg = "🔍 *Service Status Check:*\n\n"
    for svc in MONITOR_SERVICES:
        result = await run_shell_command(f"systemctl is-active {svc}")
        emoji = "✅" if result.strip() == "active" else "❌"
        msg += f"{emoji} {svc}: {result}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def system_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual check for CPU & memory."""
    if not await is_authorized(update):
        return

    msg = await get_system_alert_message()
    await update.message.reply_text(msg, parse_mode="Markdown")

# =============================== #
#        Background Alerts          #
# =============================== #

async def get_system_alert_message():
    """Build system alert message."""
    cpu_usage = psutil.cpu_percent(interval=1)
    mem_usage = psutil.virtual_memory().percent

    msg = "🚨 *System Health Check:*\n\n"
    msg += f"🧠 CPU Usage: {cpu_usage}% {'⚠️' if cpu_usage > CPU_THRESHOLD else '✅'}\n"
    msg += f"💾 Memory Usage: {mem_usage}% {'⚠️' if mem_usage > MEM_THRESHOLD else '✅'}\n"

    if cpu_usage > CPU_THRESHOLD or mem_usage > MEM_THRESHOLD:
        msg += "\n⚠️ *High usage detected!* Consider investigating."

    return msg

async def auto_alert_task(application):
    """Continuously check CPU/memory every 5 minutes."""
    await application.bot.send_message(chat_id=CHAT_ID, text="📡 Auto system alert monitor started!")

    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        mem_usage = psutil.virtual_memory().percent

        if cpu_usage > CPU_THRESHOLD or mem_usage > MEM_THRESHOLD:
            msg = await get_system_alert_message()
            await application.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

        await asyncio.sleep(ALERT_INTERVAL)

# =============================== #
#        Main Bot Setup             #
# =============================== #

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers here
    app.add_handler(CommandHandler("start", start))
    for cmd in ALLOWED_COMMANDS.keys():
        app.add_handler(CommandHandler(cmd, run_allowed))
    app.add_handler(CommandHandler("status", service_status))
    app.add_handler(CommandHandler("alert", system_alert))

    # Start background alert task
    asyncio.create_task(auto_alert_task(app))

    print("✅ Telegram system monitor bot running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # keep running forever

if __name__ == "__main__":
    asyncio.run(main())
