@echo off
REM ========================================
REM FARMAIA - Cache Clear & Turbo Start
REM ========================================
color 0C
title FarmAI Frontend - CACHE CLEAR + TURBO START ⚡

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  🧹 Clearing Cache & Starting Turbo Mode           ║
echo ╚════════════════════════════════════════════════════╝
echo.

echo 1️⃣  Deleting .angular cache...
if exist ".angular" (
    rmdir /s /q ".angular" >nul 2>&1
    echo ✅ .angular cache deleted
) else (
    echo ℹ️  .angular not found
)

echo.
echo 2️⃣  Deleting dist folder...
if exist "dist" (
    rmdir /s /q "dist" >nul 2>&1
    echo ✅ dist deleted
) else (
    echo ℹ️  dist not found
)

echo.
echo 3️⃣  Verifying node_modules...
if not exist "node_modules" (
    echo ⚠️  Installing npm packages...
    call npm install
) else (
    echo ✅ node_modules found
)

echo.
echo 4️⃣  Starting TURBO MODE...
echo.
echo ⚡ Expected results:
echo   - HMR reload: 1-2 seconds
echo   - CSS changes: instant
echo   - Rebuild time: &lt;3 seconds
echo.

call npm run start:turbo

pause
