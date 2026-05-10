import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def check():
    engine = create_async_engine('postgresql+asyncpg://autostream:autostream123@db:5432/autostream_db')
    async with engine.begin() as conn:
        res = await conn.execute(text('SELECT count(*) FROM upload_schedule;'))
        print(f"Count: {res.scalar()}")
        res2 = await conn.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \'upload_schedule\' AND column_name = \'metadata_overrides\';'))
        print(f"Has metadata_overrides: {len(res2.fetchall()) > 0}")

asyncio.run(check())
