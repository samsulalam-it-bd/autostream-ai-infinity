import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.models import Account, PlatformEnum

async def main():
    async with AsyncSessionLocal() as db:
        # Fetch all accounts
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
        
        for acc in accounts:
            if acc.platform == PlatformEnum.FACEBOOK:
                if "Reya mone" in acc.channel_name:
                    print(f"Configuring {acc.channel_name} (Image posting)")
                    acc.drive_folder_link = "https://drive.google.com/drive/folders/1VG7abdhc3VPDScs6IZxeZsLK3-UYnFQg?usp=drive_link"
                    
                    settings = dict(acc.automation_settings or {})
                    settings["facebook_post_type"] = "image"
                    # Force SQLAlchemy to detect changes on JSONB
                    acc.automation_settings = settings
                    
                elif "AutoStream AI Infinity" in acc.channel_name:
                    print(f"Configuring {acc.channel_name} (Video/Reel posting)")
                    acc.drive_folder_link = "https://drive.google.com/drive/folders/1s2KEIUvW176pIXnPPbGqHbVPnfQrpZ2V?usp=drive_link"
                    
                    settings = dict(acc.automation_settings or {})
                    settings["facebook_post_type"] = "video"
                    acc.automation_settings = settings

            elif acc.platform == PlatformEnum.INSTAGRAM:
                print(f"Configuring Instagram account: {acc.channel_name}")
                acc.drive_folder_link = "https://drive.google.com/drive/folders/1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4?usp=drive_link"
                
            elif acc.platform == PlatformEnum.YOUTUBE:
                print(f"Configuring YouTube channel: {acc.channel_name}")
                acc.drive_folder_link = "https://drive.google.com/drive/folders/1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9?usp=drive_link"
        
        await db.commit()
        print("Database updated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
