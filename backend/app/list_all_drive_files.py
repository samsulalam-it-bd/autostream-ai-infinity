import asyncio
from app.database import AsyncSessionLocal
from app.models.models import Account
from sqlalchemy import select
from app.services.uploader import list_drive_folder_videos
from app.services.token_service import get_valid_google_credentials

FOLDERS = {
    "YouTube Video": "1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9",
    "Instagram Video": "1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4",
    "Facebook Video": "1s2KEIUvW176pIXnPPbGqHbVPnfQrpZ2V",
    "Facebook Image": "1VG7abdhc3VPDScs6IZxeZsLK3-UYnFQg"
}

async def run():
    async with AsyncSessionLocal() as db:
        yt = (await db.execute(select(Account).where(Account.platform == 'youtube'))).scalars().first()
        creds = await get_valid_google_credentials(yt, db)
        
        for name, folder_id in FOLDERS.items():
            print(f"\n=== Files in folder: {name} ({folder_id}) ===")
            files = await list_drive_folder_videos(folder_id, creds.token)
            for f in files:
                print(f"Name: {f.get('name')}, MimeType: {f.get('mimeType')}, Size: {f.get('size')}")

if __name__ == "__main__":
    asyncio.run(run())
