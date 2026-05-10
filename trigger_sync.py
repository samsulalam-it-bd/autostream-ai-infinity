import httpx
import time
import asyncio

async def test_sync():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Fetching accounts...")
        resp = await client.get("http://localhost:8000/api/v1/accounts/")
        accounts = resp.json()
        if not accounts:
            print("No accounts connected!")
            return
            
        test_acc = accounts[0]
        print(f"2. Using account: {test_acc['channel_name']} ({test_acc['platform']})")
        
        folder_link = "https://drive.google.com/drive/folders/17h3mQozyJp0SF_f7ofSWDT1OOE2gGOp?usp=sharing"
        print(f"3. Syncing folder: {folder_link}")
        
        sync_resp = await client.post("http://localhost:8000/api/v1/accounts/sync-folder", json={
            "account_id": test_acc['id'],
            "folder_link": folder_link
        })
        
        print(f"4. Sync API Response [{sync_resp.status_code}]: {sync_resp.text}")
        
        print("5. Waiting for Celery worker (10 seconds)...")
        time.sleep(10)
        
        print("6. Fetching videos...")
        video_resp = await client.get("http://localhost:8000/api/v1/videos/")
        videos = video_resp.json()
        print(f"7. Total videos in DB: {len(videos)}")
        for v in videos[-3:]: # Just print last 3
            print(f"  - {v['original_filename']} ({v['status']})")

if __name__ == "__main__":
    asyncio.run(test_sync())
