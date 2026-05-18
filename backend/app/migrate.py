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
        # Add auto_comment columns to accounts table
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS auto_comment BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS auto_comment_text TEXT;",
        # Add AI time predictor columns to accounts
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS ai_time_predictor BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE accounts ADD COLUMN IF NOT EXISTS optimal_slots JSONB DEFAULT '{}';",
        # Add AI optimized columns to upload_schedule
        "ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS original_scheduled_time TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS is_optimized_by_ai BOOLEAN DEFAULT FALSE;",
        # Create channel_analytics table and index
        "CREATE TABLE IF NOT EXISTS channel_analytics (id UUID PRIMARY KEY, account_id UUID REFERENCES accounts(id) ON DELETE CASCADE, date DATE NOT NULL, followers_count BIGINT DEFAULT 0, views_count BIGINT DEFAULT 0, likes_count BIGINT DEFAULT 0, engagement_rate DOUBLE PRECISION DEFAULT 0.0, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_channel_analytics_acc_date ON channel_analytics(account_id, date);",
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
