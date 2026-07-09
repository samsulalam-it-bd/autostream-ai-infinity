from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import UploadSchedule, ApiKeyVault, Account, SystemSettings, PlatformEnum, SourceVideo, SystemLog
from app.schemas import DashboardStats, SystemReport

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
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's uploads
    uploads_today = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.is_published == True, UploadSchedule.published_at >= start_of_day)
        )
    )
    u_today = uploads_today.scalar() or 0

    # Active API Keys
    active_keys = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.is_locked == False)
    )
    
    # Pending Schedules
    pending = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.is_published == False, UploadSchedule.scheduled_time >= now)
        )
    )
    
    total_accounts = await db.execute(select(func.count(Account.id)))
    total_videos = await db.execute(select(func.count(SourceVideo.id)))
    
    # Engagement totals
    total_views = await db.execute(select(func.sum(UploadSchedule.view_count)).where(UploadSchedule.is_published == True))
    t_views = total_views.scalar() or 0
    
    total_likes = await db.execute(select(func.sum(UploadSchedule.like_count)).where(UploadSchedule.is_published == True))
    t_likes = total_likes.scalar() or 0
    
    total_comments = await db.execute(select(func.sum(UploadSchedule.comment_count)).where(UploadSchedule.is_published == True))
    t_comments = total_comments.scalar() or 0

    # Platform breakdown
    plat_counts = await db.execute(
        select(Account.platform, func.count(Account.id)).group_by(Account.platform)
    )
    acc_breakdown = {p.value: c for p, c in plat_counts.all()}
    active_plats = [p for p, c in acc_breakdown.items() if c > 0]

    # Trends (comparing today with yesterday)
    yesterday_start = start_of_day - timedelta(days=1)
    uploads_yesterday = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.is_published == True, 
                 UploadSchedule.published_at >= yesterday_start,
                 UploadSchedule.published_at < start_of_day)
        )
    )
    u_yesterday = uploads_yesterday.scalar() or 0
    trend_val = u_today - u_yesterday
    trend_str = f"+{trend_val}" if trend_val >= 0 else str(trend_val)

    # Next schedule
    next_s = await db.execute(
        select(UploadSchedule.scheduled_time).where(
            and_(UploadSchedule.is_published == False, UploadSchedule.scheduled_time >= now)
        ).order_by(UploadSchedule.scheduled_time.asc()).limit(1)
    )
    next_time = next_s.scalar()
    next_time_str = next_time.strftime("%I:%M %p") if next_time else "None"

    # API Keys breakdown
    api_counts = await db.execute(
        select(ApiKeyVault.service_name, func.count(ApiKeyVault.id)).where(ApiKeyVault.is_locked == False).group_by(ApiKeyVault.service_name)
    )
    api_break = {s: c for s, c in api_counts.all()}

    # Recent Alerts
    recent_logs = await db.execute(
        select(SystemLog).where(SystemLog.level.in_(["ERROR", "WARNING"])).order_by(SystemLog.created_at.desc()).limit(2)
    )
    alerts = []
    for l in recent_logs.scalars().all():
        alerts.append({
            "message": l.message,
            "type": l.level.lower(),
            "time": l.created_at.isoformat()
        })

    return DashboardStats(
        total_uploads_today=u_today,
        active_api_keys=active_keys.scalar() or 0,
        pending_schedules=pending.scalar() or 0,
        total_accounts=total_accounts.scalar() or 0,
        total_videos=total_videos.scalar() or 0,
        total_views=t_views,
        total_likes=t_likes,
        total_comments=t_comments,
        active_platforms=active_plats,
        daily_trend=trend_str,
        api_breakdown=api_break,
        next_schedule_time=next_time_str,
        account_breakdown=acc_breakdown,
        recent_alerts=alerts
    )


# ── Upload Chart Data (Last 7 Days) ────────────────────────────────────────
@router.get("/upload-chart")
async def get_upload_chart(db: AsyncSession = Depends(get_db)):
    """Returns daily upload counts for the last 7 days for the Dashboard chart."""
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
                    UploadSchedule.published_at <= day_end
                )
            )
        )
        days.append({
            "date": day_start.isoformat(),
            "day": day.strftime("%a"),
            "uploads": count_res.scalar() or 0
        })
    return days


async def health_check(db: AsyncSession) -> dict:
    """Helper to perform health check on DB, Redis, and Celery."""
    status = {"database": "healthy", "redis": "healthy", "celery": "healthy"}
    
    # 1. Test Database
    try:
        await db.execute(select(1))
    except Exception as e:
        status["database"] = f"unhealthy: {str(e)[:100]}"
        
    # 2. Test Redis
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, socket_timeout=3)
        r.ping()
    except Exception as e:
        status["redis"] = f"unhealthy: {str(e)[:100]}"
        
    # 3. Test Celery (via Redis or broker check)
    try:
        from celery import Celery
        from app.core.config import settings
        celery_app = Celery("autostream", broker=settings.REDIS_URL)
        inspect = celery_app.control.inspect(timeout=1.0)
        active = inspect.active()
        if not active:
            status["celery"] = "unhealthy: No active workers"
    except Exception as e:
        status["celery"] = f"unhealthy: {str(e)[:100]}"
        
    return status


# ── Full System Report ─────────────────────────────────────────────────────
@router.get("/system-report", response_model=SystemReport)
async def get_system_report(db: AsyncSession = Depends(get_db)):
    """Deep system metrics for the System Health page."""
    import psutil

    # 1. DB Stats
    t_acc = await db.execute(select(func.count(Account.id)))
    yt_acc = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.YOUTUBE))
    fb_acc = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.FACEBOOK))
    ig_acc = await db.execute(select(func.count(Account.id)).where(Account.platform == PlatformEnum.INSTAGRAM))
    t_vid = await db.execute(select(func.count(SourceVideo.id)))
    tot_sch = await db.execute(select(func.count(UploadSchedule.id)))
    pub_sch = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.is_published == True))
    pend_sch = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.is_published == False))
    fail_sch = await db.execute(select(func.count(UploadSchedule.id)).where(UploadSchedule.error_message != None))

    # 2. API Keys breakdown
    g_act = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.service_name == "google", ApiKeyVault.is_locked == False)))
    g_loc = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.service_name == "google", ApiKeyVault.is_locked == True)))
    m_act = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.service_name == "meta", ApiKeyVault.is_locked == False)))
    m_loc = await db.execute(select(func.count(ApiKeyVault.id)).where(and_(ApiKeyVault.service_name == "meta", ApiKeyVault.is_locked == True)))

    # 3. System Resources
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # 4. Last Error
    last_err_res = await db.execute(select(SystemLog).where(SystemLog.level == "ERROR").order_by(SystemLog.created_at.desc()).limit(1))
    last_err = last_err_res.scalar_one_or_none()

    return SystemReport(
        timestamp=datetime.now(timezone.utc),
        database={
            "total_accounts": t_acc.scalar() or 0,
            "youtube_accounts": yt_acc.scalar() or 0,
            "facebook_accounts": fb_acc.scalar() or 0,
            "instagram_accounts": ig_acc.scalar() or 0,
            "total_videos": t_vid.scalar() or 0,
            "total_schedules": tot_sch.scalar() or 0,
            "published_schedules": pub_sch.scalar() or 0,
            "pending_schedules": pend_sch.scalar() or 0,
            "failed_schedules": fail_sch.scalar() or 0,
        },
        api_keys={
            "google_active": g_act.scalar() or 0,
            "google_locked": g_loc.scalar() or 0,
            "meta_active": m_act.scalar() or 0,
            "meta_locked": m_loc.scalar() or 0,
        },
        system_resources={
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_gb": round(mem.used / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        },
        last_error=last_err.message if last_err else "None",
        last_error_time=last_err.created_at if last_err else None
    )


# ── Published Upload History ───────────────────────────────────────────────
@router.get("/published-history")
async def get_published_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Returns recent published uploads for the history table on Dashboard."""
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
                "published_at": s.published_at.isoformat() if s.published_at else None,
                "published_url": str(s.published_url or ""),
                "view_count": int(s.view_count or 0),
                "like_count": int(s.like_count or 0),
                "comment_count": int(s.comment_count or 0),
                "media_type": str(v.media_type.value) if (v and hasattr(v, "media_type") and v.media_type) else "VIDEO",
            })
        except Exception:
            continue
            
    return response_list


# ── Telegram Config ────────────────────────────────────────────────────────
@router.get("/telegram-config")
async def get_telegram_config(db: AsyncSession = Depends(get_db)):
    from app.core.config import settings
    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    chat_id = await get_setting("TELEGRAM_CHAT_ID", db) or settings.TELEGRAM_CHAT_ID
    
    notify_upload = await get_setting("NOTIFY_UPLOAD_SUCCESS", db, "true")
    notify_quota = await get_setting("NOTIFY_QUOTA_EXHAUSTED", db, "true")
    notify_token = await get_setting("NOTIFY_TOKEN_EXPIRED", db, "true")
    notify_fail = await get_setting("NOTIFY_TASK_FAILED", db, "true")

    masked_token = (bot_token[:8] + "••••••••") if bot_token else ""

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
    if "bot_token" in config and config["bot_token"] and "•" not in config["bot_token"]:
        await set_setting("TELEGRAM_BOT_TOKEN", config["bot_token"].strip(), db)
    if "chat_id" in config:
        await set_setting("TELEGRAM_CHAT_ID", str(config["chat_id"]), db)
    for key in ["notify_upload_success", "notify_quota_exhausted", "notify_token_expired", "notify_task_failed"]:
        if key in config:
            await set_setting(key.upper(), "true" if config[key] else "false", db)
    return {"status": "ok"}


@router.post("/telegram-bot-info")
async def get_telegram_bot_info(db: AsyncSession = Depends(get_db)):
    import httpx
    from app.core.config import settings
    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    if not bot_token: return {"ok": False}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            data = resp.json()
            if data.get("ok"):
                b = data["result"]
                return {"ok": True, "bot_name": b.get("first_name"), "username": f"@{b.get('username')}"}
            return {"ok": False}
    except Exception: return {"ok": False}


@router.post("/test-telegram")
async def test_telegram(payload: dict = {}, db: AsyncSession = Depends(get_db)):
    from app.services.telegram import send_telegram_alert
    from app.core.config import settings
    bot_token = await get_setting("TELEGRAM_BOT_TOKEN", db) or settings.TELEGRAM_BOT_TOKEN
    chat_id = await get_setting("TELEGRAM_CHAT_ID", db) or settings.TELEGRAM_CHAT_ID
    msg = payload.get("message", "Test from AutoStream AI Infinity ∞")
    success = await send_telegram_alert(msg, bot_token=bot_token, chat_id=chat_id)
    return {"status": "ok" if success else "error"}


@router.delete("/cleanup-published")
async def cleanup_published_schedules(days: int = 7, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(delete(UploadSchedule).where(and_(UploadSchedule.is_published == True, UploadSchedule.published_at <= cutoff)))
    await db.commit()
    return {"deleted": result.rowcount}
