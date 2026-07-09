import uuid
from typing import List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import UploadSchedule, SourceVideo
from app.schemas import ScheduleCreate, ScheduleOut, AutoDripRequest, ClearQueueRequest

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("/instant-post-next")
async def instant_post_next(
    req: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Find the next pending schedule for an account and trigger it immediately.
    If no pending schedules exist, find the next unpublished source video from the
    account's synced Google Drive folder, create a schedule for it, and run it.
    """
    account_id = req.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id required")
    
    # Always create a new ad-hoc schedule to upload the next video raw (without editing) from Google Drive.
    # This leaves existing scheduled posts in the queue untouched.
    from sqlalchemy import select, and_
    import uuid
    from app.models.models import UploadSchedule, Account, SourceVideo
    from app.services.uploader import extract_folder_id_from_link, list_drive_folder_videos
    from app.services.token_service import get_valid_google_credentials
    from app.models.models import PlatformEnum, AccountStatusEnum
    from datetime import datetime, timezone
    
    try:
        if isinstance(account_id, uuid.UUID):
            target_uuid = account_id
        elif isinstance(account_id, str):
            target_uuid = uuid.UUID(account_id)
        else:
            target_uuid = uuid.UUID(str(account_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format for account_id: {str(e)}")
    
    acc_result = await db.execute(select(Account).where(Account.id == target_uuid))
    account = acc_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if not account.drive_folder_link:
        raise HTTPException(status_code=404, detail="No Google Drive folder link is configured for this account.")
        
    folder_id = extract_folder_id_from_link(account.drive_folder_link)
    if not folder_id:
        raise HTTPException(status_code=400, detail="Invalid Google Drive folder link.")
        
    # Get credentials to read from Drive
    google_account = account
    if account.platform != PlatformEnum.YOUTUBE:
        yt_result = await db.execute(
            select(Account).where(
                Account.platform == PlatformEnum.YOUTUBE,
                Account.status == AccountStatusEnum.ACTIVE,
            )
        )
        google_account = yt_result.scalars().first()
        if not google_account:
            raise HTTPException(status_code=400, detail="Drive access requires at least one active YouTube/Google account to authenticate API.")
            
    try:
        creds = await get_valid_google_credentials(google_account, db)
        access_token = creds.token
        drive_files = await list_drive_folder_videos(folder_id, access_token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to access Google Drive: {str(e)}")
        
    file_ids = [f["id"] for f in drive_files if "id" in f]
    if not file_ids:
        raise HTTPException(status_code=404, detail="No videos found in the linked Google Drive folder. Please upload videos first.")
        
    # Ensure all drive files are registered in SourceVideo
    from app.models.models import MediaTypeEnum, VideoStatusEnum
    existing_videos_result = await db.execute(
        select(SourceVideo.drive_file_id).where(SourceVideo.drive_file_id.in_(file_ids))
    )
    existing_file_ids = set(existing_videos_result.scalars().all())
    
    inserted_any = False
    for f in drive_files:
        fid = f.get("id")
        if fid and fid not in existing_file_ids:
            mime = f.get("mimeType", "").lower()
            if "video" in mime:
                mtype = MediaTypeEnum.VIDEO
            elif "image" in mime:
                mtype = MediaTypeEnum.IMAGE
            else:
                continue
            
            sv = SourceVideo(
                id=uuid.uuid4(),
                drive_file_id=fid,
                drive_view_link=f.get("webViewLink"),
                drive_download_link=f"https://www.googleapis.com/drive/v3/files/{fid}?alt=media",
                original_filename=f.get("name"),
                file_size_bytes=int(f.get("size")) if f.get("size") else None,
                media_type=mtype,
                status=VideoStatusEnum.PENDING
            )
            db.add(sv)
            inserted_any = True
            
    if inserted_any:
        await db.commit()

    # Find synced videos in DB
    video_result = await db.execute(
        select(SourceVideo).where(SourceVideo.drive_file_id.in_(file_ids))
    )
    source_videos = video_result.scalars().all()
    if not source_videos:
        raise HTTPException(status_code=404, detail="No synced videos found in database. Please sync the channel folder first.")
        
    # Find already published/scheduled video IDs for this account
    published_result = await db.execute(
        select(UploadSchedule.video_id).where(UploadSchedule.account_id == target_uuid)
    )
    published_video_ids = set(published_result.scalars().all())
    
    # Pick the first video not yet published/scheduled on this account
    next_video = None
    for sv in source_videos:
        if sv.id not in published_video_ids:
            next_video = sv
            break
            
    if not next_video:
        raise HTTPException(status_code=404, detail="All synced videos in this folder have already been scheduled or published for this account.")
        
    # Create a new schedule scheduled for right now, with editing=False, watermark=False, delete_from_drive=True
    schedule = UploadSchedule(
        id=uuid.uuid4(),
        account_id=target_uuid,
        video_id=next_video.id,
        scheduled_time=datetime.now(timezone.utc),
        original_scheduled_time=datetime.now(timezone.utc),
        is_published=False,
        metadata_overrides={
            "mode": "manual",
            "custom_title_append": "",
            "custom_description": "",
            "tags": "",
            "add_watermark": False,
            "video_editing": False,
            "delete_from_drive": True
        }
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    # 2. Trigger it
    from app.worker import process_and_upload_video
    task = process_and_upload_video.apply_async(
        args=[str(schedule.id)],
        queue="video_pipeline",
    )
    schedule.celery_task_id = task.id
    await db.commit()
    
    return {"status": "success", "task_id": task.id, "message": "Instant post triggered successfully"}


@router.get("/", response_model=List[ScheduleOut])
async def list_schedules(
    is_published: bool = None,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload
    try:
        query = select(UploadSchedule).options(selectinload(UploadSchedule.video)).order_by(UploadSchedule.scheduled_time)
        if is_published is not None:
            query = query.where(UploadSchedule.is_published == is_published)
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Schedule list ORM error, attempting migration: {e}")
        try:
            from sqlalchemy import text
            await db.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS metadata_overrides JSONB;"))
            await db.commit()
            query = select(UploadSchedule).options(selectinload(UploadSchedule.video)).order_by(UploadSchedule.scheduled_time)
            if is_published is not None:
                query = query.where(UploadSchedule.is_published == is_published)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e2:
            logger.error(f"Schedule list fallback failed: {e2}")
            return []


@router.post("/", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule_in: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create a single upload schedule entry."""
    schedule = UploadSchedule(**schedule_in.model_dump())
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.post("/auto-drip", status_code=status.HTTP_201_CREATED)
async def create_auto_drip(req: AutoDripRequest, db: AsyncSession = Depends(get_db)):
    """
    Auto-Drip Scheduler.
    Supports 3 modes:
    - Single: account_id (single account)
    - Multiple: account_ids (list of accounts — each gets its own independent schedule)
    - Group: target_group_id (fan-out to all members)

    Evenly spreads N videos across the given number of days, starting from start_datetime.
    Respects daily_limit_per_account if set.
    """
    # ── Map V2 Wizard Payload to Legacy Locals ─────────────────────────────
    effective_video_ids = req.media_pool if req.media_pool else req.video_ids
    if not effective_video_ids:
        raise HTTPException(status_code=400, detail="No videos provided")

    effective_account_ids = req.targets if req.targets else req.account_ids
    if not effective_account_ids and not req.target_group_id and not req.account_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide targets, account_ids, account_id, or target_group_id"
        )

    # Transform V2 schedule configuration
    if req.schedule_config:
        req.auto_comment = req.schedule_config.comment_mode != "none"
        req.daily_time_slots = req.schedule_config.time_slots
        req.daily_limit_per_account = req.schedule_config.frequency
        freq = req.schedule_config.frequency if req.schedule_config.frequency > 0 else 1
        req.total_days = max(1, (len(effective_video_ids) + freq - 1) // freq)
        if not req.start_datetime:
            req.start_datetime = datetime.now(timezone.utc)
    elif req.settings:
        req.daily_time_slots = req.settings.get("time_slots")
        req.add_watermark = req.settings.get("add_watermark", True)
        slots = req.daily_time_slots or []
        slots_count = len(slots) if len(slots) > 0 else 1
        req.total_days = max(1, (len(effective_video_ids) + slots_count - 1) // slots_count)
        if not req.start_datetime:
            req.start_datetime = datetime.now(timezone.utc)

    # Dump V2 Metadata for JSON storage
    v2_metadata_json = None
    if req.metadata_overrides:
        v2_metadata_json = req.metadata_overrides.model_dump()
        if req.metadata_overrides.add_watermark is None:
            pass
        else:
            req.add_watermark = req.metadata_overrides.add_watermark
    elif req.settings:
        mode = req.settings.get("mode", "original")
        v2_metadata_json = {
            "mode": mode,
            "ai_mode": (mode == "ai"),
            "custom_description": req.settings.get("custom_description", ""),
            "tags": req.settings.get("tags", ""),
            "add_watermark": req.add_watermark,
            "prefer_drive_metadata": req.settings.get("prefer_drive_metadata", True)
        }


    total_videos = len(effective_video_ids)
    total_seconds = (req.total_days or 1) * 24 * 3600

    # ── Fixed Time Slots Generator ─────────────────────────────────────────
    def generate_fixed_slots(start_dt, raw_slots):
        from datetime import time as dt_time
        parsed_slots = []
        for ts in raw_slots:
            h, m = map(int, ts.split(":"))
            parsed_slots.append(dt_time(hour=h, minute=m))
        parsed_slots.sort()

        curr_date = start_dt.date()
        while True:
            for t in parsed_slots:
                slot_dt = datetime.combine(curr_date, t, tzinfo=start_dt.tzinfo)
                if slot_dt >= start_dt:
                    yield slot_dt
            curr_date += timedelta(days=1)

    # ── Determine target accounts ──────────────────────────────────────────
    account_ids_to_schedule = []
    if effective_account_ids and len(effective_account_ids) > 0:
        account_ids_to_schedule = [str(aid) for aid in effective_account_ids]
    elif req.account_id:
        account_ids_to_schedule = [str(req.account_id)]

    schedules_created = 0
    use_fixed_slots = bool(req.daily_time_slots and len(req.daily_time_slots) > 0)
    start_time_val = req.start_datetime or datetime.now(timezone.utc)

    if account_ids_to_schedule:
        # Single or Multiple mode — per-account spreading
        for acc_id in account_ids_to_schedule:
            videos_for_acc = effective_video_ids
            if req.daily_limit_per_account and req.daily_limit_per_account > 0:
                max_total = (req.total_days or 1) * req.daily_limit_per_account
                videos_for_acc = videos_for_acc[:max_total]

            n = len(videos_for_acc)
            if n == 0:
                continue

            if use_fixed_slots:
                slot_gen = generate_fixed_slots(start_time_val, req.daily_time_slots)
            else:
                interval_s = total_seconds / n

            for i, video_id in enumerate(videos_for_acc):
                if use_fixed_slots:
                    slot_time = next(slot_gen)
                else:
                    slot_time = start_time_val + timedelta(seconds=interval_s * i)

                schedule = UploadSchedule(
                    video_id=video_id,
                    account_id=uuid.UUID(acc_id) if isinstance(acc_id, str) else acc_id,
                    target_group_id=None,
                    scheduled_time=slot_time,
                    add_watermark=req.add_watermark,
                    auto_comment=req.auto_comment,
                    metadata_overrides=v2_metadata_json,
                )
                db.add(schedule)
                schedules_created += 1

    elif req.target_group_id:
        # Group mode — single group-level schedule per video
        if use_fixed_slots:
            slot_gen = generate_fixed_slots(start_time_val, req.daily_time_slots)
        else:
            interval_s = total_seconds / total_videos

        for i, video_id in enumerate(effective_video_ids):
            if use_fixed_slots:
                slot_time = next(slot_gen)
            else:
                slot_time = start_time_val + timedelta(seconds=interval_s * i)

            schedule = UploadSchedule(
                video_id=video_id,
                account_id=None,
                target_group_id=req.target_group_id,
                scheduled_time=slot_time,
                add_watermark=req.add_watermark,
                auto_comment=req.auto_comment,
                metadata_overrides=v2_metadata_json,
            )
            db.add(schedule)
            schedules_created += 1

    await db.commit()

    interval_hours = round((total_seconds / total_videos) / 3600, 2)
    return {
        "created": schedules_created,
        "total_days": req.total_days,
        "interval_hours": interval_hours,
        "message": f"Scheduled {schedules_created} entries across {req.total_days} days.",
    }


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
async def bulk_delete_schedules(
    ids: List[uuid.UUID] = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
):
    """Bulk cancel/delete multiple scheduled entries at once."""
    if not ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    from sqlalchemy import delete
    result = await db.execute(
        delete(UploadSchedule).where(UploadSchedule.id.in_(ids))
    )
    await db.commit()
    return {"deleted": result.rowcount, "message": f"Cancelled {result.rowcount} schedule(s)"}


@router.post("/clear-queue", status_code=status.HTTP_200_OK)
async def clear_queue_by_accounts(
    req: ClearQueueRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete all pending/unpublished schedules associated with one or more specified account IDs.
    Also revokes any JIT tasks in Celery to prevent orphan executions in the background.
    """
    if not req.account_ids:
        raise HTTPException(status_code=400, detail="No account_ids provided")

    # 1. Fetch the schedules first to extract Celery task IDs
    result = await db.execute(
        select(UploadSchedule).where(
            and_(
                UploadSchedule.account_id.in_(req.account_ids),
                UploadSchedule.is_published == False
            )
        )
    )
    schedules = result.scalars().all()
    deleted_count = len(schedules)

    if deleted_count > 0:
        # 2. Extract and revoke any active Celery task IDs
        task_ids = [s.celery_task_id for s in schedules if s.celery_task_id]
        if task_ids:
            try:
                from app.worker import celery_app
                import logging
                logger = logging.getLogger(__name__)
                for tid in task_ids:
                    # Ignore non-uuid or custom identifiers (like fan-out stubs)
                    if tid and "fanout" not in str(tid) and "fan_out" not in str(tid):
                        celery_app.control.revoke(str(tid), terminate=True)
                        logger.info(f"Revoked Celery JIT task {tid} during queue clearing")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to revoke celery JIT tasks during queue clearing: {e}")

        # 3. Perform database deletion
        for s in schedules:
            await db.delete(s)
        await db.commit()

    return {
        "deleted": deleted_count,
        "message": f"Successfully cleared {deleted_count} pending schedule(s) for the selected account(s)."
    }


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Revoke Celery task if present
    if schedule.celery_task_id:
        try:
            from app.worker import celery_app
            import logging
            logger = logging.getLogger(__name__)
            tid = schedule.celery_task_id
            if tid and "fanout" not in str(tid) and "fan_out" not in str(tid):
                celery_app.control.revoke(str(tid), terminate=True)
                logger.info(f"Revoked Celery JIT task {tid} during single schedule deletion")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to revoke celery JIT task {schedule.celery_task_id} during schedule deletion: {e}")

    await db.delete(schedule)
    await db.commit()


@router.post("/{schedule_id}/trigger", response_model=dict)
async def manually_trigger_schedule(
    schedule_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a scheduled upload immediately (run now)."""
    from app.worker import process_and_upload_video

    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule.is_published:
        raise HTTPException(status_code=400, detail="Already published")

    task = process_and_upload_video.apply_async(
        args=[str(schedule.id)],
        queue="video_pipeline",
    )
    schedule.celery_task_id = task.id
    await db.commit()
    return {"task_id": task.id, "message": "Pipeline task dispatched immediately"}


@router.post("/{schedule_id}/run-debug", response_model=dict)
async def run_pipeline_debug(
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    DEBUG: Run the upload pipeline synchronously in FastAPI (no Celery).
    Returns exact error details so we can diagnose Celery RETRY failures.
    """
    import traceback
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.models import SourceVideo, Account, AccountStatusEnum, PlatformEnum
    from app.services.uploader import extract_folder_id_from_link
    from app.services.token_service import get_valid_google_credentials, TokenRefreshError

    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Not available when DEBUG=false")

    try:
        result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
        schedule = result.scalar_one_or_none()
        if not schedule:
            return {"error": "Schedule not found"}

        video_result = await db.execute(select(SourceVideo).where(SourceVideo.id == schedule.video_id))
        video = video_result.scalar_one_or_none()
        if not video:
            return {"error": "Video not found for schedule"}

        account = None
        if schedule.account_id:
            acc_result = await db.execute(select(Account).where(Account.id == schedule.account_id))
            account = acc_result.scalar_one_or_none()

        if not account:
            return {"error": f"No account for schedule {schedule_id}"}

        # Try token
        try:
            creds = await get_valid_google_credentials(account, db) if account.platform == PlatformEnum.YOUTUBE else None
            access_token = creds.token if creds else None
            if not access_token:
                from app.core.security import decrypt_token
                access_token = decrypt_token(account.encrypted_access_token)
        except TokenRefreshError as e:
            return {"error": f"TokenRefreshError: {e}", "revoked": e.revoked, "traceback": traceback.format_exc()}
        except Exception as e:
            return {"error": f"Token error: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

        # Try Drive metadata fetch (first step of download)
        try:
            import httpx
            headers = {"Authorization": f"Bearer {access_token}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                meta_resp = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{video.drive_file_id}?fields=name,size,mimeType",
                    headers=headers
                )
                if meta_resp.status_code != 200:
                    return {
                        "error": f"Drive API returned {meta_resp.status_code}",
                        "drive_response": meta_resp.text,
                        "account": account.channel_name,
                        "platform": account.platform.value,
                        "drive_file_id": video.drive_file_id,
                    }
                meta = meta_resp.json()
        except Exception as e:
            return {"error": f"Drive API test failed: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

        return {
            "success": True,
            "schedule_id": str(schedule_id),
            "video": video.original_filename,
            "account": account.channel_name,
            "platform": account.platform.value,
            "drive_file_id": video.drive_file_id,
            "drive_meta": meta,
            "has_ai_title": bool(video.ai_title),
            "message": "All pre-pipeline checks PASSED. The issue is downstream (FFmpeg or upload step)."
        }
    except Exception as e:
        return {"error": f"Unexpected: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}


@router.post("/{schedule_id}/run-now", response_model=dict)
async def run_pipeline_now(schedule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Run the FULL upload pipeline in FastAPI asyncio (no Celery).
    Steps: Download from Drive -> FFmpeg processing -> Upload to YouTube/Facebook/Instagram.
    Returns immediately; pipeline runs as asyncio background task.
    On failure, error is saved to schedule.error_message.
    """
    import asyncio
    import logging
    import traceback
    import os
    from app.core.config import settings

    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Not available when DEBUG=false")

    logger = logging.getLogger("app.pipeline_now")

    res = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if sched.is_published:
        return {"status": "already_published"}

    async def _run():
        from app.database import AsyncSessionLocal
        from sqlalchemy import select as sel
        from app.models.models import (
            UploadSchedule as US, SourceVideo, Account,
            PlatformEnum, AccountStatusEnum
        )
        from app.services.uploader import (
            download_drive_video, upload_to_youtube, upload_to_facebook,
            upload_to_instagram, extract_folder_id_from_link
        )
        from app.services.ffmpeg import process_video
        from app.services.token_service import get_valid_google_credentials, TokenRefreshError
        from app.core.security import decrypt_token
        from datetime import datetime, timezone

        async with AsyncSessionLocal() as db2:
            s = None
            try:
                s = (await db2.execute(sel(US).where(US.id == schedule_id))).scalar_one_or_none()
                if not s or s.is_published:
                    return

                v = (await db2.execute(sel(SourceVideo).where(SourceVideo.id == s.video_id))).scalar_one_or_none()
                a = (await db2.execute(sel(Account).where(Account.id == s.account_id))).scalar_one_or_none()

                if not v or not a:
                    s.error_message = "Video or account not found in DB"
                    await db2.commit()
                    return

                logger.info(f"[RunNow] Starting: {v.original_filename} -> {a.channel_name} ({a.platform.value})")

                # Get access token
                gcreds = None
                if a.platform == PlatformEnum.YOUTUBE:
                    gcreds = await get_valid_google_credentials(a, db2)
                    tok = gcreds.token
                else:
                    tok = decrypt_token(a.encrypted_access_token)
                    if not tok:
                        s.error_message = f"No access token for {a.channel_name}"
                        await db2.commit()
                        return

                # Get Drive token (always use YouTube account for Drive downloads)
                drive_tok = tok
                if a.platform != PlatformEnum.YOUTUBE:
                    yt_q = sel(Account).where(
                        Account.platform == PlatformEnum.YOUTUBE,
                        Account.status == AccountStatusEnum.ACTIVE
                    )
                    yt = (await db2.execute(yt_q)).scalars().first()
                    if yt:
                        try:
                            drive_tok = (await get_valid_google_credentials(yt, db2)).token
                        except Exception:
                            drive_tok = decrypt_token(yt.encrypted_access_token) or drive_tok

                # Step 1: Download video from Google Drive
                logger.info(f"[RunNow] Downloading {v.drive_file_id}...")
                raw = await download_drive_video(
                    v.drive_file_id, drive_tok, filename=v.original_filename
                )
                logger.info(f"[RunNow] Downloaded: {raw}")

                # Step 2: FFmpeg processing (uniquify with custom brand layout settings)
                wm = getattr(s, "add_watermark", False) or False
                
                acc_settings = a.automation_settings or {}
                video_editing_enabled = acc_settings.get("video_editing", True)
                
                if not video_editing_enabled:
                    logger.info("[RunNow] Visual Video Editing is DISABLED. Uploading RAW video from Google Drive.")
                    proc = raw
                else:
                    wm_pos = acc_settings.get("watermark_pos", "BR")
                    wm_size = float(acc_settings.get("watermark_size", 15)) / 100.0
                    wm_opacity = float(acc_settings.get("watermark_opacity", 0.8))
                    
                    text_text = acc_settings.get("overlay_text", "")
                    text_pos = acc_settings.get("text_pos", "BC")
                    text_color = acc_settings.get("text_color", "#ffffff")
                    
                    proc = process_video(
                        raw, 
                        add_watermark=wm,
                        text_text=text_text,
                        target_platform=a.platform.value,
                        settings={
                            'position': wm_pos,
                            'width': wm_size,
                            'height': wm_size,
                            'opacity': wm_opacity,
                            'text_pos': text_pos,
                            'text_color': text_color
                        }
                    )
                logger.info(f"[RunNow] FFmpeg done: {proc}")

                # Step 3: Metadata
                title = v.ai_title or v.original_filename or "Video"
                desc = v.ai_description or ""
                hts = v.ai_hashtags or []
                full_desc = f"{desc}\n\n{' '.join(hts)}" if hts else desc

                # Step 4: Upload to platform
                ur = {}
                if a.platform == PlatformEnum.YOUTUBE:
                    logger.info("[RunNow] Uploading to YouTube...")
                    ur = await upload_to_youtube(
                        proc, title, full_desc, v.ai_tags or [], tok, gcreds
                    )
                elif a.platform == PlatformEnum.FACEBOOK:
                    logger.info(f"[RunNow] Uploading to Facebook page {a.channel_id}...")
                    ur = await upload_to_facebook(
                        proc, title, full_desc, tok, a.channel_id or ""
                    )
                elif a.platform == PlatformEnum.INSTAGRAM:
                    logger.info(f"[RunNow] Uploading to Instagram {a.channel_id}...")
                    yt_q2 = sel(Account).where(
                        Account.platform == PlatformEnum.YOUTUBE,
                        Account.status == AccountStatusEnum.ACTIVE
                    )
                    yt2 = (await db2.execute(yt_q2)).scalars().first()
                    gat2 = drive_tok
                    if yt2:
                        try:
                            gat2 = (await get_valid_google_credentials(yt2, db2)).token
                        except Exception:
                            pass
                    from app.core.config import settings
                    igf = extract_folder_id_from_link(
                        getattr(a, "drive_folder_link", "") or ""
                    )
                    if not igf:
                        igf = getattr(settings, "GOOGLE_DRIVE_PUBLIC_FOLDER_ID", None)
                    if not igf:
                        raise RuntimeError(
                            "Instagram upload requires GOOGLE_DRIVE_PUBLIC_FOLDER_ID in .env"
                        )
                    caption = f"{title}\n\n{full_desc}"
                    ur = await upload_to_instagram(
                        proc, caption, tok, a.channel_id or "", gat2, igf
                    )

                # Step 5: Mark published
                s.is_published = True
                s.published_at = datetime.now(timezone.utc)
                s.published_url = ur.get("url", "")
                s.error_message = None
                v.status = "uploaded"
                await db2.commit()
                logger.info(f"[RunNow] PUBLISHED: {ur.get('url')}")

                # Cleanup temp files
                for f in [raw, proc]:
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            except Exception as exc:
                err = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
                logger.error(f"[RunNow] FAILED: {err}")
                if s:
                    try:
                        s.error_message = err[:2000]
                        await db2.commit()
                    except Exception:
                        pass

    asyncio.create_task(_run())
    return {
        "status": "started",
        "schedule_id": str(schedule_id),
        "message": "Upload pipeline started in background. Check schedule for published_url or error_message.",
    }

@router.patch("/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(
    schedule_id: uuid.UUID,
    updates: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Update any field of a schedule, including metadata_overrides (title, desc, branding)."""
    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if "scheduled_time" in updates:
        try:
            schedule.scheduled_time = datetime.fromisoformat(updates["scheduled_time"].replace("Z", "+00:00"))
        except: pass
    
    if "add_watermark" in updates:
        schedule.add_watermark = bool(updates["add_watermark"])
    
    if "metadata" in updates:
        if schedule.metadata_overrides is None:
            schedule.metadata_overrides = {}
        # Merge metadata (title, description, tags, overlays)
        current = dict(schedule.metadata_overrides)
        current.update(updates["metadata"])
        schedule.metadata_overrides = current
            
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.post("/{schedule_id}/replace", response_model=ScheduleOut)
async def replace_schedule_video(
    schedule_id: uuid.UUID,
    new_video_id: uuid.UUID = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """Swap the source video for an existing schedule while keeping its metadata/time."""
    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.video_id = new_video_id
    await db.commit()
    await db.refresh(schedule)
    return schedule


