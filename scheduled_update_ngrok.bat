@echo off
echo ====================================================
echo    Gurukul Platform - Scheduled Ngrok URL Update
echo ====================================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running ngrok URL updater in auto mode...
python update_ngrok_url.py --auto

echo.
echo Update completed at %date% %time%
echo.