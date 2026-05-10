# AutoStream AI Infinity ⚡

**Production-ready automated video distribution system** — AI-powered metadata, FFmpeg processing, rotating API keys, and scheduled uploads to YouTube, Facebook & Instagram.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy (Async) |
| **Database** | PostgreSQL 16 |
| **Queue** | Celery + Redis (broker & result backend) |
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts |
| **AI** | Google Gemini (via `google-genai` SDK) |
| **Video** | FFmpeg (Uniquifier Engine) |
| **Alerts** | Telegram Bot API |
| **DevOps** | Docker & Docker Compose |

---

## 📁 Project Structure

```
autostream-ai/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # All required env vars (copy to .env)
├── assets/
│   └── watermark.png           # Optional watermark logo
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI app + CORS + routers
│       ├── database.py         # Async SQLAlchemy setup
│       ├── schemas.py          # Pydantic v2 request/response models
│       ├── worker.py           # Celery tasks (JIT pipeline + beat)
│       ├── core/
│       │   ├── config.py       # Pydantic settings from .env
│       │   └── security.py     # Fernet encrypt/decrypt
│       ├── models/
│       │   └── models.py       # SQLAlchemy ORM models
│       ├── routers/
│       │   ├── dashboard.py    # Stats + health check
│       │   ├── accounts.py     # CRUD + Google OAuth flow
│       │   ├── api_vault.py    # Bulk JSON upload + rotation stats
│       │   ├── videos.py       # Drive sync + video CRUD
│       │   ├── schedules.py    # CRUD + Auto Drip scheduler
│       │   └── logs.py         # Paginated + SSE streaming logs
│       └── services/
│           ├── rotation.py     # Dynamic API key rotation (24h lock)
│           ├── ffmpeg.py       # Video uniquifier + frame extraction
│           ├── gemini.py       # Gemini 1.5 Flash viral metadata AI
│           ├── telegram.py     # Telegram alert notifications
│           └── uploader.py     # Drive download + YT/FB/IG upload
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx             # React Router routes
│       ├── main.jsx
│       ├── index.css           # Global Tailwind + custom styles
│       ├── lib/api.js          # Axios API client (all endpoints)
│       ├── components/
│       │   └── Layout.jsx      # Sidebar + top bar layout
│       └── pages/
│           ├── Dashboard.jsx   # Stats cards + chart + health
│           ├── Accounts.jsx    # Accounts & Groups management
│           ├── ApiVault.jsx    # Drag-and-drop JSON uploader
│           ├── UploadZone.jsx  # Drive sync + scheduler hub
│           └── Logs.jsx        # Real-time terminal log viewer
└── scripts/
    ├── generate_keys.py        # Generate Fernet + JWT keys
    └── init_db.py              # Initialize DB tables + seed data
```

---

## 🚀 Quick Start

### 1. Configure Environment

```bash
# Copy and fill in your API keys
cp .env.example .env

# Generate secure encryption keys
pip install cryptography
python scripts/generate_keys.py --write

# Then fill in remaining keys in .env:
# GEMINI_API_KEY, GOOGLE_CLIENT_ID/SECRET, META_APP_ID/SECRET,
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

### 2. (Optional) Add a Watermark

```bash
# Place your logo at:
assets/watermark.png
```

### 3. Start the Full Stack

```bash
docker-compose up -d --build
```

| Service | URL |
|---|---|
| **Frontend Dashboard** | http://localhost:5173 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API ReDoc** | http://localhost:8000/redoc |

### 4. Initialize Database (first run)

```bash
docker-compose exec backend python scripts/init_db.py --seed
```

---

## ⚙️ Core Features

### 🔄 Dynamic API Key Rotation
Upload 50+ Google Cloud JSON files via the **API Vault** drag-and-drop zone. The system randomly picks an active key for each request. On a `403 Quota Exceeded` error, that key is **locked for 24 hours** and the system immediately retries with the next available key. A Telegram alert is sent every time this happens.

### 🎬 Just-In-Time Video Pipeline
Videos are **never stored permanently**. A Celery beat task checks for upcoming schedules every 5 minutes. Exactly 30 minutes before upload time:
1. Downloads from Google Drive → `/tmp/videos`
2. Runs FFmpeg Uniquifier (metadata strip + 1px crop + brightness +0.01 + watermark)
3. Extracts 3 frames → sends to Gemini 1.5 Flash for AI metadata generation
4. Uploads to YouTube / Facebook / Instagram
5. Deletes all temporary files

### 🤖 Gemini AI Vision
Sends 3 video frames to Gemini with a viral content prompt. The model is configurable via `GEMINI_MODEL` in your `.env`. Returns a clickbait title, SEO description, and 10 trending hashtags — automatically applied to the upload.

### 📅 Auto Drip Scheduler
Select N videos, set a start time and number of days. The algorithm calculates the exact interval and creates all schedule entries automatically.

### 📬 Telegram Alerts
Sends real-time alerts when:
- ✅ Upload succeeds (with URL)
- ⚠️ API key quota exhausted (with rotation confirmation)
- 🔴 Account token expires

---

## 🔑 API Key Setup

| Service | Where to get it |
|---|---|
| **Gemini** | [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey) |
| **Google OAuth** | [console.cloud.google.com](https://console.cloud.google.com) → APIs → Credentials → OAuth 2.0 |
| **YouTube Data API** | [console.cloud.google.com](https://console.cloud.google.com) → Enable YouTube Data API v3 |
| **Google Drive API** | [console.cloud.google.com](https://console.cloud.google.com) → Enable Drive API |
| **Meta App** | [developers.facebook.com](https://developers.facebook.com) → Create App |
| **Telegram Bot** | Message `@BotFather` on Telegram → `/newbot` |

---

## 🐳 Docker Services

| Container | Role |
|---|---|
| `autostream_db` | PostgreSQL 16 — application data |
| `autostream_redis` | Redis 7 — Celery broker + cache |
| `autostream_backend` | FastAPI uvicorn server |
| `autostream_worker` | Celery worker (4 concurrent) |
| `autostream_beat` | Celery beat — schedule checker every 5min |
| `autostream_frontend` | Vite dev server |
