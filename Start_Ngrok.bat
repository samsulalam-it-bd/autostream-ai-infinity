@echo off
title AutoStream AI Infinity - Ngrok Tunnel
color 0B
echo.
echo  ========================================================
echo       AutoStream AI Infinity - Ngrok Tunnel Launcher
echo  ========================================================
echo.

set NGROK_DIR=F:\ngrok-v3-stable-windows-amd64
set NGROK_EXE=%NGROK_DIR%\ngrok.exe
set NGROK_DOMAIN=contently-deflector-rejoice.ngrok-free.dev
set PORT=8000

:: Check if ngrok.exe exists in the specified folder
if not exist "%NGROK_EXE%" (
    echo [ERROR] ngrok.exe not found at "%NGROK_EXE%"
    echo.
    echo Please make sure Ngrok is extracted to:
    echo F:\ngrok-v3-stable-windows-amd64\
    echo.
    set /p USER_PATH="Enter correct path to ngrok folder (or press Enter to exit): "
    if "%USER_PATH%"=="" exit /b 1
    set NGROK_DIR=%USER_PATH%
    set NGROK_EXE=%USER_PATH%\ngrok.exe
)

if not exist "%NGROK_EXE%" (
    echo [ERROR] ngrok.exe still not found. Exiting.
    pause
    exit /b 1
)

echo [OK] Ngrok executable found at "%NGROK_EXE%"
echo.
echo [INFO] Exposing Port %PORT% on Domain %NGROK_DOMAIN%
echo.
echo [IMPORTANT] Make sure you have added your Ngrok authtoken:
echo             "%NGROK_EXE%" config add-authtoken YOUR_AUTHTOKEN
echo.
echo Starting Ngrok tunnel...
echo.
"%NGROK_EXE%" http %PORT% --domain=%NGROK_DOMAIN%
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ngrok failed to start.
    echo If it failed due to a domain/auth error, try running:
    echo "%NGROK_EXE%" http %PORT%
    echo to get a random public URL (remember to update your .env redirect URIs if you do this!)
    echo.
    pause
)
