from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """
    Get a Fernet instance using the configured FERNET_KEY.

    IMPORTANT: FERNET_KEY MUST be set in the environment.
    If it is empty, this function raises a RuntimeError at startup,
    which prevents the silent bug where a random key is generated
    per-process, making tokens encrypted by one process unreadable
    by another (or after a restart).

    Generate a valid key with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = settings.FERNET_KEY
    if not key:
        raise RuntimeError(
            "FERNET_KEY is not set in the environment. "
            "All OAuth tokens will be unreadable after a restart. "
            "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and set it in your .env file."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str) -> str:
    """Encrypt an OAuth token using Fernet symmetric encryption."""
    if not token:
        return ""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a Fernet-encrypted token.
    Returns '' on failure (e.g., corrupted data or wrong key).
    """
    if not encrypted_token:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_token.encode()).decode()
    except (InvalidToken, Exception) as e:
        logger.warning(f"Failed to decrypt token: {e}")
        return ""


async def refresh_access_token(account, db=None) -> str:
    """
    DEPRECATED: Use token_service.get_valid_google_credentials() instead.

    Exchange the stored refresh_token for a new access_token via Google OAuth.
    Updates the account's encrypted tokens and token_expiry in-place.
    Caller must commit the DB session.

    Returns the new access_token string, or '' on failure.
    """
    import httpx
    from datetime import datetime, timezone, timedelta

    refresh_token = decrypt_token(account.encrypted_refresh_token or "")
    if not refresh_token:
        logger.warning(f"No refresh token available for account '{account.channel_name}'")
        return ""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        new_access_token = token_data.get("access_token", "")
        # Use expires_in from response instead of hardcoding 3600
        expires_in = int(token_data.get("expires_in", 3600))
        # Google may issue a new refresh_token (rare but possible)
        new_refresh_token = token_data.get("refresh_token", refresh_token)

        if new_access_token:
            account.encrypted_access_token = encrypt_token(new_access_token)
            account.encrypted_refresh_token = encrypt_token(new_refresh_token)
            account.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            logger.info(
                f"Refreshed access token for account '{account.channel_name}'. "
                f"Expires in {expires_in}s."
            )
            return new_access_token

    except httpx.HTTPStatusError as e:
        error_body = e.response.text.lower()
        logger.error(
            f"Token refresh HTTP {e.response.status_code} for '{account.channel_name}': {error_body}"
        )
        # Mark as expired for permanent failures (revoked, invalid_grant)
        if e.response.status_code in (400, 401) and "invalid_grant" in error_body:
            from app.models.models import AccountStatusEnum
            account.status = AccountStatusEnum.EXPIRED
            logger.warning(
                f"Account '{account.channel_name}' marked EXPIRED due to invalid_grant. "
                "Re-authentication required."
            )
    except Exception as e:
        logger.error(f"Token refresh failed for '{account.channel_name}': {e}")

    return ""
