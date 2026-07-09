@echo off
title AutoStream AI - Server Startup
color 0A

echo.
echo ============================================
echo   AutoStream AI - Server Startup Script
echo ============================================
echo.

REM Step 1: Check if Docker is running
echo [1/4] Checking Docker status...
docker info > NUL 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker is not running or not installed!
    echo Please open Docker Desktop and wait for it to show "Engine Running"
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

REM Step 2: Pull and Build containers
echo [2/4] Building and starting all containers...
echo (This may take 2-5 minutes on first run)
echo.
docker compose up -d --build
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start containers.
    echo Check the logs below for details:
    docker compose logs --tail=50
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] All containers started.
echo.

REM Step 3: Wait for backend to be ready
echo [3/4] Waiting for backend to be ready (30 seconds)...
timeout /t 30 /nobreak > NUL
echo.

REM Step 4: Health check
echo [4/4] Checking backend health...
curl -s http://localhost:8000/health > NUL 2>&1
if %errorlevel% neq 0 (
    echo [!] Backend may still be starting. Check Docker logs.
    docker compose logs backend --tail=30
) else (
    echo [OK] Backend is healthy!
)

echo.
echo ============================================
echo   SERVERS ARE NOW RUNNING:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to view live logs (Ctrl+C to stop)
pause > NUL
docker compose logs -f
