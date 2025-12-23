@echo off
echo ════════════════════════════════════════════════════════════════
echo   STARTING CHATBOT SERVICE AND TESTING
echo ════════════════════════════════════════════════════════════════
echo.

cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat

cd Gurukul_new-main\Backend\dedicated_chatbot_service

echo 🚀 Starting chatbot service...
echo.
echo 📋 Watch for these startup messages:
echo    📦 LOADING ENVIRONMENT
echo       GROQ_API_KEY: ✅ SET
echo       GROQ_MODEL_NAME: llama-3.1-70b-versatile
echo.
echo    🚀 INITIALIZING LLM SERVICE
echo       Groq API Key: ✅ SET
echo       Groq Model: llama-3.1-70b-versatile
echo.
echo ⚠️  If you see "❌ NOT SET" - check Backend\.env file
echo.
echo Press Ctrl+C to stop the service
echo.

start "Chatbot Service" cmd /k "python chatbot_api.py"

echo.
echo ⏳ Waiting 10 seconds for service to start...
timeout /t 10 /nobreak >nul

echo.
echo 🧪 Testing health endpoint...
curl http://localhost:8001/health

echo.
echo.
echo 🧪 Testing Groq integration...
curl -X POST "http://localhost:8001/chatpost?user_id=test-user" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"What is 2+2?\",\"llm\":\"grok\"}"

timeout /t 2 /nobreak >nul

curl "http://localhost:8001/chatbot?user_id=test-user"

echo.
echo.
echo ════════════════════════════════════════════════════════════════
echo   CHECK THE RESULTS ABOVE
echo ════════════════════════════════════════════════════════════════
echo.
echo ✅ Should see: Real answer like "2+2 equals 4"
echo ❌ Should NOT see: "fallback mode" or "technical difficulties"
echo.
pause
