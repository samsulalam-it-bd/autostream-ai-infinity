path = r"f:\autostream-ai\backend\app\routers\schedules.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = """
@router.patch("/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(
    schedule_id: uuid.UUID,
    updates: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Update any field of a schedule, including metadata_overrides (title, desc, branding).\"\"\"
    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if "scheduled_time" in updates:
        try:
            schedule.scheduled_time = datetime.fromisoformat(updates["scheduled_time"].replace("Z", "+00:00"))
        except: pass
    
    if "add_watermark" in updates:
        schedule.add_watermark = bool(updates["add_watermark"])
    
    if "metadata" in updates:
        if schedule.metadata_overrides is None:
            schedule.metadata_overrides = {}
        # Merge metadata (title, description, tags, overlays)
        current = dict(schedule.metadata_overrides)
        current.update(updates["metadata"])
        schedule.metadata_overrides = current
            
    await db.commit()
    await db.refresh(schedule)
    return schedule

@router.post("/{schedule_id}/replace", response_model=ScheduleOut)
async def replace_schedule_video(
    schedule_id: uuid.UUID,
    new_video_id: uuid.UUID = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Swap the source video for an existing schedule while keeping its metadata/time.\"\"\"
    result = await db.execute(select(UploadSchedule).where(UploadSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.video_id = new_video_id
    await db.commit()
    await db.refresh(schedule)
    return schedule
"""

# Append before the last return if it exists or just at the end
if "if __name__" in content:
    content = content.replace("if __name__", new_endpoints + "\n\nif __name__")
else:
    content += new_endpoints

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("schedules.py updated with PATCH and REPLACE.")
