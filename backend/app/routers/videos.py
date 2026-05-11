import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import SourceVideo, VideoStatusEnum
from app.schemas import SourceVideoOut, DriveSyncRequest

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.get("/", response_model=List[SourceVideoOut])
async def list_videos(
    status_filter: VideoStatusEnum = None,
    unassigned_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(SourceVideo).order_by(SourceVideo.created_at.desc())
    if status_filter:
        query = query.where(SourceVideo.status == status_filter)
        
    if unassigned_only:
        from sqlalchemy.orm import aliased
        from app.models.models import UploadSchedule
        query = query.outerjoin(UploadSchedule, SourceVideo.id == UploadSchedule.video_id).where(UploadSchedule.id == None)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{video_id}", response_model=SourceVideoOut)
async def get_video(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceVideo).where(SourceVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceVideo).where(SourceVideo.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await db.delete(video)
    await db.commit()


@router.post("/sync-drive", status_code=status.HTTP_202_ACCEPTED)
async def sync_drive_folder(req: DriveSyncRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Trigger an async background sync of videos from a Google Drive folder.
    Dispatches a Celery task and returns the task_id for polling.
    """
    from app.services.uploader import extract_folder_id_from_link
    from app.worker import sync_drive_folder as sync_drive_task
    from app.models.models import Account

    folder_link = req.folder_link
    if not folder_link:
        # Try to get from account
        result = await db.execute(select(Account).where(Account.id == req.account_id))
        acc = result.scalar_one_or_none()
        if acc and acc.drive_folder_link:
            folder_link = acc.drive_folder_link
        else:
            raise HTTPException(status_code=400, detail="Drive folder link required (none provided and none saved for account)")

    folder_id = extract_folder_id_from_link(folder_link)
    if not folder_id:
        return {"error": "Invalid Drive folder link", "synced": 0}
    
    task = sync_drive_task.apply_async(args=[folder_link, str(req.account_id)], queue="default")
    return {"task_id": task.id, "folder_id": folder_id, "message": "Drive sync task queued."}


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a Celery task (e.g., Drive sync)."""
    from app.worker import celery_app

    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }


@router.post("/sync-debug")
async def sync_debug(req: DriveSyncRequest, db: AsyncSession = Depends(get_db)):
    """
    DEBUG: Run Drive sync synchronously in FastAPI process.
    Returns exact error details. Do not use in production.
    """
    import traceback
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.models import SourceVideo, Account, PlatformEnum, AccountStatusEnum
    from app.services.uploader import list_drive_folder_videos, extract_folder_id_from_link
    from app.services.token_service import get_valid_google_credentials, TokenRefreshError

    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Not available when DEBUG=false")

    try:
        folder_id = extract_folder_id_from_link(req.folder_link)
        if not folder_id:
            return {"error": f"Could not extract folder ID from: {req.folder_link}"}

        acc_result = await db.execute(select(Account).where(Account.id == req.account_id))
        account = acc_result.scalar_one_or_none()
        if not account:
            return {"error": f"Account {req.account_id} not found"}

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
                return {"error": "No active YouTube account found"}

        try:
            creds = await get_valid_google_credentials(google_account, db)
            access_token = creds.token
        except TokenRefreshError as e:
            return {"error": f"TokenRefreshError: {e}", "revoked": e.revoked}
        except Exception as e:
            return {"error": f"Token error: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

        try:
            files = await list_drive_folder_videos(folder_id, access_token)
        except Exception as e:
            return {"error": f"Drive API error: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}

        import os
        videos = [f for f in files if "video" in f.get("mimeType", "")]
        return {
            "success": True,
            "folder_id": folder_id,
            "account": google_account.channel_name,
            "total_files": len(files),
            "video_files": len(videos),
            "sample_files": files[:3],
        }
    except Exception as e:
        return {"error": f"Unexpected: {type(e).__name__}: {e}", "traceback": traceback.format_exc()}
