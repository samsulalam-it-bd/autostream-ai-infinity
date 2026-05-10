import requests
import time

def test_all():
    print("1. Fetching accounts...")
    resp = requests.get("http://localhost:8000/api/v1/accounts/")
    accounts = resp.json()
    
    folder_link = "https://drive.google.com/drive/folders/1Zh3mQozyJJp0SF_f7ofSWDT1OOE2gGOp?usp=sharing"
    
    for acc in accounts:
        if acc['status'] != 'active': continue
        print(f"\n-> Triggering Sync for: {acc['channel_name']} ({acc['platform']})")
        sync_resp = requests.post("http://localhost:8000/api/v1/videos/sync-drive", json={
            "account_id": acc['id'],
            "folder_link": folder_link
        })
        
        data = sync_resp.json()
        task_id = data.get('task_id')
        print(f"Task ID: {task_id}")
        
        # Poll
        for _ in range(15):
            time.sleep(2)
            st_resp = requests.get(f"http://localhost:8000/api/v1/videos/task-status/{task_id}")
            st = st_resp.json()
            if st['status'] in ['SUCCESS', 'FAILURE']:
                print(f"Final Status: {st['status']}")
                print(f"Result: {st['result']}")
                break
        else:
            print("Task timed out")

if __name__ == "__main__":
    test_all()
