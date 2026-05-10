endpoint = r'''

@router.post("/{schedule_id}/run-now", response_model=dict)
async def run_pipeline_now(schedule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Run the FULL pipeline in FastAPI asyncio (no Celery). Download-FFmpeg-Upload to platform."""
    import asyncio, logging, traceback, os
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
        from app.models.models import UploadSchedule as US, SourceVideo, Account, PlatformEnum, AccountStatusEnum
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
                    s.error_message = "Video or account not found"
                    await db2.commit()
                    return

                logger.info(f"[RunNow] {v.original_filename} -> {a.channel_name} ({a.platform.value})")

                gcreds = None
                if a.platform == PlatformEnum.YOUTUBE:
                    gcreds = await get_valid_google_credentials(a, db2)
                    tok = gcreds.token
                else:
                    tok = decrypt_token(a.encrypted_access_token)
                    if not tok:
                        s.error_message = f"No token for {a.channel_name}"
                        await db2.commit()
                        return

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

                # Download from Drive
                raw = await download_drive_video(v.drive_file_id, drive_tok, filename=v.original_filename)
                logger.info(f"[RunNow] Downloaded: {raw}")

                # FFmpeg processing
                wm = getattr(s, "add_watermark", False)
                proc = process_video(raw, add_watermark=wm)
                logger.info(f"[RunNow] FFmpeg: {proc}")

                title = v.ai_title or v.original_filename or "Video"
                desc = v.ai_description or ""
                hts = v.ai_hashtags or []
                full_desc = f"{desc}\n\n{' '.join(hts)}" if hts else desc

                ur = {}
                if a.platform == PlatformEnum.YOUTUBE:
                    ur = await upload_to_youtube(proc, title, full_desc, v.ai_tags or [], tok, gcreds)
                elif a.platform == PlatformEnum.FACEBOOK:
                    ur = await upload_to_facebook(proc, title, full_desc, tok, a.channel_id or "")
                elif a.platform == PlatformEnum.INSTAGRAM:
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
                    igf = extract_folder_id_from_link(getattr(a, "drive_folder_link", "") or "")
                    if not igf:
                        igf = getattr(settings, "GOOGLE_DRIVE_PUBLIC_FOLDER_ID", None)
                    if not igf:
                        raise RuntimeError("Set GOOGLE_DRIVE_PUBLIC_FOLDER_ID in .env for Instagram uploads")
                    ur = await upload_to_instagram(
                        proc, f"{title}\n\n{full_desc}", tok, a.channel_id or "", gat2, igf
                    )

                s.is_published = True
                s.published_at = datetime.now(timezone.utc)
                s.published_url = ur.get("url", "")
                s.error_message = None
                v.status = "uploaded"
                await db2.commit()
                logger.info(f"[RunNow] Published: {ur.get('url')}")
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
        "message": "Pipeline started. Poll /schedules/{id} for error_message or published_url.",
    }
'''

with open("backend/app/routers/schedules.py", "r", encoding="utf-8") as f:
    content = f.read()

# Only append if not already there
if "run_pipeline_now" not in content:
    with open("backend/app/routers/schedules.py", "w", encoding="utf-8") as f:
        f.write(content.rstrip() + endpoint)
    print("DONE: run-now endpoint appended")
else:
    print("SKIP: run_pipeline_now already exists")
