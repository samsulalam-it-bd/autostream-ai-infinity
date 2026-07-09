import asyncio
import uuid
import datetime
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models.models import Account, SourceVideo, UploadSchedule, VideoStatusEnum, MediaTypeEnum

# Setup direct data structure mapping the user's explicit Google Drive urls
DRIVE_URLS = {
    "youtube": "https://drive.google.com/drive/folders/1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9?usp=sharing",
    "instagram": "https://drive.google.com/drive/folders/1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4?usp=sharing",
    "facebook_video": "https://drive.google.com/drive/folders/1s2KEIUvW176pIXnPPbGqHbVPnfQrpZ2V?usp=sharing",
    "facebook_img": "https://drive.google.com/drive/folders/1VG7abdhc3VPDScs6IZxeZsLK3-UYnFQg?usp=sharing"
}

# UUIDs fetched from live account checks
ACCOUNT_IDS = {
    "instagram": uuid.UUID("9cfb547c-d1f3-41fd-92ad-03214ae247dc"),
    "fb_infinity": uuid.UUID("dd84348e-1450-4231-9f99-1fd8c4aecff6"),
    "fb_reya": uuid.UUID("b6af06bc-4320-4e4a-9fd7-b0ee028c5c15"),
    "youtube": uuid.UUID("a7426582-2a3c-4706-bac6-a544165a3b4d")
}

async def clear_database():
    async with AsyncSessionLocal() as db:
        print("[Setup] Cleaning database schedules and source videos...")
        await db.execute(delete(UploadSchedule))
        await db.execute(delete(SourceVideo))
        await db.commit()
        print("[Setup] Database cleared successfully.")

async def setup_accounts_drive_links():
    async with AsyncSessionLocal() as db:
        print("[Setup] Setting up Drive links for all accounts...")
        
        # 1. Instagram: IG Video share link
        res = await db.execute(select(Account).where(Account.id == ACCOUNT_IDS["instagram"]))
        ig = res.scalar_one()
        ig.drive_folder_link = DRIVE_URLS["instagram"]
        
        # 2. YouTube: YT Video share link
        res = await db.execute(select(Account).where(Account.id == ACCOUNT_IDS["youtube"]))
        yt = res.scalar_one()
        yt.drive_folder_link = DRIVE_URLS["youtube"]
        
        # 3. Facebook AutoStream AI Infinity: FB Video share link
        res = await db.execute(select(Account).where(Account.id == ACCOUNT_IDS["fb_infinity"]))
        fb_inf = res.scalar_one()
        fb_inf.drive_folder_link = DRIVE_URLS["facebook_video"]
        
        # 4. Facebook Reya mone: FB Image share link
        res = await db.execute(select(Account).where(Account.id == ACCOUNT_IDS["fb_reya"]))
        fb_reya = res.scalar_one()
        fb_reya.drive_folder_link = DRIVE_URLS["facebook_img"]
        
        await db.commit()
        print("[Setup] Drive folder links successfully saved in DB.")

if __name__ == "__main__":
    asyncio.run(clear_database())
    asyncio.run(setup_accounts_drive_links())
