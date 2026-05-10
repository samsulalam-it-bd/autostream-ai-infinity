import asyncio
from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum
from app.core.security import decrypt_token
from sqlalchemy import select

async def get_token():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Account).where(Account.platform==PlatformEnum.FACEBOOK))
        acc = res.scalars().first()
        if acc:
            token = decrypt_token(acc.encrypted_access_token)
            print(token)
            
if __name__ == "__main__":
    asyncio.run(get_token())
