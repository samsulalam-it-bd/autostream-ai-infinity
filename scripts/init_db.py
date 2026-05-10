#!/usr/bin/env python3
"""
AutoStream AI Infinity — Database Initialization Script
=======================================================
Creates all database tables and optionally seeds initial data.

Usage:
    python scripts/init_db.py              # Initialize tables
    python scripts/init_db.py --seed       # Initialize + add sample data
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Ensure we can import `app.*` in both environments:
# - Local dev (repo layout): backend/app/...
# - Docker container (build context is ./backend): /app/app/...
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))   # local dev: .../backend is import root
else:
    sys.path.insert(0, str(project_root))  # docker: /app is import root


async def init_tables():
    """Create all SQLAlchemy-mapped tables in the database."""
    from app.database import engine, Base
    # Import models so they register with Base.metadata
    import app.models.models  # noqa: F401

    print("Connecting to database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully.")


async def seed_data():
    """Seed the database with example data for development/testing."""
    from app.database import AsyncSessionLocal
    from app.models.models import ChannelGroup, Account, AccountStatusEnum, PlatformEnum
    from app.core.security import encrypt_token

    async with AsyncSessionLocal() as db:
        # Create sample channel groups
        yt_group = ChannelGroup(
            name="Main YouTube Network",
            platform=PlatformEnum.YOUTUBE,
            description="Primary YouTube channel group",
        )
        fb_group = ChannelGroup(
            name="Facebook Pages Group",
            platform=PlatformEnum.FACEBOOK,
            description="All Facebook pages",
        )
        ig_group = ChannelGroup(
            name="Instagram Accounts",
            platform=PlatformEnum.INSTAGRAM,
            description="All Instagram accounts",
        )
        db.add_all([yt_group, fb_group, ig_group])
        await db.flush()

        # Create a sample placeholder account  
        sample_account = Account(
            platform=PlatformEnum.YOUTUBE,
            channel_name="Sample YouTube Channel",
            channel_id="UC_sample_channel_id",
            group_id=yt_group.id,
            encrypted_access_token=encrypt_token("sample_access_token_placeholder"),
            encrypted_refresh_token=encrypt_token("sample_refresh_token_placeholder"),
            status=AccountStatusEnum.PENDING,
            avatar_url=None,
            subscriber_count=0,
        )
        db.add(sample_account)
        await db.commit()

        print("✅ Seed data inserted:")
        print(f"   • Channel Groups: Main YouTube Network, Facebook Pages Group, Instagram Accounts")
        print(f"   • Sample Account: {sample_account.channel_name} (status: pending)")
        print()
        print("   ℹ️  Connect real accounts via the dashboard → Accounts & Groups → Add Account")


async def main(seed: bool = False):
    print("\n" + "=" * 55)
    print("  AutoStream AI Infinity — Database Initialization")
    print("=" * 55 + "\n")

    await init_tables()

    if seed:
        print("\nSeeding sample data...")
        await seed_data()

    print("\n✅ Done! You can now start the application:")
    print("   docker-compose up -d\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the AutoStream AI database")
    parser.add_argument("--seed", action="store_true", help="Also insert sample/seed data")
    args = parser.parse_args()

    asyncio.run(main(seed=args.seed))
