@echo off
title Farm-AI AI Server [8000]
cd /d "%~dp0ai_system"
echo.
echo  *** Installing Python dependencies ***
pip install -r requirements.txt
echo.
echo  *** Starting FastAPI server on port 8000 ***
python main.py
echo.
echo  AI Server has stopped.
pause
