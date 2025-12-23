@echo off
echo ════════════════════════════════════════════════════════════════
echo   VERIFYING GROQ INTEGRATION FIX
echo ════════════════════════════════════════════════════════════════
echo.

cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat >nul 2>&1

echo [1/3] Checking .env configuration...
cd Gurukul_new-main\Backend
findstr /C:"GROQ_API_KEY=" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GROQ_API_KEY found in .env
) else (
    echo ❌ GROQ_API_KEY not found in .env
    echo    Add: GROQ_API_KEY=your_key_here
    pause
    exit /b 1
)

findstr /C:"GROQ_MODEL_NAME=" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ GROQ_MODEL_NAME found in .env
) else (
    echo ❌ GROQ_MODEL_NAME not found in .env
    echo    Add: GROQ_MODEL_NAME=llama-3.1-70b-versatile
)

echo.
echo [2/3] Testing environment loading...
cd dedicated_chatbot_service
python -c "import os; import sys; sys.path.append('..'); from dotenv import load_dotenv; env_path = os.path.join('..', '.env'); load_dotenv(env_path); key = os.getenv('GROQ_API_KEY', '').strip(); print('✅ Environment loads correctly' if key else '❌ Environment not loading'); print(f'   Groq Key: {\"SET (\" + key[:10] + \"...)\" if key else \"NOT SET\"}'); print(f'   Model: {os.getenv(\"GROQ_MODEL_NAME\", \"llama-3.1-70b-versatile\")}')"

echo.
echo [3/3] Checking chatbot_api.py has inline LLM service...
findstr /C:"def call_groq" chatbot_api.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Inline LLM service found in chatbot_api.py
) else (
    echo ❌ Inline LLM service not found
    echo    The fix may not have been applied correctly
)

findstr /C:"load_dotenv(env_path)" chatbot_api.py >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Early .env loading found in chatbot_api.py
) else (
    echo ⚠️  Early .env loading not found
    echo    Environment may not load before LLM service initializes
)

echo.
echo ════════════════════════════════════════════════════════════════
echo   VERIFICATION COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
echo 📋 Next Steps:
echo    1. If all checks passed: Run START_CHATBOT_AND_TEST.bat
echo    2. If any checks failed: Review FINAL_FIX_APPLIED.md
echo.
pause
