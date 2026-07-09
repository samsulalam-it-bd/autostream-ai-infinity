import asyncio
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(UploadSchedule))
        schedules = res.scalars().all()
        print(f"Total schedules in DB: {len(schedules)}")
        for s in schedules:
            print(f"ID: {s.id}")
            print(f"  Account ID: {s.account_id}")
            print(f"  Scheduled Time: {s.scheduled_time}")
            print(f"  Is Published: {s.is_published}")
            print(f"  Error Message: {s.error_message}")
            print(f"  Retry Count: {s.retry_count}")

if __name__ == "__main__":
    asyncio.run(main())
