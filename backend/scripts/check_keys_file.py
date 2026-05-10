import asyncio
from sqlalchemy import select
from app.database import engine
from app.models.models import ApiKeyVault

async def check_keys():
    async with engine.begin() as conn:
        result = await conn.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == "meta"))
        keys = result.fetchall()
        with open("meta_keys.txt", "w") as f:
            f.write(f"Found {len(keys)} Meta API keys in database.\n")
            for k in keys:
                f.write(f"- ID: {k.id}, Label: {k.key_label}, Locked: {k.is_locked}\n")

if __name__ == "__main__":
    asyncio.run(check_keys())
