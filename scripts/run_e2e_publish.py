import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Fix import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule, VideoStatusEnum
from app.worker import process_and_upload_video

async def main():
    # Corrected Video ID
    video_id = "0e4587c1-c182-41e3-9515-f60c1f597827" 
    account_ids = [
        "678881f6-674f-4eb0-a359-233ece4b8db5", # YouTube
        "74da6d42-4b0b-4b41-a801-556ee1d028e7", # Facebook
        "25ffcc80-8901-4c67-a590-e6a6ef878020"  # Instagram
    ]
    
    async with AsyncSessionLocal() as db:
        for acc_id in account_ids:
            print(f"Creating schedule for account: {acc_id}")
            schedule = UploadSchedule(
                video_id=video_id,
                account_id=acc_id,
                scheduled_time=datetime.now(timezone.utc),
                add_watermark=True,
                is_published=False
            )
            db.add(schedule)
            await db.flush()
            
            # Trigger task
            task = process_and_upload_video.apply_async(args=[str(schedule.id)], queue="video_pipeline")
            schedule.celery_task_id = task.id
            print(f"Task ID for {acc_id}: {task.id}")
        
        await db.commit()
    print("All tasks triggered successfully.")

if __name__ == "__main__":
    asyncio.run(main())
