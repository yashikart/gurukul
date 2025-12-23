@echo off
echo ════════════════════════════════════════════════════════════════
echo   STARTING NGROK ON CORRECT PORT (8001)
echo ════════════════════════════════════════════════════════════════
echo.
echo [1/2] Stopping any existing ngrok sessions...
taskkill /F /IM ngrok.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Stopped existing ngrok session
    timeout /t 2 /nobreak >nul
) else (
    echo ℹ️  No existing ngrok sessions found
)
echo.
echo [2/2] Starting ngrok on PORT 8001 (chatbot service)...
echo.
echo ⚠️  After ngrok starts:
echo   1. Copy the ngrok URL from this window
echo   2. Update Backend\.env with the new URL
echo   3. Update "new frontend\.env.local" with the new URL
echo   4. Restart chatbot service
echo   5. Visit ngrok URL in browser to clear warning
echo.
ngrok http 8001 --region=in --host-header=localhost
