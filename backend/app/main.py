from contextlib import asynccontextmanager
import logging
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import init_db
from app.routers import accounts, api_vault, videos, schedules, logs, dashboard, comments, workspace, engagement, analytics


_telegram_token_in_url = re.compile(r"(https://api\.telegram\.org/bot)([^/\s]+)")


class _RedactTelegramToken(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        redacted = _telegram_token_in_url.sub(r"\1***", msg)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
for _name in ("httpx", "httpcore", "telegram", "telegram.ext"):
    logging.getLogger(_name).setLevel(logging.DEBUG)
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_RedactTelegramToken())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AutoStream AI Infinity backend...")
    await init_db()
    logger.info("Database tables initialized.")

    # Start Telegram background polling
    from app.services.telegram import start_telegram_polling
    from app.services.api_rotation import reset_daily_quotas
    from app.database import AsyncSessionLocal
    import asyncio
    
    asyncio.create_task(start_telegram_polling())
    
    # Daily Quota Reset Loop
    async def quota_reset_worker():
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    await reset_daily_quotas(db)
            except Exception as e:
                logger.error(f"Quota reset failed: {e}")
            await asyncio.sleep(3600) # Check every hour

    asyncio.create_task(quota_reset_worker())
    
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AutoStream AI Infinity API",
    description="Automated video distribution system with AI-powered metadata and rotating API keys.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(api_vault.router, prefix=API_PREFIX)
app.include_router(videos.router, prefix=API_PREFIX)
app.include_router(schedules.router, prefix=API_PREFIX)
app.include_router(logs.router, prefix=API_PREFIX)
app.include_router(comments.router, prefix=API_PREFIX)
app.include_router(workspace.router, prefix=API_PREFIX)
app.include_router(engagement.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)



# ── Root & Health ──────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {"name": settings.APP_NAME, "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}


# ── Global Exception Handler ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
