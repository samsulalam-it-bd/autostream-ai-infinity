@echo off
title AutoStream AI Infinity - Bot Launcher (Docker)
color 0A
echo.
echo  ========================================================
echo       AutoStream AI Infinity - Bot + Services Launch
echo  ========================================================
echo.

cd /d "%~dp0"

docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running! Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [OK] Docker is running.
echo.

set /p BUILD_CHOICE="Build fresh images? (y/n, default=n): "
if /i "%BUILD_CHOICE%"=="y" (
    echo.
    echo [1/4] Building and starting all Docker services...
    docker compose up --build -d
) else (
    echo.
    echo [1/4] Starting all Docker services...
    docker compose up -d
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker Compose failed! Check above for errors.
    pause
    exit /b 1
)

echo.
echo [2/4] Waiting for backend to be ready (max 120 seconds)...
set /a _wait_s=0
:_wait_backend
curl -s -f http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 goto _backend_ready
set /a _wait_s+=1
if %_wait_s% GEQ 120 goto _backend_timeout
timeout /t 1 /nobreak >nul
goto _wait_backend

:_backend_ready
echo [OK] Backend is responding.
goto _after_wait

:_backend_timeout
echo [WARN] Backend is still starting. Showing recent backend logs...
docker compose logs backend --tail=50

:_after_wait

echo.
echo [3/4] Checking container status...
docker compose ps

echo.
echo  ========================================================
echo   Bot is running inside the backend container (Telegram)
echo  ========================================================
echo.
echo  Frontend  : http://localhost:5173
echo  Backend   : http://localhost:8000
echo  API Docs  : http://localhost:8000/docs
echo.

set /p OPEN_CHOICE="Open Dashboard + API Docs now? (y/n, default=y): "
if /i not "%OPEN_CHOICE%"=="n" (
    start http://localhost:5173
    start http://localhost:8000/docs
)

echo.
set /p LOG_CHOICE="Follow live logs now? (y/n, default=y): "
if /i "%LOG_CHOICE%"=="n" (
    echo.
    echo [TIP] Live logs: docker compose logs -f backend worker beat
    echo [TIP] Stop all : docker compose down
    echo.
    pause
    exit /b 0
)

echo.
echo [4/4] Streaming backend+worker+beat logs (Ctrl+C to stop)...
docker compose logs -f backend worker beat
