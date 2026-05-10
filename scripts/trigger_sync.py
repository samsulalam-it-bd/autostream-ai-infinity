import asyncio
import sys
import os
from pathlib import Path

# Fix import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.worker import sync_drive_folder

def main():
    folder_link = "https://drive.google.com/drive/folders/1Zh3mQozyJJp0SF_f7ofSWDT1OOE2gGOp"
    account_id = "25ffcc80-8901-4c67-a590-e6a6ef878020" # Instagram account
    
    print(f"Triggering sync for folder: {folder_link}")
    task = sync_drive_folder.apply_async(args=[folder_link, account_id])
    print(f"Task ID: {task.id}")

if __name__ == "__main__":
    main()
