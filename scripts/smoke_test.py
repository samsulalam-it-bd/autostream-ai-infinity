#!/usr/bin/env python3
"""
AutoStream AI — Local Smoke Test

Safe checks (does NOT print any secrets):
1) Backend health endpoint
2) Frontend HTTP response
3) Gemini API call (text-only) using google-genai SDK

Run (inside Docker):
  docker compose up -d
  docker compose exec backend python /app/scripts/smoke_test.py
"""

import os
import sys
import time

import requests


def fail(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(code)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")

def _running_in_docker() -> bool:
    # Common indicator file in Docker containers
    return os.path.exists("/.dockerenv")


def main() -> None:
    # When this script runs INSIDE a container:
    # - "localhost" refers to the *same container*, not other services
    # - so frontend must be accessed via docker-compose service name: http://frontend:5173
    default_backend = "http://localhost:8000"
    default_frontend = "http://frontend:5173" if _running_in_docker() else "http://localhost:5173"

    backend_url = os.getenv("BACKEND_URL", default_backend)
    frontend_url = os.getenv("FRONTEND_URL", default_frontend)

    # --- Backend health ---
    try:
        r = requests.get(f"{backend_url}/health", timeout=10)
        if r.status_code != 200:
            fail(f"Backend health HTTP {r.status_code}")
        ok("Backend /health = 200")
    except Exception as e:
        fail(f"Backend /health request failed: {e}")

    # --- Frontend ---
    try:
        r = requests.get(frontend_url, timeout=10)
        if r.status_code != 200:
            fail(f"Frontend HTTP {r.status_code}")
        ok(f"Frontend = 200 ({frontend_url})")
    except Exception as e:
        hint = ""
        if _running_in_docker() and "localhost" in frontend_url:
            hint = " (Docker-এর ভিতরে localhost কাজ করবে না; FRONTEND_URL=http://frontend:5173 ব্যবহার করুন)"
        fail(f"Frontend request failed: {e}{hint}")

    # --- Gemini ---
    key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
    if not key:
        fail("GEMINI_API_KEY is missing in environment/.env")

    try:
        from google import genai
    except Exception as e:
        fail(f"google-genai not installed/importable: {e}")

    try:
        # Small retry loop (sometimes first request is slow)
        last_err = None
        for attempt in range(1, 4):
            try:
                with genai.Client(api_key=key) as client:
                    resp = client.models.generate_content(
                        model=model,
                        contents="Reply with the single word: OK",
                    )
                text = (getattr(resp, "text", "") or "").strip()
                if not text:
                    fail("Gemini returned empty response")
                ok(f"Gemini call success (model={model})")
                print(f"Gemini response preview: {text[:60]}")
                return
            except Exception as e:
                last_err = e
                time.sleep(1.5)
        fail(f"Gemini call failed after retries: {last_err}")
    except SystemExit:
        raise
    except Exception as e:
        fail(f"Gemini test crashed: {e}")


if __name__ == "__main__":
    main()
