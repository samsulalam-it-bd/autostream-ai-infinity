@echo off
title AutoStream AI Infinity - LIVE MODE
color 0B
echo.
echo  ================================================================
echo       AutoStream AI Infinity - LIVE MODE LAUNCHER
echo       ngrok domain: contently-deflector-rejoice.ngrok-free.dev
echo  ================================================================
echo.

cd /d "%~dp0"

:: ── 1. Check Docker ──────────────────────────────────────────────
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running! Please start Docker Desktop first.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

:: ── 2. Check ngrok ───────────────────────────────────────────────
set NGROK_EXE=F:\ngrok-v3-stable-windows-amd64\ngrok.exe
if not exist "%NGROK_EXE%" (
    echo [ERROR] ngrok.exe not found at %NGROK_EXE%
    echo Please check the path and update this script.
    pause
    exit /b 1
)
echo [OK] ngrok found.
echo.

:: ── 3. Start Docker services ─────────────────────────────────────
echo [1/4] Starting all Docker services...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose failed! Trying with build...
    docker compose up --build -d
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose still failed. Check errors above.
        pause
        exit /b 1
    )
)
echo [OK] Docker services started.
echo.

:: ── 4. Wait for backend ──────────────────────────────────────────
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
echo [OK] Backend is responding on http://localhost:8000
goto _after_wait

:_backend_timeout
echo [WARN] Backend taking long. Continuing anyway...

:_after_wait
echo.

:: ── 5. Start ngrok tunnels in background ─────────────────────────
echo [3/4] Starting ngrok tunnels...

:: Backend tunnel (port 8000) with permanent domain
start "ngrok-backend" "%NGROK_EXE%" http 8000 --domain=contently-deflector-rejoice.ngrok-free.dev

:: Wait a moment for ngrok to initialize
timeout /t 3 /nobreak >nul
echo [OK] ngrok backend tunnel started.
echo.

:: ── 6. Final status ──────────────────────────────────────────────
echo [4/4] Checking Docker container status...
docker compose ps
echo.

echo  ================================================================
echo   [SUCCESS] AutoStream AI is now LIVE!
echo  ================================================================
echo.
echo   LOCAL ACCESS:
echo   Frontend  : http://localhost:5173
echo   Backend   : http://localhost:8000
echo   API Docs  : http://localhost:8000/docs
echo.
echo   LIVE (PUBLIC) ACCESS:
echo   Backend   : https://contently-deflector-rejoice.ngrok-free.dev
echo   API Docs  : https://contently-deflector-rejoice.ngrok-free.dev/docs
echo   Frontend  : http://localhost:5173  (Docker port)
echo.
echo   IMPORTANT: ngrok dashboard: http://127.0.0.1:4040
echo.
echo   [TIP] To view live logs:  docker compose logs -f
echo   [TIP] To stop all:        docker compose down
echo.
echo   Press any key to open the app in browser...
pause >nul

start http://localhost:5173
start https://contently-deflector-rejoice.ngrok-free.dev/docs

echo.
echo   [RUNNING] Keep this window open! Closing it will stop ngrok.
echo.
pause
