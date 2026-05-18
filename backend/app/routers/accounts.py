import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Account, ChannelGroup, AccountStatusEnum, PlatformEnum
from app.schemas import AccountCreate, AccountOut, AccountUpdate, ChannelGroupCreate, ChannelGroupOut
from app.core.security import encrypt_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["Accounts"])


# ── Channel Groups ─────────────────────────────────────────────────────────
@router.get("/groups", response_model=List[ChannelGroupOut])
async def list_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChannelGroup).order_by(ChannelGroup.name))
    return result.scalars().all()


@router.post("/groups", response_model=ChannelGroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(group_in: ChannelGroupCreate, db: AsyncSession = Depends(get_db)):
    group = ChannelGroup(**group_in.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChannelGroup).where(ChannelGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()


# ── Accounts ───────────────────────────────────────────────────────────────
@router.get("/", response_model=List[AccountOut])
async def list_accounts(
    platform: Optional[PlatformEnum] = None,
    group_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Account).order_by(Account.created_at.desc())
    if platform:
        query = query.where(Account.platform == platform)
    if group_id:
        query = query.where(Account.group_id == group_id)
    result = await db.execute(query)
    accounts = result.scalars().all()

    from app.models.models import UploadSchedule
    from sqlalchemy import func
    enriched = []
    now = datetime.now(timezone.utc)
    for acc in accounts:
        # Published count
        pub_res = await db.execute(select(func.count(UploadSchedule.id)).where(
            UploadSchedule.account_id == acc.id, UploadSchedule.is_published == True
        ))
        # Pending count
        pen_res = await db.execute(select(func.count(UploadSchedule.id)).where(
            UploadSchedule.account_id == acc.id, UploadSchedule.is_published == False, UploadSchedule.error_message == None, UploadSchedule.scheduled_time >= now
        ))
        # Failed count
        fail_res = await db.execute(select(func.count(UploadSchedule.id)).where(
            UploadSchedule.account_id == acc.id, UploadSchedule.error_message != None
        ))
        # Queue (Total pending regardless of time)
        que_res = await db.execute(select(func.count(UploadSchedule.id)).where(
            UploadSchedule.account_id == acc.id, UploadSchedule.is_published == False
        ))

        acc.stats = {
            'published': pub_res.scalar() or 0,
            'pending': pen_res.scalar() or 0,
            'failed': fail_res.scalar() or 0,
            'queue': que_res.scalar() or 0
        }
        enriched.append(acc)
    return enriched


@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(account_in: AccountCreate, db: AsyncSession = Depends(get_db)):
    """Add a new account. Tokens are Fernet-encrypted before storage."""
    encrypted_access = encrypt_token(account_in.access_token)
    encrypted_refresh = encrypt_token(account_in.refresh_token or "")

    data = account_in.model_dump(exclude={"access_token", "refresh_token"})
    account = Account(
        **data,
        encrypted_access_token=encrypted_access,
        encrypted_refresh_token=encrypted_refresh,
        status=AccountStatusEnum.ACTIVE,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(account_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: uuid.UUID,
    update_in: AccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = update_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    await db.commit()


# ── OAuth Redirect Stubs ───────────────────────────────────────────────────
@router.get("/oauth/google/init")
async def google_oauth_init(vault_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """Returns the Google OAuth authorization URL. Picks an active project from the vault for rotation."""
    from app.core.config import settings
    from app.services.api_rotation import get_google_client_config
    import urllib.parse
    
    # Rotation: Try to get a client from the vault
    if vault_id:
        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == vault_id))
        key = result.scalar_one_or_none()
        if not key: raise HTTPException(status_code=404, detail="Vault project not found")
        creds = key.credentials_json
        inner = creds.get("installed") or creds.get("web") or creds
        client_id = inner.get("client_id")
        v_id = key.id
    else:
        config = await get_google_client_config(db)
        if config:
            client_id = config["client_id"]
            v_id = config["vault_id"]
        else:
            # Fallback to .env if vault is empty
            client_id = settings.GOOGLE_CLIENT_ID
            v_id = None

    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
        "openid", "email", "profile",
    ]
    params = {
        "client_id": client_id,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": str(v_id) if v_id else "env"
    }
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    url = f"{base}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url}


@router.get("/oauth/google/callback")
async def google_oauth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback. Uses the vault_id from state to exchange tokens."""
    import httpx
    from app.core.config import settings

    # Resolve Client ID/Secret from state
    if state and state != "env":
        v_id = uuid.UUID(state)
        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == v_id))
        key = result.scalar_one_or_none()
        if not key: raise HTTPException(status_code=400, detail="Invalid vault state")
        creds = key.credentials_json
        inner = creds.get("installed") or creds.get("web") or creds
        client_id = inner.get("client_id")
        client_secret = inner.get("client_secret")
        vault_id = v_id
    else:
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        vault_id = None

    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        token_data = resp.json()

    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = int(token_data.get("expires_in", 3600))
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Get channel info
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        channel_resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
            headers=headers,
        )
    channel_data = channel_resp.json() if channel_resp.status_code == 200 else {}
    channel_items = channel_data.get("items", [{}])
    snippet = channel_items[0].get("snippet", {}) if channel_items else {}
    stats = channel_items[0].get("statistics", {}) if channel_items else {}

    channel_name = snippet.get("title", "YouTube Channel")
    channel_id = channel_items[0].get("id", "") if channel_items else ""
    avatar_url = snippet.get("thumbnails", {}).get("default", {}).get("url")
    subscribers = int(stats.get("subscriberCount", 0))

    # Check existing
    existing_result = await db.execute(
        select(Account).where(Account.channel_id == channel_id, Account.platform == PlatformEnum.YOUTUBE)
    )
    existing_account = existing_result.scalar_one_or_none()

    if existing_account:
        existing_account.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            existing_account.encrypted_refresh_token = encrypt_token(refresh_token)
        existing_account.token_expiry = token_expiry
        existing_account.status = AccountStatusEnum.ACTIVE
        existing_account.subscriber_count = subscribers
        existing_account.avatar_url = avatar_url
        existing_account.vault_id = vault_id
    else:
        account = Account(
            platform=PlatformEnum.YOUTUBE,
            channel_name=channel_name,
            channel_id=channel_id,
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token),
            token_expiry=token_expiry,
            avatar_url=avatar_url,
            subscriber_count=subscribers,
            status=AccountStatusEnum.ACTIVE,
            vault_id=vault_id
        )
        db.add(account)

    await db.commit()
    from fastapi.responses import RedirectResponse
    from app.core.config import settings as _settings
    return RedirectResponse(url=f"{_settings.FRONTEND_URL}/accounts?success=true&platform=youtube")


@router.get("/oauth/meta/init")
async def meta_oauth_init(vault_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    """Returns the Meta OAuth authorization URL. Picks an active app from the vault for rotation."""
    from app.core.config import settings
    from app.services.api_rotation import get_meta_app_config
    import urllib.parse
    
    if vault_id:
        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == vault_id))
        key = result.scalar_one_or_none()
        if not key: raise HTTPException(status_code=404, detail="Vault app not found")
        client_id = key.credentials_json.get("app_id")
        v_id = key.id
    else:
        config = await get_meta_app_config(db)
        if config:
            client_id = config["app_id"]
            v_id = config["vault_id"]
        else:
            client_id = settings.META_CLIENT_ID
            v_id = None

    scopes = [s.strip() for s in (settings.META_SCOPES or "").split(",") if s.strip()]
    if not scopes:
        scopes = ["public_profile", "pages_show_list", "pages_read_engagement", "pages_manage_posts"]
    
    params = {
        "client_id": client_id,
        "redirect_uri": settings.META_REDIRECT_URI,
        "response_type": "code",
        "auth_type": "rerequest",
        "scope": ",".join(scopes),
        "state": str(v_id) if v_id else "env"
    }
    base = "https://www.facebook.com/v19.0/dialog/oauth"
    url = f"{base}?{urllib.parse.urlencode(params)}"
    return {"auth_url": url}


@router.get("/oauth/meta/callback")
async def meta_oauth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handle Meta OAuth callback. Uses the vault_id from state to exchange tokens."""
    import httpx
    from app.core.config import settings
    from fastapi.responses import RedirectResponse

    # Resolve
    if state and state != "env":
        v_id = uuid.UUID(state)
        result = await db.execute(select(ApiKeyVault).where(ApiKeyVault.id == v_id))
        key = result.scalar_one_or_none()
        if not key: raise HTTPException(status_code=400, detail="Invalid vault state")
        client_id = key.credentials_json.get("app_id")
        client_secret = key.credentials_json.get("app_secret")
        vault_id = v_id
    else:
        client_id = settings.META_CLIENT_ID
        client_secret = settings.META_CLIENT_SECRET
        vault_id = None

    # 1. Exchange code
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    async with httpx.AsyncClient() as client:
        resp = await client.get(token_url, params={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": settings.META_REDIRECT_URI,
            "code": code,
        })
        resp.raise_for_status()
        short_lived_token = resp.json().get("access_token")

    # 2. Long-lived token
    async with httpx.AsyncClient() as client:
        ll_resp = await client.get(token_url, params={
            "grant_type": "fb_exchange_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "fb_exchange_token": short_lived_token,
        })
        long_lived_token = ll_resp.json().get("access_token", short_lived_token)

    # 3. Fetch managed Pages (which includes FB Pages and linked IG Accounts)
    async with httpx.AsyncClient() as client:
        pages_resp = await client.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={
                "access_token": long_lived_token,
                # Depending on account type / API behavior, the IG link might appear
                # under `instagram_business_account` or `connected_instagram_account`.
                "fields": "id,name,access_token,instagram_business_account{id,username},connected_instagram_account{id,username}"
            }
        )
        pages_data = pages_resp.json()
        def _redact_tokens(obj):
            if isinstance(obj, dict):
                out = {}
                for k, v in obj.items():
                    if str(k).lower() in {"access_token", "token"}:
                        out[k] = "***"
                    else:
                        out[k] = _redact_tokens(v)
                return out
            if isinstance(obj, list):
                return [_redact_tokens(x) for x in obj]
            return obj

        safe_pages_data = _redact_tokens(pages_data)
        logger.info(f"--- DEBUG META GRAPH API PAGES DATA --- : {safe_pages_data}")
        
    from app.models.models import SystemLog
    db.add(SystemLog(
        level="DEBUG",
        source="meta_oauth_callback",
        message="Raw pages_data from Meta API",
        extra_data=safe_pages_data
    ))

    # Create an account for the primary page (for demo, just picking the first one)
    # In a full implementation, you would list these to the user to select.
    accounts_created = 0
    accounts_updated = 0
    for page in pages_data.get("data", []):
        page_id = page.get("id")
        page_name = page.get("name")
        page_token = page.get("access_token")

        # Check if Facebook Page Account already exists
        existing_fb_result = await db.execute(
            select(Account).where(Account.channel_id == page_id, Account.platform == PlatformEnum.FACEBOOK)
        )
        existing_fb = existing_fb_result.scalar_one_or_none()
        
        if existing_fb:
            existing_fb.encrypted_access_token = encrypt_token(page_token)
            existing_fb.status = AccountStatusEnum.ACTIVE
            accounts_updated += 1
        else:
            # Create Facebook Page Account
            fb_account = Account(
                platform=PlatformEnum.FACEBOOK,
                channel_name=f"{page_name} (Facebook)",
                channel_id=page_id,
                encrypted_access_token=encrypt_token(page_token),
                status=AccountStatusEnum.ACTIVE,
            )
            db.add(fb_account)
            accounts_created += 1

        # Safely parse instagram_business_account to prevent NoneType error
        ig_account_id = None
        ig_username = None

        ig_obj = page.get("instagram_business_account")
        if not isinstance(ig_obj, dict):
            ig_obj = page.get("connected_instagram_account")

        if isinstance(ig_obj, dict):
            ig_account_id = ig_obj.get("id")
            ig_username = ig_obj.get("username")
            
        if ig_account_id:
            existing_ig_result = await db.execute(
                select(Account).where(Account.channel_id == ig_account_id, Account.platform == PlatformEnum.INSTAGRAM)
            )
            existing_ig = existing_ig_result.scalar_one_or_none()
            
            ig_display_name = f"@{ig_username} (IG)" if ig_username else f"{page_name} (Instagram)"
            
            if existing_ig:
                existing_ig.encrypted_access_token = encrypt_token(page_token)
                existing_ig.status = AccountStatusEnum.ACTIVE
                # Update username if it wasn't there before
                existing_ig.channel_name = ig_display_name
                accounts_updated += 1
            else:
                ig_account = Account(
                    platform=PlatformEnum.INSTAGRAM,
                    channel_name=ig_display_name,
                    channel_id=ig_account_id,
                    encrypted_access_token=encrypt_token(page_token), # IG uses the Page token
                    status=AccountStatusEnum.ACTIVE,
                )
                db.add(ig_account)
                accounts_created += 1

    await db.commit()

    from app.core.config import settings as _settings
    return RedirectResponse(url=f"{_settings.FRONTEND_URL}/accounts?success=true&created={accounts_created}")


# ── Manual Token Refresh ───────────────────────────────────────────────────
@router.post("/{account_id}/refresh-token")
async def manual_refresh_token(account_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger a token refresh for a YouTube/Google account.
    Called by the frontend when a user clicks 'Refresh Token' on an account card.
    Uses the central token_service for consistent refresh logic.
    """
    from app.services.token_service import get_valid_google_credentials, TokenRefreshError

    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.platform != PlatformEnum.YOUTUBE:
        raise HTTPException(
            status_code=400,
            detail="Token refresh is only supported for YouTube/Google accounts."
        )

    try:
        await get_valid_google_credentials(account, db)
        return {
            "success": True,
            "message": f"Token refreshed successfully for '{account.channel_name}'.",
            "token_expiry": account.token_expiry.isoformat() if account.token_expiry else None,
        }
    except TokenRefreshError as e:
        status_msg = "REVOKED — re-authentication required" if e.revoked else "Refresh failed"
        raise HTTPException(
            status_code=401 if e.revoked else 503,
            detail=f"{status_msg}: {str(e)}"
        )

@router.get("/debug/meta-logs")
async def get_meta_debug_logs(db: AsyncSession = Depends(get_db)):
    """Fetch the recent Meta OAuth API responses logged to the DB for debugging."""
    from app.core.config import settings
    from app.models.models import SystemLog
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Not available when DEBUG=false")
    # Need to query the latest ones
    from sqlalchemy import select
    result = await db.execute(select(SystemLog).where(SystemLog.source == "meta_oauth_callback").order_by(SystemLog.created_at.desc()).limit(5))
    logs = result.scalars().all()
    def _redact_tokens(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if str(k).lower() in {"access_token", "token"}:
                    out[k] = "***"
                else:
                    out[k] = _redact_tokens(v)
            return out
        if isinstance(obj, list):
            return [_redact_tokens(x) for x in obj]
        return obj

    return [{"created_at": str(log.created_at), "data": _redact_tokens(log.extra_data)} for log in logs]
