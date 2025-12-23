@echo off
echo ════════════════════════════════════════════════════════════════
echo   RESTARTING DEDICATED CHATBOT SERVICE
echo ════════════════════════════════════════════════════════════════
echo.

REM Kill existing chatbot service
echo [1/3] Stopping existing chatbot service...
taskkill /F /FI "WINDOWTITLE eq *Chatbot Service*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *chatbot_api.py*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ Stopped old service
echo.

REM Activate venv
echo [2/3] Activating virtual environment...
cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Start chatbot service
echo [3/3] Starting chatbot service on port 8001...
cd Gurukul_new-main\Backend\dedicated_chatbot_service
echo.
echo 🚀 Starting service with real Groq API integration...
echo 📋 Watch for:
echo    - "LLM Service Configuration" showing Groq key status
echo    - "Calling Groq API" when processing messages
echo    - "Groq Success" for real AI responses
echo.
python chatbot_api.py
