@echo off
echo Stopping chatbot service...
taskkill /F /FI "WINDOWTITLE eq *Chatbot Service*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq *chatbot_api*" >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting chatbot service with new code...
cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat
cd Gurukul_new-main\Backend\dedicated_chatbot_service
start "Chatbot Service" cmd /k python chatbot_api.py

echo.
echo ✅ Service restarted!
echo 📋 Watch the "Chatbot Service" window for:
echo    - "GROQ_API_KEY: ✅ SET"
echo    - "Groq Model: llama-3.1-70b-versatile"
echo.
echo Wait 10 seconds, then test in browser at:
echo http://localhost:5173/chatbot
