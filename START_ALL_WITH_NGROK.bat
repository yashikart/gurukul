@echo off
echo Starting All Services + Ngrok...
cd /d "%~dp0"

echo [1/5] Starting Gateway (8000)...
start "Gateway" cmd /k "cd Backend && python main.py > ..\logs\gateway.log 2>&1"
timeout /t 3 /nobreak >nul

echo [2/5] Starting Chatbot (8001)...
start "Chatbot" cmd /k "cd Backend\dedicated_chatbot_service && python chatbot_api.py > ..\..\logs\chatbot.log 2>&1"
timeout /t 3 /nobreak >nul

echo [3/5] Starting TTS (8007)...
start "TTS" cmd /k "cd Backend\tts_service && python tts.py > ..\..\logs\tts.log 2>&1"
timeout /t 3 /nobreak >nul

echo [4/5] Starting Ngrok Tunnels...
start "Ngrok-8001" cmd /k "ngrok http 8001 --region=in --host-header=localhost --log=stdout"
timeout /t 2 /nobreak >nul
start "Ngrok-8007" cmd /k "ngrok http 8007 --region=in --host-header=localhost --log=stdout"

echo [5/5] Waiting for services...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo All Services Started!
echo ========================================
echo Gateway:  http://localhost:8000
echo Chatbot:  http://localhost:8001
echo TTS:      http://localhost:8007
echo Ngrok:    Check ngrok windows for URLs
echo ========================================
echo.
echo Next: cd "new frontend" ^&^& npm run dev
pause
