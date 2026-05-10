import asyncio
from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UploadSchedule).order_by(UploadSchedule.scheduled_time.desc()).limit(10))
        schedules = result.scalars().all()
        for s in schedules:
            print(f"ID: {s.id} | Video: {s.video_id} | Account: {s.account_id}")
            print(f"  Published: {s.is_published} | Err: {s.error_message}")
            print(f"  Task ID: {s.celery_task_id}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
