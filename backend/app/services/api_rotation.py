import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import ApiKeyVault

logger = logging.getLogger(__name__)

class ApiRotationError(Exception):
    pass

# Global registry for system-level key failures (reset on restart)
# Maps virtual_id -> {"locked_until": datetime, "reason": str}
SYSTEM_KEY_STATUS = {}

async def get_active_api_key(service_name: str, db: AsyncSession) -> Optional[ApiKeyVault]:
    """
    Returns the best available API key for a service.
    Criteria: Not locked, has daily limit remaining, lowest usage first.
    """
    # 1. First, find all keys for the service that are not locked
    # and have usage below the limit
    query = select(ApiKeyVault).where(
        and_(
            ApiKeyVault.service_name == service_name,
            ApiKeyVault.is_locked == False,
            ApiKeyVault.daily_usage < ApiKeyVault.daily_limit
        )
    ).order_by(ApiKeyVault.daily_usage.asc()) # Pick the least used one to balance load

    result = await db.execute(query)
    key = result.scalars().first()

    if not key:
        logger.warning(f"No active API keys available for service: {service_name}")
        return None
    
    return key

async def report_quota_exceeded(key_id: str, db: AsyncSession, reason: str = "Quota Exceeded"):
    """
    Locks an API key when a quota error is encountered.
    Typically locks it for 24 hours.
    """
    if str(key_id).startswith("00000000-0000-0000-0000-00000000000"):
        SYSTEM_KEY_STATUS[str(key_id)] = {
            "locked_until": datetime.now(timezone.utc) + timedelta(hours=24),
            "reason": reason
        }
        logger.info(f"System Key {key_id} marked as locked globally: {reason}")
        return

    result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
    key = result.scalar_one_or_none()
    
    if key:
        key.is_locked = True
        key.unlock_time = datetime.now(timezone.utc) + timedelta(hours=24)
        key.lock_reason = reason
        await db.commit()
        logger.info(f"API Key {key_id} locked due to: {reason}")

async def increment_usage(key_id: str, db: AsyncSession, amount: int = 1):
    """Increments the daily usage counter for a key."""
    result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
    key = result.scalar_one_or_none()
    
    if key:
        key.daily_usage += amount
        await db.commit()

async def get_google_client_config(db: AsyncSession) -> Optional[dict]:
    """Returns an active Google Client ID/Secret from the vault."""
    key = await get_active_api_key("google", db)
    if not key:
        return None
    
    creds = key.credentials_json
    inner = creds.get("installed") or creds.get("web") or creds
    return {
        "client_id": inner.get("client_id"),
        "client_secret": inner.get("client_secret"),
        "vault_id": key.id
    }

async def get_meta_app_config(db: AsyncSession) -> Optional[dict]:
    """Returns an active Meta App ID/Secret from the vault."""
    key = await get_active_api_key("meta", db)
    if not key:
        return None
    
    creds = key.credentials_json
    return {
        "app_id": creds.get("app_id"),
        "app_secret": creds.get("app_secret"),
        "access_token": creds.get("access_token"),
        "vault_id": key.id
    }

async def reset_daily_quotas(db: AsyncSession):
    """
    Resets all daily usage counters.
    This should be called by a cron/worker once a day at midnight UTC.
    """
    from sqlalchemy import update
    await db.execute(
        update(ApiKeyVault).values(daily_usage=0)
    )
    # Also unlock keys whose unlock_time has passed
    now = datetime.now(timezone.utc)
    await db.execute(
        update(ApiKeyVault)
        .where(and_(ApiKeyVault.is_locked == True, ApiKeyVault.unlock_time <= now))
        .values(is_locked=False, unlock_time=None, lock_reason=None)
    )
    await db.commit()
    logger.info("Daily API quotas reset and eligible keys unlocked.")
