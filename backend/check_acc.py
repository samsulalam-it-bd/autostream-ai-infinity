import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.models import Account

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        if not accounts:
            print("No accounts found.")
            return
        for a in accounts:
            print(f"[{a.platform.value}] {a.channel_name} (ID: {a.id}) - Status: {a.status.value}")

if __name__ == "__main__":
    asyncio.run(main())
