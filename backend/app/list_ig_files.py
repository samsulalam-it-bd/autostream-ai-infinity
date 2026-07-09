import asyncio
from app.database import AsyncSessionLocal
from app.models.models import Account
from sqlalchemy import select
from app.services.uploader import list_drive_folder_videos
from app.services.token_service import get_valid_google_credentials

async def run():
    async with AsyncSessionLocal() as db:
        yt = (await db.execute(select(Account).where(Account.platform == 'youtube'))).scalars().first()
        creds = await get_valid_google_credentials(yt, db)
        files = await list_drive_folder_videos('1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4', creds.token)
        print('Files in Instagram folder:')
        for f in files:
            print(f"Name: {f.get('name')}, MimeType: {f.get('mimeType')}, Size: {f.get('size')}")

if __name__ == "__main__":
    asyncio.run(run())
