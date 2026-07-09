import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum
from app.services.token_service import get_valid_google_credentials

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(Account).where(Account.platform == PlatformEnum.YOUTUBE))
        account = res.scalars().first()
        if not account:
            print("No YouTube account found!")
            return
            
        print(f"Testing YouTube account: {account.channel_name}")
        try:
            creds = await get_valid_google_credentials(account, db)
            print("YouTube token refresh: SUCCESS")
            print(f"Token: {creds.token[:20]}...")
            
            # Call YouTube channels API to verify access
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true",
                    headers={"Authorization": f"Bearer {creds.token}"}
                )
                print(f"YouTube API Status: {r.status_code}")
                print(f"YouTube Response: {r.text[:500]}")
        except Exception as e:
            print(f"YouTube token failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
