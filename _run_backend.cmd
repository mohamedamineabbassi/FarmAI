@echo off
title Farm-AI Backend [8081]
cd /d "C:\Users\21628\Downloads\farm-ai-project-main (2)\farm-ai-project-main\backend"
echo.
echo  *** Starting Spring Boot on port 8081 ***
echo.
call mvn spring-boot:run
echo.
echo  Backend has stopped.
pause
