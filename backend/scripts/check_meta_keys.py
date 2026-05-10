import asyncio
from sqlalchemy import select
from app.database import engine
from app.models.models import ApiKeyVault

async def check_keys():
    async with engine.begin() as conn:
        result = await conn.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == "meta"))
        keys = result.fetchall()
        print(f"Found {len(keys)} Meta API keys in database.")
        for k in keys:
            print(f"- ID: {k.id}, Label: {k.key_label}, Locked: {k.is_locked}")

if __name__ == "__main__":
    asyncio.run(check_keys())
