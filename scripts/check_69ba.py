import asyncio
from app.database import AsyncSessionLocal
from app.models.models import SourceVideo
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SourceVideo))
        videos = res.scalars().all()
        for v in videos:
            print(f"ID: {v.id} | original_filename: {repr(v.original_filename)}")

if __name__ == "__main__":
    asyncio.run(main())
