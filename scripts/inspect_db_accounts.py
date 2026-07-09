import asyncio
import sys

sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Account))
        accounts = res.scalars().all()
        print(f"Total accounts in DB: {len(accounts)}")
        for a in accounts:
            print(f"ID: {a.id}")
            print(f"  Channel Name: {a.channel_name}")
            print(f"  Platform: {a.platform}")
            print(f"  Group ID: {a.group_id}")

if __name__ == "__main__":
    asyncio.run(main())
