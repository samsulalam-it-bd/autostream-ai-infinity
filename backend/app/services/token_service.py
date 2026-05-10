"""
token_service.py — Central Google OAuth Token Management

All workers, routers, and services should use `get_valid_google_credentials()`
instead of calling decrypt_token / refresh_access_token in scattered locations.

This guarantees:
  - Token is refreshed proactively when it's about to expire (within 5 min buffer)
  - DB is always updated atomically after a successful refresh
  - Distinct error handling for revoked vs. network-error vs. expired-test-app tokens
  - Logs are informative and traceable
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

# Buffer: if token expires within 5 minutes, refresh it preemptively
EXPIRY_BUFFER_SECONDS = 300

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    # Needed for deleting/moving source videos in Drive after publish.
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

    Strategy:
      1. Decrypt stored access_token and refresh_token.
      2. Build a Credentials object with full context (client_id, client_secret, etc.)
      3. If the token is expired or will expire within EXPIRY_BUFFER_SECONDS, refresh it.
      4. On refresh: update DB with new access_token + expiry + (new refresh_token if provided).
      5. On invalid_grant / revoked: set account.status = "REVOKED", raise TokenRefreshError.
      6. On network error: raise TokenRefreshError with revoked=False (temporary, can retry).

    Raises:
      TokenRefreshError: If the token cannot be refreshed and the account should be marked.
    """
    from app.models.models import AccountStatusEnum

    access_token = decrypt_token(account.encrypted_access_token or "")
    refresh_token = decrypt_token(account.encrypted_refresh_token or "")

    # expiry from DB (may be None for old accounts that predate this fix)
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
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=YOUTUBE_SCOPES,
        expiry=expiry,
    )

    # Determine if we need to refresh
    now_utc = datetime.utcnow()
    needs_refresh = (
        not access_token
        or (expiry is not None and expiry <= now_utc + timedelta(seconds=EXPIRY_BUFFER_SECONDS))
        or (expiry is None and not access_token)  # old account, no expiry recorded
    )

    if not needs_refresh:
        logger.debug(f"[TokenService] Token for '{account.channel_name}' is valid until {expiry}.")
        return creds

    # ── Refresh flow ────────────────────────────────────────────────────────
    if not refresh_token:
        # No refresh token stored → cannot renew, must re-authenticate
        account.status = AccountStatusEnum.EXPIRED
        await db.commit()
        raise TokenRefreshError(
            f"No refresh_token stored for account '{account.channel_name}'. "
            "User must re-authenticate via OAuth.",
            revoked=False,
        )

    logger.info(f"[TokenService] Refreshing access token for '{account.channel_name}'...")

    try:
        import asyncio
        # google-auth's Request is synchronous; run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: creds.refresh(Request()))

    except RefreshError as e:
        error_str = str(e).lower()
        is_revoked = "invalid_grant" in error_str or "token has been expired or revoked" in error_str
        if is_revoked:
            logger.warning(
                f"[TokenService] Refresh token REVOKED for '{account.channel_name}': {e}"
            )
            account.status = AccountStatusEnum.EXPIRED  # Maps to "re-auth needed"
            await db.commit()
            raise TokenRefreshError(
                f"Refresh token revoked/invalid for account '{account.channel_name}'. "
                "User must re-authenticate via OAuth.",
                revoked=True,
            ) from e
        else:
            logger.error(f"[TokenService] RefreshError (non-revoke) for '{account.channel_name}': {e}")
            raise TokenRefreshError(str(e), revoked=False) from e

    except TransportError as e:
        logger.error(f"[TokenService] Network error refreshing token for '{account.channel_name}': {e}")
        raise TokenRefreshError(f"Network error during token refresh: {e}", revoked=False) from e

    except Exception as e:
        logger.error(f"[TokenService] Unexpected error refreshing token for '{account.channel_name}': {e}")
        raise TokenRefreshError(str(e), revoked=False) from e

    # ── Persist refreshed token to DB ─────────────────────────────────────
    new_token = creds.token
    new_expiry = creds.expiry  # datetime returned by google-auth (UTC, naive)
    # Make timezone-aware if naive
    if new_expiry and new_expiry.tzinfo is None:
        new_expiry = new_expiry.replace(tzinfo=timezone.utc)

    # Google may rotate the refresh_token; use the new one if provided
    new_refresh = creds.refresh_token or refresh_token

    account.encrypted_access_token = encrypt_token(new_token)
    account.encrypted_refresh_token = encrypt_token(new_refresh)
    account.token_expiry = new_expiry
    account.status = AccountStatusEnum.ACTIVE
    await db.commit()

    logger.info(
        f"[TokenService] Token refreshed for '{account.channel_name}'. "
        f"New expiry: {new_expiry}"
    )
    return creds
