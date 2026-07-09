import io
import json
import os
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Tuple

import httpx

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

GOOGLE_APIS_BASE = "https://www.googleapis.com"
GOOGLE_OAUTH_BASE = "https://oauth2.googleapis.com"
DRIVE_DOWNLOAD_BASE = "https://drive.google.com/uc"
VIDEO_TMP_DIR = "/tmp/videos"


async def download_drive_video(
    file_id: str,
    access_token: str,
    output_dir: str = VIDEO_TMP_DIR,
    filename: Optional[str] = None,
) -> str:
    """
    Download a video from Google Drive using an authorized access token.
    Uses the Drive files.get API with alt=media for direct download.
    Returns the local path to the downloaded file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # First, get file metadata to get the filename
    metadata_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}?fields=name,size,mimeType"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        meta_response = await client.get(metadata_url, headers=headers)
        meta_response.raise_for_status()
        meta = meta_response.json()

    file_name = filename or meta.get("name", f"{file_id}.mp4")
    file_size = int(meta.get("size", 0))
    output_path = Path(output_dir) / file_name

    logger.info(f"Downloading Drive file: {file_name} ({file_size / 1024 / 1024:.1f} MB)")

    # Stream download
    download_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}?alt=media"
    async with httpx.AsyncClient(timeout=3600.0) as client:
        async with client.stream("GET", download_url, headers=headers) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    f.write(chunk)

    logger.info(f"Download complete: {output_path}")
    return str(output_path)


async def read_drive_file_text(file_id: str, access_token: str) -> str:
    """
    Downloads and reads a text file from Google Drive directly into memory.
    Useful for reading metadata (.txt) files quickly.
    """
    download_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}?alt=media"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(download_url, headers=headers)
        response.raise_for_status()
        return response.text


async def list_drive_folder_videos(folder_id: str, access_token: str) -> list[dict]:
    """
    List all video files in a Google Drive folder.
    Returns a list of file metadata dicts.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    query = f"'{folder_id}' in parents and trashed=false"

    all_files = []
    page_token = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            params = {
                "q": query,
                "fields": "files(id,name,size,mimeType,webViewLink,createdTime),nextPageToken",
                "pageSize": "1000",
            }
            if page_token:
                params["pageToken"] = page_token

            response = await client.get(
                f"{GOOGLE_APIS_BASE}/drive/v3/files",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            all_files.extend(data.get("files", []))

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    logger.info(f"Found {len(all_files)} videos in Drive folder {folder_id}")
    return all_files


def extract_folder_id_from_link(drive_link: str) -> Optional[str]:
    """Extract a Google Drive folder ID from a share URL."""
    if not drive_link or not isinstance(drive_link, str):
        return None
    import re
    patterns = [
        r"folders/([a-zA-Z0-9_-]{25,})",
        r"id=([a-zA-Z0-9_-]{25,})",
        r"/d/([a-zA-Z0-9_-]{25,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_link)
        if match:
            return match.group(1)
    # Fallback: if it's just a raw ID
    if re.match(r"^[a-zA-Z0-9_-]{25,}$", drive_link):
        return drive_link
    return None


async def upload_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    access_token: str,
    privacy_status: str = "public",
    credentials: Optional["Credentials"] = None,
) -> dict:
    """
    Upload a video to YouTube using the YouTube Data API v3.

    Prefers `credentials` (google.oauth2.credentials.Credentials) over raw
    `access_token`, because the Credentials object carries refresh_token +
    client_id/client_secret → the Google client library auto-refreshes the
    token if it expires mid-upload (large files can take >1 hour).

    Returns the upload response with video URL.
    """
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from googleapiclient.http import MediaFileUpload

    if credentials is None:
        # Fallback: build a bare Credentials from the raw access_token
        # (no refresh capability — only works if token is still valid)
        credentials = Credentials(token=access_token)

    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags[:500],
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/*",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            logger.info(f"YouTube upload progress: {progress}%")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
    logger.info(f"YouTube upload complete: {video_url}")
    
    try:
        from app.database import AsyncSessionLocal
        from app.services.api_rotation import increment_usage
        from app.models.models import Account
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            acc_res = await db.execute(select(Account).where(Account.id == credentials.account_id if hasattr(credentials, 'account_id') else None))
            acc = acc_res.scalar_one_or_none()
            if acc and acc.vault_id:
                await increment_usage(acc.vault_id, db, amount=1600) # YouTube upload is expensive (approx 1600 units)
    except Exception as e:
        logger.error(f"Failed to increment YouTube usage: {e}")

    return {"video_id": video_id, "url": video_url, "response": response}


async def upload_to_facebook(
    video_path: str,
    title: str,
    description: str,
    access_token: str,
    page_id: str,
    account_id: Optional[str] = None,
) -> dict:
    """Upload a video to a Facebook Page using the Graph API."""
    upload_url = f"https://graph-video.facebook.com/v19.0/{page_id}/videos"

    with open(video_path, "rb") as f:
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                upload_url,
                data={
                    "access_token": access_token,
                    "title": title[:255],
                    "description": description,
                    "published": "true",
                },
                files={"source": f},
            )
            response.raise_for_status()
            data = response.json()

    video_id = data.get("id")
    video_url = f"https://www.facebook.com/video/{video_id}" if video_id else ""
    logger.info(f"Facebook upload complete: {video_url}")

    try:
        if account_id:
            from app.database import AsyncSessionLocal
            from app.services.api_rotation import increment_usage
            from app.models.models import Account
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                import uuid
                acc_res = await db.execute(select(Account).where(Account.id == uuid.UUID(account_id)))
                acc = acc_res.scalar_one_or_none()
                if acc and acc.vault_id:
                    await increment_usage(acc.vault_id, db, amount=1)
    except Exception as e:
        logger.error(f"Failed to increment Meta usage: {e}")

    return {"video_id": video_id, "url": video_url, "response": data}


async def upload_photo_to_facebook(
    image_path: str,
    caption: str,
    access_token: str,
    page_id: str,
    account_id: Optional[str] = None,
) -> dict:
    """Upload a photo/image post to a Facebook Page using the Graph API."""
    upload_url = f"https://graph.facebook.com/v20.0/{page_id}/photos"

    with open(image_path, "rb") as f:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                upload_url,
                data={
                    "access_token": access_token,
                    "caption": caption,
                    "published": "true",
                },
                files={"source": f},
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Facebook photo upload failed. Status: {response.status_code}. Body: {response.text}")
                raise e
            data = response.json()

    photo_id = data.get("id")
    photo_url = f"https://www.facebook.com/photo?fbid={photo_id}" if photo_id else ""
    logger.info(f"Facebook photo upload complete: {photo_url}")

    try:
        if account_id:
            from app.database import AsyncSessionLocal
            from app.services.api_rotation import increment_usage
            from app.models.models import Account
            from sqlalchemy import select
            async with AsyncSessionLocal() as db:
                import uuid
                acc_res = await db.execute(select(Account).where(Account.id == uuid.UUID(account_id)))
                acc = acc_res.scalar_one_or_none()
                if acc and acc.vault_id:
                    await increment_usage(acc.vault_id, db, amount=1)
    except Exception as e:
        logger.error(f"Failed to increment Meta usage: {e}")

    return {"video_id": photo_id, "url": photo_url, "response": data}


async def delete_drive_file(file_id: str, access_token: str, parent_id: Optional[str] = None):
    """Deletes a file from Google Drive permanently, falling back to trash and parent removal if needed."""
    from typing import Optional
    import httpx
    url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    last_exception = None

    # Try permanent delete
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"Successfully permanently deleted Drive file: {file_id}")
            return
    except Exception as e:
        last_exception = e
        logger.warning(f"Failed to permanently delete Drive file {file_id}: {e}")

    # Fallback 1: Try trashing the file
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(url, headers=headers, json={"trashed": True})
            response.raise_for_status()
            logger.info(f"Successfully trashed Drive file: {file_id}")
            return
    except Exception as e:
        last_exception = e
        logger.warning(f"Failed to trash Drive file {file_id}: {e}")

    # Fallback 2: Try to remove the file from the parent folder (for shared drives/folders we don't own)
    if parent_id:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                remove_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}"
                params = {"removeParents": parent_id}
                response = await client.patch(remove_url, headers=headers, params=params)
                response.raise_for_status()
                logger.info(f"Successfully removed Drive file {file_id} from parent folder {parent_id}")
                return
        except Exception as e:
            last_exception = e
            logger.warning(f"Failed to remove Drive file {file_id} from parent folder {parent_id}: {e}")

    if last_exception:
        logger.error(f"Failed all delete fallbacks for Drive file {file_id}. Last error: {last_exception}")
        raise last_exception

async def upload_to_drive_public(
    local_file_path: Path,
    filename: str,
    access_token: str,
    folder_id: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Uploads a processed video back to a Google Drive folder and makes it public.
    Returns a tuple of (public webContentLink, file_id) or (None, None) if it fails.
    """
    import httpx
    import mimetypes
    
    # Guess the mime type
    mime_type, _ = mimetypes.guess_type(filename)
    mime_type = mime_type or "application/octet-stream"
    
    # Step 1: Upload the file
    upload_url = f"{GOOGLE_APIS_BASE}/upload/drive/v3/files?uploadType=multipart"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    metadata = {
        "name": f"processed_{filename}",
        "parents": [folder_id],
        "mimeType": mime_type
    }

    try:
        # We need sequential awaits for this to work cleanly with httpx
        with open(local_file_path, "rb") as f:
            files = {
                "metadata": (None, json.dumps(metadata), "application/json"),
                "file": (filename, f, mime_type),
            }
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(upload_url, headers=headers, files=files)
                response.raise_for_status()
                drive_file = response.json()
        
        file_id = drive_file.get("id")
        if not file_id:
            logger.error("Failed to get file ID after Drive upload.")
            return None, None

        # Step 2: Make the file public (Anyone with the link can view)
        permission_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}/permissions"
        permission_body = {
            "role": "reader",
            "type": "anyone"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            perm_response = await client.post(
                permission_url, 
                headers=headers, 
                json=permission_body
            )
            perm_response.raise_for_status()

        # Step 3: Get the webContentLink (download link)
        file_url = f"{GOOGLE_APIS_BASE}/drive/v3/files/{file_id}?fields=webContentLink"
        async with httpx.AsyncClient(timeout=30.0) as client:
            link_response = await client.get(file_url, headers=headers)
            link_response.raise_for_status()
            
            public_url = link_response.json().get("webContentLink")
            if not public_url:
                logger.error("Drive upload succeeded but webContentLink missing.")
                return None, None

        # Some consumers (e.g., Instagram Graph) are sensitive to redirects.
        # Resolve to a final direct URL (often drive.usercontent.google.com).
        direct_url = public_url
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                async with client.stream("GET", public_url) as r:
                    r.raise_for_status()
                    direct_url = str(r.url)
        except Exception:
            direct_url = public_url

        logger.info(f"Successfully uploaded to Drive public folder: {direct_url}")
        return direct_url, file_id
            
    except httpx.HTTPError as e:
        detail = ""
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = f" | status={e.response.status_code} body={e.response.text[:500]}"
            except Exception:
                detail = ""
        logger.error(f"HTTP Error during Drive upload: {e}{detail}")
        return None, None
    except Exception as e:
        logger.error(f"Error during Drive upload: {e}")
        return None, None


async def upload_to_instagram(
    video_path: str,
    caption: str,
    access_token: str,
    ig_user_id: str,
    google_access_token: str,
    target_folder_id: str,
) -> dict:
    """
    Upload a Reel to Instagram using resumable uploads (rupload.facebook.com).
    This avoids relying on a publicly reachable video_url which can fail in practice.
    """
    import asyncio

    api_version = "v19.0"

    # Step 1: Create container (resumable)
    container_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            container_url,
            data={
                "access_token": access_token,
                "media_type": "REELS",
                "caption": caption[:2200],
                "upload_type": "resumable",
            },
        )
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Instagram container create failed ({resp.status_code}): {resp.text[:500]}",
                request=resp.request,
                response=resp,
            )
        container_id = (resp.json() or {}).get("id")
        if not container_id:
            raise RuntimeError(f"Instagram container create returned no id. body={resp.text[:500]}")

    # Step 2: Upload bytes to Meta (rupload)
    import aiofiles

    file_size = os.path.getsize(video_path)
    upload_url = f"https://rupload.facebook.com/ig-api-upload/{api_version}/{container_id}"

    async with httpx.AsyncClient(timeout=180.0) as client:
        async with aiofiles.open(video_path, "rb") as f:
            payload = await f.read()
        resp = await client.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {access_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream",
                "Content-Length": str(file_size),
            },
            content=payload,
        )
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Instagram rupload failed ({resp.status_code}): {resp.text[:500]}",
                request=resp.request,
                response=resp,
            )
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json() or {}
            if data.get("success") is not True:
                raise RuntimeError(f"Instagram rupload returned failure: {str(data)[:500]}")

    # Step 3: Wait for processing
    status_url = f"https://graph.facebook.com/{api_version}/{container_id}"
    status_code = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(36):
            r = await client.get(status_url, params={"access_token": access_token, "fields": "status_code"})
            if r.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"Instagram container status failed ({r.status_code}): {r.text[:500]}",
                    request=r.request,
                    response=r,
                )
            status_code = (r.json() or {}).get("status_code")
            if status_code == "FINISHED":
                break
            if status_code == "ERROR":
                raise RuntimeError(f"Instagram container processing ERROR. body={r.text[:500]}")
            await asyncio.sleep(5)

    if status_code != "FINISHED":
        raise RuntimeError(f"Instagram container not ready. status_code={status_code}")

    # Step 4: Publish
    publish_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media_publish"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(publish_url, data={"access_token": access_token, "creation_id": container_id})
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Instagram media_publish failed ({resp.status_code}): {resp.text[:500]}",
                request=resp.request,
                response=resp,
            )
        data = resp.json()

    media_id = data.get("id")
    logger.info(f"Instagram upload complete. Media ID: {media_id}")
    return {"video_id": media_id, "url": f"https://www.instagram.com/reels/{media_id}/", "response": data}


async def upload_photo_to_instagram(
    image_path: str,
    caption: str,
    access_token: str,
    ig_user_id: str,
    google_access_token: str,
    target_folder_id: str,
) -> dict:
    """
    Upload a Photo/Image post to Instagram.
    Instagram Graph API requires a public URL for image uploads.
    We first upload the processed/raw image to the Google Drive public folder,
    get its public direct link, and use it as `image_url` to create the container.
    """
    import asyncio
    from pathlib import Path
    
    filename = Path(image_path).name
    public_url, drive_file_id = await upload_to_drive_public(
        local_file_path=Path(image_path),
        filename=filename,
        access_token=google_access_token,
        folder_id=target_folder_id,
    )
    
    if not public_url:
        raise RuntimeError("Failed to upload image to Google Drive public folder to get public URL for Instagram.")
        
    api_version = "v19.0"
    container_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"
    
    try:
        # Create container
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                container_url,
                data={
                    "access_token": access_token,
                    "image_url": public_url,
                    "caption": caption[:2200],
                },
            )
            if resp.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"Instagram image container create failed ({resp.status_code}): {resp.text[:500]}",
                    request=resp.request,
                    response=resp,
                )
            container_id = (resp.json() or {}).get("id")
            if not container_id:
                raise RuntimeError(f"Instagram image container create returned no id. body={resp.text[:500]}")

        # Wait for processing (usually instant for images)
        status_url = f"https://graph.facebook.com/{api_version}/{container_id}"
        status_code = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for _ in range(12):
                r = await client.get(status_url, params={"access_token": access_token, "fields": "status_code"})
                if r.status_code >= 400:
                    break
                status_code = (r.json() or {}).get("status_code")
                if status_code in ["FINISHED", "READY"] or not status_code:
                    break
                if status_code == "ERROR":
                    raise RuntimeError(f"Instagram container processing ERROR. body={r.text[:500]}")
                await asyncio.sleep(2)

        # Publish container
        publish_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media_publish"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(publish_url, data={"access_token": access_token, "creation_id": container_id})
            if resp.status_code >= 400:
                raise httpx.HTTPStatusError(
                    f"Instagram media_publish failed ({resp.status_code}): {resp.text[:500]}",
                    request=resp.request,
                    response=resp,
                )
            data = resp.json()

        media_id = data.get("id")
        logger.info(f"Instagram photo upload complete. Media ID: {media_id}")
        return {"video_id": media_id, "url": f"https://www.instagram.com/reels/{media_id}/", "response": data}
        
    finally:
        # Clean up temporary public file from Google Drive
        if drive_file_id:
            try:
                await delete_drive_file(drive_file_id, google_access_token, parent_id=target_folder_id)
                logger.info(f"Successfully cleaned up temporary public Drive file: {drive_file_id}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary public Drive file {drive_file_id}: {e}")


async def get_youtube_stats(video_id: str, access_token: str) -> dict:
    """Fetch views, likes, and comments for a YouTube video."""
    url = f"{GOOGLE_APIS_BASE}/youtube/v3/videos"
    params = {
        "part": "statistics",
        "id": video_id
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            if data.get("items"):
                stats = data["items"][0]["statistics"]
                return {
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                }
    except Exception as e:
        logger.error(f"Error fetching YouTube stats for {video_id}: {e}")
    return {}


async def get_facebook_stats(video_id: str, access_token: str) -> dict:
    """Fetch views, likes, and comments for a Facebook video/reel."""
    url = f"https://graph.facebook.com/v19.0/{video_id}"
    params = {
        "fields": "views,likes.summary(true),comments.summary(true)",
        "access_token": access_token
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            return {
                "view_count": int(data.get("views", 0)),
                "like_count": int(data.get("likes", {}).get("summary", {}).get("total_count", 0)),
                "comment_count": int(data.get("comments", {}).get("summary", {}).get("total_count", 0)),
            }
    except Exception as e:
        logger.error(f"Error fetching Facebook stats for {video_id}: {e}")
    return {}


async def get_instagram_stats(media_id: str, access_token: str) -> dict:
    """Fetch likes and comments for an Instagram media item."""
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    params = {
        "fields": "like_count,comments_count",
        "access_token": access_token
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            return {
                "view_count": 0, # Reels views often require separate insights permission
                "like_count": int(data.get("like_count", 0)),
                "comment_count": int(data.get("comments_count", 0)),
            }
    except Exception as e:
        logger.error(f"Error fetching Instagram stats for {media_id}: {e}")
    return {}

