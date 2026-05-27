@echo off
echo ====================================================
echo DEMARRAGE MOTEUR SOC AI (Security Operations Center)
echo ====================================================
cd /d "%~dp0"
echo Installation des dependances (si besoin)...
pip install -r ai_engine/requirements.txt
echo.
echo Lancement du serveur FastAPI...
python -m ai_engine.main
pause
