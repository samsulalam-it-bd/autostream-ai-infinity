path = r"f:\autostream-ai\backend\app\worker.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Retry Logic to decorator
old_decorator = '@celery_app.task(name="app.worker.process_and_upload_video", bind=True, queue="video_pipeline")'
new_decorator = """@celery_app.task(
    name="app.worker.process_and_upload_video",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    queue="video_pipeline"
)"""
content = content.replace(old_decorator, new_decorator)

# 2. Add Target Platform for smart formatting
old_processing = """                # ── Step 4: Process video (Watermark, etc.) ──────────────────────
                logger.info(f"[Pipeline] Processing video: {video.original_filename}")
                processed_path = process_video(
                    input_path=local_video_path,
                    add_watermark=schedule.add_watermark,
                    text_text=schedule.text_overlay or "",
                )"""

new_processing = """                # ── Step 4: Process video (Watermark, etc.) ──────────────────────
                logger.info(f"[Pipeline] Processing video: {video.original_filename}")
                
                # Determine target platform for smart formatting
                target_platform = account.platform.value
                if target_platform == "instagram":
                    target_platform = "instagram" # Reels
                elif target_platform == "youtube":
                    target_platform = "youtube_shorts" # Assume shorts for auto-reels logic
                elif target_platform == "facebook":
                    target_platform = "facebook_reels"

                processed_path = process_video(
                    input_path=local_video_path,
                    add_watermark=schedule.add_watermark,
                    text_text=schedule.text_overlay or "",
                    target_platform=target_platform
                )"""
content = content.replace(old_processing, new_processing)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("worker.py updated successfully.")
