import os
import sys
import subprocess
import json
import asyncio

async def test_db():
    try:
        from sqlalchemy import select
        from app.database import AsyncSessionLocal
        from app.models.models import UploadSchedule, SourceVideo
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(UploadSchedule).order_by(UploadSchedule.created_at.desc()).limit(10))
            schedules = result.scalars().all()
            
            output = []
            for s in schedules:
                output.append({
                    "id": str(s.id),
                    "video_id": str(s.video_id),
                    "account_id": str(s.account_id),
                    "is_published": s.is_published,
                    "error_message": s.error_message,
                    "celery_task_id": s.celery_task_id,
                    "target_group_id": str(s.target_group_id) if s.target_group_id else None
                })
            
            with open("db_diagnostic_raw.json", "w") as f:
                json.dump(output, f, indent=2)
            print("DB Diagnostic successful")
    except Exception as e:
        with open("db_diagnostic_raw.json", "w") as f:
            f.write(f"DB Error: {str(e)}")
        print("DB Diagnostic Failed")

if __name__ == "__main__":
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        # Check docker
        out = subprocess.check_output("docker ps", shell=True).decode()
        with open("docker_ps_raw.txt", "w") as f:
            f.write(out)
        
        asyncio.run(test_db())
    except Exception as e:
        with open("crash_log.txt", "w") as f:
            f.write(f"Fatal error: {str(e)}")
