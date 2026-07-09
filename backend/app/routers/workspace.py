from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.database import get_db
from app.models.models import UploadSchedule, Account, PlatformEnum, SourceVideo

router = APIRouter(prefix="/workspace", tags=["Workspace"])

@router.get("/{account_id}/summary")
async def get_workspace_summary(account_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch detailed glance info for a specific account workspace."""
    
    # 1. Get Account Info
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # 2. Upload Counts
    published_res = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.account_id == account_id, UploadSchedule.is_published == True)
        )
    )
    pending_res = await db.execute(
        select(func.count(UploadSchedule.id)).where(
            and_(UploadSchedule.account_id == account_id, UploadSchedule.is_published == False)
        )
    )

    # 3. Schedule Range
    next_up_res = await db.execute(
        select(UploadSchedule.scheduled_time).where(
            and_(UploadSchedule.account_id == account_id, UploadSchedule.is_published == False)
        ).order_by(UploadSchedule.scheduled_time.asc()).limit(1)
    )
    last_up_res = await db.execute(
        select(UploadSchedule.scheduled_time).where(
            and_(UploadSchedule.account_id == account_id, UploadSchedule.is_published == False)
        ).order_by(UploadSchedule.scheduled_time.desc()).limit(1)
    )

    # 4. Engagement
    views_res = await db.execute(
        select(func.sum(UploadSchedule.view_count)).where(UploadSchedule.account_id == account_id)
    )

    # 5. Last Used Branding Snapshot
    branding_res = await db.execute(
        select(UploadSchedule.metadata_overrides).where(
            and_(UploadSchedule.account_id == account_id, UploadSchedule.metadata_overrides != None)
        ).order_by(UploadSchedule.created_at.desc()).limit(1)
    )
    last_branding = branding_res.scalar_one_or_none() or {}

    return {
        "account_name": account.channel_name,
        "platform": account.platform,
        "drive_folder_link": account.drive_folder_link,
        "published_count": published_res.scalar() or 0,

        "pending_count": pending_res.scalar() or 0,
        "total_views": int(views_res.scalar() or 0),
        "next_upload": next_up_res.scalar_one_or_none(),
        "scheduled_until": last_up_res.scalar_one_or_none(),
        "branding_catalog": {
            "watermark_enabled": (account.automation_settings or {}).get("add_watermark", last_branding.get("add_watermark", False)),
            "position": (account.automation_settings or {}).get("watermark_position", last_branding.get("watermark_position", "bottom-right")),
            "has_logo": "logo" in str(last_branding),
        },
        "automation_settings": account.automation_settings or {}
    }


@router.get("/{account_id}/pipeline")
async def get_account_pipeline(account_id: uuid.UUID, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch the full list of pending and recent videos for this workspace."""
    result = await db.execute(
        select(UploadSchedule, SourceVideo)
        .join(SourceVideo, UploadSchedule.video_id == SourceVideo.id)
        .where(UploadSchedule.account_id == account_id)
        .order_by(UploadSchedule.scheduled_time.desc())
        .limit(limit)
    )
    rows = result.all()
    pipeline = []
    for s, v in rows:
        pipeline.append({
            "id": s.id,
            "video_id": v.id,
            "title": (s.metadata_overrides or {}).get("title") or v.ai_title or v.original_filename,
            "scheduled_time": s.scheduled_time,
            "is_published": s.is_published,
            "published_url": s.published_url,
            "view_count": s.view_count,
            "status": "published" if s.is_published else ("failed" if s.error_message else "pending")
        })
    return pipeline

@router.patch("/{account_id}/settings")
async def update_automation_settings(
    account_id: uuid.UUID,
    settings: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """Update automation settings for a specific account."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if "drive_folder_link" in settings:
        account.drive_folder_link = settings["drive_folder_link"]
    
    if "automation_settings" in settings:
        account.automation_settings = settings["automation_settings"]
    else:
        current = dict(account.automation_settings or {})
        current.update(settings)
        account.automation_settings = current

    if account.automation_settings and "drive_folder_link" in account.automation_settings:
        account.drive_folder_link = account.automation_settings["drive_folder_link"]
    
    await db.commit()
    return {"status": "success", "settings": account.automation_settings, "drive_folder_link": account.drive_folder_link}

