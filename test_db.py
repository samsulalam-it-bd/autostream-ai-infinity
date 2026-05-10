import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    engine = create_async_engine("postgresql+asyncpg://autostream:autostream123@localhost:5432/autostream_db", echo=False)
    async with engine.connect() as conn:
        from sqlalchemy import text
        res = await conn.execute(text("SELECT id, is_published, metadata_overrides FROM upload_schedule LIMIT 5;"))
        rows = res.fetchall()
        
        with open("db_out.txt", "w") as f:
            f.write(f"Connected. Rows: {len(rows)}\n")
            for r in rows:
                f.write(str(r) + "\n")
                
asyncio.run(check())
