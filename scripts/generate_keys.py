#!/usr/bin/env python3
"""
AutoStream AI Infinity — Secure Key Generator
=============================================
Generates all required secret keys for the .env file and optionally
writes them directly into .env for you.

Usage:
    python scripts/generate_keys.py            # Print keys to screen
    python scripts/generate_keys.py --write    # Write keys to .env
"""

import os
import sys
import secrets
import argparse
from pathlib import Path

def generate_fernet_key() -> str:
    """Generate a URL-safe base64-encoded 32-byte Fernet key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()

def generate_secret_key(length: int = 64) -> str:
    """Generate a cryptographically secure hex secret key for JWT."""
    return secrets.token_hex(length)

def generate_postgres_password(length: int = 24) -> str:
    """Generate a strong alphanumeric database password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description="Generate secure keys for AutoStream AI Infinity")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write generated keys directly into .env (creates from .env.example if .env doesn't exist)",
    )
    args = parser.parse_args()

    # ── Generate all keys ──────────────────────────────────────────────────
    try:
        fernet_key = generate_fernet_key()
    except ImportError:
        print("❌  cryptography package not installed. Run: pip install cryptography")
        sys.exit(1)

    secret_key    = generate_secret_key()
    db_password   = generate_postgres_password()

    # ── Print to console ───────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  AutoStream AI Infinity — Generated Security Keys")
    print("="*60)
    print(f"\n🔐  FERNET_KEY (token encryption):")
    print(f"    {fernet_key}")
    print(f"\n🗝️   SECRET_KEY (JWT signing):")
    print(f"    {secret_key}")
    print(f"\n🗄️   POSTGRES_PASSWORD (suggested):")
    print(f"    {db_password}")
    print("\n" + "="*60)

    if args.write:
        root_dir  = Path(__file__).resolve().parent.parent
        env_path  = root_dir / ".env"
        example_path = root_dir / ".env.example"

        # Bootstrap from .env.example if .env doesn't exist
        if not env_path.exists():
            if example_path.exists():
                import shutil
                shutil.copy(example_path, env_path)
                print(f"\n📋  Created .env from .env.example")
            else:
                print("❌  Neither .env nor .env.example found. Aborting --write.")
                sys.exit(1)

        # Read existing .env content
        content = env_path.read_text(encoding="utf-8")

        replacements = {
            "FERNET_KEY=your_fernet_key_here":           f"FERNET_KEY={fernet_key}",
            "SECRET_KEY=your_long_random_jwt_secret_key_here": f"SECRET_KEY={secret_key}",
            "POSTGRES_PASSWORD=supersecretpassword":      f"POSTGRES_PASSWORD={db_password}",
        }

        changed = 0
        for old, new in replacements.items():
            if old in content:
                content = content.replace(old, new)
                changed += 1

        env_path.write_text(content, encoding="utf-8")
        print(f"\n✅  Wrote {changed} key(s) into: {env_path}")
        print("   ⚠️  Review the .env file and fill in remaining API keys before starting.")
    else:
        print("\n💡  Tip: Run with --write to automatically inject these into .env")
        print("   Copy the values above and paste them into your .env file.\n")


if __name__ == "__main__":
    main()
