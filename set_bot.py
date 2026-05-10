import asyncio
import os

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    database_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL") or ""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or ""
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or ""

    if not database_url:
        raise SystemExit("DATABASE_URL is missing")
    if not bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is missing")
    if not chat_id:
        raise SystemExit("TELEGRAM_CHAT_ID is missing")

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO system_settings (key, value) VALUES ('TELEGRAM_BOT_TOKEN', :v) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            ),
            {"v": bot_token},
        )
        await conn.execute(
            text(
                "INSERT INTO system_settings (key, value) VALUES ('TELEGRAM_CHAT_ID', :v) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            ),
            {"v": chat_id},
        )
        for k in ("NOTIFY_UPLOAD_SUCCESS", "NOTIFY_QUOTA_EXHAUSTED", "NOTIFY_TOKEN_EXPIRED", "NOTIFY_TASK_FAILED"):
            await conn.execute(
                text(
                    "INSERT INTO system_settings (key, value) VALUES (:k, 'true') "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
                ),
                {"k": k},
            )
    await engine.dispose()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise SystemExit("Telegram token invalid")


asyncio.run(main())
