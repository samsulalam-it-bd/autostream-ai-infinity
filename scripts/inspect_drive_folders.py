import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum, AccountStatusEnum
from app.services.token_service import get_valid_google_credentials
from app.services.uploader import list_drive_folder_videos, extract_folder_id_from_link

async def main():
    folders = {
        "YT Video": "https://drive.google.com/drive/folders/1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9?usp=sharing",
        "IG Video": "https://drive.google.com/drive/folders/1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4?usp=sharing",
        "FB Video": "https://drive.google.com/drive/folders/1s2KEIUvW176pIXnPPbGqHbVPnfQrpZ2V?usp=sharing",
        "FB Img": "https://drive.google.com/drive/folders/1VG7abdhc3VPDScs6IZxeZsLK3-UYnFQg?usp=sharing"
    }

    async with AsyncSessionLocal() as db:
        # Borrow credentials from YouTube account
        yt_result = await db.execute(
            select(Account).where(
                Account.platform == PlatformEnum.YOUTUBE,
                Account.status == AccountStatusEnum.ACTIVE,
            )
        )
        google_account = yt_result.scalars().first()
        if not google_account:
            print("Error: No active YouTube account found to get Google Drive credentials.")
            return

        print(f"Using Google credentials from account: {google_account.channel_name}")
        creds = await get_valid_google_credentials(google_account, db)
        access_token = creds.token

        for name, link in folders.items():
            folder_id = extract_folder_id_from_link(link)
            print(f"\nFolder: {name} (ID: {folder_id})")
            try:
                files = await list_drive_folder_videos(folder_id, access_token)
                print(f"Total files: {len(files)}")
                for f in files:
                    print(f"- Name: {f.get('name')} | ID: {f.get('id')} | MIME: {f.get('mimeType')}")
            except Exception as e:
                print(f"Error listing folder {name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
