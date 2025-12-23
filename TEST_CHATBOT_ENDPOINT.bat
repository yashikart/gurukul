@echo off
echo ════════════════════════════════════════════════════════════════
echo   TESTING CHATBOT ENDPOINT
echo ════════════════════════════════════════════════════════════════
echo.

set NGROK_URL=https://541633dcfdba.ngrok-free.app
set TEST_USER=test-user-%RANDOM%

echo 📋 Test Configuration:
echo    Ngrok URL: %NGROK_URL%
echo    User ID: %TEST_USER%
echo    Query: "What is Pythagoras theorem?"
echo.

echo [1/2] Sending message to chatbot...
curl -X POST "%NGROK_URL%/chatpost?user_id=%TEST_USER%" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"What is Pythagoras theorem?\",\"llm\":\"grok\",\"type\":\"chat_message\"}"

echo.
echo.
echo [2/2] Waiting 3 seconds for processing...
timeout /t 3 /nobreak >nul

echo.
echo Fetching response...
curl "%NGROK_URL%/chatbot?user_id=%TEST_USER%"

echo.
echo.
echo ════════════════════════════════════════════════════════════════
echo   TEST COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
echo 📋 Check the response above:
echo    ✅ Should contain mathematical explanation of Pythagoras theorem
echo    ❌ Should NOT contain "fallback mode" or "technical difficulties"
echo.
pause
