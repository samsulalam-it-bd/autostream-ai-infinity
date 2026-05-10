# AutoStream AI Infinity — Technical Audit Report

This report contains the full architectural breakdown, infrastructure configuration, database schemas, and critical core logic snippets for the AutoStream AI Infinity project.

---

## 📂 1. Project File Structure

```text
autostream-ai/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py        # Token encryption/decryption (Fernet)
│   │   ├── models/
│   │   │   └── models.py          # SQLAlchemy Models (UUIDs, JSONB, Enums)
│   │   ├── routers/
│   │   │   ├── accounts.py
│   │   │   ├── api_vault.py
│   │   │   ├── dashboard.py       # Redis & Celery Health Checks
│   │   │   ├── logs.py            # SSE Streaming
│   │   │   ├── schedules.py
│   │   │   └── videos.py
│   │   ├── services/
│   │   │   ├── ffmpeg.py          # Video Uniquifier (crop, metadata strip, brightness)
│   │   │   ├── gemini.py          # Vision AI (Flash 1.5 frame analysis)
│   │   │   ├── rotation.py        # Dynamic Multi-Account API Rotation
│   │   │   ├── telegram.py        # Bot messaging alerts
│   │   │   └── uploader.py
│   │   ├── database.py            # Asyncpg connection pools
│   │   ├── main.py                # FastAPI lifecycle & exception handlers
│   │   ├── schemas.py             # Pydantic validation structures
│   │   └── worker.py              # Celery JIT Pipeline & Fan-out scheduler
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx         # Sidebar navigation wrapper
│   │   │   └── ProtectedRoute.jsx
│   │   ├── lib/
│   │   │   └── api.js             # Axios interceptors
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # Recharts + Stats overview
│   │   │   ├── Accounts.jsx       # Platform tabs & OAuth flow
│   │   │   ├── ApiVault.jsx       # JSON file drag-drop uploader
│   │   │   ├── UploadZone.jsx     # Google Drive Sync & Scheduler
│   │   │   └── LiveLogs.jsx       # Real-time SSE terminal
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js         # Custom dark theme colors
│   └── vite.config.js
├── scripts/
│   ├── generate_keys.py
│   ├── init_db.py
│   └── test_backend.py            # 31-endpoint E2E integration tests
├── demo_full.html                 # Zero-dependency browser mock API tester
├── docker-compose.yml             # Full stack orchestration
└── README.md
```

---

## ⚙️ 2. Infrastructure Config

### `docker-compose.yml`
```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    container_name: autostream_db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-autostream}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-supersecretpassword}
      POSTGRES_DB: ${POSTGRES_DB:-autostream_db}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-autostream}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: autostream_redis
    restart: always
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: autostream_backend
    restart: always
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-autostream}:${POSTGRES_PASSWORD:-supersecretpassword}@db:5432/${POSTGRES_DB:-autostream_db}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - video_tmp:/tmp/videos
      - ./assets:/app/assets

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: autostream_worker
    restart: always
    command: celery -A app.worker.celery_app worker --loglevel=info --queues=video_pipeline,default -c 4
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-autostream}:${POSTGRES_PASSWORD:-supersecretpassword}@db:5432/${POSTGRES_DB:-autostream_db}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - video_tmp:/tmp/videos
      - ./assets:/app/assets

  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: autostream_beat
    restart: always
    command: celery -A app.worker.celery_app beat --loglevel=info --scheduler redbeat.RedBeatScheduler
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER:-autostream}:${POSTGRES_PASSWORD:-supersecretpassword}@db:5432/${POSTGRES_DB:-autostream_db}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: autostream_frontend
    restart: always
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
  video_tmp:
```

### `backend/requirements.txt`
```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.2
pydantic==2.8.2
pydantic-settings==2.3.4
redis==5.0.7
celery==5.4.0
redbeat==2.2.0
cryptography==42.0.8
google-generativeai==0.7.2
google-auth==2.32.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
google-api-python-client==2.139.0
python-telegram-bot==21.4
httpx==0.27.0
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiofiles==24.1.0
pillow==10.4.0
requests==2.32.3
psutil==6.0.0
```

---

## 🗄️ 3. Database Schema (SQLAlchemy Models)

### `accounts` (Uses Fernet encryption for tokens)
```python
class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(Enum(PlatformEnum), nullable=False)
    channel_name = Column(String(255), nullable=False)
    channel_id = Column(String(255), nullable=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("channel_groups.id"), nullable=True)
    
    # Tokens stored encrypted using Fernet (handled in app.core.security)
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AccountStatusEnum), default=AccountStatusEnum.PENDING, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    subscriber_count = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channel_group = relationship("ChannelGroup", back_populates="accounts")
    upload_schedules = relationship("UploadSchedule", back_populates="account")
```

### `api_key_vault` (Dynamic Pool Logic support)
```python
class ApiKeyVault(Base):
    __tablename__ = "api_key_vault"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False)  # google, meta
    project_name = Column(String(255), nullable=True)
    credentials_json = Column(JSONB, nullable=False)  # Stores the full GCP service account JSON
    daily_usage = Column(Integer, default=0)
    daily_limit = Column(Integer, default=10000)
    
    # Dynamic Pool Lock Logic
    is_locked = Column(Boolean, default=False)
    unlock_time = Column(DateTime(timezone=True), nullable=True)
    lock_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### `channel_groups`
```python
class ChannelGroup(Base):
    __tablename__ = "channel_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    platform = Column(Enum(PlatformEnum), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    accounts = relationship("Account", back_populates="channel_group")
    upload_schedules = relationship("UploadSchedule", back_populates="target_group")
```

### `source_videos`
```python
class SourceVideo(Base):
    __tablename__ = "source_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_file_id = Column(String(255), nullable=False, unique=True)
    drive_view_link = Column(String(500), nullable=True)
    drive_download_link = Column(String(500), nullable=True)
    original_filename = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # AI-generated metadata generated via Gemini Vision
    ai_title = Column(String(500), nullable=True)
    ai_description = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True)  # list of strings
    ai_hashtags = Column(JSON, nullable=True)  # list of strings
    
    # Processing status
    status = Column(Enum(VideoStatusEnum), default=VideoStatusEnum.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    upload_schedules = relationship("UploadSchedule", back_populates="video")
```

---

## 🧠 4. Core Logic Code Snippets

### A. The Rotation Logic (Multi-Account 403 Fallback)
This script wraps API calls. When a `403 Quota Exceeded` happens, it locks the key for 24h, triggers a Telegram alert, and immediately recursively tries another key from the Redis/Postgres pool.

```python
async def execute_with_rotation(
    self,
    service_name: str,
    operation: Callable,
    max_retries: int = 5,
    **kwargs: Any,
) -> Any:
    tried_keys = set()

    async with AsyncSessionLocal() as db:
        for attempt in range(max_retries):
            key_entry = await self.get_active_key(service_name, db)

            if not key_entry or key_entry.id in tried_keys:
                raise QuotaExceededException(
                    f"All API keys for service '{service_name}' are exhausted/locked."
                )

            tried_keys.add(key_entry.id)

            try:
                # Attempt the actual API call
                result = await operation(key_entry.credentials_json, **kwargs)
                await self.increment_usage(str(key_entry.id), db)
                return result

            except Exception as e:
                error_str = str(e).lower()
                # Detect quota exceeded errors
                if any(keyword in error_str for keyword in ["403", "quota", "ratelimit", "exceeded"]):
                    logger.warning(
                        f"Quota exceeded on key {key_entry.id} (attempt {attempt + 1}). "
                        f"Locking and rotating."
                    )
                    await self.lock_key(str(key_entry.id), f"Quota error: {str(e)[:200]}", db)
                    
                    # Fire async Telegram alert
                    from app.services.telegram import send_telegram_alert
                    asyncio.create_task(send_telegram_alert(
                        f"⚠️ API Key Quota Exhausted! Service: {service_name}. Rotating..."
                    ))
                    continue  # Retry with next key in loop
                else:
                    raise # Non-quota error, fail fast

        raise QuotaExceededException(f"Exceeded max retries for '{service_name}'.")
```

### B. The Uniquifier (FFmpeg Processing)
Removes metadata tracking, applies a microscopic crop & brightness adjustment to bypass Content ID duplication checks, and optionally adds a watermark.

```python
def process_video(input_path: str, add_watermark: bool = True) -> str:
    input_path = Path(input_path)
    output_path = Path(VIDEO_TMP_DIR) / f"processed_{input_path.stem}.mp4"

    # Step 1: Crop 1px from limits to alter pixel hashes
    # Step 2: Tiny 1% brightness shift
    video_filters = "crop=iw-1:ih-1,eq=brightness=0.01"

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-map_metadata", "-1",         # STRIP ALL METADATA
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
    ]

    watermark_exists = add_watermark and Path(WATERMARK_PATH).exists()

    if watermark_exists:
        # Complex filter merges the uniquifier with the watermark overlay
        complex_filter = (
            f"[0:v]{video_filters}[base];"
            f"[1:v]scale=120:-1[wm];"
            f"[base][wm]overlay=W-w-20:H-h-20"
        )
        ffmpeg_cmd += [
            "-i", WATERMARK_PATH,
            "-filter_complex", complex_filter,
        ]
    else:
        ffmpeg_cmd += ["-vf", video_filters]

    ffmpeg_cmd.append(str(output_path))
    
    subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=3600)
    return str(output_path)
```

### C. Vision AI (Google Gemini Prompting)
Uploads 3 extracted frames to Gemini 1.5 Flash to automatically interpret visual context and generate a JSON object with Title, Descriptions, and Hashtags.

```python
async def analyze_video_with_gemini(frame_paths: list[str], api_key: Optional[str] = None) -> dict:
    genai.configure(api_key=api_key or settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    content_parts = []
    # Inject images into context window
    for frame_path in frame_paths:
        with open(frame_path, "rb") as f:
            content_parts.append({
                "inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(f.read()).decode()}
            })

    prompt = """Analyze these video frames carefully and act as a viral content marketing expert.
    Based on the visual content shown in these frames, generate the following in JSON format:
    {
      "title": "A compelling, click-bait style YouTube/Reels title (max 100 chars).",
      "description": "An SEO-optimized video description (200-400 words).",
      "tags": ["tag1", "tag2", ...] (10-15 SEO tags),
      "hashtags": ["#hashtag1", "#hashtag2", ...] (exactly 10 trending hashtags)
    }
    Rules: Return ONLY valid JSON, no extra text."""

    content_parts.append({"text": prompt})

    try:
        response = model.generate_content(content_parts)
        response_text = response.text.strip()
        # Clean markdown wrappers if present
        if response_text.startswith("```"):
            response_text = "\n".join(response_text.split("\n")[1:-1])
        
        metadata = json.loads(response_text)
        return metadata
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return _fallback_metadata()
```

### D. Scheduler (Just-in-Time Pipeline worker)
The Celery beat scheduler scans the database every minute. If a video is exactly 30 minutes away from its `scheduled_time`, it launches the pipeline.

```python
# In worker.py: Celery Beat periodic task (runs every 60s)
@celery_app.task(name="app.worker.check_pending_schedules")
def check_pending_schedules():
    async def _check():
        now = datetime.now(timezone.utc)
        trigger_window = now + timedelta(minutes=35) # Catch anything needing processing soon
        
        async with AsyncSessionLocal() as db:
            schedules = await db.execute(select(UploadSchedule).where(
                and_(
                    UploadSchedule.is_published == False,
                    UploadSchedule.scheduled_time <= trigger_window,
                    UploadSchedule.celery_task_id == None,
                )
            )).scalars().all()

            for schedule in schedules:
                if schedule.target_group_id:
                    # FAN-OUT: Spawns sub-tasks for every account in the group
                    task = fan_out_group_schedule.apply_async(
                        args=[str(schedule.id)],
                        eta=schedule.scheduled_time - timedelta(minutes=30),
                        queue="default"
                    )
                else:
                    # Direct JIT processing delay queue
                    task = process_and_upload_video.apply_async(
                        args=[str(schedule.id)],
                        eta=schedule.scheduled_time - timedelta(minutes=30), 
                        queue="video_pipeline"
                    )
                schedule.celery_task_id = task.id
            await db.commit()
    run_async(_check())
```

---

## 💻 5. Frontend Overview (React + Vite)
The Dashboard interface was built in React using Vite, standard Tailwind CSS (no external bloated libraries), and `lucide-react` for iconography. 

| Component/Page | Primary Function |
| :--- | :--- |
| **Layout** & `Sidebar` | Persistent dark-mode navigation sidebar highlighting active routes. |
| `Dashboard.js` | Top-level analytics showing `Recharts` metrics, API keys active, and celery health. |
| `Accounts.js` | Manage platforms (YT/FB/IG), Group Channels, and initialize Google OAuth flow. |
| `ApiVault.js` | Drag-and-drop GCP `.json` credentials upload with dynamic multi-key pooling logic tracking. |
| `UploadZone.js` | Form block to input Drive folders, Auto-Drip scheduler (e.g. "spread 30 videos over 15 days"). |
| `LiveLogs.js` | Real-time `Server-Sent Events (SSE)` simulated terminal to monitor Celery workers live. |
| `api.js` (Lib) | Axios centralized instance that formats requests to `localhost:8000`. |
