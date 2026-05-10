import asyncio
from sqlalchemy import text
from app.database import engine

async def run_migrations():
    async with engine.begin() as conn:
        try:
            # UploadSchedule new columns
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITH TIME ZONE"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS published_url VARCHAR(500)"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS add_watermark BOOLEAN DEFAULT TRUE"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS auto_comment BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS auto_comment_text TEXT"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255)"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS error_message TEXT"))
            await conn.execute(text("ALTER TABLE upload_schedule ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0"))
            
            # SourceVideo new columns
            await conn.execute(text("ALTER TABLE source_videos ADD COLUMN IF NOT EXISTS ai_title VARCHAR(500)"))
            await conn.execute(text("ALTER TABLE source_videos ADD COLUMN IF NOT EXISTS ai_description TEXT"))
            await conn.execute(text("ALTER TABLE source_videos ADD COLUMN IF NOT EXISTS ai_tags JSONB"))
            await conn.execute(text("ALTER TABLE source_videos ADD COLUMN IF NOT EXISTS ai_hashtags JSONB"))
            
            # Account new columns
            await conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS drive_folder_link VARCHAR(1000)"))
            
            print("Successfully altered tables to add missing columns.")
        except Exception as e:
            print(f"Error altering tables: {e}")

if __name__ == "__main__":
    asyncio.run(run_migrations())
