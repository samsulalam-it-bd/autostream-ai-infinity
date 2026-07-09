import asyncio
import json
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import ApiKeyVault

async def check_keys():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == 'openrouter'))
        keys = res.scalars().all()
        print(f"Found {len(keys)} OpenRouter keys:")
        for k in keys:
            print(k.id, k.project_name, k.daily_usage, k.daily_limit, k.is_locked)

        # Let's also test the quick_gen fallback
        # First check if we have any key at all
        res_all = await db.execute(select(ApiKeyVault))
        print(f"Total keys in vault: {len(res_all.scalars().all())}")

if __name__ == "__main__":
    asyncio.run(check_keys())
