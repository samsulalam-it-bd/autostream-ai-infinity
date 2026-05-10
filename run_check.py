import urllib.request
import json
import uuid

try:
    print("Fetching active accounts...")
    req = urllib.request.Request("http://localhost:8000/api/v1/accounts/")
    with urllib.request.urlopen(req) as res:
        accounts = json.loads(res.read().decode())
        active = [a for a in accounts if a.get("status") == "active"]
        print(f"Active Accounts: {len(active)}")
        for a in active:
            print(f"- {a['platform']}: {a['channel_name']} (ID: {a['id']})")
            
    print("\nFetching synced videos...")
    req = urllib.request.Request("http://localhost:8000/api/v1/videos/")
    with urllib.request.urlopen(req) as res:
        videos = json.loads(res.read().decode())
        print(f"Total Videos: {len(videos)}")
        for i, v in enumerate(videos[:5]):
            print(f"{i+1}. {v['original_filename']} - Status: {v['status']} (Drive ID: {v['drive_file_id']})")
            if v.get('error_message'):
                print(f"   Error: {v['error_message']}")

    print("\nFetching schedules...")
    req = urllib.request.Request("http://localhost:8000/api/v1/schedules/")
    with urllib.request.urlopen(req) as res:
        scheds = json.loads(res.read().decode())
        print(f"Total Schedules: {len(scheds)}")
        for s in scheds[:5]:
            print(f"Schedule {s['id']} - Published: {s['is_published']}, Time: {s['scheduled_time']}")
            if s.get('error_message'):
                print(f"   Error: {s['error_message']}")

except Exception as e:
    print("Error:", e)
