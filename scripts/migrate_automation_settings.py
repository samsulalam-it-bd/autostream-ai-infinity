import asyncio
from app.database import engine
from sqlalchemy import text

async def run():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS automation_settings JSONB DEFAULT '{}';"))
    print("DB migration successful: automation_settings added to accounts table.")

if __name__ == "__main__":
    asyncio.run(run())
