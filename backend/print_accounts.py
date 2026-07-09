import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        print(f"Total accounts found: {len(accounts)}")
        for acc in accounts:
            print("-" * 50)
            print(f"ID: {acc.id}")
            print(f"Platform: {acc.platform.value if hasattr(acc.platform, 'value') else acc.platform}")
            print(f"Name: {acc.channel_name}")
            print(f"Channel ID: {acc.channel_id}")
            print(f"Drive Folder Link: {acc.drive_folder_link}")
            print(f"Automation Settings: {acc.automation_settings}")
            print(f"Status: {acc.status}")

if __name__ == "__main__":
    asyncio.run(main())
