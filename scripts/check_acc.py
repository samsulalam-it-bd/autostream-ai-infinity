import asyncio
import sys
import os
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import AsyncSessionLocal
from app.models.models import Account

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        if not accounts:
            print("No accounts found.")
            return
        for a in accounts:
            print(f"[{a.platform.value}] {a.channel_name} (ID: {a.id}) - Status: {a.status.value}")

if __name__ == "__main__":
    asyncio.run(main())
