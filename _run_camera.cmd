@echo off
title Farm-AI Camera Stream
cd /d "%~dp0ai_system"
echo.
echo  *** Launching camera stream ***
python camera_ai_stream.py --source 0 --camera_id 1
echo.
echo  Camera stream has stopped.
pause
