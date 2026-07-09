import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_telegram_alert(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    """
    Send an alert message to a configured Telegram chat.
    Accepts optional bot_token and chat_id overrides (from DB settings).
    Falls back to settings from .env if not provided.
    Returns True if successful, False otherwise.
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    cid = chat_id or settings.TELEGRAM_CHAT_ID

    if not token or not cid:
        logger.warning("Telegram bot not configured. Skipping alert.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {message[:80]}")
                return True
            else:
                logger.error(f"Telegram API error {response.status_code}: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


async def alert_upload_success(video_title: str, platform: str, channel_name: str, url: str = "") -> None:
    """Send alert when a video is successfully uploaded."""
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_setting
    
    async with AsyncSessionLocal() as db:
        if await get_setting("NOTIFY_UPLOAD_SUCCESS", db, "true") != "true":
            return

    message = (
        f"✅ <b>Upload Successful!</b>\n"
        f"📺 Platform: {platform.upper()}\n"
        f"📢 Channel: {channel_name}\n"
        f"🎬 Title: {video_title}\n"
    )
    if url:
        message += f"🔗 URL: {url}"
    await send_telegram_alert(message)



async def alert_quota_exhausted(service_name: str, key_id: str) -> None:
    """Send alert when an API key quota is exhausted."""
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_setting
    
    async with AsyncSessionLocal() as db:
        if await get_setting("NOTIFY_QUOTA_EXHAUSTED", db, "true") != "true":
            return

    message = (
        f"⚠️ <b>API Key Quota Exhausted!</b>\n"
        f"🔑 Service: {service_name.upper()}\n"
        f"🆔 Key ID: {key_id}\n"
        f"⏰ Key locked for 24 hours. Rotating to next available key..."
    )
    await send_telegram_alert(message)



async def alert_token_expired(channel_name: str, platform: str) -> None:
    """Send alert when an account OAuth token expires."""
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_setting
    
    async with AsyncSessionLocal() as db:
        if await get_setting("NOTIFY_TOKEN_EXPIRED", db, "true") != "true":
            return

    message = (
        f"🔴 <b>Account Token Expired!</b>\n"
        f"📢 Channel: {channel_name}\n"
        f"📺 Platform: {platform.upper()}\n"
        f"⚡ Action required: Re-authenticate the account in the dashboard."
    )
    await send_telegram_alert(message)



async def alert_task_failed(task_name: str, error: str) -> None:
    """Send alert when a Celery task fails."""
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_setting
    
    async with AsyncSessionLocal() as db:
        if await get_setting("NOTIFY_TASK_FAILED", db, "true") != "true":
            return

    message = (
        f"❌ <b>Task Failed!</b>\n"
        f"📋 Task: {task_name}\n"
        f"💥 Error: {error[:500]}"
    )
    await send_telegram_alert(message)



# ── Telegram Bot Command Handling (Polling) ────────────────────────────────
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

async def get_system_report_msg() -> str:
    """Helper to generate the system report string."""
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_system_report
    try:
        async with AsyncSessionLocal() as db:
            report_obj = await get_system_report(db)
            report = report_obj.dict()
            
        msg = (
            f"📊 <b>AutoStream System Report</b>\n\n"
            f"💻 <b>Host Resources:</b>\n"
            f"├ CPU: {report['system_resources']['cpu_percent']}%\n"
            f"├ RAM: {report['system_resources']['memory_percent']}% ({report['system_resources']['memory_used_gb']}GB)\n"
            f"└ Disk Free: {report['system_resources']['disk_free_gb']}GB ({report['system_resources']['disk_percent']}% used)\n\n"
            f"🔑 <b>API Keys:</b>\n"
            f"├ Google: {report['api_keys']['google_active']} Active | {report['api_keys']['google_locked']} Locked\n"
            f"└ Meta:   {report['api_keys']['meta_active']} Active | {report['api_keys']['meta_locked']} Locked\n\n"
            f"🗄️ <b>Database Items:</b>\n"
            f"├ Accounts: {report['database']['total_accounts']} (YT: {report['database']['youtube_accounts']}, FB: {report['database']['facebook_accounts']}, IG: {report['database']['instagram_accounts']})\n"
            f"├ Videos Synced: {report['database']['total_videos']}\n\n"
            f"🚀 <b>Upload Schedules:</b>\n"
            f"├ Total:     {report['database']['total_schedules']}\n"
            f"├ Published: {report['database']['published_schedules']}\n"
            f"├ Pending:   {report['database']['pending_schedules']}\n"
            f"└ Failed:    {report['database']['failed_schedules']}\n\n"
            f"⚠️ <b>Last System Error:</b>\n"
            f"<code>{report['last_error'][:100]}</code>"
        )
        return msg
    except Exception as e:
        logger.error(f"Error generating system report: {e}")
        return f"❌ Failed to generate report: {str(e)[:100]}"


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /report command from the Telegram bot."""
    msg = await get_system_report_msg()
    await update.message.reply_text(msg, parse_mode="HTML")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start or /menu command to show the control panel."""
    msg = "🎛️ <b>AutoStream AI Control Panel</b>\nSelect an option below to manage your system:"
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /stats command")
    msg = await get_system_report_msg()
    await update.message.reply_text(msg, parse_mode="HTML")

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /channels command")
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import Account, AccountStatusEnum, PlatformEnum
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account).where(Account.status == AccountStatusEnum.ACTIVE))
        accounts = result.scalars().all()
        if not accounts:
            msg = "ℹ️ No active accounts found."
        else:
            msg = "👥 <b>Active Accounts</b>\n\n"
            for acc in accounts:
                icon = "🎬" if acc.platform == PlatformEnum.YOUTUBE else "📘" if acc.platform == PlatformEnum.FACEBOOK else "📸"
                msg += f"{icon} {acc.channel_name} ({acc.platform.value})\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /pending command")
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.models import UploadSchedule
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.is_published == False))
        count = result.scalar()
        msg = f"🚀 <b>Pending Schedules:</b> {count} video(s) waiting in queue."
    await update.message.reply_text(msg, parse_mode="HTML")

async def failed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /failed command")
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import UploadSchedule
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UploadSchedule).where(UploadSchedule.error_message != None).order_by(UploadSchedule.updated_at.desc()).limit(5)
        )
        failed = result.scalars().all()
        if not failed:
            msg = "✅ No failed schedules found in recent logs."
        else:
            msg = "❌ <b>Recent Failed Schedules</b>\n\n"
            for s in failed:
                msg += f"• ID: <code>{str(s.id)[:8]}</code>\n  Error: {s.error_message[:100]}...\n\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /health command")
    from app.routers.dashboard import health_check
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        health = await health_check(db)
        msg = (
            f"🩺 <b>System Health Status</b>\n\n"
            f"├ Database: {'✅' if health['database'] == 'healthy' else '❌ ' + health['database']}\n"
            f"├ Redis:    {'✅' if health['redis'] == 'healthy' else '❌ ' + health['redis']}\n"
            f"└ Workers:  {'✅' if health['celery'] == 'healthy' else '❌ ' + health['celery']}"
        )
    await update.message.reply_text(msg, parse_mode="HTML")

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /logs command")
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.models import SystemLog
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SystemLog).order_by(SystemLog.created_at.desc()).limit(5))
        logs = result.scalars().all()
        if not logs:
            msg = "ℹ️ No system logs found."
        else:
            msg = "📜 <b>Recent System Logs</b>\n\n"
            for log in logs:
                level_icon = "🔴" if log.level == "ERROR" else "🟠" if log.level == "WARNING" else "🔵"
                msg += f"{level_icon} {log.message[:150]}\n\n"
    await update.message.reply_text(msg, parse_mode="HTML")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handling /settings command")
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_telegram_config
    async with AsyncSessionLocal() as db:
        config = await get_telegram_config(db)
        msg = (
            f"⚙️ <b>Telegram Bot Settings</b>\n\n"
            f"├ Token: <code>{config['bot_token_masked']}</code>\n"
            f"├ Chat ID: <code>{config['chat_id']}</code>\n\n"
            f"<b>Notifications:</b>\n"
            f"├ Success: {'✅' if config['notify_upload_success'] else '❌'}\n"
            f"├ Quota:   {'✅' if config['notify_quota_exhausted'] else '❌'}\n"
            f"├ Token:   {'✅' if config['notify_token_expired'] else '❌'}\n"
            f"└ Failure: {'✅' if config['notify_task_failed'] else '❌'}\n\n"
            f"<i>Edit these in the Web Dashboard.</i>"
        )
    await update.message.reply_text(msg, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Handle the /help command."""
    msg = (
        "📖 <b>AutoStream AI Bot Help</b>\n\n"
        "Available Commands:\n"
        "/start - Show the interactive menu\n"
        "/menu - Show the interactive menu\n"
        "/report - Get a full system health report\n"
        "/help - Show this help message\n\n"
        "<i>Interactive Menu Buttons:</i>\n"
        "• System Report: Full stats overview\n"
        "• Pending Schedules: View queued tasks\n"
        "• Active Accounts: List connected social accounts\n"
        "• System Health: Check Redis, DB, and Workers"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

def get_main_menu_keyboard():
    """Builds the main control panel keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 System Report", callback_data="system_report"),
         InlineKeyboardButton("🩺 System Health", callback_data="system_health")],
        [InlineKeyboardButton("🚀 Pending Schedules", callback_data="pending_schedules"),
         InlineKeyboardButton("👥 Active Accounts", callback_data="active_accounts")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle interactive button clicks from the inline keyboard."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    data = query.data
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, func
    from app.models.models import Account, UploadSchedule, AccountStatusEnum, PlatformEnum

    try:
        reply_msg = ""
        if data == "system_report":
            reply_msg = await get_system_report_msg()
            
        elif data == "active_accounts":
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Account.channel_name, Account.platform).where(Account.status == AccountStatusEnum.ACTIVE)
                )
                accounts = result.all()
                if not accounts:
                    reply_msg = "ℹ️ No active accounts found."
                else:
                    reply_msg = "👥 <b>Active Accounts</b>\n"
                    for acc in accounts:
                        icon = "🎬" if acc.platform == PlatformEnum.YOUTUBE else "📘" if acc.platform == PlatformEnum.FACEBOOK else "📸"
                        reply_msg += f"{icon} {acc.channel_name}\n"
                        
        elif data == "pending_schedules":
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.is_published == False))
                count = result.scalar()
                reply_msg = f"🚀 <b>Pending Schedules:</b> {count} video(s) waiting in queue."

        elif data == "system_health":
            from app.routers.dashboard import health_check
            async with AsyncSessionLocal() as db:
                health = await health_check(db)
                reply_msg = (
                    f"🩺 <b>System Health Status</b>\n\n"
                    f"├ Database: {'✅' if health['database'] == 'healthy' else '❌ ' + health['database']}\n"
                    f"├ Redis:    {'✅' if health['redis'] == 'healthy' else '❌ ' + health['redis']}\n"
                    f"└ Workers:  {'✅' if health['celery'] == 'healthy' else '❌ ' + health['celery']}"
                )


        # Update the message with the new text and keep the menu keyboard below it
        if reply_msg:
            await query.edit_message_text(text=reply_msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.error(f"Error handling callback query {data}: {e}")
        await query.edit_message_text(text=f"❌ Error processing request: {e}", reply_markup=get_main_menu_keyboard())


_telegram_application = None

async def start_telegram_polling(force_restart=False):
    """Background task to run the python-telegram-bot application loop.
    If force_restart is True, stops the existing loop and restarts it with a new token.
    """
    global _telegram_application
    from app.database import AsyncSessionLocal
    from app.routers.dashboard import get_setting

    if _telegram_application and not force_restart:
        return

    if _telegram_application and force_restart:
        logger.info("Stopping existing Telegram polling...")
        try:
            await _telegram_application.updater.stop()
            await _telegram_application.stop()
        except Exception as e:
            logger.error(f"Error stopping old telegram polling: {e}")
        _telegram_application = None

    async with AsyncSessionLocal() as db:
        bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
        
    if not bot_token:
        logger.warning("Telegram Bot Token not configured. Polling disabled.")
        return

    logger.info("Starting Telegram bot polling for slash commands...")
    try:
        application = Application.builder().token(bot_token).build()
        application.add_handler(CommandHandler("start", menu_command))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("report", report_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("channels", channels_command))
        application.add_handler(CommandHandler("pending", pending_command))
        application.add_handler(CommandHandler("failed", failed_command))
        application.add_handler(CommandHandler("health", health_command))
        application.add_handler(CommandHandler("logs", logs_command))
        application.add_handler(CommandHandler("settings", settings_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button_handler))


        
        # Initialize and start the application in the background event loop
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        # Store for future restarts
        _telegram_application = application
    except Exception as e:
        logger.error(f"Failed to start telegram polling: {e}")
