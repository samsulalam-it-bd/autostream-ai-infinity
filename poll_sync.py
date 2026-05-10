import asyncio
import httpx
import time

async def poll_task():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Fetching accounts...")
        resp = await client.get("http://localhost:8000/api/v1/accounts/")
        accounts = resp.json()
        if not accounts:
            print("No accounts connected!")
            return
            
        test_acc = accounts[0]
        print(f"2. Using account: {test_acc['channel_name']} ({test_acc['platform']})")
        
        # User's exact link
        folder_link = "https://drive.google.com/drive/folders/17h3mQozyJ1p0SF_f7ofSWDT1OQf2ggOp?usp=sharing"
        print(f"3. Syncing folder: {folder_link}")
        
        sync_resp = await client.post("http://localhost:8000/api/v1/videos/sync-drive", json={
            "account_id": test_acc['id'],
            "folder_link": folder_link
        })
        sync_data = sync_resp.json()
        task_id = sync_data.get("task_id")
        
        print(f"4. Task ID: {task_id}")
        
        print("5. Polling for results...")
        for _ in range(20):
            time.sleep(2)
            status_resp = await client.get(f"http://localhost:8000/api/v1/videos/task-status/{task_id}")
            st = status_resp.json()
            print(f"   -> Status: {st['status']}")
            if st['status'] in ['SUCCESS', 'FAILURE']:
                print(f"   -> Result: {st['result']}")
                break

if __name__ == "__main__":
    asyncio.run(poll_task())
