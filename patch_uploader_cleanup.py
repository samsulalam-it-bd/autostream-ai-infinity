import re
from pathlib import Path

file_path = Path(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\backend\app\services\uploader.py")
content = file_path.read_text(encoding="utf-8")

# 1. Update typing import
content = content.replace(
    "from typing import Optional, TYPE_CHECKING",
    "from typing import Optional, TYPE_CHECKING, Tuple"
)

# 2. Add delete_drive_file function
delete_func = """
async def delete_drive_file(file_id: str, access_token: str):
    \"\"\"Deletes a file from Google Drive.\"\"\"
    import httpx
    url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Successfully deleted temporary Drive file: {file_id}")
    except Exception as e:
        logger.error(f"Failed to delete temporary Drive file {file_id}: {e}")

"""

# Insert it before upload_to_drive_public
content = content.replace("async def upload_to_drive_public(", delete_func + "async def upload_to_drive_public(")

# 3. Modify upload_to_drive_public signature and return values
content = content.replace(
    ") -> Optional[str]:",
    ") -> Tuple[Optional[str], Optional[str]]:"
)

content = content.replace(
    "return None",
    "return None, None"
)

content = content.replace(
    "return public_url",
    "return public_url, file_id"
)

# 4. Update upload_to_instagram to unpack and clean up
old_ig = """    public_video_url = await upload_to_drive_public(
        video_path, 
        filename, 
        google_access_token, 
        target_folder_id
    )
    
    if not public_video_url:
        raise RuntimeError("Failed to upload video to Drive. Cannot proceed with Instagram upload.")

    # Step 1: Create media container
    container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            container_url,
            data={
                "access_token": access_token,
                "media_type": "REELS",
                "video_url": public_video_url,
                "caption": caption[:2200],
            }
        )
        response.raise_for_status()
        container_id = response.json().get("id")

    # Step 2: Publish container
    publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            publish_url,
            data={"access_token": access_token, "creation_id": container_id}
        )
        response.raise_for_status()
        data = response.json()

    media_id = data.get("id")
    logger.info(f"Instagram upload complete. Media ID: {media_id}")
    return {"media_id": media_id, "url": f"https://www.instagram.com/p/{media_id}/", "response": data}"""

new_ig = """    public_video_url, file_id = await upload_to_drive_public(
        video_path, 
        filename, 
        google_access_token, 
        target_folder_id
    )
    
    if not public_video_url or not file_id:
        raise RuntimeError("Failed to upload video to Drive. Cannot proceed with Instagram upload.")

    try:
        # Step 1: Create media container
        container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                container_url,
                data={
                    "access_token": access_token,
                    "media_type": "REELS",
                    "video_url": public_video_url,
                    "caption": caption[:2200],
                }
            )
            response.raise_for_status()
            container_id = response.json().get("id")

        # Step 2: Publish container
        publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                publish_url,
                data={"access_token": access_token, "creation_id": container_id}
            )
            response.raise_for_status()
            data = response.json()

        media_id = data.get("id")
        logger.info(f"Instagram upload complete. Media ID: {media_id}")
        return {"media_id": media_id, "url": f"https://www.instagram.com/p/{media_id}/", "response": data}
    finally:
        # Step 3: Clean up temporary Drive file
        await delete_drive_file(file_id, google_access_token)"""

content = content.replace(old_ig, new_ig)

file_path.write_text(content, encoding="utf-8")
print("Uploader updated successfully!")
