import asyncio
import sys
from pathlib import Path

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import UploadSchedule, SourceVideo

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import delete
        # Delete all schedules
        res = await db.execute(delete(UploadSchedule))
        # Delete all source videos
        res2 = await db.execute(delete(SourceVideo))
        await db.commit()
        print("Successfully cleared all schedules and source videos from the DB.")

if __name__ == "__main__":
    asyncio.run(main())
