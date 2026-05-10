#!/usr/bin/env python3
"""
AutoStream AI Infinity — Backend API Test Suite
================================================
Tests every endpoint of the FastAPI backend.

Usage:
    # With backend running locally (python -m uvicorn app.main:app --reload):
    python scripts/test_backend.py

    # Or against a custom host:
    BASE_URL=http://localhost:8000 python scripts/test_backend.py

Requirements:
    pip install httpx  (already in requirements.txt)

Output:
    Prints a colored test report. Exits with code 1 if any test fails.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

import httpx

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
API = f"{BASE_URL}/api/v1"

# ── ANSI Colors ───────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0
results = []


def ok(name: str, data=None):
    global passed
    passed += 1
    results.append((True, name, data))
    print(f"  {GREEN}✓{RESET} {name}")


def fail(name: str, reason: str):
    global failed
    failed += 1
    results.append((False, name, reason))
    print(f"  {RED}✗{RESET} {name}")
    print(f"    {RED}→ {reason}{RESET}")


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")


async def run_tests():
    global passed, failed

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:

        # ── Health ────────────────────────────────────────────────────────────
        section("Root & Health")

        r = await c.get("/")
        if r.status_code == 200 and "name" in r.json():
            ok("GET / — API root returns name", r.json().get("name"))
        else:
            fail("GET / — API root", f"{r.status_code}: {r.text[:200]}")

        r = await c.get("/health")
        if r.status_code == 200 and r.json().get("status") == "ok":
            ok("GET /health — health check")
        else:
            fail("GET /health", f"{r.status_code}: {r.text[:200]}")

        # ── Dashboard ─────────────────────────────────────────────────────────
        section("Dashboard")

        r = await c.get(f"{API}/dashboard/stats")
        if r.status_code == 200:
            d = r.json()
            expected_keys = {"total_uploads_today", "active_api_keys", "pending_schedules", "total_accounts", "total_videos"}
            missing = expected_keys - set(d.keys())
            if not missing:
                ok("GET /dashboard/stats — all stat fields present")
            else:
                fail("GET /dashboard/stats — missing keys", f"{missing}")
        else:
            fail("GET /dashboard/stats", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/dashboard/health")
        if r.status_code == 200:
            d = r.json()
            if "database" in d and "redis" in d and "celery" in d:
                ok(f"GET /dashboard/health — DB:{d['database']} Redis:{d['redis']} Celery:{d['celery']}")
            else:
                fail("GET /dashboard/health — missing fields", str(d))
        else:
            fail("GET /dashboard/health", f"{r.status_code}: {r.text[:200]}")

        # ── Channel Groups ────────────────────────────────────────────────────
        section("Channel Groups")

        r = await c.get(f"{API}/accounts/groups")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /accounts/groups — returned {len(r.json())} groups")
        else:
            fail("GET /accounts/groups", f"{r.status_code}: {r.text[:200]}")

        r = await c.post(f"{API}/accounts/groups", json={
            "name": f"Test Group {uuid.uuid4().hex[:6]}",
            "platform": "youtube",
            "description": "Created by test suite",
        })
        if r.status_code == 201:
            created_group = r.json()
            ok(f"POST /accounts/groups — created '{created_group['name']}'")
        else:
            fail("POST /accounts/groups", f"{r.status_code}: {r.text[:200]}")
            created_group = None

        if created_group:
            r = await c.delete(f"{API}/accounts/groups/{created_group['id']}")
            if r.status_code == 204:
                ok("DELETE /accounts/groups/{id} — deleted successfully")
            else:
                fail("DELETE /accounts/groups/{id}", f"{r.status_code}: {r.text[:200]}")

        # ── Accounts ──────────────────────────────────────────────────────────
        section("Accounts")

        r = await c.get(f"{API}/accounts/")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /accounts/ — returned {len(r.json())} accounts")
        else:
            fail("GET /accounts/", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/accounts/?platform=youtube")
        if r.status_code == 200:
            ok(f"GET /accounts/?platform=youtube — {len(r.json())} YouTube accounts")
        else:
            fail("GET /accounts/?platform=youtube", f"{r.status_code}: {r.text[:200]}")

        r = await c.post(f"{API}/accounts/", json={
            "platform": "youtube",
            "channel_name": "Test Channel (e2e)",
            "channel_id": f"UC_test_{uuid.uuid4().hex[:8]}",
            "access_token": "demo_access_token_for_test",
            "refresh_token": "demo_refresh_token_for_test",
            "subscriber_count": 12345,
        })
        if r.status_code == 201:
            created_acc = r.json()
            ok(f"POST /accounts/ — created '{created_acc['channel_name']}'")
        else:
            fail("POST /accounts/", f"{r.status_code}: {r.text[:200]}")
            created_acc = None

        if created_acc:
            r = await c.get(f"{API}/accounts/{created_acc['id']}")
            if r.status_code == 200 and r.json()["id"] == created_acc["id"]:
                ok("GET /accounts/{id} — retrieved by ID")
            else:
                fail("GET /accounts/{id}", f"{r.status_code}: {r.text[:200]}")

            r = await c.patch(f"{API}/accounts/{created_acc['id']}", json={"status": "expired"})
            if r.status_code == 200 and r.json()["status"] == "expired":
                ok("PATCH /accounts/{id} — status updated to expired")
            else:
                fail("PATCH /accounts/{id}", f"{r.status_code}: {r.text[:200]}")

            r = await c.delete(f"{API}/accounts/{created_acc['id']}")
            if r.status_code == 204:
                ok("DELETE /accounts/{id} — deleted")
            else:
                fail("DELETE /accounts/{id}", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/accounts/oauth/google/init")
        if r.status_code == 200 and "auth_url" in r.json():
            ok("GET /accounts/oauth/google/init — returns auth_url")
        else:
            fail("GET /accounts/oauth/google/init", f"{r.status_code}: {r.text[:200]}")

        # ── API Vault ─────────────────────────────────────────────────────────
        section("API Vault")

        r = await c.get(f"{API}/api-vault/")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /api-vault/ — {len(r.json())} keys")
        else:
            fail("GET /api-vault/", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/api-vault/stats/summary")
        if r.status_code == 200:
            d = r.json()
            if "total" in d and "active" in d and "locked" in d:
                ok(f"GET /api-vault/stats/summary — total:{d['total']} active:{d['active']} locked:{d['locked']}")
            else:
                fail("GET /api-vault/stats/summary — missing fields", str(d))
        else:
            fail("GET /api-vault/stats/summary", f"{r.status_code}: {r.text[:200]}")

        # Upload a JSON credential file
        test_creds = json.dumps({
            "type": "service_account",
            "project_id": f"test-project-{uuid.uuid4().hex[:8]}",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
        }).encode()

        r = await c.post(
            f"{API}/api-vault/upload-json",
            files=[("files", ("test_creds.json", test_creds, "application/json"))],
            params={"service_name": "google"},
        )
        if r.status_code == 201 and (r.json().get("added", 0) > 0 or r.json().get("skipped", 0) > 0):
            ok(
                f"POST /api-vault/upload-json — added {r.json().get('added', 0)} key(s), "
                f"skipped {r.json().get('skipped', 0)}"
            )
        else:
            fail("POST /api-vault/upload-json", f"{r.status_code}: {r.text[:200]}")

        # Get keys to find one to test unlock/delete
        r = await c.get(f"{API}/api-vault/")
        if r.status_code == 200 and r.json():
            key_id = r.json()[0]["id"]
            r2 = await c.post(f"{API}/api-vault/{key_id}/unlock")
            if r2.status_code == 200:
                ok("POST /api-vault/{id}/unlock — key unlocked")
            else:
                fail("POST /api-vault/{id}/unlock", f"{r2.status_code}: {r2.text[:200]}")

        # ── Videos ────────────────────────────────────────────────────────────
        section("Videos")

        r = await c.get(f"{API}/videos/")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /videos/ — {len(r.json())} videos")
        else:
            fail("GET /videos/", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/videos/?status_filter=pending")
        if r.status_code == 200:
            ok(f"GET /videos/?status_filter=pending — {len(r.json())} pending")
        else:
            fail("GET /videos/?status_filter=pending", f"{r.status_code}: {r.text[:200]}")

        # ── Schedules ─────────────────────────────────────────────────────────
        section("Schedules")

        r = await c.get(f"{API}/schedules/")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /schedules/ — {len(r.json())} schedules")
        else:
            fail("GET /schedules/", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/schedules/?is_published=false")
        if r.status_code == 200:
            ok(f"GET /schedules/?is_published=false — {len(r.json())} pending")
        else:
            fail("GET /schedules/?is_published=false", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/schedules/?is_published=true")
        if r.status_code == 200:
            ok(f"GET /schedules/?is_published=true — {len(r.json())} published")
        else:
            fail("GET /schedules/?is_published=true", f"{r.status_code}: {r.text[:200]}")

        # ── Logs ──────────────────────────────────────────────────────────────
        section("Logs")

        r = await c.get(f"{API}/logs/")
        if r.status_code == 200 and isinstance(r.json(), list):
            ok(f"GET /logs/ — {len(r.json())} log entries")
        else:
            fail("GET /logs/", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/logs/?limit=5")
        if r.status_code == 200 and len(r.json()) <= 5:
            ok("GET /logs/?limit=5 — limit respected")
        else:
            fail("GET /logs/?limit=5", f"{r.status_code}: {r.text[:200]}")

        r = await c.get(f"{API}/logs/?level=ERROR")
        if r.status_code == 200:
            errors = r.json()
            all_error_level = all(l["level"] == "ERROR" for l in errors)
            if all_error_level or len(errors) == 0:
                ok(f"GET /logs/?level=ERROR — {len(errors)} error log(s)")
            else:
                fail("GET /logs/?level=ERROR — returned non-ERROR logs", str(errors[:2]))
        else:
            fail("GET /logs/?level=ERROR", f"{r.status_code}: {r.text[:200]}")

        # ── SSE Stream (quick connect test) ────────────────────────────────────
        section("SSE Logs Stream")
        try:
            async with c.stream("GET", f"{API}/logs/stream", timeout=5.0) as stream:
                async for chunk in stream.aiter_text():
                    if chunk.strip():
                        ok("GET /logs/stream — SSE connection established, receiving data")
                        break
        except httpx.ReadTimeout:
            ok("GET /logs/stream — SSE connected (timed out waiting for data, which is OK)")
        except Exception as e:
            fail("GET /logs/stream", str(e))

        # ── 404 / Error Handling ──────────────────────────────────────────────
        section("Error Handling")

        r = await c.get(f"{API}/accounts/{uuid.uuid4()}")
        if r.status_code == 404:
            ok("GET /accounts/{nonexistent_id} — returns 404")
        else:
            fail("GET /accounts/{nonexistent_id} — expected 404", f"{r.status_code}")

        r = await c.post(f"{API}/accounts/groups", json={"invalid": "data"})
        if r.status_code == 422:
            ok("POST /accounts/groups with invalid body — returns 422 Unprocessable")
        else:
            fail("POST /accounts/groups invalid body — expected 422", f"{r.status_code}")

    # ── Summary ───────────────────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'═'*55}")
    print(f"{BOLD}  Test Results: {passed}/{total} passed{RESET}")
    if failed == 0:
        print(f"  {GREEN}{BOLD}✅ ALL TESTS PASSED!{RESET}")
    else:
        print(f"  {RED}{BOLD}❌ {failed} test(s) failed.{RESET}")
        print(f"\n  {RED}Failed tests:{RESET}")
        for ok_, name, data in results:
            if not ok_:
                print(f"    {RED}• {name}{RESET}")
                print(f"      {data}")
    print(f"{'═'*55}\n")

    return failed == 0


if __name__ == "__main__":
    print(f"\n{BOLD}AutoStream AI — Backend Test Suite{RESET}")
    print(f"  Target: {BOLD}{BASE_URL}{RESET}")
    print(f"  Note: Backend must be running. Start with:")
    print(f"  {YELLOW}  cd backend && uvicorn app.main:app --reload{RESET}\n")

    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
