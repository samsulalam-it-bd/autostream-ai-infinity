import asyncio
import os
import sys

# Add backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.models import Account
from app.services.token_service import get_valid_google_credentials
from app.services.uploader import list_drive_folder_videos

async def main():
    folder_id = "17h3mQozyIpDSF_f7ofSWDT1OQf2ggOp"
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Account).where(Account.platform == 'youtube'))
        accounts = result.scalars().all()
        
        if not accounts:
            print("No YouTube account found to get Google credentials from.")
            return

        # Try to get credentials from the first youtube account
        account = accounts[0]
        print(f"Using account {account.channel_name} ({account.id}) for Google Auth")
        
        try:
            creds = await get_valid_google_credentials(account, db)
            access_token = creds.token
            print(f"Got access token: {access_token[:10]}...")
            
            files = await list_drive_folder_videos(folder_id, access_token)
            print(f"Total RAW files found: {len(files)}")
            for f in files:
                print(f" - {f.get('name')} | Mime: {f.get('mimeType')} | ID: {f.get('id')}")
                
            videos = [f for f in files if "video" in f.get("mimeType", "")]
            texts = [f for f in files if "text" in f.get("mimeType", "")]
            
            print(f"\nFiltered videos: {len(videos)}")
            print(f"Filtered texts: {len(texts)}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
