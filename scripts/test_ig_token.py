import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum

async def test_token(platform_name):
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(Account).where(Account.platform == platform_name))
        account = res.scalars().first()
        if not account:
            print(f"No {platform_name} account found!")
            return
            
        from app.core.security import decrypt_token
        access_token = decrypt_token(account.encrypted_access_token)
        
        print(f"\n--- Testing {platform_name.upper()} Token ---")
        print(f"Channel Name in DB: {account.channel_name}")
        print(f"Channel ID in DB: {account.channel_id}")
        
        # Test basic Graph API inspect
        url = "https://graph.facebook.com/v20.0/me"
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Let's try /me
            r = await client.get(url, params={"access_token": access_token})
            print(f"Inspect /me Status: {r.status_code}")
            print(f"Inspect /me Response: {r.text}")
            
            if platform_name == PlatformEnum.FACEBOOK:
                # Page info
                page_url = f"https://graph.facebook.com/v20.0/{account.channel_id}"
                r2 = await client.get(page_url, params={"access_token": access_token})
                print(f"Inspect Page ID Status: {r2.status_code}")
                print(f"Inspect Page ID Response: {r2.text}")
                
            if platform_name == PlatformEnum.INSTAGRAM:
                # Instagram business info
                ig_url = f"https://graph.facebook.com/v20.0/{account.channel_id}"
                r2 = await client.get(ig_url, params={"access_token": access_token, "fields": "username,name"})
                print(f"Inspect IG User Status: {r2.status_code}")
                print(f"Inspect IG User Response: {r2.text}")

async def main():
    await test_token(PlatformEnum.FACEBOOK)
    await test_token(PlatformEnum.INSTAGRAM)

if __name__ == "__main__":
    asyncio.run(main())
