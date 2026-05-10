import asyncio
import json
import os
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.models import Account

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        for a in accounts:
            print(f"[{a.platform.value}] {a.channel_name} (ID: {a.channel_id}) - Status: {a.status.value}")

if __name__ == "__main__":
    asyncio.run(main())
