import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(Account).where(Account.platform == PlatformEnum.FACEBOOK))
        account = res.scalars().first()
        if not account:
            print("No Facebook account found!")
            return
            
        from app.core.security import decrypt_token
        access_token = decrypt_token(account.encrypted_access_token)
        
        print(f"Facebook account channel name in DB: {account.channel_name}")
        print(f"Facebook Page ID in DB: {account.channel_id}")
        
        # Query /me/accounts to see which pages this token has access to
        url = "https://graph.facebook.com/v20.0/me/accounts"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params={"access_token": access_token})
            print(f"Status of /me/accounts: {resp.status_code}")
            print(f"Response: {resp.text}")
            
            # Query debug_token to see metadata
            debug_url = f"https://graph.facebook.com/debug_token"
            # We can inspect the token itself
            inspect_url = f"https://graph.facebook.com/v20.0/me?fields=id,name"
            r = await client.get(inspect_url, params={"access_token": access_token})
            print(f"Inspect /me: {r.status_code}")
            print(f"Response: {r.text}")

if __name__ == "__main__":
    asyncio.run(main())
