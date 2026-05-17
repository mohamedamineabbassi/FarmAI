@echo off
REM ============================================================
REM  FARM-AI  -  Start All Services (Windows)
REM  Backend (Spring Boot) + Frontend (Angular) + AI (FastAPI)
REM ============================================================

setlocal enabledelayedexpansion
title Farm-AI  -  Service Launcher
color 0A

REM --- Resolve project root (where this .bat lives) ----------
set "PROJECT_ROOT=%~dp0"
REM Remove trailing backslash
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo.
echo  ============================================================
echo       FARM-AI  ^|  Automated Service Launcher
echo  ============================================================
echo   Project : %PROJECT_ROOT%
echo   Date    : %date%  %time%
echo  ============================================================
echo.

REM ============================================================
REM  1. PREREQUISITE CHECKS
REM ============================================================

echo  [STEP 1/5]  Checking prerequisites ...
echo  ------------------------------------------------------------

if exist "%PROJECT_ROOT%\backend\mvnw.cmd" (
    echo   [OK] Maven Wrapper found
) else (
    where mvn >nul 2>&1
    if errorlevel 1 (
        echo   [X] Maven not found in PATH and no Maven Wrapper!
        pause & exit /b 1
    )
    echo   [OK] Maven found
)

where node >nul 2>&1
if errorlevel 1 (
    echo   [X] Node.js not found in PATH!
    pause & exit /b 1
)
echo   [OK] Node.js found

where python >nul 2>&1
if errorlevel 1 (
    echo   [X] Python not found in PATH!
    pause & exit /b 1
)
echo   [OK] Python found

echo   [..] Testing MySQL connection ...
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot123 -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo   [!] Cannot connect to MySQL. Continuing anyway...
) else (
    echo   [OK] MySQL is reachable
)

echo.
echo  [OK] All prerequisites satisfied.
echo  ============================================================
echo.

REM ============================================================
REM  2. WRITE LAUNCHER SCRIPTS (persistent, not deleted)
REM ============================================================

REM -- Backend launcher --
(
echo @echo off
echo title Farm-AI Backend [8081]
echo cd /d "%%~dp0backend"
echo echo.
echo echo  *** Starting Spring Boot on port 8081 ***
echo echo.
echo call .\mvnw.cmd spring-boot:run
echo echo.
echo echo  Backend has stopped.
echo pause
) > "%PROJECT_ROOT%\_run_backend.cmd"

REM -- Frontend launcher --
(
echo @echo off
echo title Farm-AI Frontend [4200]
echo cd /d "%%~dp0forntend"
echo echo.
echo echo  *** Installing npm dependencies ***
echo call npm install
echo echo.
echo echo  *** Starting Angular dev server on port 4200 ***
echo call npx ng serve --open
echo echo.
echo echo  Frontend has stopped.
echo pause
) > "%PROJECT_ROOT%\_run_frontend.cmd"

REM -- AI Server launcher --
(
echo @echo off
echo title Farm-AI SOC Engine [8000]
echo cd /d "%%~dp0"
echo echo.
echo echo  *** Installing Python dependencies ***
echo pip install -r ai_engine/requirements.txt
echo echo.
echo echo  *** Starting FastAPI server on port 8000 ***
echo python -m ai_engine.main
echo echo.
echo echo  AI Server has stopped.
echo pause
) > "%PROJECT_ROOT%\_run_ai_server.cmd"

REM -- Camera launcher (Disabled because SOC Engine handles it) --
(
echo @echo off
echo title Farm-AI Camera Stream
echo echo  *** Camera stream is now handled centrally by the SOC Engine ***
echo echo  You can close this window.
echo pause
) > "%PROJECT_ROOT%\_run_camera.cmd"

echo  Launcher scripts created.
echo.

REM ============================================================
REM  3. LAUNCH ALL SERVICES
REM ============================================================

echo  [STEP 2/5]  Starting Backend (port 8081) ...
start "" "%PROJECT_ROOT%\_run_backend.cmd"
echo   [OK] Backend window opened.

echo   Waiting 10 seconds for backend to initialize ...
timeout /t 10 /nobreak >nul
echo.

echo  [STEP 3/5]  Starting Frontend (port 4200) ...
start "" "%PROJECT_ROOT%\_run_frontend.cmd"
echo   [OK] Frontend window opened.

echo   Waiting 5 seconds ...
timeout /t 5 /nobreak >nul
echo.

echo  [STEP 4/5]  Starting AI Server (port 8000) ...
start "" "%PROJECT_ROOT%\_run_ai_server.cmd"
echo   [OK] AI Server window opened.

echo   Waiting 5 seconds ...
timeout /t 5 /nobreak >nul
echo.

echo  [STEP 5/5]  Starting Camera Stream ...
start "" "%PROJECT_ROOT%\_run_camera.cmd"
echo   [OK] Camera window opened.
echo.

REM ============================================================
REM  SUMMARY
REM ============================================================

echo.
echo  ============================================================
echo       All services have been launched!
echo  ============================================================
echo.
echo   Service             Port    Window Title
echo   ------------------  ------  -------------------------
echo   Backend  (Spring)   8081    Farm-AI Backend [8081]
echo   Frontend (Angular)  4200    Farm-AI Frontend [4200]
echo   AI Server(FastAPI)  8000    Farm-AI AI Server [8000]
echo   Camera Stream       --      Farm-AI Camera Stream
echo.
echo  ============================================================
echo       Quick Links
echo  ============================================================
echo.
echo   Frontend App    : http://localhost:4200
echo   Backend API     : http://localhost:8081
echo   AI API Swagger  : http://localhost:8000/docs
echo.
echo  ============================================================
echo   TIP: Close each service window to stop it.
echo        The frontend takes 1-2 min to compile on first run.
echo  ============================================================
echo.
echo  Press any key to close this launcher window.
echo  (Services will keep running in their own windows)
pause >nul
