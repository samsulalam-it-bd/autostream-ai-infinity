import asyncio
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path inside the container
sys.path.insert(0, "/app")

from app.database import AsyncSessionLocal
from app.models.models import SourceVideo, UploadSchedule, VideoStatusEnum, MediaTypeEnum, Account
from app.worker import sync_drive_folder, process_and_upload_video, celery_app

# Define custom drive folders and mapped accounts
TARGETS = [
    {
        "name": "YouTube Video Uploads",
        "folder_link": "https://drive.google.com/drive/folders/1CdXXE7I4VPnlYkKGD20zlNg2z_BcGTe9?usp=sharing",
        "account_id": "a7426582-2a3c-4706-bac6-a544165a3b4d", # Fajle Rabbi
        "instant_file_id": "15p2UMfoySxmS7r_uG08h5RhVLQ7qhxmz", # 20260519_Video by lolita_DYgznO-OMNN.mp4
        "scheduled_file_ids": [
            "1_Mz3wgrFH2ryBSwgp7SqWlb30xRn8j8l", # 20260519_Video by lolita_DYgFdKqB8mP.mp4
            "1Ld3JA0oSAWNEAuja_j9C9_joANcGHnDP", # 20260519_Video by lolita_DYg5VyGuudo.mp4
            "1l-hB3MjZnyQv6RW2dmiRj0QnfOwJsdn4", # 20260420_Video by megtravelstories_DXVzMrDkfGW.mp4
        ]
    },
    {
        "name": "Instagram Video Uploads",
        "folder_link": "https://drive.google.com/drive/folders/1S4LN_EMrWpjpGmb0mVnXwBPYc1sin8P4?usp=sharing",
        "account_id": "9cfb547c-d1f3-41fd-92ad-03214ae247dc", # @trusted.overseas.ltd (IG)
        "instant_file_id": "1MmWcqfWiHl_1BrnU3Lo8LmLxXHkhVCAk", # 20260516_Video by casper_smc_DYZ3Tjxt9uW.mp4
        "scheduled_file_ids": [
            "1oY2xhGLvwQ3gCu1XKBq2BNGKCHar5TBn", # 20260519_Video by lolita_DYg7uuWuO9S.mp4
            "1bgZHI-llT-c8Kn43ffYJtf3UiqCEQUl8", # 20260414_Video by baselgazi_DXHpK44CBQz.mp4
            "104NSztSTkGa8cAPtz_p3gKK544VPujlS", # 20260519_Video by lolita_DYg-GsuuUJj.mp4
        ]
    },
    {
        "name": "Facebook Video Uploads",
        "folder_link": "https://drive.google.com/drive/folders/1s2KEIUvW176pIXnPPbGqHbVPnfQrpZ2V?usp=sharing",
        "account_id": "dd84348e-1450-4231-9f99-1fd8c4aecff6", # AutoStream AI Infinity (Facebook)
        "instant_file_id": "1wyTP0MBZTSeNvSitIdQol5Xl7cgOTgI1", # 20260402_Video by leomessi_DWn_nn2jJfe.mp4
        "scheduled_file_ids": [
            "1gStI4k8AvyTT7pCQQBjqP70ibYvEPoqq", # 20260325_Video by thenexasports_DWT6_E8jApP.mp4
            "1RlMmsu27d7Z4mi8YowiVeROsdMKxtkgu", # 20260504_Video by caitlinnates_travels360_DX69dMBxhv2.mp4
            "1ecWn-WlTmhjH1VT5CY6dyPsMfKJnv6xf", # 20260219_Video by rachel.points_DU9IbnMjDaZ.mp4
        ]
    },
    {
        "name": "Facebook Image Uploads",
        "folder_link": "https://drive.google.com/drive/folders/1VG7abdhc3VPDScs6IZxeZsLK3-UYnFQg?usp=sharing",
        "account_id": "dd84348e-1450-4231-9f99-1fd8c4aecff6", # AutoStream AI Infinity (Facebook)
        "instant_file_id": "1iAwyA5GsaQo57qomz328aAmsqCMxrX6C", # 0314f524b204088b16a686958226d6d0.jpg
        "scheduled_file_ids": [
            "1-F653zJf0bwCw2iwilk9SypZPDGahgr2", # 395295fdaafa1997a669e2fa1a311f8b.jpg
            "1vcQIss1-hBeIXDBgBdE3CgZZxYEANWVo", # 065ff735ee45297eff90beb4dcd5cf4e.jpg
            "1Fnm9sg_493daQcD2O3owQRwDQb1UAkcY", # 31aa45765c6ee98cf06b0ee784c6af2d.jpg
        ]
    }
]

async def monitor_task(task_id: str):
    """Poll Celery task status until finished."""
    print(f"Monitoring Celery Task: {task_id}")
    while True:
        res = celery_app.AsyncResult(task_id)
        if res.ready():
            print(f"Task {task_id} status: {res.status} (Result: {res.result})")
            return res.status == "SUCCESS"
        await asyncio.sleep(2)

async def main():
    import uuid
    print("=" * 60)
    print("           AUTOSTREAM AI CUSTOM PUBLISHING WORKFLOW")
    print("=" * 60)

    # Step 1: Sync Google Drive folders using Celery
    sync_tasks = []
    print("\n[STEP 1] Starting Google Drive folder synchronization...")
    for target in TARGETS:
        print(f"-> Syncing: {target['name']} | Account: {target['account_id']}")
        task = sync_drive_folder.apply_async(args=[target["folder_link"], target["account_id"]], queue="default")
        sync_tasks.append((target["name"], task.id))

    # Wait for all sync tasks to complete
    print("\nWaiting for sync tasks to finish...")
    all_success = True
    for name, task_id in sync_tasks:
        success = await monitor_task(task_id)
        if not success:
            print(f"[!] Warning: Sync for {name} failed or completed with warnings.")
            all_success = False
        else:
            print(f"[OK] Sync for {name} succeeded.")

    # Step 2: Fetch SourceVideo records and queue uploads
    print("\n[STEP 2] Creating and dispatching upload schedules...")
    now = datetime.now(timezone.utc)
    
    instant_tasks = []
    scheduled_tasks_count = 0

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        for target in TARGETS:
            print(f"\nProcessing target: {target['name']}")
            
            # Fetch Instant SourceVideo
            res = await db.execute(select(SourceVideo).where(SourceVideo.drive_file_id == target["instant_file_id"]))
            instant_video = res.scalar_one_or_none()
            
            if not instant_video:
                print(f"[ERROR] Instant video {target['instant_file_id']} not found in DB! Skipping.")
                continue
                
            # Create Instant Schedule
            print(f"-> Creating Instant Upload Schedule for: {instant_video.original_filename}")
            instant_sched = UploadSchedule(
                video_id=instant_video.id,
                account_id=uuid.UUID(target["account_id"]),
                scheduled_time=now,
                add_watermark=True,
                is_published=False
            )
            db.add(instant_sched)
            await db.flush() # Populate schedule ID
            
            # Trigger celery pipeline for instant upload
            task = process_and_upload_video.apply_async(args=[str(instant_sched.id)], queue="video_pipeline")
            instant_sched.celery_task_id = task.id
            instant_tasks.append((target["name"], instant_sched.id, task.id))
            print(f"   Instant Task enqueued with ID: {task.id}")
            
            # Fetch and Create 3 Scheduled Uploads (T+10, T+20, T+30 minutes)
            for idx, file_id in enumerate(target["scheduled_file_ids"]):
                res = await db.execute(select(SourceVideo).where(SourceVideo.drive_file_id == file_id))
                sched_video = res.scalar_one_or_none()
                
                if not sched_video:
                    print(f"[ERROR] Scheduled video {file_id} not found in DB! Skipping.")
                    continue
                    
                minutes_delay = (idx + 1) * 10
                scheduled_time = now + timedelta(minutes=minutes_delay)
                
                print(f"-> Scheduling Upload for: {sched_video.original_filename} in {minutes_delay} mins (at {scheduled_time})")
                sched_item = UploadSchedule(
                    video_id=sched_video.id,
                    account_id=uuid.UUID(target["account_id"]),
                    scheduled_time=scheduled_time,
                    add_watermark=True,
                    is_published=False
                )
                db.add(sched_item)
                await db.flush()
                
                # Queue task with ETA (Celery worker holds it until that exact time)
                task = process_and_upload_video.apply_async(args=[str(sched_item.id)], queue="video_pipeline", eta=scheduled_time)
                sched_item.celery_task_id = task.id
                scheduled_tasks_count += 1
                print(f"   Scheduled Task enqueued with ID: {task.id} (ETA: {scheduled_time})")
        
        await db.commit()

    print(f"\n[OK] Enqueued {len(instant_tasks)} instant tasks and {scheduled_tasks_count} scheduled tasks.")

    # Step 3: Monitor Instant Upload Tasks in Real Time
    print("\n[STEP 3] Monitoring Instant Upload tasks in real time...")
    active_instances = list(instant_tasks)
    
    while active_instances:
        await asyncio.sleep(5)
        remaining = []
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            for name, sched_id, task_id in active_instances:
                # Check celery status
                res = celery_app.AsyncResult(task_id)
                # Check DB for error messages or publication status
                sched_res = await db.execute(select(UploadSchedule).where(UploadSchedule.id == sched_id))
                sched = sched_res.scalar_one_or_none()
                
                if res.ready() or (sched and sched.is_published):
                    status = res.status
                    print(f"\n[Instant Task Completed] {name}:")
                    print(f"   Celery Status: {status}")
                    if sched:
                        print(f"   DB Published: {sched.is_published}")
                        print(f"   Published URL: {sched.published_url}")
                        if sched.error_message:
                            print(f"   ERROR Details: {sched.error_message}")
                    else:
                        print("   DB record not found!")
                else:
                    remaining.append((name, sched_id, task_id))
        active_instances = remaining
        if active_instances:
            print(f"Still processing {len(active_instances)} instant uploads...")

    print("\n" + "=" * 60)
    print("                   WORKFLOW EXECUTION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
