@echo off
title Farm-AI SOC Engine [8000]
cd /d "%~dp0"
echo.
echo  *** Installing Python dependencies ***
pip install -r ai_engine/requirements.txt
echo.
echo  *** Starting FastAPI server on port 8000 ***
python -m ai_engine.main
echo.
echo  AI Server has stopped.
pause
