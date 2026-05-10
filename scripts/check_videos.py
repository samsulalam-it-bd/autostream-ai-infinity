import asyncio
import sys
import os
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.models import SourceVideo

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(SourceVideo))
        videos = result.scalars().all()
        if not videos:
            print("No videos found.")
            return
        for v in videos:
            print(f"Video: {v.original_filename} (ID: {v.id})")

if __name__ == "__main__":
    asyncio.run(main())
