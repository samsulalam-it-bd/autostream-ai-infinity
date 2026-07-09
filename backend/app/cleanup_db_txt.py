import asyncio
from app.database import AsyncSessionLocal
from app.models.models import SourceVideo, UploadSchedule
from sqlalchemy import select, delete

async def main():
    async with AsyncSessionLocal() as db:
        # 1. Find all SourceVideo IDs ending with .txt
        res = await db.execute(select(SourceVideo).where(SourceVideo.original_filename.like("%.txt")))
        txt_videos = res.scalars().all()
        txt_video_ids = [v.id for v in txt_videos]
        
        print(f"Found {len(txt_videos)} misclassified text files in SourceVideo.")
        
        if txt_video_ids:
            # 2. Delete UploadSchedule records pointing to these videos
            sched_del = await db.execute(
                delete(UploadSchedule).where(UploadSchedule.video_id.in_(txt_video_ids))
            )
            print(f"Deleted {sched_del.rowcount} associated schedules.")
            
            # 3. Delete the SourceVideo records
            video_del = await db.execute(
                delete(SourceVideo).where(SourceVideo.id.in_(txt_video_ids))
            )
            print(f"Deleted {video_del.rowcount} text files from SourceVideo table.")
            
            await db.commit()
            print("Database cleaned up successfully!")
        else:
            print("No text files found in SourceVideo table.")

if __name__ == "__main__":
    asyncio.run(main())
