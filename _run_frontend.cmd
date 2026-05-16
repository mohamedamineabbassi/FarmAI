@echo off
title Farm-AI Frontend [4200]
cd /d "%~dp0forntend"
echo.
echo  *** Installing npm dependencies ***
call npm install
echo.
echo  *** Starting Angular dev server on port 4200 ***
call npx ng serve --open
echo.
echo  Frontend has stopped.
pause
