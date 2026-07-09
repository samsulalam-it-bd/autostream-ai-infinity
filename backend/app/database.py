import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import settings

# ── SSL Context for Neon PostgreSQL (cloud) ───────────────────────
# NullPool is best for cloud/serverless — avoids stale connections.
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# Strip ?ssl=require from URL if present (we handle SSL via connect_args)
_db_url = settings.DATABASE_URL.split("?")[0]

engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    poolclass=NullPool,
    connect_args={"ssl": _ssl_ctx},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

