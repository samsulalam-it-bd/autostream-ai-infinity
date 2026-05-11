
import sys
import os

path = r"f:\autostream-ai\backend\app\routers\accounts.py"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "return result.scalars().all()" in line and i > 50 and i < 65:
        # Found it
        indent = line[:line.find("return")]
        new_lines.append(f"{indent}accounts = result.scalars().all()\n")
        new_lines.append("\n")
        new_lines.append(f"{indent}from app.models.models import UploadSchedule\n")
        new_lines.append(f"{indent}from sqlalchemy import func\n")
        new_lines.append(f"{indent}enriched = []\n")
        new_lines.append(f"{indent}now = datetime.now(timezone.utc)\n")
        new_lines.append(f"{indent}for acc in accounts:\n")
        new_lines.append(f"{indent}    # Published count\n")
        new_lines.append(f"{indent}    pub_res = await db.execute(select(func.count(UploadSchedule.id)).where(\n")
        new_lines.append(f"{indent}        UploadSchedule.account_id == acc.id, UploadSchedule.is_published == True\n")
        new_lines.append(f"{indent}    ))\n")
        new_lines.append(f"{indent}    # Pending count\n")
        new_lines.append(f"{indent}    pen_res = await db.execute(select(func.count(UploadSchedule.id)).where(\n")
        new_lines.append(f"{indent}        UploadSchedule.account_id == acc.id, UploadSchedule.is_published == False, UploadSchedule.error_message == None, UploadSchedule.scheduled_time >= now\n")
        new_lines.append(f"{indent}    ))\n")
        new_lines.append(f"{indent}    # Failed count\n")
        new_lines.append(f"{indent}    fail_res = await db.execute(select(func.count(UploadSchedule.id)).where(\n")
        new_lines.append(f"{indent}        UploadSchedule.account_id == acc.id, UploadSchedule.error_message != None\n")
        new_lines.append(f"{indent}    ))\n")
        new_lines.append(f"{indent}    # Queue (Total pending regardless of time)\n")
        new_lines.append(f"{indent}    que_res = await db.execute(select(func.count(UploadSchedule.id)).where(\n")
        new_lines.append(f"{indent}        UploadSchedule.account_id == acc.id, UploadSchedule.is_published == False\n")
        new_lines.append(f"{indent}    ))\n")
        new_lines.append("\n")
        new_lines.append(f"{indent}    acc.stats = {{\n")
        new_lines.append(f"{indent}        'published': pub_res.scalar() or 0,\n")
        new_lines.append(f"{indent}        'pending': pen_res.scalar() or 0,\n")
        new_lines.append(f"{indent}        'failed': fail_res.scalar() or 0,\n")
        new_lines.append(f"{indent}        'queue': que_res.scalar() or 0\n")
        new_lines.append(f"{indent}    }}\n")
        new_lines.append(f"{indent}    enriched.append(acc)\n")
        new_lines.append(f"{indent}return enriched\n")
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Successfully patched accounts.py")
