import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.models import Account
from app.worker import sync_drive_folder

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        
        for acc in accounts:
            if not acc.drive_folder_link:
                print(f"Skipping {acc.channel_name} (no folder link)")
                continue
            
            print(f"Queuing sync task for: {acc.channel_name} ({acc.platform.value})")
            print(f"Folder Link: {acc.drive_folder_link}")
            
            # Dispatch Celery task
            task = sync_drive_folder.apply_async(
                args=[acc.drive_folder_link, str(acc.id), True],
                queue="default"
            )
            print(f"Task queued. Task ID: {task.id}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
