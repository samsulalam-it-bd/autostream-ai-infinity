import asyncio
import httpx
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.models import Account
from backend.app.core.security import decrypt_token

async def main():
    try:
        async with AsyncSessionLocal() as db:
            fb_acc = await db.execute(select(Account).where(Account.platform == "facebook").limit(1))
            fb_acc = fb_acc.scalar_one_or_none()
            if not fb_acc:
                print("No Facebook account found in DB.")
                return

            token = decrypt_token(fb_acc.encrypted_access_token)
            print(f"Using Token: {token[:15]}...")

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.facebook.com/v19.0/me/accounts",
                    params={
                        "access_token": token,
                        "fields": "id,name,access_token,instagram_business_account,tasks"
                    }
                )
                print(f"Graph API Status: {resp.status_code}")
                
                data = resp.json()
                print("--- PAGES RETURNED ---")
                for page in data.get("data", []):
                    print(f"Page: {page.get('name')} (ID: {page.get('id')})")
                    print(f"  Tasks: {page.get('tasks')}")
                    ig = page.get('instagram_business_account')
                    print(f"  Instagram: {ig}")
                print("----------------------")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
