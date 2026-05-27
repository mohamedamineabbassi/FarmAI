@echo off
REM ========================================
REM FARMAIA - Frontend Turbo Start Script
REM ========================================
color 0A
title FarmAI Frontend - TurboMode ⚡

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  🚀 FarmAI Frontend - TURBO MODE START            ║
echo ║  Ultra-fast development environment                ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Vérifier si node_modules existe
if not exist "node_modules" (
    echo ⚠️  node_modules not found. Installing dependencies...
    echo.
    call npm install
    if errorlevel 1 (
        echo ❌ npm install failed!
        pause
        exit /b 1
    )
)

REM Vérifier si Angular CLI est installé
if not exist "node_modules\@angular\cli" (
    echo ⚠️  Angular CLI not found. Installing...
    call npm install -g @angular/cli
)

echo ✅ Starting development server...
echo 📍 Server will run on: http://localhost:4200
echo 🔄 File watching: ACTIVE (500ms polling)
echo 💾 Changes auto-reload: ENABLED
echo.
echo Press CTRL+C to stop the server
echo.

REM Clear .angular cache for fresh build
if exist ".angular" (
    echo 🧹 Clearing Angular cache...
    rmdir /s /q .angular >nul 2>&1
)

REM Start the turbo server
call npm run start:turbo

pause
