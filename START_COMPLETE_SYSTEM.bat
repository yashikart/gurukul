@echo off
echo ════════════════════════════════════════════════════════════════
echo   GURUKUL COMPLETE SYSTEM STARTUP
echo ════════════════════════════════════════════════════════════════
echo.
echo This will start:
echo   1. All backend services (ports 8000-8007)
echo   2. Chatbot service on port 8001
echo   3. Frontend dev server
echo.
echo ⚠️  Make sure ngrok is already running on port 8001
echo    If not, run START_NGROK_CORRECT_PORT.bat first
echo.
pause

REM Start backend services
echo.
echo [1/2] Starting backend services...
cd /d C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\Backend
start "Backend Services" cmd /k start_all_services.bat

REM Wait for services to start
echo.
echo ⏳ Waiting 15 seconds for backend services to initialize...
timeout /t 15 /nobreak >nul

REM Start frontend
echo.
echo [2/2] Starting frontend dev server...
cd /d "C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\new frontend"
start "Frontend Dev Server" cmd /k npm run dev

echo.
echo ════════════════════════════════════════════════════════════════
echo   SYSTEM STARTUP COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
echo ✅ Backend services starting on ports 8000-8007
echo ✅ Frontend dev server starting on port 5173
echo.
echo 🌐 Access the application:
echo    http://localhost:5173
echo    http://192.168.0.77:5174
echo.
echo 📋 Service Health Checks:
echo    Backend:  http://localhost:8000/health
echo    Chatbot:  http://localhost:8001/health
echo    Ngrok:    https://541633dcfdba.ngrok-free.app/health
echo.
echo 🔧 To test Groq integration:
echo    Run TEST_GROQ_INTEGRATION.bat
echo.
pause
