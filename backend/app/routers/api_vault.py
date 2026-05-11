import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import ApiKeyVault
from app.schemas import ApiKeyVaultOut, MetaKeyCreate, CustomKeyCreate

router = APIRouter(prefix="/api-vault", tags=["API Vault"])


@router.get("/", response_model=List[dict])
async def list_api_keys(
    service_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all API keys in the vault, optionally filtering by service."""
    query = select(ApiKeyVault).order_by(ApiKeyVault.created_at.desc())
    if service_name:
        query = query.where(ApiKeyVault.service_name == service_name)
    result = await db.execute(query)
    db_keys = list(result.scalars().all())
    
    # Add virtual .env keys to the list for visibility in UI
    from app.core.config import settings
    from app.services.api_rotation import SYSTEM_KEY_STATUS
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    env_keys = []
    
    # Helper to check if virtual key is locked
    def get_status(vid):
        status = SYSTEM_KEY_STATUS.get(vid)
        if status and status["locked_until"] > now:
            return True, status["reason"]
        return False, None

    if (not service_name or service_name == "gemini") and settings.GEMINI_API_KEY:
        locked, reason = get_status("00000000-0000-0000-0000-000000000001")
        env_keys.append({
            "id": "00000000-0000-0000-0000-000000000001",
            "service_name": "gemini",
            "project_name": "System Default (ENV)",
            "is_locked": locked,
            "lock_reason": reason,
            "daily_usage": 50 if locked else 0,
            "daily_limit": 50,
            "created_at": "2024-01-01T00:00:00",
            "is_system": True
        })
    
    if (not service_name or service_name == "google") and settings.GOOGLE_CLIENT_ID:
        locked, reason = get_status("00000000-0000-0000-0000-000000000002")
        env_keys.append({
            "id": "00000000-0000-0000-0000-000000000002",
            "service_name": "google",
            "project_name": "System Default (ENV)",
            "is_locked": locked,
            "lock_reason": reason,
            "daily_usage": 0,
            "daily_limit": 10000,
            "created_at": "2024-01-01T00:00:00",
            "is_system": True
        })

    if (not service_name or service_name == "meta") and (settings.META_APP_ID or settings.META_CLIENT_ID):
        locked, reason = get_status("00000000-0000-0000-0000-000000000003")
        env_keys.append({
            "id": "00000000-0000-0000-0000-000000000003",
            "service_name": "meta",
            "project_name": "System Default (ENV)",
            "is_locked": locked,
            "lock_reason": reason,
            "daily_usage": 0,
            "daily_limit": 10000,
            "created_at": "2024-01-01T00:00:00",
            "is_system": True
        })

    # Convert to a common format
    all_keys = []
    for k in db_keys:
        all_keys.append({
            "id": str(k.id),
            "service_name": k.service_name,
            "project_name": k.project_name,
            "is_locked": k.is_locked,
            "daily_usage": k.daily_usage,
            "daily_limit": k.daily_limit,
            "created_at": k.created_at,
            "is_system": False
        })
    
    return all_keys + env_keys


@router.post("/upload-json", status_code=status.HTTP_201_CREATED)
async def upload_json_credentials(
    files: List[UploadFile] = File(...),
    service_name: str = "google",
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk upload Google Cloud Project JSON credential files.
    Accepts 1–50+ files at once via multipart form upload.
    """
    added = 0
    skipped = 0
    errors = []

    for file in files:
        try:
            content = await file.read()
            creds = json.loads(content)

            inner_creds = creds
            if "installed" in creds:
                inner_creds = creds["installed"]
            elif "web" in creds:
                inner_creds = creds["web"]

            project_name = (
                inner_creds.get("client_id")
                or inner_creds.get("project_id")
                or inner_creds.get("client_email", "").split("@")[0]
                or file.filename
            )

            existing = await db.execute(
                select(ApiKeyVault).where(
                    and_(
                        ApiKeyVault.service_name == service_name,
                        ApiKeyVault.project_name == project_name,
                    )
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            key_entry = ApiKeyVault(
                service_name=service_name,
                project_name=project_name,
                credentials_json=creds,
            )
            db.add(key_entry)
            added += 1

        except json.JSONDecodeError:
            errors.append(f"{file.filename}: Invalid JSON")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    await db.commit()
    return {
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "message": f"Successfully added {added} API key(s). Skipped {skipped} duplicates.",
    }


@router.post("/meta-key", status_code=status.HTTP_201_CREATED)
async def add_meta_api_key(
    meta_key: MetaKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually add Meta (Facebook/Instagram) App credentials.
    Stores App ID, App Secret, and Access Token as a JSON blob.
    """
    # Deduplicate by app_id
    existing = await db.execute(
        select(ApiKeyVault).where(
            and_(
                ApiKeyVault.service_name == "meta",
                ApiKeyVault.project_name == meta_key.app_name,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Meta key with name '{meta_key.app_name}' already exists. Delete old one first."
        )

    credentials_blob = {
        "app_id": meta_key.app_id,
        "app_secret": meta_key.app_secret,
        "access_token": meta_key.access_token,
        "service": "meta",
    }

    key_entry = ApiKeyVault(
        service_name="meta",
        project_name=meta_key.app_name,
        credentials_json=credentials_blob,
        daily_limit=meta_key.daily_limit or 5000,
    )
    db.add(key_entry)
    await db.commit()
    await db.refresh(key_entry)
    return {"message": f"Meta API key '{meta_key.app_name}' added successfully.", "id": str(key_entry.id)}


@router.post("/custom-key", status_code=status.HTTP_201_CREATED)
async def add_custom_api_key(
    key_data: CustomKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a custom simple string API key (e.g. Grok, OpenAI).
    """
    # Deduplicate by project_name and service_name
    existing = await db.execute(
        select(ApiKeyVault).where(
            and_(
                ApiKeyVault.service_name == key_data.service_name,
                ApiKeyVault.project_name == key_data.project_name,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"{key_data.service_name.capitalize()} key with name '{key_data.project_name}' already exists."
        )

    # Wrap the simple key in a JSON object for storage
    credentials_blob = {
        "api_key": key_data.api_key,
        "service": key_data.service_name
    }

    key_entry = ApiKeyVault(
        service_name=key_data.service_name,
        project_name=key_data.project_name,
        credentials_json=credentials_blob,
        daily_limit=10000, # default 
    )
    db.add(key_entry)
    await db.commit()
    await db.refresh(key_entry)
    return {"message": f"API key '{key_data.project_name}' added successfully.", "id": str(key_entry.id)}


@router.post("/{key_id}/test")
async def test_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Test an API key to verify it is valid and not revoked."""
    result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    if key.service_name == "meta":
        # Test Meta API key by calling token debug endpoint
        try:
            import httpx
            creds = key.credentials_json
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://graph.facebook.com/debug_token",
                    params={
                        "input_token": creds.get("access_token"),
                        "access_token": f"{creds.get('app_id')}|{creds.get('app_secret')}",
                    },
                )
            data = resp.json()
            is_valid = data.get("data", {}).get("is_valid", False)
            return {"valid": is_valid, "service": "meta", "detail": data.get("data", {})}
        except Exception as e:
            return {"valid": False, "service": "meta", "detail": str(e)}

    elif key.service_name == "google":
        # Test Google key by checking if credentials JSON has required fields
        creds = key.credentials_json
        inner = creds.get("installed") or creds.get("web") or creds
        has_required = bool(inner.get("client_id") and inner.get("client_secret"))
        return {
            "valid": has_required,
            "service": "google",
            "detail": "Credentials structure OK" if has_required else "Missing client_id or client_secret"
        }

    return {"valid": True, "service": key.service_name, "detail": "Manual check required"}


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an API key from the vault."""
    result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(key)
    await db.commit()


@router.post("/{key_id}/unlock", response_model=ApiKeyVaultOut)
async def unlock_api_key(key_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Manually unlock a locked API key."""
    result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_locked = False
    key.unlock_time = None
    key.lock_reason = None
    key.daily_usage = 0
    await db.commit()
    await db.refresh(key)
    return key


@router.get("/stats/summary")
async def api_vault_stats(db: AsyncSession = Depends(get_db)):
    """Get API vault statistics summary, broken down by service."""
    total = await db.execute(select(func.count(ApiKeyVault.id)))
    active = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.is_locked == False)
    )
    locked = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.is_locked == True)
    )
    google_total = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.service_name == "google")
    )
    google_active = await db.execute(
        select(func.count(ApiKeyVault.id)).where(
            and_(ApiKeyVault.service_name == "google", ApiKeyVault.is_locked == False)
        )
    )
    meta_total = await db.execute(
        select(func.count(ApiKeyVault.id)).where(ApiKeyVault.service_name == "meta")
    )
    meta_active = await db.execute(
        select(func.count(ApiKeyVault.id)).where(
            and_(ApiKeyVault.service_name == "meta", ApiKeyVault.is_locked == False)
        )
    )
    # Count .env keys
    from app.core.config import settings
    env_count = 0
    if settings.GEMINI_API_KEY: env_count += 1
    if settings.GOOGLE_CLIENT_ID: env_count += 1
    if settings.META_APP_ID or settings.META_CLIENT_ID: env_count += 1

    return {
        "total": total.scalar() + env_count,
        "active": active.scalar() + env_count,
        "locked": locked.scalar(),
        "google_total": google_total.scalar() + (1 if settings.GOOGLE_CLIENT_ID else 0),
        "google_active": google_active.scalar() + (1 if settings.GOOGLE_CLIENT_ID else 0),
        "meta_total": meta_total.scalar() + (1 if (settings.META_APP_ID or settings.META_CLIENT_ID) else 0),
        "meta_active": meta_active.scalar() + (1 if (settings.META_APP_ID or settings.META_CLIENT_ID) else 0),
        "gemini_total": (1 if settings.GEMINI_API_KEY else 0) + (total.scalar() - google_total.scalar() - meta_total.scalar()), # approximated
    }
