import os
import secrets
from cryptography.fernet import Fernet
from pathlib import Path

# Paths
root = Path(__file__).resolve().parents[1]  # project root (../)
env_example = root / ".env.example"
env_file = root / ".env"

if not env_example.exists():
    print("No .env.example found!")
    exit(1)

content = env_example.read_text(encoding="utf-8")

# Keys
fernet_key = Fernet.generate_key().decode()
secret_key = secrets.token_hex(32)
db_pass = secrets.token_hex(12)

# Replacements
content = content.replace("POSTGRES_PASSWORD=supersecretpassword", f"POSTGRES_PASSWORD={db_pass}")
content = content.replace("FERNET_KEY=your_fernet_key_here", f"FERNET_KEY={fernet_key}")
content = content.replace("SECRET_KEY=your_long_random_jwt_secret_key_here", f"SECRET_KEY={secret_key}")

env_file.write_text(content, encoding="utf-8")

print("SUCCESS: `.env` file generated with secure secrets.")
print("NEXT: Set GEMINI_API_KEY / GOOGLE / META / TELEGRAM values manually in `.env`.")
