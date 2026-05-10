import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"

async def test_publish():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Fetching active accounts...")
        resp = await client.get(f"{BASE_URL}/accounts/")
        accounts = [a for a in resp.json() if a['status'] == 'active']
        if not accounts:
            print("❌ No active accounts found.")
            return
            
        print(f"✅ Found {len(accounts)} active accounts:")
        platforms = {}
        for a in accounts:
            print(f"   - {a['platform'].upper()}: {a['channel_name']}")
            if a['platform'] not in platforms:
                platforms[a['platform']] = a
                
        print("\n2. Fetching synced videos...")
        resp = await client.get(f"{BASE_URL}/videos/")
        videos = resp.json()
        if not videos:
            print("❌ No videos found in the database. Cannot test publishing without a video.")
            return
            
        # Get a ready video
        ready_videos = [v for v in videos if v['status'] == 'ready' or v['status'] == 'synced']
        if not ready_videos:
            print("❌ No ready/synced videos found.")
            return
            
        test_video = ready_videos[0]
        print(f"✅ Selected Video for Test: {test_video['original_filename']} (ID: {test_video['id']})")
        
        # 3. Schedule for one of each platform
        print("\n3. Scheduling video for each platform...")
        for platform, account in platforms.items():
            print(f"   -> Scheduling for {platform.upper()} ({account['channel_name']})")
            payload = {
                "video_ids": [test_video['id']],
                "account_ids": [account['id']],
                "target_group_id": None,
                "start_datetime": "2026-03-07T00:00:00Z", # Future dummy date
                "total_days": 1,
                "add_watermark": False,
                "auto_comment": False
            }
            
            resp = await client.post(f"{BASE_URL}/schedules/auto-drip", json=payload)
            if resp.status_code != 200:
                print(f"   ❌ Failed to schedule: {resp.text}")
                continue
                
            print(f"   ✅ Scheduled successfully.")
            
        print("\n4. Fetching pending schedules and triggering them immediately...")
        resp = await client.get(f"{BASE_URL}/schedules/")
        schedules = [s for s in resp.json() if not s['is_published'] and s['video_id'] == test_video['id']]
        
        for s in schedules:
            print(f"   -> Triggering Schedule ID: {s['id']}")
            resp = await client.post(f"{BASE_URL}/schedules/{s['id']}/trigger")
            if resp.status_code == 200:
                print(f"      ✅ Dispatched to Celery (Task ID: {resp.json().get('task_id')})")
            else:
                print(f"      ❌ Failed to trigger: {resp.text}")
                
        print("\n⏳ Test dispatched successfully! Please monitor celery worker logs to see the upload flow.")

if __name__ == "__main__":
    asyncio.run(test_publish())
