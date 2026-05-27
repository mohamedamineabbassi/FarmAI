@echo off
title Farm-AI Backend [8081]
cd /d "%~dp0backend"
echo.
echo  *** Starting Spring Boot on port 8081 ***
echo.
call .\mvnw.cmd spring-boot:run
echo.
echo  Backend has stopped.
pause
