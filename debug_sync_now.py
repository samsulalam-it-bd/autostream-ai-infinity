import requests
import time
import json

BASE = "http://localhost:8000/api/v1"

print("=== Fetching YouTube Accounts ===")
r = requests.get(f"{BASE}/accounts/?platform=youtube")
yt_accounts = r.json()
print(json.dumps(yt_accounts, indent=2))

if not yt_accounts:
    print("ERROR: No YouTube accounts found! Cannot proceed with Drive sync.")
    exit(1)

yt_id = yt_accounts[0]['id']
print(f"\nUsing YouTube account: {yt_accounts[0]['channel_name']} (ID: {yt_id})")

DRIVE_LINK = "https://drive.google.com/drive/folders/1mgLJ1Y-DijeEM7SqCq1VdMJZSEqSMDdr?usp=sharing"

print(f"\n=== Triggering Drive Sync ===")
r2 = requests.post(f"{BASE}/videos/sync-drive", json={
    "folder_link": DRIVE_LINK,
    "account_id": yt_id
})
print(f"Status: {r2.status_code}")
result = r2.json()
print(json.dumps(result, indent=2))

task_id = result.get("task_id")
if not task_id:
    print("ERROR: No task_id returned!")
    exit(1)

print(f"\n=== Monitoring Task: {task_id} ===")
for i in range(12):  # Poll for up to 60 seconds
    time.sleep(5)
    r3 = requests.get(f"{BASE}/videos/task-status/{task_id}")
    status_data = r3.json()
    print(f"[{(i+1)*5}s] Status: {status_data.get('status')} | Result: {status_data.get('result')}")
    if status_data.get('status') in ('SUCCESS', 'FAILURE'):
        break

print("\n=== Current Video Count ===")
r4 = requests.get(f"{BASE}/videos/")
videos = r4.json()
print(f"Total videos in DB: {len(videos)}")
if videos:
    for v in videos[:3]:
        print(f"  - {v.get('original_filename', 'N/A')} | Status: {v.get('status')}")
