#!/bin/bash
# ================================================================
# AutoStream AI — Single Container Startup Script
# Runs: FastAPI (uvicorn) + Celery Worker + Celery Beat
# together in one container using supervisord
# ================================================================

set -e

echo "========================================"
echo "  AutoStream AI - Starting All Services"
echo "========================================"

# Run database migrations first
echo "[1/4] Running database migrations..."
python -m app.migrate || echo "[WARN] Migration skipped or already up to date."

echo "[2/4] Starting Celery Beat (scheduler)..."
celery -A app.worker.celery_app beat \
    --loglevel=info \
    --scheduler redbeat.RedBeatScheduler \
    --pidfile=/tmp/celerybeat.pid \
    &
BEAT_PID=$!
echo "  Beat PID: $BEAT_PID"

echo "[3/4] Starting Celery Worker..."
celery -A app.worker.celery_app worker \
    --loglevel=info \
    --queues=video_pipeline,default \
    --concurrency=2 \
    &
WORKER_PID=$!
echo "  Worker PID: $WORKER_PID"

echo "[4/4] Starting FastAPI (uvicorn)..."
echo "========================================"

# Trap signals to gracefully shut down background processes
trap "kill $BEAT_PID $WORKER_PID 2>/dev/null; exit" SIGTERM SIGINT

# uvicorn runs in foreground (keeps container alive)
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info
