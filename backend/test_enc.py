import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.security import encrypt_token, decrypt_token
import cryptography.exceptions

try:
    token = encrypt_token("dummy_token")
    print("SUCCESS_ENCRYPT:", token)
except Exception as e:
    print("FAIL_ENCRYPT:", e)
