
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import os

DATABASE_URL = "postgresql+asyncpg://autostream:supersecretpassword@localhost:5432/autostream_db"

async def fix_schedules():
    engine = create_async_engine(DATABASE_URL)
    async with AsyncSession(engine) as session:
        await session.execute(text("UPDATE upload_schedule SET metadata_overrides = '{\"delete_from_drive\": true}'::jsonb;"))
        await session.commit()
        print("Updated metadata_overrides successfully.")

if __name__ == "__main__":
    asyncio.run(fix_schedules())
