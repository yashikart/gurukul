@echo off
echo Starting Backend Services...

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\Backend\api_data"
start "API Data Service - Port 8001" cmd /k python api.py

timeout /t 2 /nobreak >nul

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\Backend\tts_service"
start "TTS Service - Port 8007" cmd /k python tts.py

echo Services started!
echo API Data Service: http://localhost:8001
echo TTS Service: http://localhost:8007
