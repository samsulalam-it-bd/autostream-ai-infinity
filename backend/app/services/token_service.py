"""
token_service.py — Central Google OAuth Token Management

All workers, routers, and services should use `get_valid_google_credentials()`
instead of calling decrypt_token / refresh_access_token in scattered locations.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

EXPIRY_BUFFER_SECONDS = 300
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive",
    "openid",
    "email",
    "profile",
]

class TokenRefreshError(Exception):
    """Raised when a token refresh fails permanently (revoked, invalid_grant, etc.)."""
    def __init__(self, message: str, revoked: bool = False):
        super().__init__(message)
        self.revoked = revoked

async def get_valid_google_credentials(account, db) -> Credentials:
    """
    Returns a valid, non-expired Google OAuth Credentials object for the given account.
    Refreshes automatically if expired or near expiry.
    """
    from app.models.models import AccountStatusEnum, ApiKeyVault

    access_token = decrypt_token(account.encrypted_access_token or "")
    refresh_token = decrypt_token(account.encrypted_refresh_token or "")

    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    
    if account.vault_id:
        v_res = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == account.vault_id))
        v_key = v_res.scalar_one_or_none()
        if v_key:
            creds_json = v_key.credentials_json
            inner = creds_json.get("installed") or creds_json.get("web") or creds_json
            client_id = inner.get("client_id")
            client_secret = inner.get("client_secret")

    expiry_db: Optional[datetime] = account.token_expiry
    expiry: Optional[datetime] = None
    if expiry_db is not None:
        if expiry_db.tzinfo is not None:
            expiry = expiry_db.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            expiry = expiry_db

    creds = Credentials(
        token=access_token or None,
        refresh_token=refresh_token or None,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=YOUTUBE_SCOPES,
        expiry=expiry,
    )

    now_utc = datetime.utcnow()
    needs_refresh = (
        not access_token
        or (expiry is not None and expiry <= now_utc + timedelta(seconds=EXPIRY_BUFFER_SECONDS))
    )

    if not needs_refresh:
        return creds

    if not refresh_token:
        logger.warning(f"No refresh_token for '{account.channel_name}'. Status set to EXPIRED.")
        account.status = AccountStatusEnum.EXPIRED
        await db.commit()
        raise TokenRefreshError(f"No refresh_token stored for '{account.channel_name}'")

    logger.info(f"[TokenService] Refreshing access token for '{account.channel_name}'...")

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: creds.refresh(Request()))

    except RefreshError as e:
        error_str = str(e).lower()
        is_revoked = "invalid_grant" in error_str or "token has been expired or revoked" in error_str
        if is_revoked:
            account.status = AccountStatusEnum.EXPIRED
            await db.commit()
            raise TokenRefreshError(f"Token revoked for '{account.channel_name}'", revoked=True) from e
        else:
            raise TokenRefreshError(str(e), revoked=False) from e

    except TransportError as e:
        raise TokenRefreshError(f"Network error during token refresh: {e}", revoked=False) from e

    except Exception as e:
        raise TokenRefreshError(str(e), revoked=False) from e

    # Persist
    new_token = creds.token
    new_expiry = creds.expiry
    if new_expiry and new_expiry.tzinfo is None:
        new_expiry = new_expiry.replace(tzinfo=timezone.utc)

    new_refresh = creds.refresh_token or refresh_token

    account.encrypted_access_token = encrypt_token(new_token)
    account.encrypted_refresh_token = encrypt_token(new_refresh)
    account.token_expiry = new_expiry
    account.status = AccountStatusEnum.ACTIVE
    await db.commit()

    logger.info(f"[TokenService] Token refreshed for '{account.channel_name}'.")
    return creds
