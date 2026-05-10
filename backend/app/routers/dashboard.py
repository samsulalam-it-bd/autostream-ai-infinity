from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import UploadSchedule, ApiKeyVault, Account, SystemSettings, PlatformEnum
from app.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ── Helper: Read/Write SystemSettings ─────────────────────────────────────
async def get_setting(key: str, db: AsyncSession, default: str = "") -> str:
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(key: str, value: str, db: AsyncSession) -> None:
    result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
    else:
        db.add(SystemSettings(key=key, value=value))
    await db.commit()


# ── Dashboard Stats ────────────────────────────────────────────────────────
@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats for the dashboard home page."""
    from app.models.models import SourceVideo

    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    uploads_today = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.is_published == True, UploadSchedule.published_at >= start_of_day)
        )
    )
    active_keys = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.is_locked == False)
    )
    pending = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.is_published == False, UploadSchedule.scheduled_time >= now)
        )
    )
    total_accounts = await db.execute(select(func.count(Account.id)))
    total_videos = await db.execute(select(func.count(SourceVideo.id)))
    
    # Engagement totals
    total_views = await db.execute(select(func.sum(UploadSchedule.view_count)).where(UploadSchedule.is_published == True))
    total_likes = await db.execute(select(func.sum(UploadSchedule.like_count)).where(UploadSchedule.is_published == True))
    total_comments = await db.execute(select(func.sum(UploadSchedule.comment_count)).where(UploadSchedule.is_published == True))

    return DashboardStats(
        total_uploads_today=uploads_today.scalar() or 0,
        active_api_keys=active_keys.scalar() or 0,
        pending_schedules=pending.scalar() or 0,
        total_accounts=total_accounts.scalar() or 0,
        total_videos=total_videos.scalar() or 0,
        total_views=total_views.scalar() or 0,
        total_likes=total_likes.scalar() or 0,
        total_comments=total_comments.scalar() or 0,
    )


# ── Upload Chart Data (Last 7 Days) ────────────────────────────────────────
@router.get("/upload-chart")
async def get_upload_chart(db: AsyncSession = Depends(get_db)):
    """Returns daily upload counts for the last 7 days for the Dashboard chart."""
    from sqlalchemy import cast, Date
    now = datetime.now(timezone.utc)
    days = []
    for i in range(6, -1, -1):  # 6 days ago → today
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        count_res = await db.execute(
            select(func.count(UploadSchedule.id)).where(
                and_(
                    UploadSchedule.is_published == True,
                    UploadSchedule.published_at >= day_start,
                    UploadSchedule.published_at <= day_end,
                )
            )
        )
        days.append({
            "day": day.strftime("%a"),   # Mon, Tue …
            "date": day.strftime("%m/%d"),
            "uploads": count_res.scalar() or 0,
        })
    return days


# ── Published Upload History ───────────────────────────────────────────────
@router.get("/published-history")
async def get_published_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Returns recent published uploads for the history table on Dashboard."""
    from app.models.models import SourceVideo

    result = await db.execute(
        select(UploadSchedule, Account, SourceVideo)
        .join(Account, UploadSchedule.account_id == Account.id, isouter=True)
        .join(SourceVideo, UploadSchedule.video_id == SourceVideo.id, isouter=True)
        .where(UploadSchedule.is_published == True)
        .order_by(UploadSchedule.published_at.desc())
        .limit(limit)
    )
    rows = result.all()
    response_list = []
    for row in rows:
        try:
            s = row[0]  # UploadSchedule
            a = row[1]  # Account
            v = row[2]  # SourceVideo
            
            # Ultra safe extraction
            title = "Unknown Video"
            if v:
                title = getattr(v, "ai_title", None) or getattr(v, "original_filename", None) or "Video"
                
            plat = "unknown"
            if a and hasattr(a, "platform"):
                plat = getattr(a.platform, "value", str(a.platform))
                
            response_list.append({
                "id": str(s.id),
                "video_title": str(title),
                "platform": str(plat),
                "channel_name": str(getattr(a, "channel_name", "—")) if a else "—",
                "published_at": s.published_at.isoformat() if hasattr(s, "published_at") and s.published_at else None,
                "published_url": str(getattr(s, "published_url", "") or ""),
                "add_watermark": bool(getattr(s, "add_watermark", False)),
                "view_count": int(getattr(s, "view_count", 0)),
                "like_count": int(getattr(s, "like_count", 0)),
                "comment_count": int(getattr(s, "comment_count", 0)),
            })
        except Exception as e:
            import logging
            logging.error(f"Error parsing published history row: {e}")
            continue
            
    return response_list


# ── System Health ──────────────────────────────────────────────────────────
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check for Redis, DB, and Celery."""
    import redis as redis_sync
    from app.core.config import settings

    health = {
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await db.execute(select(func.now()))
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"error: {str(e)[:100]}"

    try:
        r = redis_sync.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"error: {str(e)[:100]}"

    try:
        from app.worker import celery_app
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        health["celery"] = "healthy" if active is not None else "no_workers"
    except Exception as e:
        health["celery"] = f"error: {str(e)[:100]}"

    return health


@router.get("/preflight")
async def preflight_check(db: AsyncSession = Depends(get_db)):
    from app.core.config import settings
    from app.core.security import decrypt_token
    from app.models.models import AccountStatusEnum
    from app.services.token_service import get_valid_google_credentials, TokenRefreshError
    import httpx

    errors = []
    warnings = []

    if not settings.FERNET_KEY:
        errors.append("FERNET_KEY missing (token decrypt/encrypt will break after restart)")

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        errors.append("GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET missing (YouTube+Drive OAuth will fail)")

    if not settings.META_CLIENT_ID or not settings.META_CLIENT_SECRET:
        errors.append("META_CLIENT_ID/META_CLIENT_SECRET missing (Facebook/Instagram OAuth will fail)")

    yt_result = await db.execute(
        select(Account).where(
            Account.platform == PlatformEnum.YOUTUBE,
            Account.status == AccountStatusEnum.ACTIVE,
        )
    )
    yt_accounts = yt_result.scalars().all()

    fb_result = await db.execute(
        select(Account).where(
            Account.platform == PlatformEnum.FACEBOOK,
            Account.status == AccountStatusEnum.ACTIVE,
        )
    )
    fb_accounts = fb_result.scalars().all()

    ig_result = await db.execute(
        select(Account).where(
            Account.platform == PlatformEnum.INSTAGRAM,
            Account.status == AccountStatusEnum.ACTIVE,
        )
    )
    ig_accounts = ig_result.scalars().all()

    yt_with_refresh = 0
    for a in yt_accounts:
        refresh_token = decrypt_token(a.encrypted_refresh_token or "")
        if refresh_token:
            yt_with_refresh += 1
        else:
            warnings.append(f"YouTube account missing refresh_token: {a.channel_name}")

    fb_missing = 0
    for a in fb_accounts:
        token = decrypt_token(a.encrypted_access_token or "")
        if not token:
            fb_missing += 1
            errors.append(f"Facebook token missing/unreadable: {a.channel_name}")

    ig_missing = 0
    ig_needs_drive_folder = 0
    for a in ig_accounts:
        token = decrypt_token(a.encrypted_access_token or "")
        if not token:
            ig_missing += 1
            errors.append(f"Instagram token missing/unreadable: {a.channel_name}")
        if not a.drive_folder_link and not settings.GOOGLE_DRIVE_PUBLIC_FOLDER_ID:
            ig_needs_drive_folder += 1
            errors.append(
                f"Instagram requires Drive folder (set account.drive_folder_link or GOOGLE_DRIVE_PUBLIC_FOLDER_ID): {a.channel_name}"
            )

    if ig_accounts and yt_with_refresh == 0:
        errors.append("Instagram publishing requires at least one active YouTube account with refresh_token (Drive upload step)")

    if ig_accounts and yt_accounts:
        try:
            yt = yt_accounts[0]
            creds = await get_valid_google_credentials(yt, db)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"access_token": creds.token},
                )
            if r.status_code == 200:
                scope_str = (r.json().get("scope") or "")
                scopes = set(scope_str.split())
                if (
                    "https://www.googleapis.com/auth/drive.file" not in scopes
                    and "https://www.googleapis.com/auth/drive" not in scopes
                ):
                    errors.append(
                        "Google OAuth missing drive.file scope (Instagram needs Drive upload). Reconnect Google account."
                    )
            else:
                warnings.append("Could not verify Google token scopes (tokeninfo failed).")
        except TokenRefreshError as e:
            errors.append(f"Google token refresh failed (required for Instagram): {e}")
        except Exception:
            warnings.append("Could not verify Google token scopes.")

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        warnings.append("Telegram alerts not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing)")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "youtube_active": len(yt_accounts),
            "youtube_with_refresh": yt_with_refresh,
            "facebook_active": len(fb_accounts),
            "facebook_missing_token": fb_missing,
            "instagram_active": len(ig_accounts),
            "instagram_missing_token": ig_missing,
            "instagram_missing_drive_folder": ig_needs_drive_folder,
        },
    }


# ── Full System Report ─────────────────────────────────────────────────────
@router.get("/system-report")
async def get_system_report(db: AsyncSession = Depends(get_db)):
    """Deep system metrics for the System Health page and Telegram /report command."""
    import psutil
    import os
    from app.models.models import SystemLog, SourceVideo

    # 1. DB Stats
    total_accs = await db.execute(select(func.count(Account.id)))
    # Account platforms breakdown
    youtube_accs = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.YOUTUBE))
    facebook_accs = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.FACEBOOK))
    instagram_accs = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.INSTAGRAM))

    total_vids = await db.execute(select(func.count(SourceVideo.id)))
    
    # Upload Schedule breakdown
    total_schedules = await db.execute(select(func.count(UploadSchedule.id)))
    published_schedules = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.is_published == True))
    pending_schedules = await db.execute(select(func.count(UploadSchedule.id)).where(and_(UploadSchedule.is_published == False, UploadSchedule.error_message == None)))
    failed_schedules = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.error_message != None))
    
    # 2. API Keys breakdown
    active_google = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.is_locked == False, ApiKeyVault.service_name == "google")))
    locked_google = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.is_locked == True, ApiKeyVault.service_name == "google")))
    active_meta = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.is_locked == False, ApiKeyVault.service_name == "meta")))
    locked_meta = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.is_locked == True, ApiKeyVault.service_name == "meta")))
    
    # 3. Last Error Log
    last_error_log = await db.execute(select(SystemLog).where(SystemLog.level == "ERROR").order_by(SystemLog.created_at.desc()).limit(1))
    last_error = last_error_log.scalar_one_or_none()

    # 4. Host System Metrics
    cpu_usage = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "total_accounts": total_accs.scalar() or 0,
            "youtube_accounts": youtube_accs.scalar() or 0,
            "facebook_accounts": facebook_accs.scalar() or 0,
            "instagram_accounts": instagram_accs.scalar() or 0,
            "total_videos": total_vids.scalar() or 0,
            "total_schedules": total_schedules.scalar() or 0,
            "published_schedules": published_schedules.scalar() or 0,
            "pending_schedules": pending_schedules.scalar() or 0,
            "failed_schedules": failed_schedules.scalar() or 0,
        },
        "api_keys": {
            "google_active": active_google.scalar() or 0,
            "google_locked": locked_google.scalar() or 0,
            "meta_active": active_meta.scalar() or 0,
            "meta_locked": locked_meta.scalar() or 0,
        },
        "system_resources": {
            "cpu_percent": cpu_usage,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        },
        "last_error": last_error.message if last_error else "None",
        "last_error_time": last_error.created_at.isoformat() if last_error else None,
    }


# ── Telegram Config ────────────────────────────────────────────────────────
@router.get("/telegram-config")
async def get_telegram_config(db: AsyncSession = Depends(get_db)):
    """Get current Telegram configuration (tokens are masked for security)."""
    from app.core.config import settings

    # DB-stored values take priority over .env
    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    chat_id = await get_setting("TELEGRAM_CHAT_ID", db) or settings.TELEGRAM_CHAT_ID

    # Notification toggles
    notify_upload = await get_setting("NOTIFY_UPLOAD_SUCCESS", db, "true")
    notify_quota = await get_setting("NOTIFY_QUOTA_EXHAUSTED", db, "true")
    notify_token = await get_setting("NOTIFY_TOKEN_EXPIRED", db, "true")
    notify_fail = await get_setting("NOTIFY_TASK_FAILED", db, "true")

    # Mask token for display security
    masked_token = ""
    if bot_token:
        visible = bot_token[:8] if len(bot_token) > 8 else bot_token
        masked_token = visible + "••••••••••••••"

    return {
        "bot_token_configured": bool(bot_token),
        "bot_token_masked": masked_token,
        "chat_id": chat_id,
        "configured": bool(bot_token and chat_id),
        "notify_upload_success": notify_upload == "true",
        "notify_quota_exhausted": notify_quota == "true",
        "notify_token_expired": notify_token == "true",
        "notify_task_failed": notify_fail == "true",
    }


@router.post("/telegram-config")
async def save_telegram_config(config: dict, db: AsyncSession = Depends(get_db)):
    """Save Telegram Bot Token, Chat ID, and notification preferences to DB."""
    token_changed = False
    
    if "bot_token" in config and config["bot_token"] and "•" not in config["bot_token"]:
        token_str = config["bot_token"].strip()
        if ":" not in token_str:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid token format. A valid token must contain a colon (:) separating the Bot ID and the Secret Token (e.g. 123456789:ABCdef...). Please copy the FULL token from @BotFather.")
        
        await set_setting("TELEGRAM_BOT_TOKEN", token_str, db)
        token_changed = True

    if "chat_id" in config:
        await set_setting("TELEGRAM_CHAT_ID", str(config["chat_id"]), db)

    # Notification toggles
    for key in ["notify_upload_success", "notify_quota_exhausted", "notify_token_expired", "notify_task_failed"]:
        if key in config:
            db_key = key.upper()
            await set_setting(db_key, "true" if config[key] else "false", db)

    # If the token changed, orchestrate a restart of the background polling
    if token_changed:
        from app.services.telegram import start_telegram_polling
        import asyncio
        asyncio.create_task(start_telegram_polling(force_restart=True))

    return {"status": "ok", "message": "Telegram configuration saved successfully!"}


# ── AI Routing Config ──────────────────────────────────────────────────────
@router.get("/ai-routing")
async def get_ai_routing_config(db: AsyncSession = Depends(get_db)):
    """Get the current AI routing preferences."""
    metadata_provider = await get_setting("AI_PROVIDER_METADATA", db, "gemini")
    comments_provider = await get_setting("AI_PROVIDER_COMMENTS", db, "gemini")
    return {
        "metadata_provider": metadata_provider,
        "comments_provider": comments_provider,
    }

@router.post("/ai-routing")
async def save_ai_routing_config(config: dict, db: AsyncSession = Depends(get_db)):
    """Save the AI routing preferences."""
    if "metadata_provider" in config:
        await set_setting("AI_PROVIDER_METADATA", config["metadata_provider"], db)
    if "comments_provider" in config:
        await set_setting("AI_PROVIDER_COMMENTS", config["comments_provider"], db)
    return {"status": "ok", "message": "AI routing preferences saved successfully!"}


@router.post("/telegram-bot-info")
async def get_telegram_bot_info(db: AsyncSession = Depends(get_db)):
    """Fetch Telegram bot info (username, name) from the Bot API using the stored token."""
    import httpx
    from app.core.config import settings

    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        return {"ok": False, "error": "No Bot Token configured"}

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            data = resp.json()
            if data.get("ok"):
                bot = data["result"]
                return {
                    "ok": True,
                    "bot_name": bot.get("first_name"),
                    "username": f"@{bot.get('username')}",
                    "bot_id": bot.get("id"),
                }
            return {"ok": False, "error": data.get("description", "Invalid token")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/test-telegram")
async def test_telegram(payload: dict = {}, db: AsyncSession = Depends(get_db)):
    """Send a test message to the configured Telegram chat."""
    from app.services.telegram import send_telegram_alert
    from app.core.config import settings

    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    chat_id = await get_setting("TELEGRAM_CHAT_ID", db) or settings.TELEGRAM_CHAT_ID

    custom_msg = payload.get("message", "")
    message = custom_msg if custom_msg else (
        "✅ <b>AutoStream AI Infinity</b>\n"
        "🤖 Telegram integration is working correctly!\n"
        "📡 You will receive alerts for uploads, errors, and quota exhaustion here."
    )

    success = await send_telegram_alert(message, bot_token=bot_token, chat_id=chat_id)
    if success:
        return {"status": "ok", "message": "Test message sent to Telegram successfully!"}
    return {"status": "error", "message": "Failed to send. Check your Bot Token and Chat ID."}


@router.delete("/cleanup-published")
async def cleanup_published_schedules(days: int = 7, db: AsyncSession = Depends(get_db)):
    """Delete published schedules older than N days to keep the database tidy."""
    from sqlalchemy import delete
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        delete(UploadSchedule).where(
            and_(UploadSchedule.is_published == True, UploadSchedule.published_at <= cutoff)
        )
    )
    await db.commit()
    return {"deleted": result.rowcount, "cutoff_days": days}

@router.get("/db-test")
async def db_test(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    try:
        res1 = await db.execute(text("SELECT count(*) FROM upload_schedule;"))
        cnt = res1.scalar()
        res2 = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'upload_schedule' AND column_name = 'metadata_overrides';"))
        cols = res2.fetchall()
        return {"success": True, "count": cnt, "has_metadata_overrides": len(cols) > 0}
    except Exception as e:
        return {"success": False, "error": str(e)}
