#!/usr/bin/env python3
"""Run directly inside the container: python app/migrate.py"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://autostream:autostream123@db:5432/autostream_db"
)

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    migrations = [
        # Add metadata_overrides column if not exists (table name from models.py = upload_schedule)
        "ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS metadata_overrides JSONB;",
        # Clean dirty ai_title values that have Source Link prefix
        "UPDATE source_videos SET ai_title = NULL WHERE ai_title LIKE 'Source Link:%';",
        "UPDATE source_videos SET ai_description = NULL WHERE ai_description LIKE 'Title: Video by%';",
    ]

    async with async_session() as session:
        for sql in migrations:
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"✅ {sql[:60]}...")
            except Exception as e:
                print(f"⚠️  SKIPPED: {str(e)[:100]}")
                await session.rollback()

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
