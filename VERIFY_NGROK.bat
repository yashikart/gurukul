@echo off
echo ========================================
echo Gurukul Platform - Ngrok Verification
echo ========================================
echo.

echo [1/5] Checking Service Ports...
echo.
echo Checking port 8000 (Backend):
netstat -ano | findstr :8000
echo.
echo Checking port 8001 (Chatbot):
netstat -ano | findstr :8001
echo.
echo Checking port 8007 (TTS):
netstat -ano | findstr :8007
echo.

echo [2/5] Testing Local Endpoints...
echo.
echo Testing Backend (8000):
curl -s http://localhost:8000/health
echo.
echo.
echo Testing Chatbot (8001):
curl -s http://localhost:8001/health
echo.
echo.
echo Testing TTS (8007):
curl -s http://localhost:8007/api/health
echo.
echo.

echo [3/5] Testing CORS Preflight...
echo.
echo Testing Chatbot CORS:
curl -i -X OPTIONS http://localhost:8001/chatbot -H "Origin: https://c7d82cf2656d.ngrok-free.app" -H "Access-Control-Request-Method: GET"
echo.

echo [4/5] Checking Frontend Configuration...
echo.
if exist "new frontend\.env.local" (
    echo ✅ .env.local exists
    echo Contents:
    type "new frontend\.env.local"
) else (
    echo ⚠️ .env.local not found
    echo Create it from .env.local template for ngrok testing
)
echo.

echo [5/5] Testing Ngrok Endpoint...
echo.
echo Testing ngrok URL (if tunnel is active):
curl -s https://c7d82cf2656d.ngrok-free.app/health
echo.
echo.

echo ========================================
echo Verification Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. If services not running: Run START_ALL.bat
echo 2. Check ngrok windows for forwarding URLs
echo 3. Update new frontend\.env.local with URLs
echo 4. Restart frontend: cd "new frontend" ^&^& npm run dev
echo 5. Test in browser with ad blocker disabled
echo ========================================
echo.
pause
