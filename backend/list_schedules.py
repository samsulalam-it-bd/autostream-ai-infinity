import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import UploadSchedule, Account

async def main():
    async with AsyncSessionLocal() as session:
        r = await session.execute(select(UploadSchedule))
        schedules = r.scalars().all()
        print(f"Total schedules in DB: {len(schedules)}")
        for s in schedules:
            acc_res = await session.execute(select(Account).where(Account.id == s.account_id))
            acc = acc_res.scalar_one_or_none()
            print(f"Schedule ID: {s.id} | Account: {acc.channel_name if acc else 'None'} ({acc.platform if acc else 'None'}) | Scheduled Time: {s.scheduled_time} | Published: {s.is_published} | Task ID: {s.celery_task_id}")

if __name__ == "__main__":
    asyncio.run(main())
