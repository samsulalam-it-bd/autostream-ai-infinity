
import asyncio
import httpx
import json

API_BASE = "http://localhost:8000/api/v1"
DRIVE_URL = "https://drive.google.com/drive/folders/1Zh3mQozyJJp0SF_f7ofSWDT1OOE2gGOp?usp=sharing"

async def run_test():
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 1. Get Accounts
        print("Fetching accounts...")
        acc_res = await client.get(f"{API_BASE}/accounts/")
        accounts = acc_res.json()
        print(f"Found {len(accounts)} accounts.")

        # 2. Sync Folder
        print("Syncing Drive folder...")
        sync_res = await client.post(f"{API_BASE}/videos/sync-drive", json={
            "account_id": accounts[0]['id'],
            "folder_link": DRIVE_URL
        })
        task_id = sync_res.json().get("task_id")
        print(f"Sync started. Task ID: {task_id}")

        # 3. Poll for completion
        while True:
            status_res = await client.get(f"{API_BASE}/videos/task-status/{task_id}")
            status = status_res.json().get("status")
            print(f"Sync status: {status}")
            if status == "SUCCESS":
                break
            if status in ["FAILURE", "REVOKED"]:
                print("Sync failed!")
                return
            await asyncio.sleep(3)

        # 4. Fetch Videos (TRYING BOTH)
        print("Fetching all synced videos...")
        vid_res = await client.get(f"{API_BASE}/videos/")
        all_videos = vid_res.json()
        print(f"Total videos in API: {len(all_videos)}")

        print("Fetching unassigned videos...")
        vid_res = await client.get(f"{API_BASE}/videos/", params={"unassigned_only": True})
        unassigned_videos = vid_res.json()
        print(f"Unassigned videos in API: {len(unassigned_videos)}")

        videos = unassigned_videos if unassigned_videos else all_videos
        
        if not videos:
            print("NO VIDEOS FOUND AT ALL. ABORTING.")
            return
        
        # 5. Schedule 1 video per platform
        platforms = ['facebook', 'instagram', 'youtube']
        scheduled_vids = []
        
        for i, platform in enumerate(platforms):
            target_accs = [a for a in accounts if a['platform'].lower() == platform]
            if not target_accs:
                continue
            
            acc = target_accs[0]
            vid_idx = i % len(videos)
            vid = videos[vid_idx]
            
            print(f"Scheduling {vid['original_filename']} for {acc['channel_name']} ({platform})...")
            
            res = await client.post(f"{API_BASE}/schedules/auto-drip", json={
                "account_ids": [acc['id']],
                "video_ids": [vid['id']],
                "settings": {
                    "timezone": "Asia/Dhaka",
                    "time_slots": ["10:00"],
                    "mode": "ai",
                    "custom_description": f"AutoStream Multi-Platform Test ({platform}) 🔥",
                    "tags": f"#autostream #{platform}",
                    "add_watermark": False,
                    "delete_from_drive": True
                }
            })
            if res.status_code in [200, 201]:
                scheduled_vids.append((acc, vid))
            else:
                print(f"Failed to schedule for {platform}: {res.text}")

        # 6. Trigger Instant Post
        print("\nTriggering Instant Posts...")
        for acc, vid in scheduled_vids:
            print(f"Launching {acc['platform']}...")
            await client.post(f"{API_BASE}/schedules/instant-post-next", json={"account_id": acc['id']})
            await asyncio.sleep(2)

        print("\n" + "="*50)
        print("ALL TASKS TRIGGERED.")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(run_test())
