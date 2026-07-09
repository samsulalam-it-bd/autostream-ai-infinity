import asyncio
import sys
from pathlib import Path

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule, SourceVideo, Account

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(
            select(UploadSchedule)
            .order_by(UploadSchedule.created_at.desc())
        )
        schedules = res.scalars().all()
        print(f"Total schedules in DB: {len(schedules)}")
        for sched in schedules[:10]: # Print top 10 most recent
            print(f"- ID: {sched.id}")
            print(f"  Account ID: {sched.account_id}")
            print(f"  Video ID: {sched.video_id}")
            print(f"  Scheduled Time: {sched.scheduled_time}")
            print(f"  Published: {sched.is_published}")
            print(f"  Published URL: {sched.published_url}")
            print(f"  Task ID: {sched.celery_task_id}")
            if sched.error_message:
                print(f"  Error Message: {sched.error_message[:400]}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
