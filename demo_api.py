#!/usr/bin/env python3
"""
AutoStream AI Infinity — Demo API Server
=========================================
Zero-dependency mock API server using Python stdlib only.
Simulates ALL backend endpoints with realistic mock data.

Usage:
    python demo_api.py

Then open:  http://localhost:8000/docs-demo  (API test page)
Or open:   demo.html  in your browser (connects automatically)

Works with Python 3.8+. No pip installs required.
"""

import json
import uuid
import time
import random
import threading
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Mock Database (in-memory) ─────────────────────────────────────────────
DB = {
    "channel_groups": [
        {"id": "a1b2c3d4-0001-0001-0001-000000000001", "name": "Gaming Network", "platform": "youtube", "description": "Primary gaming channels", "created_at": "2025-01-10T10:00:00Z"},
        {"id": "a1b2c3d4-0002-0002-0002-000000000002", "name": "Tech Reviews Hub", "platform": "youtube", "description": "Tech review channels", "created_at": "2025-01-12T10:00:00Z"},
        {"id": "a1b2c3d4-0003-0003-0003-000000000003", "name": "Facebook Pages", "platform": "facebook", "description": "All FB pages", "created_at": "2025-01-15T10:00:00Z"},
    ],
    "accounts": [
        {"id": "acc00001-0001-0001-0001-000000000001", "platform": "youtube", "channel_name": "TechReviews Central", "channel_id": "UC_tech_001", "group_id": "a1b2c3d4-0002-0002-0002-000000000002", "status": "active", "avatar_url": None, "subscriber_count": 2340000, "created_at": "2025-01-10T10:00:00Z"},
        {"id": "acc00002-0002-0002-0002-000000000002", "platform": "youtube", "channel_name": "Gaming Network Hub", "channel_id": "UC_gaming_002", "group_id": "a1b2c3d4-0001-0001-0001-000000000001", "status": "active", "avatar_url": None, "subscriber_count": 890500, "created_at": "2025-01-11T10:00:00Z"},
        {"id": "acc00003-0003-0003-0003-000000000003", "platform": "youtube", "channel_name": "Daily Vlogs Channel", "channel_id": "UC_vlogs_003", "group_id": None, "status": "expired", "avatar_url": None, "subscriber_count": 120000, "created_at": "2025-01-13T10:00:00Z"},
        {"id": "acc00004-0004-0004-0004-000000000004", "platform": "facebook", "channel_name": "Tech Page Official", "channel_id": "fb_tech_001", "group_id": "a1b2c3d4-0003-0003-0003-000000000003", "status": "active", "avatar_url": None, "subscriber_count": 567000, "created_at": "2025-01-14T10:00:00Z"},
        {"id": "acc00005-0005-0005-0005-000000000005", "platform": "instagram", "channel_name": "@techreviews_ig", "channel_id": "ig_tech_001", "group_id": None, "status": "active", "avatar_url": None, "subscriber_count": 1200000, "created_at": "2025-01-15T10:00:00Z"},
    ],
    "api_keys": [
        {"id": "key00001-0001-0001-0001-000000000001", "service_name": "google", "project_name": "autostream-prod-01", "daily_usage": 2340, "daily_limit": 10000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": "2025-01-10T10:00:00Z"},
        {"id": "key00002-0002-0002-0002-000000000002", "service_name": "google", "project_name": "autostream-prod-02", "daily_usage": 8900, "daily_limit": 10000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": "2025-01-11T10:00:00Z"},
        {"id": "key00003-0003-0003-0003-000000000003", "service_name": "google", "project_name": "autostream-backup-03", "daily_usage": 10000, "daily_limit": 10000, "is_locked": True, "unlock_time": "2026-02-26T10:00:00Z", "lock_reason": "403 Quota Exceeded", "created_at": "2025-01-12T10:00:00Z"},
        {"id": "key00004-0004-0004-0004-000000000004", "service_name": "google", "project_name": "autostream-prod-04", "daily_usage": 1200, "daily_limit": 10000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": "2025-01-13T10:00:00Z"},
        {"id": "key00005-0005-0005-0005-000000000005", "service_name": "google", "project_name": "autostream-prod-05", "daily_usage": 500, "daily_limit": 10000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": "2025-01-14T10:00:00Z"},
        {"id": "key00006-0006-0006-0006-000000000006", "service_name": "meta", "project_name": "meta-app-01", "daily_usage": 3000, "daily_limit": 200000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": "2025-01-15T10:00:00Z"},
    ],
    "videos": [
        {"id": "vid00001-0001-0001-0001-000000000001", "drive_file_id": "1Bx9mAbCdEfGhIj001", "drive_view_link": "https://drive.google.com/file/d/1Bx9mAbCdEfGhIj001", "original_filename": "viral_gaming_clip_001.mp4", "file_size_bytes": 142500000, "ai_title": "You Won't BELIEVE This Gaming Setup!! 🤯", "ai_description": "Check out the most insane gaming setup we've ever reviewed...", "ai_tags": ["gaming", "setup", "viral", "review"], "ai_hashtags": ["#gaming", "#viral", "#fyp", "#setup"], "status": "pending", "error_message": None, "created_at": "2025-02-01T10:00:00Z"},
        {"id": "vid00002-0002-0002-0002-000000000002", "drive_file_id": "1Bx9mAbCdEfGhIj002", "drive_view_link": "https://drive.google.com/file/d/1Bx9mAbCdEfGhIj002", "original_filename": "tech_review_iphone16.mp4", "file_size_bytes": 285000000, "ai_title": None, "ai_description": None, "ai_tags": None, "ai_hashtags": None, "status": "synced", "error_message": None, "created_at": "2025-02-02T10:00:00Z"},
        {"id": "vid00003-0003-0003-0003-000000000003", "drive_file_id": "1Bx9mAbCdEfGhIj003", "drive_view_link": "https://drive.google.com/file/d/1Bx9mAbCdEfGhIj003", "original_filename": "daily_vlog_episode_42.mp4", "file_size_bytes": 98000000, "ai_title": "My UNFILTERED Tokyo Day Vlog (You Asked For This...)", "ai_description": "Finally showing the raw, unfiltered side of life...", "ai_tags": ["vlog", "tokyo", "travel", "daily"], "ai_hashtags": ["#vlog", "#tokyo", "#travel", "#dailyvlog"], "status": "uploaded", "error_message": None, "created_at": "2025-02-03T10:00:00Z"},
        {"id": "vid00004-0004-0004-0004-000000000004", "drive_file_id": "1Bx9mAbCdEfGhIj004", "drive_view_link": "https://drive.google.com/file/d/1Bx9mAbCdEfGhIj004", "original_filename": "coding_tutorial_react.mp4", "file_size_bytes": 210000000, "ai_title": None, "ai_description": None, "ai_tags": None, "ai_hashtags": None, "status": "pending", "error_message": None, "created_at": "2025-02-04T10:00:00Z"},
        {"id": "vid00005-0005-0005-0005-000000000005", "drive_file_id": "1Bx9mAbCdEfGhIj005", "drive_view_link": "https://drive.google.com/file/d/1Bx9mAbCdEfGhIj005", "original_filename": "travel_vlog_tokyo_2025.mp4", "file_size_bytes": 312000000, "ai_title": None, "ai_description": None, "ai_tags": None, "ai_hashtags": None, "status": "processing", "error_message": None, "created_at": "2025-02-05T10:00:00Z"},
    ],
    "schedules": [
        {"id": "sch00001-0001-0001-0001-000000000001", "video_id": "vid00001-0001-0001-0001-000000000001", "target_group_id": "a1b2c3d4-0001-0001-0001-000000000001", "account_id": None, "scheduled_time": "2026-02-25T16:00:00Z", "is_published": False, "published_at": None, "published_url": None, "add_watermark": True, "auto_comment": False, "celery_task_id": "celery-task-abc123", "error_message": None, "retry_count": 0, "created_at": "2025-02-20T10:00:00Z"},
        {"id": "sch00002-0002-0002-0002-000000000002", "video_id": "vid00002-0002-0002-0002-000000000002", "target_group_id": None, "account_id": "acc00001-0001-0001-0001-000000000001", "scheduled_time": "2026-02-26T10:00:00Z", "is_published": False, "published_at": None, "published_url": None, "add_watermark": True, "auto_comment": True, "celery_task_id": None, "error_message": None, "retry_count": 0, "created_at": "2025-02-21T10:00:00Z"},
        {"id": "sch00003-0003-0003-0003-000000000003", "video_id": "vid00003-0003-0003-0003-000000000003", "target_group_id": None, "account_id": "acc00002-0002-0002-0002-000000000002", "scheduled_time": "2026-02-24T08:00:00Z", "is_published": True, "published_at": "2026-02-24T08:02:00Z", "published_url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "add_watermark": True, "auto_comment": False, "celery_task_id": "celery-task-done456", "error_message": None, "retry_count": 0, "created_at": "2025-02-22T10:00:00Z"},
    ],
    "logs": [],
}

LOG_SOURCES = ["beat_scheduler", "celery_worker", "ffmpeg_engine", "gemini_ai", "drive_downloader", "youtube_uploader", "telegram_bot", "api_rotation", "system"]
LOG_MESSAGES = [
    ("INFO",    "beat_scheduler",    "Checking pending schedules... Found 2 upcoming uploads"),
    ("INFO",    "celery_worker",     "[Pipeline] Starting: viral_gaming_clip_001.mp4"),
    ("INFO",    "drive_downloader",  "Downloading from Drive (1Bx9mAbC) — 142.5 MB"),
    ("SUCCESS", "drive_downloader",  "Download complete: /tmp/videos/viral_gaming_clip_001.mp4"),
    ("INFO",    "ffmpeg_engine",     "Running FFmpeg: crop=iw-1:ih-1, brightness+0.01, watermark overlay"),
    ("SUCCESS", "ffmpeg_engine",     "FFmpeg complete → /tmp/videos/processed_viral_gaming_clip_001.mp4"),
    ("INFO",    "gemini_ai",         "Extracting 3 frames for Gemini 1.5 Flash analysis..."),
    ("SUCCESS", "gemini_ai",         'AI title generated: "You Won\'t BELIEVE This Gaming Setup!! 🤯"'),
    ("INFO",    "youtube_uploader",  "Uploading to YouTube — TechReviews Central (progress 45%)"),
    ("SUCCESS", "youtube_uploader",  "Upload complete → https://youtube.com/watch?v=dQw4w9WgXcQ"),
    ("INFO",    "telegram_bot",      "✅ Alert sent: Upload Successful on TechReviews Central"),
    ("INFO",    "api_rotation",      "Rotating API key: autostream-prod-01 → selected"),
    ("WARNING", "api_rotation",      "Key autostream-prod-02 near daily limit (8900/10000)"),
    ("ERROR",   "api_rotation",      "403 Quota Exceeded on autostream-backup-03 → Locked 24h"),
    ("INFO",    "cleanup",           "Deleted temp files from /tmp/videos/ (3 files, 640 MB freed)"),
]

def add_log(level, source, message, extra=None):
    DB["logs"].append({
        "id": str(uuid.uuid4()),
        "level": level,
        "source": source,
        "message": message,
        "extra_data": extra,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    if len(DB["logs"]) > 500:
        DB["logs"] = DB["logs"][-500:]

# Seed some initial logs
for lvl, src, msg in LOG_MESSAGES[:6]:
    add_log(lvl, src, msg)


# ── HTTP Handler ──────────────────────────────────────────────────────────
class APIHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default server logs

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def send_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try:
                return json.loads(self.rfile.read(length))
            except Exception:
                return {}
        return {}

    def route(self, method, path, query):
        p = path.rstrip("/")

        # ── Root / docs-demo ─────────────────────────────────────────────
        if p in ("", "/", "/api/v1"):
            return self.send_json({"name": "AutoStream AI Infinity Demo API", "version": "1.0.0", "docs": "/docs-demo"})

        if p == "/docs-demo":
            return self.serve_docs()

        if p == "/health":
            return self.send_json({"status": "ok"})

        # ── Dashboard ─────────────────────────────────────────────────────
        if p == "/api/v1/dashboard/stats":
            return self.send_json({
                "total_uploads_today": 47,
                "active_api_keys": len([k for k in DB["api_keys"] if not k["is_locked"]]),
                "pending_schedules": len([s for s in DB["schedules"] if not s["is_published"]]),
                "total_accounts": len(DB["accounts"]),
                "total_videos": len(DB["videos"]),
            })

        if p == "/api/v1/dashboard/health":
            return self.send_json({"database": "healthy", "redis": "healthy", "celery": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})

        # ── Channel Groups ────────────────────────────────────────────────
        if p == "/api/v1/accounts/groups" and method == "GET":
            return self.send_json(DB["channel_groups"])

        if p == "/api/v1/accounts/groups" and method == "POST":
            body = self.read_body()
            new_group = {"id": str(uuid.uuid4()), "name": body.get("name", "New Group"), "platform": body.get("platform", "youtube"), "description": body.get("description"), "created_at": datetime.now(timezone.utc).isoformat()}
            DB["channel_groups"].append(new_group)
            add_log("INFO", "api", f"Channel group created: {new_group['name']}")
            return self.send_json(new_group, 201)

        if p.startswith("/api/v1/accounts/groups/") and method == "DELETE":
            gid = p.split("/")[-1]
            DB["channel_groups"] = [g for g in DB["channel_groups"] if g["id"] != gid]
            add_log("INFO", "api", f"Channel group deleted: {gid}")
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            return

        # ── Accounts ──────────────────────────────────────────────────────
        if p == "/api/v1/accounts/" and method == "GET":
            platform = query.get("platform", [None])[0]
            result = DB["accounts"] if not platform else [a for a in DB["accounts"] if a["platform"] == platform]
            return self.send_json(result)

        if p == "/api/v1/accounts/" and method == "POST":
            body = self.read_body()
            new_acc = {"id": str(uuid.uuid4()), "platform": body.get("platform", "youtube"), "channel_name": body.get("channel_name", "New Channel"), "channel_id": body.get("channel_id"), "group_id": body.get("group_id"), "status": "active", "avatar_url": body.get("avatar_url"), "subscriber_count": body.get("subscriber_count", 0), "created_at": datetime.now(timezone.utc).isoformat()}
            DB["accounts"].append(new_acc)
            add_log("SUCCESS", "api", f"Account created: {new_acc['channel_name']} ({new_acc['platform']})")
            return self.send_json(new_acc, 201)

        if p.startswith("/api/v1/accounts/oauth/google/init"):
            return self.send_json({"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=DEMO&scope=youtube.upload"})

        if p.startswith("/api/v1/accounts/") and method == "DELETE":
            aid = p.split("/")[-1]
            DB["accounts"] = [a for a in DB["accounts"] if a["id"] != aid]
            add_log("INFO", "api", f"Account deleted: {aid}")
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            return

        if p.startswith("/api/v1/accounts/") and method == "PATCH":
            aid = p.split("/")[-1]
            body = self.read_body()
            for acc in DB["accounts"]:
                if acc["id"] == aid:
                    acc.update({k: v for k, v in body.items() if v is not None})
                    add_log("INFO", "api", f"Account updated: {acc['channel_name']}")
                    return self.send_json(acc)
            return self.send_json({"detail": "Not found"}, 404)

        if p.startswith("/api/v1/accounts/") and method == "GET":
            aid = p.split("/")[-1]
            for acc in DB["accounts"]:
                if acc["id"] == aid:
                    return self.send_json(acc)
            return self.send_json({"detail": "Not found"}, 404)

        # ── API Vault ─────────────────────────────────────────────────────
        if p == "/api/v1/api-vault/" and method == "GET":
            svc = query.get("service_name", [None])[0]
            result = DB["api_keys"] if not svc else [k for k in DB["api_keys"] if k["service_name"] == svc]
            return self.send_json(result)

        if p == "/api/v1/api-vault/stats/summary":
            return self.send_json({"total": len(DB["api_keys"]), "active": len([k for k in DB["api_keys"] if not k["is_locked"]]), "locked": len([k for k in DB["api_keys"] if k["is_locked"]])})

        if p == "/api/v1/api-vault/upload-json" and method == "POST":
            # Multipart — just simulate adding keys
            n = random.randint(1, 5)
            for i in range(n):
                new_key = {"id": str(uuid.uuid4()), "service_name": "google", "project_name": f"demo-project-{int(time.time())}-{i}", "daily_usage": 0, "daily_limit": 10000, "is_locked": False, "unlock_time": None, "lock_reason": None, "created_at": datetime.now(timezone.utc).isoformat()}
                DB["api_keys"].append(new_key)
            add_log("SUCCESS", "api_vault", f"Uploaded {n} new API key credentials to vault")
            return self.send_json({"added": n, "skipped": 0, "errors": [], "message": f"Successfully added {n} API key(s). Skipped 0 duplicates."}, 201)

        if p.startswith("/api/v1/api-vault/") and "/unlock" in p and method == "POST":
            kid = p.split("/")[-2]
            for k in DB["api_keys"]:
                if k["id"] == kid:
                    k["is_locked"] = False; k["unlock_time"] = None; k["lock_reason"] = None; k["daily_usage"] = 0
                    add_log("INFO", "api_rotation", f"Key manually unlocked: {k['project_name']}")
                    return self.send_json(k)
            return self.send_json({"detail": "Not found"}, 404)

        if p.startswith("/api/v1/api-vault/") and method == "DELETE":
            kid = p.split("/")[-1]
            DB["api_keys"] = [k for k in DB["api_keys"] if k["id"] != kid]
            add_log("INFO", "api_vault", f"API key deleted: {kid}")
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            return

        # ── Videos ───────────────────────────────────────────────────────
        if p == "/api/v1/videos/" and method == "GET":
            sf = query.get("status_filter", [None])[0]
            result = DB["videos"] if not sf else [v for v in DB["videos"] if v["status"] == sf]
            return self.send_json(result)

        if p == "/api/v1/videos/sync-drive" and method == "POST":
            body = self.read_body()
            folder_link = body.get("folder_link", "")
            task_id = f"celery-sync-{uuid.uuid4().hex[:8]}"
            # Simulate adding 3 new videos
            for i in range(3):
                fid = uuid.uuid4().hex[:16]
                DB["videos"].append({"id": str(uuid.uuid4()), "drive_file_id": fid, "drive_view_link": f"https://drive.google.com/file/d/{fid}", "original_filename": f"synced_video_{int(time.time())}_{i+1}.mp4", "file_size_bytes": random.randint(50, 500) * 1000000, "ai_title": None, "ai_description": None, "ai_tags": None, "ai_hashtags": None, "status": "synced", "error_message": None, "created_at": datetime.now(timezone.utc).isoformat()})
            add_log("INFO", "drive_downloader", f"Synced Drive folder: {folder_link[:60]}...")
            add_log("SUCCESS", "drive_downloader", f"Found and imported 3 new videos from Drive")
            return self.send_json({"task_id": task_id, "message": "Drive sync started. Videos will appear in the list once synced."}, 202)

        if p.startswith("/api/v1/videos/task-status/"):
            return self.send_json({"task_id": p.split("/")[-1], "status": "SUCCESS", "result": {"synced": 3, "total": 3}})

        if p.startswith("/api/v1/videos/") and method == "DELETE":
            vid = p.split("/")[-1]
            DB["videos"] = [v for v in DB["videos"] if v["id"] != vid]
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            return

        if p.startswith("/api/v1/videos/") and method == "GET":
            vid = p.split("/")[-1]
            for v in DB["videos"]:
                if v["id"] == vid:
                    return self.send_json(v)
            return self.send_json({"detail": "Not found"}, 404)

        # ── Schedules ─────────────────────────────────────────────────────
        if p == "/api/v1/schedules/" and method == "GET":
            ip = query.get("is_published", [None])[0]
            if ip is not None:
                result = [s for s in DB["schedules"] if str(s["is_published"]).lower() == ip.lower()]
            else:
                result = DB["schedules"]
            return self.send_json(result)

        if p == "/api/v1/schedules/" and method == "POST":
            body = self.read_body()
            new_sch = {"id": str(uuid.uuid4()), "video_id": body.get("video_id"), "target_group_id": body.get("target_group_id"), "account_id": body.get("account_id"), "scheduled_time": body.get("scheduled_time"), "is_published": False, "published_at": None, "published_url": None, "add_watermark": body.get("add_watermark", True), "auto_comment": body.get("auto_comment", False), "celery_task_id": None, "error_message": None, "retry_count": 0, "created_at": datetime.now(timezone.utc).isoformat()}
            DB["schedules"].append(new_sch)
            add_log("INFO", "beat_scheduler", f"New schedule created for video: {new_sch['video_id']}")
            return self.send_json(new_sch, 201)

        if p == "/api/v1/schedules/auto-drip" and method == "POST":
            body = self.read_body()
            video_ids = body.get("video_ids", [])
            total_days = int(body.get("total_days", 7))
            start = body.get("start_datetime", datetime.now(timezone.utc).isoformat())
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            except Exception:
                start_dt = datetime.now(timezone.utc)
            interval = (total_days * 86400) / max(len(video_ids), 1)
            for i, vid in enumerate(video_ids):
                slot = start_dt + timedelta(seconds=interval * i)
                sch = {"id": str(uuid.uuid4()), "video_id": vid, "target_group_id": body.get("target_group_id"), "account_id": body.get("account_id"), "scheduled_time": slot.isoformat(), "is_published": False, "published_at": None, "published_url": None, "add_watermark": body.get("add_watermark", True), "auto_comment": body.get("auto_comment", False), "celery_task_id": None, "error_message": None, "retry_count": 0, "created_at": datetime.now(timezone.utc).isoformat()}
                DB["schedules"].append(sch)
            interval_h = round(interval / 3600, 2)
            add_log("SUCCESS", "beat_scheduler", f"Auto-drip: scheduled {len(video_ids)} videos over {total_days} days (every {interval_h}h)")
            return self.send_json({"created": len(video_ids), "total_days": total_days, "interval_hours": interval_h, "message": f"Scheduled {len(video_ids)} videos across {total_days} days."}, 201)

        if p.startswith("/api/v1/schedules/") and "/trigger" in p and method == "POST":
            sid = p.split("/")[-2]
            task_id = f"celery-pipeline-{uuid.uuid4().hex[:8]}"
            for s in DB["schedules"]:
                if s["id"] == sid:
                    s["celery_task_id"] = task_id
                    add_log("INFO", "celery_worker", f"Pipeline task manually triggered: {task_id}")
                    add_log("INFO", "ffmpeg_engine", "Running FFmpeg uniquifier (metadata strip, crop, brightness, watermark)...")
                    add_log("SUCCESS", "gemini_ai", 'AI analysis complete: "Viral title generated successfully!"')
            return self.send_json({"task_id": task_id, "message": "Pipeline task dispatched"})

        if p.startswith("/api/v1/schedules/") and method == "DELETE":
            sid = p.split("/")[-1]
            DB["schedules"] = [s for s in DB["schedules"] if s["id"] != sid]
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            return

        # ── Logs ──────────────────────────────────────────────────────────
        if p == "/api/v1/logs/" and method == "GET":
            limit = int(query.get("limit", ["100"])[0])
            lvl = query.get("level", [None])[0]
            src = query.get("source", [None])[0]
            result = DB["logs"]
            if lvl:
                result = [l for l in result if l["level"] == lvl.upper()]
            if src:
                result = [l for l in result if l["source"] == src]
            return self.send_json(result[-limit:])

        if p == "/api/v1/logs/stream":
            return self.handle_sse_stream()

        # ── Docs Demo ─────────────────────────────────────────────────────
        if p == "/docs-demo":
            return self.serve_docs()

        return self.send_json({"detail": f"Endpoint not found: {method} {p}"}, 404)

    def handle_sse_stream(self):
        self.send_sse()
        idx = 0
        try:
            while True:
                log = LOG_MESSAGES[idx % len(LOG_MESSAGES)]
                add_log(log[0], log[1], log[2])
                data = json.dumps({"id": str(uuid.uuid4()), "level": log[0], "source": log[1], "message": log[2], "time": datetime.now(timezone.utc).isoformat()})
                self.wfile.write(f"data: {data}\n\n".encode())
                self.wfile.flush()
                idx += 1
                time.sleep(2)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/docs-demo":
            self.serve_docs()
        else:
            self.route("GET", parsed.path, query)

    def do_POST(self):
        parsed = urlparse(self.path)
        self.route("POST", parsed.path, parse_qs(parsed.query))

    def do_PATCH(self):
        parsed = urlparse(self.path)
        self.route("PATCH", parsed.path, parse_qs(parsed.query))

    def do_DELETE(self):
        parsed = urlparse(self.path)
        self.route("DELETE", parsed.path, parse_qs(parsed.query))

    def serve_docs(self):
        html = DOCS_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)


DOCS_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"/><title>AutoStream AI – Demo API Tester</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',sans-serif;background:#0e0f16;color:#fff;display:flex;height:100vh;}
aside{width:260px;background:#13141c;border-right:1px solid rgba(255,255,255,.06);display:flex;flex-direction:column;overflow-y:auto;}
.logo{padding:20px;border-bottom:1px solid rgba(255,255,255,.06);}
.logo h1{font-size:16px;font-weight:700;background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.logo p{font-size:11px;color:rgba(255,255,255,.3);margin-top:3px;}
.section{padding:12px 10px 4px;font-size:10px;font-weight:700;color:rgba(255,255,255,.25);text-transform:uppercase;letter-spacing:1px;}
.ep{display:flex;align-items:center;gap:8px;padding:7px 12px;border-radius:8px;cursor:pointer;transition:.15s;font-size:12.5px;color:rgba(255,255,255,.55);}
.ep:hover{background:rgba(255,255,255,.05);color:#fff;}
.ep.active{background:rgba(100,112,243,.15);color:#a5b4fc;}
.method{font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;font-family:'JetBrains Mono',monospace;flex-shrink:0;}
.GET{background:rgba(34,197,94,.15);color:#4ade80;}
.POST{background:rgba(100,112,243,.15);color:#818cf8;}
.PATCH{background:rgba(234,179,8,.15);color:#facc15;}
.DELETE{background:rgba(239,68,68,.15);color:#f87171;}
main{flex:1;display:flex;flex-direction:column;overflow:hidden;}
header{padding:16px 24px;border-bottom:1px solid rgba(255,255,255,.06);display:flex;align-items:center;justify-content:space-between;}
header h2{font-size:15px;font-weight:600;}
.status-dot{width:8px;height:8px;border-radius:50%;background:#4ade80;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.content{flex:1;overflow-y:auto;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:20px;}
.panel{background:#1a1b25;border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:18px;}
.panel h3{font-size:13px;font-weight:600;margin-bottom:14px;color:rgba(255,255,255,.8);}
label{font-size:11px;color:rgba(255,255,255,.4);display:block;margin-bottom:5px;}
input,textarea,select{width:100%;background:#0e0f16;border:1px solid rgba(255,255,255,.1);border-radius:7px;padding:8px 12px;color:#fff;font-size:12.5px;outline:none;margin-bottom:10px;font-family:'JetBrains Mono',monospace;}
input:focus,textarea:focus{border-color:#4f52e8;}
textarea{height:100px;resize:vertical;}
button{background:#4f52e8;color:#fff;border:none;border-radius:7px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;width:100%;transition:.2s;}
button:hover{background:#6470f3;}
.response{background:#090a0f;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:14px;font-family:'JetBrains Mono',monospace;font-size:11.5px;line-height:1.7;white-space:pre-wrap;max-height:300px;overflow-y:auto;color:#94a3b8;margin-top:12px;}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;}
.s200{color:#4ade80;} .s201{color:#818cf8;} .s204{color:#facc15;} .s4xx{color:#f87171;}
</style></head>
<body>
<aside>
  <div class="logo"><h1>⚡ AutoStream AI</h1><p>Demo API Tester — All Endpoints</p></div>
  <div class="section">Dashboard</div>
  <div class="ep active" onclick="load('GET','/api/v1/dashboard/stats','stats')"><span class="method GET">GET</span>/dashboard/stats</div>
  <div class="ep" onclick="load('GET','/api/v1/dashboard/health','health')"><span class="method GET">GET</span>/dashboard/health</div>
  <div class="section">Accounts</div>
  <div class="ep" onclick="load('GET','/api/v1/accounts/?platform=youtube','accounts_list')"><span class="method GET">GET</span>/accounts/ (YouTube)</div>
  <div class="ep" onclick="load('POST','/api/v1/accounts/','create_account')"><span class="method POST">POST</span>/accounts/ (create)</div>
  <div class="ep" onclick="load('GET','/api/v1/accounts/groups','groups_list')"><span class="method GET">GET</span>/accounts/groups</div>
  <div class="ep" onclick="load('POST','/api/v1/accounts/groups','create_group')"><span class="method POST">POST</span>/accounts/groups</div>
  <div class="ep" onclick="load('GET','/api/v1/accounts/oauth/google/init','oauth_init')"><span class="method GET">GET</span>/accounts/oauth/google/init</div>
  <div class="section">API Vault</div>
  <div class="ep" onclick="load('GET','/api/v1/api-vault/','vault_list')"><span class="method GET">GET</span>/api-vault/ (list)</div>
  <div class="ep" onclick="load('GET','/api/v1/api-vault/stats/summary','vault_stats')"><span class="method GET">GET</span>/api-vault/stats/summary</div>
  <div class="ep" onclick="load('POST','/api/v1/api-vault/upload-json','vault_upload')"><span class="method POST">POST</span>/api-vault/upload-json</div>
  <div class="section">Videos</div>
  <div class="ep" onclick="load('GET','/api/v1/videos/','videos_list')"><span class="method GET">GET</span>/videos/ (all)</div>
  <div class="ep" onclick="load('POST','/api/v1/videos/sync-drive','drive_sync')"><span class="method POST">POST</span>/videos/sync-drive</div>
  <div class="section">Schedules</div>
  <div class="ep" onclick="load('GET','/api/v1/schedules/?is_published=false','schedules_pending')"><span class="method GET">GET</span>/schedules/ (pending)</div>
  <div class="ep" onclick="load('POST','/api/v1/schedules/auto-drip','auto_drip')"><span class="method POST">POST</span>/schedules/auto-drip</div>
  <div class="ep" onclick="load('POST','/api/v1/schedules/sch00001-0001-0001-0001-000000000001/trigger','trigger_schedule')"><span class="method POST">POST</span>/schedules/{id}/trigger</div>
  <div class="section">Logs</div>
  <div class="ep" onclick="load('GET','/api/v1/logs/?limit=20','logs_list')"><span class="method GET">GET</span>/logs/ (latest 20)</div>
  <div class="ep" onclick="startSSE()"><span class="method GET">GET</span>/logs/stream (SSE)</div>
</aside>

<main>
  <header>
    <h2 id="ep-title">GET /api/v1/dashboard/stats</h2>
    <div style="display:flex;align-items:center;gap:10px;">
      <div class="status-dot"></div>
      <span style="font-size:12px;color:#4ade80;font-weight:600;">API Server: Online</span>
    </div>
  </header>
  <div class="content">
    <div class="panel">
      <h3>Request</h3>
      <label>Method</label>
      <select id="method"><option>GET</option><option>POST</option><option>PATCH</option><option>DELETE</option></select>
      <label>URL</label>
      <input id="url" value="/api/v1/dashboard/stats"/>
      <label>Request Body (JSON)</label>
      <textarea id="body" placeholder="{}"></textarea>
      <button onclick="sendRequest()">▶ Send Request</button>
    </div>
    <div class="panel">
      <h3>Response <span id="status-badge"></span></h3>
      <div class="response" id="response">Click "Send Request" or select an endpoint from the sidebar...</div>
    </div>
  </div>
</main>

<script>
const PRESETS = {
  stats:{method:'GET',url:'/api/v1/dashboard/stats',body:''},
  health:{method:'GET',url:'/api/v1/dashboard/health',body:''},
  accounts_list:{method:'GET',url:'/api/v1/accounts/?platform=youtube',body:''},
  create_account:{method:'POST',url:'/api/v1/accounts/',body:JSON.stringify({platform:"youtube",channel_name:"My New Channel",channel_id:"UC_new_001",access_token:"demo_token_123",subscriber_count:50000},null,2)},
  groups_list:{method:'GET',url:'/api/v1/accounts/groups',body:''},
  create_group:{method:'POST',url:'/api/v1/accounts/groups',body:JSON.stringify({name:"My Gaming Group",platform:"youtube",description:"All gaming channels"},null,2)},
  oauth_init:{method:'GET',url:'/api/v1/accounts/oauth/google/init',body:''},
  vault_list:{method:'GET',url:'/api/v1/api-vault/',body:''},
  vault_stats:{method:'GET',url:'/api/v1/api-vault/stats/summary',body:''},
  vault_upload:{method:'POST',url:'/api/v1/api-vault/upload-json',body:'(multipart — simulated)'},
  videos_list:{method:'GET',url:'/api/v1/videos/',body:''},
  drive_sync:{method:'POST',url:'/api/v1/videos/sync-drive',body:JSON.stringify({folder_link:"https://drive.google.com/drive/folders/1ABCdemoFolderID",account_id:"acc00001-0001-0001-0001-000000000001"},null,2)},
  schedules_pending:{method:'GET',url:'/api/v1/schedules/?is_published=false',body:''},
  auto_drip:{method:'POST',url:'/api/v1/schedules/auto-drip',body:JSON.stringify({video_ids:["vid00001-0001-0001-0001-000000000001","vid00002-0002-0002-0002-000000000002"],start_datetime:new Date(Date.now()+3600000).toISOString(),total_days:7,add_watermark:true,auto_comment:false},null,2)},
  trigger_schedule:{method:'POST',url:'/api/v1/schedules/sch00001-0001-0001-0001-000000000001/trigger',body:''},
  logs_list:{method:'GET',url:'/api/v1/logs/?limit=20',body:''},
};

let sseSource=null;

function load(m,u,preset){
  document.querySelectorAll('.ep').forEach(e=>e.classList.remove('active'));
  event.currentTarget.classList.add('active');
  const p=PRESETS[preset]||{method:m,url:u,body:''};
  document.getElementById('method').value=p.method;
  document.getElementById('url').value=p.url;
  document.getElementById('body').value=p.body||'';
  document.getElementById('ep-title').textContent=p.method+' '+p.url;
  document.getElementById('response').textContent='Click ▶ Send Request to test this endpoint...';
  document.getElementById('status-badge').textContent='';
}

async function sendRequest(){
  const method=document.getElementById('method').value;
  const url='http://localhost:8000'+document.getElementById('url').value;
  const bodyStr=document.getElementById('body').value.trim();
  const opts={method,headers:{'Content-Type':'application/json'}};
  if(bodyStr&&bodyStr!=='(multipart — simulated)'&&method!=='GET') opts.body=bodyStr;
  const res_el=document.getElementById('response');
  const badge=document.getElementById('status-badge');
  res_el.textContent='⏳ Sending request...';
  try{
    const t0=Date.now();
    const r=await fetch(url,opts);
    const ms=Date.now()-t0;
    let data;
    try{data=await r.json();}catch{data=await r.text();}
    const cls=r.status<300?'s'+r.status:r.status<500?'s4xx':'s4xx';
    badge.className='badge '+cls;
    badge.textContent=r.status+' '+r.statusText+' ('+ms+'ms)';
    res_el.textContent=typeof data==='string'?data:JSON.stringify(data,null,2);
  }catch(e){
    badge.className='badge s4xx'; badge.textContent='Network Error';
    res_el.textContent='❌ '+e.message+'\n\nMake sure demo_api.py is running:\n  python demo_api.py';
  }
}

function startSSE(){
  document.querySelectorAll('.ep').forEach(e=>e.classList.remove('active'));
  event.currentTarget.classList.add('active');
  document.getElementById('method').value='GET';
  document.getElementById('url').value='/api/v1/logs/stream';
  document.getElementById('body').value='';
  document.getElementById('ep-title').textContent='GET /api/v1/logs/stream (SSE)';
  if(sseSource){sseSource.close();sseSource=null;}
  const res=document.getElementById('response');
  res.textContent='🔴 Connecting to SSE stream...\\n';
  const badge=document.getElementById('status-badge');
  badge.className='badge s200'; badge.textContent='200 SSE Connected';
  sseSource=new EventSource('http://localhost:8000/api/v1/logs/stream');
  sseSource.onmessage=e=>{
    try{const d=JSON.parse(e.data);res.textContent+='['+d.level+'] '+d.source+': '+d.message+'\\n';res.scrollTop=res.scrollHeight;}catch{}
  };
  sseSource.onerror=()=>{res.textContent+='\\n⚠️ Stream ended or disconnected.';sseSource.close();sseSource=null;};
}

// Initial request on load
window.onload=()=>sendRequest();
</script>
</body></html>"""


def run_log_generator():
    """Background thread: add a new log entry every 5 seconds."""
    idx = 6
    while True:
        time.sleep(5)
        log = LOG_MESSAGES[idx % len(LOG_MESSAGES)]
        add_log(log[0], log[1], log[2])
        idx += 1


if __name__ == "__main__":
    port = 8000
    server = HTTPServer(("0.0.0.0", port), APIHandler)

    # Start background log generator
    t = threading.Thread(target=run_log_generator, daemon=True)
    t.start()

    print("\n" + "="*55)
    print("  AutoStream AI Infinity — Demo API Server")
    print("="*55)
    print(f"\n  ✅ API running at:  http://localhost:{port}")
    print(f"  📋 API Tester:      http://localhost:{port}/docs-demo")
    print(f"  ❤️  Health check:    http://localhost:{port}/health")
    print(f"\n  Open demo.html in your browser to use the dashboard.")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
