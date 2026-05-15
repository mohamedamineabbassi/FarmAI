@echo off
title Farm-AI Frontend [4200]
cd /d "C:\Users\21628\Downloads\farm-ai-project-main (2)\farm-ai-project-main\forntend"
echo.
echo  *** Installing npm dependencies ***
call npm install
echo.
echo  *** Starting Angular dev server on port 4200 ***
call npx ng serve --open
echo.
echo  Frontend has stopped.
pause
