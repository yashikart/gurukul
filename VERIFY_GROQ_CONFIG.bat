@echo off
echo ════════════════════════════════════════════════════════════════
echo   GROQ CONFIGURATION VERIFICATION
echo ════════════════════════════════════════════════════════════════
echo.

cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat >nul 2>&1

cd Gurukul_new-main\Backend

echo 📋 Checking Backend/.env configuration...
echo.

REM Check if GROQ_API_KEY is set
findstr /C:"GROQ_API_KEY=" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GROQ_API_KEY found in .env
    for /f "tokens=2 delims==" %%a in ('findstr /C:"GROQ_API_KEY=" .env') do (
        set KEY=%%a
    )
    echo    Key starts with: !KEY:~0,10!...
) else (
    echo ❌ GROQ_API_KEY not found in .env
)

REM Check if GROQ_MODEL_NAME is set
findstr /C:"GROQ_MODEL_NAME=" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GROQ_MODEL_NAME found in .env
    for /f "tokens=2 delims==" %%a in ('findstr /C:"GROQ_MODEL_NAME=" .env') do (
        echo    Model: %%a
    )
) else (
    echo ❌ GROQ_MODEL_NAME not found in .env
)

REM Check if GROQ_API_ENDPOINT is set
findstr /C:"GROQ_API_ENDPOINT=" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GROQ_API_ENDPOINT found in .env
    for /f "tokens=2 delims==" %%a in ('findstr /C:"GROQ_API_ENDPOINT=" .env') do (
        echo    Endpoint: %%a
    )
) else (
    echo ❌ GROQ_API_ENDPOINT not found in .env
)

echo.
echo 📋 Checking Frontend configuration...
echo.

cd /d "C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\new frontend"

REM Check if VITE_CHAT_API_BASE_URL is set
findstr /C:"VITE_CHAT_API_BASE_URL=" .env.local >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ VITE_CHAT_API_BASE_URL found in .env.local
    for /f "tokens=2 delims==" %%a in ('findstr /C:"VITE_CHAT_API_BASE_URL=" .env.local') do (
        echo    URL: %%a
    )
) else (
    echo ❌ VITE_CHAT_API_BASE_URL not found in .env.local
)

REM Check if VITE_CHATBOT_API_URL is set
findstr /C:"VITE_CHATBOT_API_URL=" .env.local >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ VITE_CHATBOT_API_URL found in .env.local
    for /f "tokens=2 delims==" %%a in ('findstr /C:"VITE_CHATBOT_API_URL=" .env.local') do (
        echo    URL: %%a
    )
) else (
    echo ❌ VITE_CHATBOT_API_URL not found in .env.local
)

echo.
echo ════════════════════════════════════════════════════════════════
echo   VERIFICATION COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
echo 📋 Next Steps:
echo    1. If all checks passed, run: RESTART_CHATBOT.bat
echo    2. Test the chat at http://localhost:5173/chatbot
echo    3. Verify you get real AI responses (not fallback mode)
echo.
echo ⚠️  SECURITY REMINDER:
echo    The API key in Backend/.env was shared publicly.
echo    Go to https://console.groq.com/keys and revoke it!
echo    Then generate a new key and update Backend/.env
echo.
pause
