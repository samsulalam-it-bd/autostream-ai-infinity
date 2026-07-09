import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from backend.app.database import AsyncSessionLocal
from backend.app.models.models import Account

async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res = await db.execute(select(Account))
        accounts = res.scalars().all()
        print(f"Found {len(accounts)} accounts:")
        for acc in accounts:
            print(f"- ID: {acc.id}")
            print(f"  Platform: {acc.platform.value}")
            print(f"  Channel: {acc.channel_name}")
            print(f"  Status: {acc.status.value}")
            print(f"  Channel ID: {acc.channel_id}")
            print(f"  Group ID: {acc.group_id}")
            print(f"  Drive Folder: {acc.drive_folder_link}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
