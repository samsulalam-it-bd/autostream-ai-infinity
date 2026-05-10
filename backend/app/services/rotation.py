import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Callable

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ApiKeyVault
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class QuotaExceededException(Exception):
    """Raised when all API keys are exhausted."""
    pass


class ApiRotationService:
    """
    Dynamic API Key Rotation Service.
    Picks a random active key from api_key_vault.
    On 403/quota error, locks that key for 24h and retries with another.
    """

    async def get_active_key(self, service_name: str, db: AsyncSession) -> Optional[ApiKeyVault]:
        """Fetch a random active (non-locked) API key for a given service."""
        now = datetime.now(timezone.utc)

        # First, unlock any keys whose 24h lockout has expired
        result = await db.execute(
            select(ApiKeyVault).where(
                and_(
                    ApiKeyVault.service_name == service_name,
                    ApiKeyVault.is_locked == True,
                    ApiKeyVault.unlock_time <= now,
                )
            )
        )
        expired_locks = result.scalars().all()
        for key in expired_locks:
            key.is_locked = False
            key.unlock_time = None
            key.daily_usage = 0
            key.lock_reason = None
            logger.info(f"Auto-unlocked API key {key.id} for service {service_name}")
        if expired_locks:
            await db.commit()

        # Now fetch all available (non-locked) keys
        result = await db.execute(
            select(ApiKeyVault).where(
                and_(
                    ApiKeyVault.service_name == service_name,
                    ApiKeyVault.is_locked == False,
                )
            )
        )
        available_keys = result.scalars().all()

        if not available_keys:
            return None

        # Pick a random one to distribute load
        return random.choice(available_keys)

    async def lock_key(self, key_id: str, reason: str, db: AsyncSession) -> None:
        """Lock an API key for 24 hours due to quota exhaustion."""
        now = datetime.now(timezone.utc)
        unlock_time = now + timedelta(hours=24)

        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
        key = result.scalar_one_or_none()
        if key:
            key.is_locked = True
            key.unlock_time = unlock_time
            key.lock_reason = reason
            await db.commit()
            logger.warning(f"Locked API key {key_id} until {unlock_time}. Reason: {reason}")

    async def increment_usage(self, key_id: str, db: AsyncSession) -> None:
        """Increment daily usage counter for an API key."""
        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == key_id))
        key = result.scalar_one_or_none()
        if key:
            key.daily_usage = (key.daily_usage or 0) + 1
            await db.commit()

    async def execute_with_rotation(
        self,
        service_name: str,
        operation: Callable,
        max_retries: int = 5,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an API operation with automatic key rotation on quota errors.
        
        :param service_name: The service to look up keys for (e.g., 'google').
        :param operation: An async callable that accepts credentials_json as first arg.
        :param max_retries: Max number of keys to try before giving up.
        :param kwargs: Additional keyword arguments to pass to the operation.
        """
        tried_keys = set()

        async with AsyncSessionLocal() as db:
            for attempt in range(max_retries):
                key_entry = await self.get_active_key(service_name, db)

                if not key_entry or key_entry.id in tried_keys:
                    # No more unique keys to try
                    raise QuotaExceededException(
                        f"All API keys for service '{service_name}' are exhausted or locked."
                    )

                tried_keys.add(key_entry.id)

                try:
                    result = await operation(key_entry.credentials_json, **kwargs)
                    await self.increment_usage(str(key_entry.id), db)
                    return result

                except Exception as e:
                    error_str = str(e).lower()
                    # Detect quota exceeded errors (403, quota, rateLimitExceeded)
                    if any(keyword in error_str for keyword in ["403", "quota", "ratelimit", "rate limit", "exceeded"]):
                        logger.warning(
                            f"Quota exceeded on key {key_entry.id} (attempt {attempt + 1}). "
                            f"Locking and rotating to next key."
                        )
                        await self.lock_key(str(key_entry.id), f"Quota error: {str(e)[:200]}", db)
                        # Send Telegram alert
                        from app.services.telegram import send_telegram_alert
                        asyncio.create_task(
                            send_telegram_alert(
                                f"⚠️ API Key Quota Exhausted!\n"
                                f"Service: {service_name}\n"
                                f"Key ID: {key_entry.id}\n"
                                f"Rotating to next available key..."
                            )
                        )
                        continue  # Retry with next key
                    else:
                        # Non-quota error, re-raise
                        raise

            raise QuotaExceededException(
                f"Exceeded max retries ({max_retries}) for service '{service_name}'."
            )


# Global singleton
rotation_service = ApiRotationService()
