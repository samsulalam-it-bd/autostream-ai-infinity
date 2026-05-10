import asyncio
import logging
import os
import httpx

import sys
from pathlib import Path

# Fix python path for local imports
sys.path.append(str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.models.models import Account, AccountStatusEnum, ApiKeyVault, PlatformEnum
from app.core.security import encrypt_token
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inject_meta_accounts():
    meta_user_access_token = os.environ.get("META_USER_ACCESS_TOKEN") or os.environ.get("META_ACCESS_TOKEN") or ""
    meta_app_id = os.environ.get("META_APP_ID") or os.environ.get("META_CLIENT_ID") or ""
    meta_app_secret = os.environ.get("META_APP_SECRET") or os.environ.get("META_CLIENT_SECRET") or ""
    if not meta_user_access_token:
        raise SystemExit("META_USER_ACCESS_TOKEN is missing")

    async with httpx.AsyncClient() as client:
        # Fetch managed Pages
        try:
            pages_resp = await client.get(
                "https://graph.facebook.com/v19.0/me/accounts",
                params={
                    "access_token": meta_user_access_token,
                    "fields": "id,name,access_token,instagram_business_account"
                }
            )
            pages_resp.raise_for_status()
            pages_data = pages_resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch Meta pages using token: {e}")
            return
            
    async with AsyncSessionLocal() as db:
        accounts_created = 0
        accounts_updated = 0
        
        # We also want to save tracking of the provided token in ApiKeyVault for completeness
        existing_key = await db.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == "meta"))
        existing_key = existing_key.scalar_one_or_none()
        credentials_blob = {
            "app_id": meta_app_id,
            "app_secret": meta_app_secret,
            "access_token": meta_user_access_token,
            "service": "meta",
        }
        if existing_key:
            existing_key.credentials_json = credentials_blob
            accounts_updated += 1
            logger.info("Updated Meta ApiKeyVault tracking.")
        else:
            new_key = ApiKeyVault(
                service_name="meta",
                project_name="AutoStream Meta App",
                credentials_json=credentials_blob,
                daily_limit=5000,
            )
            db.add(new_key)
            logger.info("Added Meta ApiKeyVault tracking.")

        for page in pages_data.get("data", []):
            page_id = page.get("id")
            page_name = page.get("name")
            page_token = page.get("access_token")

            # FB Page Account
            existing_fb_result = await db.execute(
                select(Account).where(Account.channel_id == page_id, Account.platform == PlatformEnum.FACEBOOK)
            )
            existing_fb = existing_fb_result.scalar_one_or_none()
            if existing_fb:
                existing_fb.encrypted_access_token = encrypt_token(page_token)
                existing_fb.channel_name = f"{page_name} (Facebook)"
                existing_fb.status = AccountStatusEnum.ACTIVE
                accounts_updated += 1
            else:
                fb_account = Account(
                    platform=PlatformEnum.FACEBOOK,
                    channel_name=f"{page_name} (Facebook)",
                    channel_id=page_id,
                    encrypted_access_token=encrypt_token(page_token),
                    status=AccountStatusEnum.ACTIVE,
                )
                db.add(fb_account)
                accounts_created += 1

            # IG Business Account
            ig_account_id = page.get("instagram_business_account", {}).get("id")
            if ig_account_id:
                existing_ig_result = await db.execute(
                    select(Account).where(Account.channel_id == ig_account_id, Account.platform == PlatformEnum.INSTAGRAM)
                )
                existing_ig = existing_ig_result.scalar_one_or_none()
                if existing_ig:
                    existing_ig.encrypted_access_token = encrypt_token(page_token) # IG uses the Page token
                    existing_ig.channel_name = f"{page_name} (Instagram)"
                    existing_ig.status = AccountStatusEnum.ACTIVE
                    accounts_updated += 1
                else:
                    ig_account = Account(
                        platform=PlatformEnum.INSTAGRAM,
                        channel_name=f"{page_name} (Instagram)",
                        channel_id=ig_account_id,
                        encrypted_access_token=encrypt_token(page_token), 
                        status=AccountStatusEnum.ACTIVE,
                    )
                    db.add(ig_account)
                    accounts_created += 1
                    
        await db.commit()
        logger.info(f"Successfully processed Meta insertion. Created: {accounts_created}, Updated: {accounts_updated}")

if __name__ == "__main__":
    asyncio.run(inject_meta_accounts())
