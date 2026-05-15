@echo off
title Farm-AI Camera Stream
cd /d "C:\Users\21628\Downloads\farm-ai-project-main (2)\farm-ai-project-main\ai_system"
echo.
echo  *** Launching camera stream ***
python camera_ai_stream.py --source 0 --camera_id 1
echo.
echo  Camera stream has stopped.
pause
