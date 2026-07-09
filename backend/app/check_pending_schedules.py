import asyncio
from app.database import AsyncSessionLocal
from app.models.models import Account, UploadSchedule, SourceVideo
from sqlalchemy import select, and_

ACCOUNTS = {
    "YouTube (Fajle Rabbi)": "a7426582-2a3c-4706-bac6-a544165a3b4d",
    "Instagram (@trusted.overseas.ltd)": "9cfb547c-d1f3-41fd-92ad-03214ae247dc",
    "Facebook Reels (AutoStream AI Infinity)": "dd84348e-1450-4231-9f99-1fd8c4aecff6",
    "Facebook Images (Reya mone)": "b6af06bc-4320-4e4a-9fd7-b0ee028c5c15"
}

async def run():
    async with AsyncSessionLocal() as db:
        for name, acc_id in ACCOUNTS.items():
            print(f"\n=== Pending schedules for: {name} ===")
            res = await db.execute(
                select(UploadSchedule)
                .where(and_(UploadSchedule.account_id == acc_id, UploadSchedule.is_published == False))
                .order_by(UploadSchedule.scheduled_time)
            )
            schedules = res.scalars().all()
            if not schedules:
                print("No pending schedules found.")
                continue
                
            for s in schedules[:3]:  # Print next 3 pending
                v = (await db.execute(select(SourceVideo).where(SourceVideo.id == s.video_id))).scalar_one()
                print(f"Schedule ID: {s.id} | Scheduled Time: {s.scheduled_time} | File: {v.original_filename} ({v.media_type.value})")

if __name__ == "__main__":
    asyncio.run(run())
