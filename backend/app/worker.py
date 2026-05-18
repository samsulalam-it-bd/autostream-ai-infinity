import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Celery App ──────────────────────────────────────────────────────────────
celery_app = Celery(
    "autostream",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.worker.process_and_upload_video": {"queue": "video_pipeline"},
        "app.worker.sync_drive_folder": {"queue": "default"},
        "app.worker.check_pending_schedules": {"queue": "default"},
        "app.worker.reset_daily_api_usage": {"queue": "default"},
        "app.worker.poll_youtube_comments": {"queue": "default"},
        "app.worker.proactive_token_refresh": {"queue": "default"},
    },
    task_queues=(
        Queue("video_pipeline"),
        Queue("default"),
    ),
    beat_schedule={
        # Check for upcoming schedules every 5 minutes
        "check-pending-schedules": {
            "task": "app.worker.check_pending_schedules",
            "schedule": 300,  # every 5 minutes
        },
        # Reset daily API usage counters at midnight UTC
        "reset-daily-api-usage": {
            "task": "app.worker.reset_daily_api_usage",
            "schedule": crontab(hour=0, minute=0),
        },
        # Poll YouTube for new comments every 5 minutes
        "poll-youtube-comments": {
            "task": "app.worker.poll_youtube_comments",
            "schedule": 300,  # every 5 minutes
        },
        # Proactively refresh YouTube tokens expiring within 10 minutes (every 30 min)
        "proactive-token-refresh": {
            "task": "app.worker.proactive_token_refresh",
            "schedule": 1800,  # every 30 minutes
        },
    },
    redbeat_redis_url=settings.CELERY_BROKER_URL,
)


# ── Helper: Run async functions in Celery sync tasks ───────────────────────
_celery_async_loop = None


def run_async(coro):
    """Run an async coroutine in a Celery synchronous task context."""
    global _celery_async_loop
    if _celery_async_loop is None or _celery_async_loop.is_closed():
        _celery_async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_celery_async_loop)
    return _celery_async_loop.run_until_complete(coro)


async def _get_toggle(db, key: str, default: bool = True) -> bool:
    """Read a boolean toggle from SystemSettings using provided db session."""
    from sqlalchemy import select
    from app.models.models import SystemSettings
    row_result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    row = row_result.scalar_one_or_none()
    if row is None:
        return default
    return row.value == "true"


# ── Task: Check Pending Schedules ──────────────────────────────────────────
@celery_app.task(name="app.worker.check_pending_schedules", bind=True)
def check_pending_schedules(self):
    """
    Beat scheduler task. Runs every 5 minutes.
    Finds all scheduled uploads within the next 35 minutes (to account for
    the 30-minute JIT trigger window) and enqueues process_and_upload_video.
    """
    async def _check():
        from sqlalchemy import select, and_
        from app.database import AsyncSessionLocal
        from app.models.models import UploadSchedule, VideoStatusEnum

        logger.info("Checking pending schedules...")
        now = datetime.now(timezone.utc)
        trigger_window = now + timedelta(minutes=35)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UploadSchedule).where(
                    and_(
                        UploadSchedule.is_published == False,
                        UploadSchedule.scheduled_time <= trigger_window,
                        UploadSchedule.scheduled_time >= now,
                        UploadSchedule.celery_task_id == None,
                    )
                )
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                if schedule.target_group_id:
                    # Group schedule: fan out to all accounts in the group
                    task = fan_out_group_schedule.apply_async(
                        args=[str(schedule.id)],
                        eta=schedule.scheduled_time - timedelta(minutes=30),
                        queue="default",
                    )
                    schedule.celery_task_id = f"fanout_pending:{task.id}"
                    logger.info(f"Fan-out task {task.id} for group schedule {schedule.id}")
                else:
                    # Single account schedule: dispatch JIT pipeline directly
                    task = process_and_upload_video.apply_async(
                        args=[str(schedule.id)],
                        eta=schedule.scheduled_time - timedelta(minutes=30),
                        queue="video_pipeline",
                    )
                    schedule.celery_task_id = task.id
                    logger.info(f"Pipeline task {task.id} for schedule {schedule.id}")

            if schedules:
                await db.commit()
            logger.info(f"Dispatched {len(schedules)} upload tasks.")

    run_async(_check())


# ── Task: Group Fan-Out Scheduler ─────────────────────────────────────────
@celery_app.task(name="app.worker.fan_out_group_schedule", bind=True, queue="default")
def fan_out_group_schedule(self, schedule_id: str):
    """
    For a schedule targeting a channel group, create individual pipeline
    tasks for EACH active account in the group (fan-out pattern).
    """
    async def _fan_out():
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.models import UploadSchedule, Account, AccountStatusEnum

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UploadSchedule).where(UploadSchedule.id == schedule_id)
            )
            schedule = result.scalar_one_or_none()
            if not schedule or not schedule.target_group_id:
                return

            # Get all active accounts in the group
            acc_result = await db.execute(
                select(Account).where(
                    Account.group_id == schedule.target_group_id,
                    Account.status == AccountStatusEnum.ACTIVE,
                )
            )
            accounts = acc_result.scalars().all()
            if not accounts:
                logger.warning(f"No active accounts in group for schedule {schedule_id}")
                return

            dispatched = 0
            for account in accounts:
                # Create a per-account schedule entry cloned from the group schedule
                from app.models.models import UploadSchedule as Sched
                per_account = Sched(
                    video_id=schedule.video_id,
                    account_id=account.id,
                    target_group_id=None,
                    scheduled_time=schedule.scheduled_time,
                    add_watermark=schedule.add_watermark,
                    auto_comment=schedule.auto_comment,
                )
                db.add(per_account)
                await db.flush()  # Get the ID

                task = process_and_upload_video.apply_async(
                    args=[str(per_account.id)],
                    queue="video_pipeline",
                )
                per_account.celery_task_id = task.id
                dispatched += 1

            # Mark original group-level schedule as handled
            schedule.celery_task_id = f"fan_out:{dispatched}_accounts"
            await db.commit()
            logger.info(f"Fan-out: dispatched {dispatched} tasks for group schedule {schedule_id}")

    run_async(_fan_out())


# ── Task: Reset Daily API Usage ────────────────────────────────────────────
@celery_app.task(name="app.worker.reset_daily_api_usage", bind=True)
def reset_daily_api_usage(self):
    """Resets daily_usage counter on all API keys at midnight UTC."""
    async def _reset():
        from sqlalchemy import update
        from app.database import AsyncSessionLocal
        from app.models.models import ApiKeyVault

        async with AsyncSessionLocal() as db:
            await db.execute(update(ApiKeyVault).values(daily_usage=0))
            await db.commit()
            logger.info("Reset daily API usage counters.")

    run_async(_reset())


# ── Main Task: Just-In-Time Video Pipeline ─────────────────────────────────
@celery_app.task(
    name="app.worker.process_and_upload_video",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=3600,
    autoretry_for=(Exception,),
    queue="video_pipeline",
)
def process_and_upload_video(self, schedule_id: str):
    """
    Just-In-Time Video Processing Pipeline.

    Triggered 30 minutes before the scheduled upload time.
    Steps:
      1. Load schedule + video + account data from DB
      2. Download video from Google Drive to /tmp/videos
      3. Run FFmpeg Uniquifier (strip metadata, crop 1px, brightness +0.01, watermark)
      4. Extract 3 frames → Gemini AI analysis → viral metadata
      5. Upload processed video to the target platform (YT/FB/Instagram)
      6. Mark schedule as published + send Telegram success alert
      7. Clean up all temporary files
    """
    async def _pipeline():
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.models import UploadSchedule, Account, SourceVideo, AccountStatusEnum, VideoStatusEnum, MediaTypeEnum
        from app.services.ffmpeg import process_video, extract_frames, cleanup_tmp_files
        from app.services.gemini import analyze_video_with_gemini
        from app.services.uploader import (
            download_drive_video,
            upload_to_youtube,
            upload_to_facebook,
            upload_photo_to_facebook,
            upload_to_instagram,
            delete_drive_file,
        )
        from app.services.telegram import (
            alert_upload_success,
            alert_token_expired,
            alert_task_failed,
        )
        from app.core.security import decrypt_token
        from app.models.models import PlatformEnum

        tmp_files_to_cleanup = []

        try:
            async with AsyncSessionLocal() as db:

                # ── Step 1: Load schedule ──────────────────────────────────────
                result = await db.execute(
                    select(UploadSchedule).where(UploadSchedule.id == schedule_id)
                )
                schedule = result.scalar_one_or_none()

                if not schedule:
                    logger.error(f"Schedule {schedule_id} not found.")
                    return

                if schedule.is_published:
                    logger.info(f"Schedule {schedule_id} already published. Skipping.")
                    return

                # Load video
                video_result = await db.execute(
                    select(SourceVideo).where(SourceVideo.id == schedule.video_id)
                )
                video = video_result.scalar_one_or_none()

                if not video:
                    logger.error(f"Video not found for schedule {schedule_id}")
                    return

                logger.info(f"[Pipeline] Starting: {video.original_filename or video.drive_file_id}")

                # ── Load account ───────────────────────────────────────────────
                account = None
                if schedule.account_id:
                    acc_result = await db.execute(
                        select(Account).where(Account.id == schedule.account_id)
                    )
                    account = acc_result.scalar_one_or_none()

                if not account and schedule.target_group_id:
                    # Pick first active account from the group
                    from app.models.models import ChannelGroup
                    acc_result = await db.execute(
                        select(Account).where(
                            Account.group_id == schedule.target_group_id,
                            Account.status == AccountStatusEnum.ACTIVE,
                        ).limit(1)
                    )
                    account = acc_result.scalar_one_or_none()

                if not account:
                    raise RuntimeError(f"No active account found for schedule {schedule_id}")

                # ── Token: refresh if empty or expiring within 5 min ───────────
                from app.services.token_service import get_valid_google_credentials, TokenRefreshError
                from app.core.security import decrypt_token

                access_token = decrypt_token(account.encrypted_access_token)

                google_credentials = None
                drive_access_token = access_token
                if account.platform == PlatformEnum.YOUTUBE:
                    try:
                        google_credentials = await get_valid_google_credentials(account, db)
                        access_token = google_credentials.token
                        drive_access_token = access_token
                    except TokenRefreshError as e:
                        if await _get_toggle(db, "NOTIFY_TOKEN_EXPIRED"):
                            await alert_token_expired(account.channel_name, account.platform.value)
                        raise RuntimeError(f"Token refresh failed for '{account.channel_name}': {e}") from e
                else:
                    yt_result = await db.execute(
                        select(Account).where(
                            Account.platform == PlatformEnum.YOUTUBE,
                            Account.status == AccountStatusEnum.ACTIVE,
                        ).limit(1)
                    )
                    yt_account = yt_result.scalar_one_or_none()
                    if not yt_account:
                        raise RuntimeError("No active YouTube account available for Google Drive download step.")
                    try:
                        drive_access_token = (await get_valid_google_credentials(yt_account, db)).token
                    except TokenRefreshError:
                        from app.core.security import decrypt_token
                        drive_access_token = decrypt_token(yt_account.encrypted_access_token or "") or ""

                if not access_token:
                    if await _get_toggle(db, "NOTIFY_TOKEN_EXPIRED"):
                        await alert_token_expired(account.channel_name, account.platform.value)
                    raise RuntimeError(f"Token expired/refresh failed for account '{account.channel_name}'")
                if not drive_access_token:
                    raise RuntimeError("Google Drive access token missing. Re-authenticate the YouTube/Google account.")

                # ── Step 2: Download from Drive ────────────────────────────────
                logger.info(f"[Pipeline] Downloading from Drive: {video.drive_file_id}")
                base_name = os.path.basename(video.original_filename or f"{video.drive_file_id}.mp4")
                unique_name = f"{schedule_id}_{base_name}"
                raw_video_path = await download_drive_video(
                    file_id=video.drive_file_id,
                    access_token=drive_access_token,
                    filename=unique_name,
                )
                tmp_files_to_cleanup.append(raw_video_path)

                # ── Step 3: FFmpeg Uniquifier (Videos only) ────────────────────
                overrides = schedule.metadata_overrides or {}
                wm_pos = overrides.get("watermark_position", "bottom-right")

                if video.media_type == MediaTypeEnum.IMAGE:
                    logger.info("[Pipeline] Media is an Image. Skipping FFmpeg processing.")
                    processed_path = raw_video_path
                else:
                    logger.info("[Pipeline] Processing video with FFmpeg...")
                    processed_path = process_video(
                        input_path=raw_video_path,
                        add_watermark=schedule.add_watermark,
                        settings={'position': wm_pos}
                    )
                    tmp_files_to_cleanup.append(processed_path)

                ai_mode = overrides.get("ai_mode", True)
                if video.ai_title and video.ai_description:
                    logger.info("[Pipeline] Custom metadata (from .txt) found. Skipping AI analysis.")
                    title = video.ai_title
                    description = video.ai_description
                    tags = video.ai_tags or []
                    hashtags = video.ai_hashtags or []
                elif not ai_mode:
                    logger.info("[Pipeline] AI Mode is DISABLED in Master Setup. Using filename as title.")
                    title = video.original_filename or "New Video"
                    description = f"Check out this new video from {account.channel_name}!"
                    tags = []
                    hashtags = [f"#{account.platform.value}"]
                else:

                    # ── Step 4: Gemini / AI Analysis ───────────────────────────────
                    if video.media_type == MediaTypeEnum.IMAGE:
                        logger.info("[Pipeline] Media is an Image. Using original path for AI analysis.")
                        frame_paths = [processed_path]
                    else:
                        logger.info("[Pipeline] Extracting frames for AI analysis...")
                        frame_paths = extract_frames(processed_path, num_frames=3)
                        tmp_files_to_cleanup.extend(frame_paths)

                    # Get AI Provider and Key
                    from app.models.models import SystemSettings, ApiKeyVault
                    pref_row = await db.execute(select(SystemSettings).where(SystemSettings.key == "AI_PROVIDER_METADATA"))
                    pref = pref_row.scalar_one_or_none()
                    provider = pref.value if pref else "gemini"

                    api_key = None
                    if provider != "gemini":
                        key_row = await db.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == provider))
                        key_obj = key_row.scalar_one_or_none()
                        if key_obj:
                            api_key = key_obj.credentials_json.get("api_key")

                    ai_metadata = await analyze_video_with_gemini(
                        frame_paths, 
                        platform=account.platform.value,
                        provider=provider, 
                        api_key=api_key
                    )


                    title       = video.ai_title or ai_metadata["title"]
                    description = video.ai_description or ai_metadata["description"]
                    tags        = video.ai_tags or ai_metadata["tags"]
                    hashtags    = video.ai_hashtags or ai_metadata["hashtags"]

                    # Save AI metadata to DB
                    video.ai_title = title
                    video.ai_description = description
                    video.ai_tags = tags
                    video.ai_hashtags = hashtags
                    await db.commit()

                full_description = f"{description}\n\n{' '.join(hashtags)}"

                # ── Step 4.5: Send Telegram Preview (Notification Only) ──────────
                from app.services.telegram import send_telegram_alert
                preview_msg = (
                    f"👀 <b>Incoming Upload Preview</b>\n"
                    f"📺 Platform: {account.platform.value.upper()}\n"
                    f"📢 Channel: {account.channel_name}\n"
                    f"🎬 Title: {title}\n"
                    f"📝 Description: {description[:150]}...\n"
                    f"🏷️ Hashtags: {' '.join(hashtags)}\n"
                    f"⏳ <i>Uploading now... (Retry attempt: {self.request.retries})</i>"
                )
                await send_telegram_alert(preview_msg)

                # ── Step 5: Upload to platform ─────────────────────────────────
                logger.info(f"[Pipeline] Uploading to {account.platform.value}...")

                upload_result = {}

                if account.platform == PlatformEnum.YOUTUBE:
                    upload_result = await upload_to_youtube(
                        video_path=processed_path,
                        title=title,
                        description=full_description,
                        tags=tags,
                        access_token=access_token,
                        credentials=google_credentials,  # Full creds for auto-refresh during upload
                    )
                elif account.platform == PlatformEnum.FACEBOOK:
                    if video.media_type == MediaTypeEnum.IMAGE:
                        upload_result = await upload_photo_to_facebook(
                            image_path=processed_path,
                            caption=full_description,
                            access_token=access_token,
                            page_id=account.channel_id or "",
                            account_id=str(account.id),
                        )
                    else:
                        upload_result = await upload_to_facebook(
                            video_path=processed_path,
                            title=title,
                            description=full_description,
                            access_token=access_token,
                            page_id=account.channel_id or "",
                        )
                elif account.platform == PlatformEnum.INSTAGRAM:
                    # Instagram requires a public URL via Google Drive.
                    google_acc_result = await db.execute(
                        select(Account).where(
                            Account.platform == PlatformEnum.YOUTUBE,
                            Account.status == AccountStatusEnum.ACTIVE
                        ).limit(1)
                    )
                    google_account = google_acc_result.scalar_one_or_none()
                    if not google_account:
                        raise RuntimeError("No active YouTube/Google account found for Drive upload step.")

                    try:
                        google_creds = await get_valid_google_credentials(google_account, db)
                        google_access_token = google_creds.token
                    except TokenRefreshError as e:
                        raise RuntimeError(f"Failed to refresh Google token for Drive upload step: {e}") from e

                    caption = f"{title}\n\n{full_description}"
                    
                    from app.services.uploader import extract_folder_id_from_link
                    from app.core.config import settings
                    ig_folder_id = None
                    if account.drive_folder_link:
                        ig_folder_id = extract_folder_id_from_link(account.drive_folder_link)
                    if not ig_folder_id:
                        ig_folder_id = "" # Fixed by AI

                    upload_result = await upload_to_instagram(
                        video_path=processed_path,
                        caption=caption,
                        access_token=access_token,
                        ig_user_id=account.channel_id or "",
                        google_access_token=google_access_token,
                        target_folder_id=ig_folder_id,
                    )
                # ── Step 6: Mark as published ──────────────────────────────────
                published_url = upload_result.get("url", "")
                platform_vid_id = upload_result.get("video_id") or upload_result.get("media_id")
                
                schedule.is_published = True
                schedule.published_at = datetime.now(timezone.utc)
                schedule.published_url = published_url
                schedule.platform_video_id = str(platform_vid_id) if platform_vid_id else None
                schedule.error_message = None
                video.status = VideoStatusEnum.UPLOADED
                await db.commit()

                # ── Auto-comment (Facebook & Instagram) ──────────────────────────
                if account.auto_comment and account.auto_comment_text and platform_vid_id:
                    try:
                        import httpx
                        comment_text = account.auto_comment_text
                        
                        if account.platform == PlatformEnum.FACEBOOK:
                            comment_url = f"https://graph.facebook.com/v20.0/{platform_vid_id}/comments"
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                resp = await client.post(
                                    comment_url,
                                    data={
                                        "access_token": access_token,
                                        "message": comment_text,
                                    }
                                )
                                resp.raise_for_status()
                            logger.info(f"[Pipeline] Facebook Auto-comment posted successfully under post {platform_vid_id}")
                            
                        elif account.platform == PlatformEnum.INSTAGRAM:
                            comment_url = f"https://graph.facebook.com/v20.0/{platform_vid_id}/comments"
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                resp = await client.post(
                                    comment_url,
                                    data={
                                        "access_token": access_token,
                                        "message": comment_text,
                                    }
                                )
                                resp.raise_for_status()
                            logger.info(f"[Pipeline] Instagram Auto-comment posted successfully under Reel/Media {platform_vid_id}")
                    except Exception as e:
                        logger.warning(f"[Pipeline] Facebook/Instagram Auto-comment failed (non-critical): {e}")

                logger.info(f"[Pipeline] Upload complete: {published_url}")

                # ── Optional: Delete source file from Google Drive ─────────────
                from app.core.config import settings
                should_delete = overrides.get("delete_from_drive", settings.DELETE_SOURCE_DRIVE_FILE_AFTER_PUBLISH)
                
                if should_delete:
                    try:
                        # Uses the Drive token used for download step.
                        await delete_drive_file(video.drive_file_id, drive_access_token)
                        logger.info(f"[Pipeline] Source Drive file deleted: {video.drive_file_id}")
                    except Exception as e:
                        # Non-fatal: upload is already done.
                        logger.warning(f"[Pipeline] Drive source delete failed (non-fatal): {e}")

                # ── Auto-comment (YouTube) ──────────────────────────────────────
                if account.auto_comment and account.auto_comment_text and account.platform == PlatformEnum.YOUTUBE and published_url:
                    try:
                        import httpx, re
                        match = re.search(r'[?&]v=([\w-]+)', published_url)
                        if match:
                            video_yt_id = match.group(1)
                            comment_text = account.auto_comment_text
                            async with httpx.AsyncClient(timeout=15.0) as client:
                                r = await client.post(
                                    "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
                                    headers={"Authorization": f"Bearer {access_token}"},
                                    json={
                                        "snippet": {
                                            "videoId": video_yt_id,
                                            "topLevelComment": {
                                                "snippet": {"textOriginal": comment_text}
                                            },
                                        }
                                    },
                                )
                                r.raise_for_status()
                                comment_data = r.json()
                                comment_id = comment_data.get("id")
                                if comment_id:
                                    await client.post(
                                        f"https://www.googleapis.com/youtube/v3/comments/pin?id={comment_id}",
                                        headers={"Authorization": f"Bearer {access_token}"}
                                    )
                                    logger.info(f"[Pipeline] YouTube Auto-comment posted and PINNED successfully: {comment_id}")
                                else:
                                    logger.info(f"[Pipeline] YouTube Auto-comment posted successfully: {video_yt_id}")
                    except Exception as e:
                        logger.warning(f"[Pipeline] YouTube Auto-comment failed (non-critical): {e}")

                # Send Telegram success alert (if toggle enabled)
                if await _get_toggle(db, "NOTIFY_UPLOAD_SUCCESS"):
                    await alert_upload_success(
                        video_title=title,
                        platform=account.platform.value,
                        channel_name=account.channel_name,
                        url=published_url,
                    )

                # ── Step 7: Cleanup tmp files (in finally block below) ──────────

        except Exception as exc:
            import traceback as _tb
            err_detail = f"{type(exc).__name__}: {exc}\n{_tb.format_exc()}"
            logger.exception(f"Pipeline failed for schedule {schedule_id}: {exc}")
            # Store error in schedule record so it's readable via API
            try:
                from app.database import AsyncSessionLocal
                from sqlalchemy import select as _sel
                async with AsyncSessionLocal() as _db:
                    _res = await _db.execute(_sel(UploadSchedule).where(UploadSchedule.id == schedule_id))
                    _sched = _res.scalar_one_or_none()
                    if _sched:
                        _sched.error_message = err_detail[:2000]
                        await _db.commit()
            except Exception:
                pass
            raise exc
        finally:
            cleanup_tmp_files(*tmp_files_to_cleanup)
            logger.info("[Pipeline] Done. Temp files cleaned up.")

    try:
        run_async(_pipeline())
    except Exception as exc:
        raise self.retry(exc=exc)


# ── Task: Sync Drive Folder ────────────────────────────────────────────────
@celery_app.task(name="app.worker.sync_drive_folder", bind=True, queue="default")
def sync_drive_folder(self, folder_link: str, account_id: str):
    """
    Sync all videos from a Google Drive folder link into source_videos table.
    Creates SourceVideo records for each video found (skips duplicates).
    """
    async def _sync():
        from sqlalchemy import select, and_, func
        from app.database import AsyncSessionLocal
        from app.models.models import Account, SourceVideo, VideoStatusEnum, MediaTypeEnum, UploadSchedule, PlatformEnum, AccountStatusEnum
        from app.services.uploader import (
            list_drive_folder_videos,
            extract_folder_id_from_link,
            read_drive_file_text,
        )
        from app.services.token_service import get_valid_google_credentials, TokenRefreshError

        folder_id = extract_folder_id_from_link(folder_link)
        if not folder_id:
            logger.error(f"[DriveSync] Could not extract folder ID from: {folder_link}")
            return {"error": "Invalid Drive folder link", "synced": 0}

        logger.info(f"[DriveSync] Starting sync | Folder ID: {folder_id} | Account: {account_id}")

        async with AsyncSessionLocal() as db:
            acc_result = await db.execute(select(Account).where(Account.id == account_id))
            target_account = acc_result.scalar_one_or_none()
            if not target_account:
                logger.error(f"[DriveSync] Account {account_id} not found in DB")
                return {"error": "Account not found", "synced": 0}

            logger.info(f"[DriveSync] Account: {target_account.channel_name} | Platform: {target_account.platform}")

            # We need a Google token to read from Google Drive.
            # If the target is a Meta account, borrow credentials from any active YouTube account.
            google_account = target_account
            if target_account.platform != PlatformEnum.YOUTUBE:
                yt_result = await db.execute(
                    select(Account).where(
                        Account.platform == PlatformEnum.YOUTUBE,
                        Account.status == AccountStatusEnum.ACTIVE,
                    )
                )
                google_account = yt_result.scalars().first()
                if not google_account:
                    logger.error("[DriveSync] No active YouTube account found to authenticate Drive API!")
                    return {"error": "Drive Sync requires at least one connected Google/YouTube account.", "synced": 0}
                logger.info(f"[DriveSync] Borrowing Google token from: {google_account.channel_name}")

            # Refresh token if needed before Drive access
            try:
                creds = await get_valid_google_credentials(google_account, db)
                access_token = creds.token
                logger.info(f"[DriveSync] Got valid Google token. Calling Drive API...")
            except TokenRefreshError as e:
                logger.error(f"[DriveSync] Token refresh failed: {e}")
                return {"error": f"Token refresh failed: {e}", "synced": 0}
            except Exception as e:
                logger.error(f"[DriveSync] Critical error getting Google token: {e}", exc_info=True)
                return {"error": str(e), "synced": 0}

            try:
                files = await list_drive_folder_videos(folder_id, access_token)
                logger.info(f"[DriveSync] Drive API returned {len(files)} files")
            except Exception as e:
                logger.error(f"[DriveSync] Drive API fetch failed: {e}", exc_info=True)
                return {"error": str(e), "synced": 0}

            from app.services.uploader import read_drive_file_text
            import os

            videos = [f for f in files if "video" in f.get("mimeType", "")]
            images = [f for f in files if "image" in f.get("mimeType", "")]
            texts = [f for f in files if "text" in f.get("mimeType", "")]

            logger.info(f"[DriveSync] Found {len(videos)} videos, {len(images)} images, and {len(texts)} text files in folder")

            txt_map = {}
            for t in texts:
                name = t.get("name", "")
                base = os.path.splitext(name)[0]
                txt_map[base] = t

            def parse_metadata_text(text_content: str):
                metadata = {"title": None, "description": None, "tags": [], "hashtags": []}
                has_strict_keys = any(text_content.lower().startswith(k) for k in ["title:", "description:", "tags:", "hashtags:"])

                if has_strict_keys:
                    lines = text_content.split('\n')
                    current_key = None
                    for line in lines:
                        line_stripped = line.strip()
                        lower_line = line_stripped.lower()

                        if lower_line.startswith("title:"):
                            metadata["title"] = line_stripped[6:].strip()
                            current_key = "title"
                        elif lower_line.startswith("description:"):
                            metadata["description"] = line_stripped[12:].strip()
                            current_key = "description"
                        elif lower_line.startswith("tags:"):
                            tags_str = line_stripped[5:].strip()
                            metadata["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
                            current_key = "tags"
                        elif lower_line.startswith("hashtags:"):
                            hash_str = line_stripped[9:].strip()
                            metadata["hashtags"] = [h.strip() for h in hash_str.split() if h.strip().startswith("#")]
                            current_key = "hashtags"
                        else:
                            if current_key == "description" and line_stripped:
                                metadata["description"] += "\n" + line_stripped
                else:
                    lines = [ln.strip() for ln in text_content.split('\n') if ln.strip()]
                    if lines:
                        metadata["title"] = lines[0]
                        metadata["description"] = "\n".join(lines[1:])
                return metadata

            # Merge videos and images into media items list
            media_items = []
            for f in videos:
                media_items.append((f, MediaTypeEnum.VIDEO))
            for f in images:
                media_items.append((f, MediaTypeEnum.IMAGE))

            synced = 0
            for f, m_type in media_items:
                existing = await db.execute(
                    select(SourceVideo).where(SourceVideo.drive_file_id == f["id"])
                )
                if existing.scalar_one_or_none():
                    logger.info(f"[DriveSync] Skipping duplicate: {f.get('name')}")
                    continue

                new_video = SourceVideo(
                    drive_file_id=f["id"],
                    drive_view_link=f.get("webViewLink"),
                    drive_download_link=f"https://drive.google.com/uc?id={f['id']}&export=download",
                    original_filename=f.get("name"),
                    file_size_bytes=int(f.get("size", 0)) if f.get("size") else None,
                    media_type=m_type,
                )

                base_name = os.path.splitext(f.get("name", ""))[0]
                matching_txt = txt_map.get(base_name)
                if matching_txt:
                    try:
                        logger.info(f"[DriveSync] Found matching .txt for {base_name}, applying metadata...")
                        txt_content = await read_drive_file_text(matching_txt["id"], access_token)
                        custom_meta = parse_metadata_text(txt_content)
                        if custom_meta["title"]:
                            new_video.ai_title = custom_meta["title"]
                        if custom_meta["description"]:
                            new_video.ai_description = custom_meta["description"]
                        if custom_meta["tags"]:
                            new_video.ai_tags = custom_meta["tags"]
                        if custom_meta["hashtags"]:
                            new_video.ai_hashtags = custom_meta["hashtags"]
                    except Exception as e:
                        logger.error(f"[DriveSync] Failed to read metadata txt for {base_name}: {e}")

                db.add(new_video)
                synced += 1
                logger.info(f"[DriveSync] Added {m_type.value} media: {f.get('name')}")

            await db.commit()
            logger.info(f"[DriveSync] Done. Synced {synced} new media assets from folder {folder_id}")

            # ── Auto-Scheduling Logic ──
            if synced > 0 and target_account.automation_settings:
                settings = target_account.automation_settings
                frequency = settings.get("frequency", 1)
                time_slots = settings.get("time_slots", ["10:00", "18:00"])
                add_watermark = settings.get("add_watermark", True)
                ai_metadata = settings.get("ai_metadata", True)
                
                if not time_slots:
                    time_slots = ["10:00"]

                # Find all unscheduled media matching target media type for this account
                post_type = settings.get("facebook_post_type", "video")
                if target_account.platform == PlatformEnum.FACEBOOK and post_type == "image":
                    target_media_type = MediaTypeEnum.IMAGE
                else:
                    target_media_type = MediaTypeEnum.VIDEO

                unscheduled_res = await db.execute(
                    select(SourceVideo).outerjoin(UploadSchedule, SourceVideo.id == UploadSchedule.video_id)
                    .where(UploadSchedule.id == None, SourceVideo.media_type == target_media_type)
                    .order_by(SourceVideo.created_at.asc())
                )
                videos_to_schedule = unscheduled_res.scalars().all()
                
                if videos_to_schedule:
                    # Find last scheduled time for this account
                    last_sched_res = await db.execute(
                        select(UploadSchedule.scheduled_time)
                        .where(UploadSchedule.account_id == target_account.id)
                        .order_by(UploadSchedule.scheduled_time.desc())
                        .limit(1)
                    )
                    last_time = last_sched_res.scalar_one_or_none()
                    
                    if not last_time or last_time < datetime.now(timezone.utc):
                        last_time = datetime.now(timezone.utc)
                    
                    scheduled_count = 0
                    for vid in videos_to_schedule:
                        # Find next slot
                        # Basic logic: Increment day if we exceeded frequency, or just step through time slots
                        current_date = last_time.date()
                        
                        # Find which slot is next
                        next_slot = None
                        for slot_str in sorted(time_slots):
                            h, m = map(int, slot_str.split(':'))
                            slot_time = datetime.combine(current_date, datetime.min.time(), tzinfo=timezone.utc).replace(hour=h, minute=m)
                            if slot_time > last_time + timedelta(hours=1): # At least 1 hour gap
                                next_slot = slot_time
                                break
                        if not next_slot:
                            # Jump to next day first slot
                            h, m = map(int, sorted(time_slots)[0].split(':'))
                            next_slot = datetime.combine(current_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).replace(hour=h, minute=m)

                        # AI Time Optimizer shift
                        scheduled_time = next_slot
                        is_optimized = False
                        original_time = None
                        
                        if target_account.ai_time_predictor:
                            import random
                            opt_slots = target_account.optimal_slots or {}
                            weekday_name = next_slot.strftime("%A")
                            opt_slot_str = opt_slots.get(weekday_name)
                            
                            if not opt_slot_str:
                                # Pre-populate a high-retention active slot (e.g. 12:00, 18:00, 20:00)
                                active_hours = ["12:00", "18:00", "19:00", "20:00"]
                                opt_slot_str = random.choice(active_hours)
                                if not target_account.optimal_slots:
                                    target_account.optimal_slots = {}
                                # Update SQLAlchemy mutable dictionary
                                new_slots = dict(target_account.optimal_slots)
                                new_slots[weekday_name] = opt_slot_str
                                target_account.optimal_slots = new_slots
                            
                            h, m = map(int, opt_slot_str.split(':'))
                            original_time = next_slot
                            scheduled_time = next_slot.replace(hour=h, minute=m)
                            is_optimized = True

                        new_sched = UploadSchedule(
                            video_id=vid.id,
                            account_id=target_account.id,
                            scheduled_time=scheduled_time,
                            original_scheduled_time=original_time,
                            is_optimized_by_ai=is_optimized,
                            add_watermark=add_watermark,
                            metadata_overrides={
                                "watermark_position": settings.get("watermark_position", "bottom-right"),
                                "ai_mode": ai_metadata
                            }
                        )
                        db.add(new_sched)
                        last_time = next_slot
                        scheduled_count += 1
                    
                    await db.commit()
                    logger.info(f"[DriveSync] Auto-scheduled {scheduled_count} videos for {target_account.channel_name}")

            return {"synced": synced, "total": len(files)}


    return run_async(_sync())


# ── Task: Poll YouTube Comments ────────────────────────────────────────────
@celery_app.task(name="app.worker.poll_youtube_comments", bind=True)
def poll_youtube_comments(self):
    """
    Beat scheduler task. Runs every 5 minutes.
    Checks recent YouTube comments for accounts that have comment_rules active,
    generates AI replies via Gemini, and posts them.
    """
    async def _poll():
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.models import CommentRule, CommentLog, Account, PlatformEnum, SystemSettings, ApiKeyVault
        from app.services.ai_responder import generate_comment_reply
        from app.services.token_service import get_valid_google_credentials, TokenRefreshError
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        logger.info("Polling YouTube comments...")
        async with AsyncSessionLocal() as db:
            # Get all active YouTube accounts that have an auto_reply rule
            result = await db.execute(select(CommentRule).where(CommentRule.auto_reply_enabled == True))
            rules = result.scalars().all()

            for rule in rules:
                acc_result = await db.execute(
                    select(Account).where(
                        Account.id == rule.account_id,
                        Account.platform == PlatformEnum.YOUTUBE
                    )
                )
                acc = acc_result.scalar_one_or_none()

                if not acc or not acc.encrypted_access_token or not acc.channel_id:
                    continue

                # Refresh token if needed before polling
                try:
                    creds = await get_valid_google_credentials(acc, db)
                    access_token = creds.token
                except TokenRefreshError as e:
                    logger.warning(f"Skipping comment poll for '{acc.channel_name}' — token error: {e}")
                    continue

                # Fetch recent comments using YouTube Data API v3
                logger.info(f"Checking YouTube comments for {acc.channel_name}...")
                try:
                    credentials = Credentials(token=access_token)
                    youtube = build("youtube", "v3", credentials=credentials)
                except Exception as e:
                    logger.error(f"Failed to build YouTube service client for {acc.channel_name}: {e}")
                    continue

                try:
                    def _fetch():
                        req = youtube.commentThreads().list(
                            part="snippet",
                            allThreadsRelatedToChannelId=acc.channel_id,
                            maxResults=20
                        )
                        return req.execute()

                    response = await asyncio.to_thread(_fetch)
                except Exception as e:
                    logger.error(f"Failed to fetch YouTube comment threads for {acc.channel_name}: {e}")
                    continue

                threads = response.get("items", [])
                for thread in threads:
                    top_comment = thread.get("snippet", {}).get("topLevelComment", {})
                    comment_id = top_comment.get("id")
                    if not comment_id:
                        continue

                    # Extract details
                    snippet = top_comment.get("snippet", {})
                    comment_author_channel_id = snippet.get("authorChannelId", {}).get("value")
                    comment_text = snippet.get("textOriginal", "")
                    author_name = snippet.get("authorDisplayName", "Unknown")

                    # Skip if it is our own comment
                    if comment_author_channel_id == acc.channel_id:
                        continue

                    # Check if already replied
                    log_res = await db.execute(
                        select(CommentLog).where(
                            CommentLog.platform == "youtube",
                            CommentLog.comment_id == comment_id
                        )
                    )
                    if log_res.scalar_one_or_none():
                        continue  # Already replied!

                    # 3. Lookup Provider preferences
                    pref_row = await db.execute(select(SystemSettings).where(SystemSettings.key == "AI_PROVIDER_COMMENTS"))
                    pref = pref_row.scalar_one_or_none()
                    provider = pref.value if pref else "gemini"

                    # 4. Lookup Custom Key if not gemini
                    api_key = None
                    if provider != "gemini":
                        key_row = await db.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == provider))
                        key_obj = key_row.scalar_one_or_none()
                        if key_obj:
                            api_key = key_obj.credentials_json.get("api_key")

                    # 5. Use chosen AI to generate the reply
                    ai_reply = await generate_comment_reply(comment_text, rule.ai_persona, provider=provider, api_key=api_key, db=db)
                    
                    if ai_reply:
                        # Post reply to YouTube using API
                        try:
                            def _reply():
                                body = {
                                    "snippet": {
                                        "parentId": comment_id,
                                        "textOriginal": ai_reply
                                    }
                                }
                                req = youtube.comments().insert(
                                    part="snippet",
                                    body=body
                                )
                                return req.execute()

                            await asyncio.to_thread(_reply)
                            logger.info(f"Successfully posted YouTube reply to comment {comment_id} on channel {acc.channel_name}")
                        except Exception as e:
                            logger.error(f"Failed to post YouTube comment reply: {e}")
                            continue

                        # Log the comment
                        log = CommentLog(
                            account_id=acc.id,
                            platform="youtube",
                            comment_id=comment_id,
                            author_name=author_name,
                            comment_text=comment_text,
                            ai_reply_text=ai_reply,
                            dm_sent=False
                        )
                        db.add(log)
                        await db.commit()

    run_async(_poll())


# ── Task: Proactive Token Refresh ──────────────────────────────────────────
@celery_app.task(name="app.worker.proactive_token_refresh", bind=True)
def proactive_token_refresh(self):
    """
    Beat scheduler task. Runs every 30 minutes.
    Proactively refreshes Google OAuth tokens for all ACTIVE YouTube accounts
    whose token expires within the next 10 minutes.

    This prevents upload failures caused by tokens that expire right as a
    scheduled upload begins. The manual /refresh-token endpoint handles
    user-initiated refreshes; this task handles automatic background renewal.
    """
    async def _refresh():
        from sqlalchemy import select, and_
        from app.database import AsyncSessionLocal
        from app.models.models import Account, AccountStatusEnum, PlatformEnum
        from app.services.token_service import get_valid_google_credentials, TokenRefreshError

        now_utc = datetime.now(timezone.utc)
        # Tokens expiring within 10 minutes need a proactive refresh
        expiry_threshold = now_utc + timedelta(minutes=10)

        logger.info("[ProactiveRefresh] Checking for soon-to-expire tokens...")

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Account).where(
                    and_(
                        Account.platform == PlatformEnum.YOUTUBE,
                        Account.status == AccountStatusEnum.ACTIVE,
                        # Refresh if: expiry is known and approaching, OR expiry is unknown (old record)
                        (Account.token_expiry <= expiry_threshold) | (Account.token_expiry == None),
                    )
                )
            )
            accounts = result.scalars().all()

            refreshed = 0
            failed = 0
            for account in accounts:
                try:
                    await get_valid_google_credentials(account, db)
                    refreshed += 1
                    logger.info(
                        f"[ProactiveRefresh] Refreshed token for '{account.channel_name}'. "
                        f"New expiry: {account.token_expiry}"
                    )
                except TokenRefreshError as e:
                    failed += 1
                    logger.warning(
                        f"[ProactiveRefresh] Failed for '{account.channel_name}': {e}. "
                        f"Revoked: {e.revoked}"
                    )
                except Exception as e:
                    failed += 1
                    logger.error(f"[ProactiveRefresh] Unexpected error for '{account.channel_name}': {e}")

            logger.info(
                f"[ProactiveRefresh] Done. Refreshed: {refreshed}, Failed: {failed}, "
                f"Skipped (still valid): {len(accounts) - refreshed - failed}"
            )

    run_async(_refresh())


# ── Task: Update Video Analytics ──────────────────────────────────────────
@celery_app.task(name="app.worker.update_video_analytics")
def update_video_analytics():
    """Periodically fetch and update stats for all published videos from the last 30 days."""
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

# ── Task: Auto-Healing Unlock For Locked API Keys ─────────────────────────
@celery_app.task(name="app.worker.auto_unlock_expired_keys")
def auto_unlock_expired_keys():
    """
    Beat scheduler task. Runs every hour.
    Automatically unlocks keys whose 24-hour cooldown lockout period has ended.
    """
    async def _unlock():
        from app.database import AsyncSessionLocal
        from app.models.models import ApiKeyVault
        from sqlalchemy import update, and_
        
        logger.info("[AutoUnlock] Checking for expired API key lockouts...")
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                update(ApiKeyVault)
                .where(and_(ApiKeyVault.is_locked == True, ApiKeyVault.unlock_time <= now))
                .values(is_locked=False, unlock_time=None, lock_reason=None)
            )
            await db.commit()
            if result.rowcount > 0:
                logger.info(f"[AutoUnlock] Successfully unlocked {result.rowcount} API key(s).")
                
    run_async(_unlock())


# ── Task: Reset Daily API Usage ───────────────────────────────────────────
@celery_app.task(name="app.worker.reset_daily_api_usage")
def reset_daily_api_usage():
    """
    Beat scheduler task. Runs once a day at midnight UTC.
    Resets daily usage counters to 0.
    """
    async def _reset():
        from app.database import AsyncSessionLocal
        from app.models.models import ApiKeyVault
        from sqlalchemy import update
        
        logger.info("[QuotaReset] Resetting daily API usage counters to 0...")
        async with AsyncSessionLocal() as db:
            await db.execute(update(ApiKeyVault).values(daily_usage=0))
            await db.commit()
            logger.info("[QuotaReset] Daily usage limits successfully cleared.")
            
    run_async(_reset())


# ── Celery Beat Schedule ───────────────────────────────────────────────────
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 1. Check for upcoming schedules every 5 minutes
    "check-pending-schedules-every-5-min": {
        "task": "app.worker.check_pending_schedules",
        "schedule": 300,
    },
    # 2. Poll YouTube for new comments to auto-reply every 5 minutes
    "poll-youtube-comments-every-5-min": {
        "task": "app.worker.poll_youtube_comments",
        "schedule": 300,
    },
    # 3. Proactively refresh expiring YouTube tokens every 30 minutes
    "proactive-token-refresh-every-30-min": {
        "task": "app.worker.proactive_token_refresh",
        "schedule": 1800,
    },
    # 4. Sync Drive folders every hour
    "sync-drive-folders-every-hour": {
        "task": "app.worker.sync_all_accounts_drive",
        "schedule": crontab(minute=0),
    },
    # 5. Update published video performance analytics every 3 hours
    "update-video-analytics-every-3-hours": {
        "task": "app.worker.update_video_analytics",
        "schedule": crontab(minute=0, hour="*/3"),
    },
    # 6. Hourly self-healing key validations and unlocking of cooldown tokens
    "hourly-self-healing-cooldown-unlock": {
        "task": "app.worker.auto_unlock_expired_keys",
        "schedule": crontab(minute=30),
    },
    # 7. Reset daily usage limits at midnight UTC
    "daily-api-usage-quota-reset": {
        "task": "app.worker.reset_daily_api_usage",
        "schedule": crontab(hour=0, minute=0),
    },
}

