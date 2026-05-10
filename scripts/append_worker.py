path = r"f:\autostream-ai\backend\app\worker.py"
with open(path, 'a', encoding='utf-8') as f:
    f.write("""

# ── Task: Update Video Analytics ──────────────────────────────────────────
@celery_app.task(name="app.worker.update_video_analytics")
def update_video_analytics():
    \"\"\"Periodically fetch and update stats for all published videos from the last 30 days.\"\"\"
    async def _update():
        from app.database import AsyncSessionLocal
        from app.models.models import UploadSchedule, Account, PlatformEnum
        from app.services.uploader import get_youtube_stats, get_facebook_stats, get_instagram_stats
        from app.services.token_service import get_valid_google_credentials, decrypt_token
        from sqlalchemy import select, and_
        
        logger.info("[Analytics] Starting periodic update...")
        async with AsyncSessionLocal() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            res = await db.execute(
                select(UploadSchedule, Account)
                .join(Account, UploadSchedule.account_id == Account.id)
                .where(and_(UploadSchedule.is_published == True, UploadSchedule.published_at >= cutoff))
            )
            rows = res.all()
            
            for schedule, account in rows:
                if not schedule.platform_video_id: continue
                
                stats = {}
                try:
                    if account.platform == PlatformEnum.YOUTUBE:
                        creds = await get_valid_google_credentials(account, db)
                        stats = await get_youtube_stats(schedule.platform_video_id, creds.token)
                    elif account.platform == PlatformEnum.FACEBOOK:
                        token = decrypt_token(account.encrypted_access_token)
                        stats = await get_facebook_stats(schedule.platform_video_id, token)
                    elif account.platform == PlatformEnum.INSTAGRAM:
                        token = decrypt_token(account.encrypted_access_token)
                        stats = await get_instagram_stats(schedule.platform_video_id, token)
                except Exception as e:
                    logger.warning(f"[Analytics] Failed to fetch stats for {schedule.id}: {e}")
                    continue
                
                if stats:
                    schedule.view_count = stats.get("view_count", schedule.view_count)
                    schedule.like_count = stats.get("like_count", schedule.like_count)
                    schedule.comment_count = stats.get("comment_count", schedule.comment_count)
            
            await db.commit()
            logger.info(f"[Analytics] Update complete. Processed {len(rows)} videos.")

    run_async(_update())


# ── Celery Beat Schedule ───────────────────────────────────────────────────
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    "sync-drive-folders-every-hour": {
        "task": "app.worker.sync_all_accounts_drive",
        "schedule": crontab(minute=0), # Every hour
    },
    "update-video-analytics-every-3-hours": {
        "task": "app.worker.update_video_analytics",
        "schedule": crontab(minute=0, hour=\"*/3\"), # Every 3 hours
    },
}
""")
print("worker.py tail updated.")
