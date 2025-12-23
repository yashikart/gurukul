@echo off
echo ========================================
echo Starting Gurukul Platform + Ngrok
echo ========================================
echo.

echo [1/5] Starting Backend Gateway (Port 8000)...
start "Backend" cmd /k "cd /d %~dp0Backend && python main.py"
timeout /t 5 /nobreak >nul

echo [2/5] Starting Chatbot Service (Port 8001)...
start "Chatbot" cmd /k "cd /d %~dp0Backend\dedicated_chatbot_service && python chatbot_api.py"
timeout /t 5 /nobreak >nul

echo [3/5] Starting TTS Service (Port 8007)...
start "TTS" cmd /k "cd /d %~dp0Backend\tts_service && python tts.py"
timeout /t 3 /nobreak >nul

echo [4/5] Starting Frontend (Port 5173)...
start "Frontend" cmd /k "cd /d %~dp0new frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo [5/5] Starting Ngrok Tunnels...
echo Starting ngrok for Backend (8000)...
start "Ngrok-Backend" cmd /k "ngrok http 8000 --region=in --host-header=localhost"
timeout /t 2 /nobreak >nul

echo Starting ngrok for Chatbot (8001)...
start "Ngrok-Chat" cmd /k "ngrok http 8001 --region=in --host-header=localhost"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo Backend:  http://localhost:8000
echo Chatbot:  http://localhost:8001
echo TTS:      http://localhost:8007
echo Frontend: http://localhost:5173
echo ========================================
echo Ngrok Tunnels:
echo Check ngrok windows for public URLs
echo ========================================
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

echo Running health check...
python Backend\comprehensive_health_check.py

echo.
echo ========================================
echo IMPORTANT: Update .env.local with ngrok URLs
echo ========================================
echo 1. Check ngrok windows for forwarding URLs
echo 2. Update new frontend\.env.local with URLs
echo 3. Restart frontend if needed
echo ========================================
echo.
echo Press any key to open browser...
pause >nul
start http://localhost:5173
