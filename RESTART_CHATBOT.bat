@echo off
echo ════════════════════════════════════════════════════════════════
echo   RESTARTING CHATBOT SERVICE WITH NEW API KEY
echo ════════════════════════════════════════════════════════════════
echo.
echo [1/2] Stopping existing chatbot service...
taskkill /F /FI "WINDOWTITLE eq *chatbot_api.py*" >nul 2>&1
taskkill /F /FI "CommandLine eq *chatbot_api.py*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo ✅ Stopped old chatbot service
echo.
echo [2/2] Starting chatbot service with new API key...
cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat
cd Gurukul_new-main\Backend\dedicated_chatbot_service
echo.
echo 🚀 Starting chatbot on port 8001...
echo.
python chatbot_api.py
