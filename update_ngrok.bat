@echo off
echo ====================================================
echo    Gurukul Platform - Ngrok URL Updater
echo ====================================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running ngrok URL updater...
python update_ngrok_url.py

echo.
echo Press any key to exit...
pause >nul