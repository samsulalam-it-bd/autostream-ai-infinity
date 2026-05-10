import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"
DRIVE_LINK = "https://drive.google.com/drive/folders/1Zh3mQozyJJp0SF_f7ofSWDT1OOE2gGOp?usp=sharing"

async def run_publish():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("1. Fetching active accounts...")
        resp = await client.get(f"{BASE_URL}/accounts/")
        accounts = [a for a in resp.json() if a.get('status') == 'active']
        
        if not accounts:
            print("❌ No active accounts found. Cannot publish.")
            return

        print(f"✅ Found {len(accounts)} active accounts:")
        for a in accounts:
            print(f"   - {a['platform'].upper()}: {a['channel_name']}")

        account_ids = [a['id'] for a in accounts]
        
        print(f"\n2. Syncing Google Drive Link: {DRIVE_LINK}")
        # The schema requires account_id, supplying the first one just for credential purposes
        payload = {
            "account_id": account_ids[0],
            "folder_link": DRIVE_LINK
        }
        res = await client.post(f"{BASE_URL}/videos/sync-drive", json=payload)
        if res.status_code != 202:
            print(f"❌ Failed to start sync: {res.status_code} {res.text}")
            return
            
        task_id = res.json().get("task_id")
        print(f"✅ Sync started! Celery Task ID: {task_id}")
        
        print("\n3. Waiting for Drive Sync Celery Task to complete...")
        while True:
            status_res = await client.get(f"{BASE_URL}/videos/task-status/{task_id}")
            state = status_res.json().get('status')
            print(f"   -> Status: {state}")
            if state in ['SUCCESS', 'FAILURE']:
                break
            await asyncio.sleep(3)
            
        print("\n4. Fetching newly synced videos...")
        resp = await client.get(f"{BASE_URL}/videos/")
        videos = resp.json()
        ready_videos = [v for v in videos if v['status'] in ['ready', 'synced']]
        
        if not ready_videos:
            print("❌ No valid videos were synced from the drive link.")
            return
            
        # Select the first video to test publish
        test_video = ready_videos[0]
        print(f"✅ Selected Video for Publishing: {test_video['original_filename']} (ID: {test_video['id']})")
        
        print("\n5. Publishing Video to ALL Accounts...")
        sched_payload = {
            "video_ids": [test_video['id']],
            "account_ids": account_ids,
            "target_group_id": None,
            "start_datetime": "2026-03-08T00:00:00Z", # Dummy future
            "total_days": 1,
            "add_watermark": False,
            "auto_comment": False
        }
        
        sched_res = await client.post(f"{BASE_URL}/schedules/auto-drip", json=sched_payload)
        if sched_res.status_code != 200:
            print(f"❌ Failed to schedule: {sched_res.text}")
            return
            
        print("✅ Scheduled successfully. Now triggering immediate publish via Celery...")
        
        resp = await client.get(f"{BASE_URL}/schedules/")
        schedules = [s for s in resp.json() if not s['is_published'] and s['video_id'] == test_video['id']]
        
        for s in schedules:
            print(f"   -> Dispatched Publish Task for Schedule ID: {s['id']}")
            await client.post(f"{BASE_URL}/schedules/{s['id']}/trigger")
            
        print("\n🎉 ALL DONE! The videos are now publishing in the background.")

if __name__ == "__main__":
    asyncio.run(run_publish())
