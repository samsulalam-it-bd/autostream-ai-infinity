import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.models import SystemLog
from app.schemas import SystemLogOut

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=list[SystemLogOut])
async def list_logs(
    limit: int = Query(default=100, le=500),
    level: str = None,
    source: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Get latest system logs."""
    query = select(SystemLog).order_by(desc(SystemLog.created_at)).limit(limit)
    if level:
        query = query.where(SystemLog.level == level.upper())
    if source:
        query = query.where(SystemLog.source == source)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stream")
async def stream_logs():
    """
    Server-Sent Events (SSE) endpoint for real-time log streaming.
    The frontend connects here and receives new log lines as they arrive.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        last_id = None
        while True:
            async with AsyncSessionLocal() as db:
                query = select(SystemLog).order_by(desc(SystemLog.created_at)).limit(10)
                if last_id:
                    query = query.where(SystemLog.id > last_id)
                result = await db.execute(query)
                logs = result.scalars().all()

            if logs:
                for log in reversed(logs):
                    last_id = log.id
                    data = {
                        "id": str(log.id),
                        "level": log.level,
                        "source": log.source or "system",
                        "message": log.message,
                        "time": log.created_at.isoformat(),
                    }
                    import json
                    yield f"data: {json.dumps(data)}\n\n"

            await asyncio.sleep(2)  # Poll every 2 seconds

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def write_log(
    message: str,
    level: str = "INFO",
    source: str = "system",
    extra_data: dict = None,
):
    """Helper to write a log entry to the database from anywhere in the app."""
    async with AsyncSessionLocal() as db:
        log = SystemLog(
            level=level.upper(),
            source=source,
            message=message,
            extra_data=extra_data,
        )
        db.add(log)
        await db.commit()
