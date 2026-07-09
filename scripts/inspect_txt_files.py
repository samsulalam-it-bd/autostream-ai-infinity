import asyncio
import sys
from pathlib import Path
import httpx

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum, AccountStatusEnum
from app.services.token_service import get_valid_google_credentials
from app.services.uploader import list_drive_folder_videos, extract_folder_id_from_link, read_drive_file_text

async def main():
    folder_link = "https://drive.google.com/drive/folders/1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9?usp=sharing"
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        yt_result = await db.execute(
            select(Account).where(
                Account.platform == PlatformEnum.YOUTUBE,
                Account.status == AccountStatusEnum.ACTIVE,
            )
        )
        google_account = yt_result.scalars().first()
        creds = await get_valid_google_credentials(google_account, db)
        access_token = creds.token

        folder_id = extract_folder_id_from_link(folder_link)
        files = await list_drive_folder_videos(folder_id, access_token)
        texts = [f for f in files if "text" in f.get("mimeType", "")]
        
        for t in texts[:2]:
            print(f"\n--- Reading Text File: {t['name']} ---")
            txt_content = await read_drive_file_text(t["id"], access_token)
            print(f"Length of text: {len(txt_content)}")
            print(txt_content[:600])

if __name__ == "__main__":
    asyncio.run(main())
