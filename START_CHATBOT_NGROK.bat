@echo off
echo ========================================
echo GURUKUL CHATBOT SERVICE + NGROK STARTUP
echo ========================================
echo.

REM Kill any existing processes on port 8001
echo [1/3] Cleaning up port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8001
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Start Chatbot Service
echo [2/3] Starting Chatbot Service on port 8001...
cd /d "%~dp0Backend\dedicated_chatbot_service"
start "Chatbot Service (8001)" cmd /k "python chatbot_api.py"
timeout /t 5 /nobreak >nul

REM Start ngrok tunnel
echo [3/3] Starting ngrok tunnel...
echo.
echo IMPORTANT: Update the ngrok URL in:
echo   - Backend\.env (NGROK_URL and ALLOWED_ORIGINS)
echo   - new frontend\.env.local (VITE_CHAT_API_BASE_URL and VITE_CHATBOT_API_URL)
echo.
start "Ngrok Tunnel" cmd /k "ngrok http 8001 --region=in --host-header=localhost"

echo.
echo ========================================
echo STARTUP COMPLETE!
echo ========================================
echo.
echo Services:
echo   - Chatbot API: http://localhost:8001
echo   - Ngrok Tunnel: Check the ngrok window for URL
echo.
echo Next Steps:
echo   1. Copy the ngrok URL from the ngrok window
echo   2. Update Backend\.env with the new URL
echo   3. Update new frontend\.env.local with the new URL
echo   4. Restart the chatbot service
echo   5. Test: curl -i "https://YOUR-NGROK-URL/health"
echo.
pause
