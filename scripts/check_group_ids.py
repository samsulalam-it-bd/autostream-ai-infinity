import asyncio
import sys

sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(UploadSchedule).limit(5))
        schedules = res.scalars().all()
        for s in schedules:
            print(f"ID: {s.id}")
            print(f"  Account ID: {s.account_id}")
            print(f"  Target Group ID: {s.target_group_id}")
            print(f"  Scheduled Time: {s.scheduled_time}")

if __name__ == "__main__":
    asyncio.run(main())
