@echo off
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                         IMMEDIATE CORS FIX                                    ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo The CORS error is happening because:
echo   1. Ngrok is NOT running
echo   2. OR ngrok is forwarding to wrong port (8000 instead of 8001)
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.

REM Check if chatbot service is running
echo [Step 1/4] Checking if chatbot service is running on port 8001...
netstat -ano | findstr ":8001" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Chatbot service is running on port 8001
) else (
    echo ❌ Chatbot service is NOT running!
    echo.
    echo Starting chatbot service now...
    cd /d "%~dp0Backend\dedicated_chatbot_service"
    start "Chatbot Service (8001)" cmd /k "python chatbot_api.py"
    echo ⏳ Waiting 5 seconds for service to start...
    timeout /t 5 /nobreak >nul
    cd /d "%~dp0"
)
echo.

REM Kill any existing ngrok
echo [Step 2/4] Stopping any existing ngrok tunnels...
taskkill /F /IM ngrok.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ Cleared any existing ngrok processes
echo.

REM Start ngrok with CORRECT port
echo [Step 3/4] Starting ngrok tunnel to PORT 8001...
echo.
echo ⚠️  CRITICAL: Ngrok MUST forward to PORT 8001 (chatbot service)
echo.
start "Ngrok Tunnel to Port 8001" cmd /k "ngrok http 8001 --region=in --host-header=localhost"
echo.
echo ⏳ Waiting 5 seconds for ngrok to start...
timeout /t 5 /nobreak >nul
echo.

REM Instructions
echo [Step 4/4] MANUAL STEPS REQUIRED:
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo 1. Look at the NGROK window that just opened
echo    Find the line that says: "Forwarding https://XXXXX.ngrok-free.app"
echo    Copy that URL (e.g., https://abc123xyz.ngrok-free.app)
echo.
echo 2. Open Backend\.env in a text editor
echo    Find the line: ALLOWED_ORIGINS=...
echo    Replace the OLD ngrok URL with your NEW ngrok URL
echo    Find the line: NGROK_URL=...
echo    Replace with your NEW ngrok URL
echo.
echo 3. Open "new frontend\.env.local" in a text editor
echo    Find the line: VITE_CHAT_API_BASE_URL=...
echo    Replace with your NEW ngrok URL
echo    Find the line: VITE_CHATBOT_API_URL=...
echo    Replace with your NEW ngrok URL
echo.
echo 4. Restart the chatbot service:
echo    - Close the "Chatbot Service (8001)" window
echo    - Run: cd Backend\dedicated_chatbot_service
echo    - Run: python chatbot_api.py
echo.
echo 5. Visit your ngrok URL in a browser to clear the warning page
echo    Click "Visit Site" button
echo.
echo 6. Refresh your frontend (http://localhost:5173)
echo    Try sending a message again
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo QUICK REFERENCE:
echo   - Chatbot service should be on: http://localhost:8001
echo   - Ngrok should forward to: localhost:8001
echo   - Frontend should use: https://YOUR-NGROK-URL.ngrok-free.app
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
pause
