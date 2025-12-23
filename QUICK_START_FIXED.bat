@echo off
echo ========================================
echo   GURUKUL QUICK START (FIXED VERSION)
echo ========================================
echo.
echo This script will guide you through starting
echo all services with proper CORS configuration.
echo.
echo ========================================
echo   STEP 1: Start Backend Services
echo ========================================
echo.
echo Opening backend services in new window...
start "Gurukul Backend Services" cmd /k "cd /d %~dp0Backend && start_all_services.bat"
echo.
echo ✅ Backend services starting...
echo    Wait 20-30 seconds for all services to initialize
echo.
timeout /t 5 /nobreak >nul
echo.
echo ========================================
echo   STEP 2: Start Ngrok Tunnel
echo ========================================
echo.
echo Opening ngrok in new window...
start "Ngrok Tunnel (Port 8001)" cmd /k "cd /d %~dp0 && START_NGROK_CORRECT_PORT.bat"
echo.
echo ⚠️  IMPORTANT: Copy the ngrok URL from the ngrok window!
echo    It will look like: https://abc123.ngrok-free.app
echo.
echo Press any key after you've copied the ngrok URL...
pause >nul
echo.
echo ========================================
echo   STEP 3: Update Configuration
echo ========================================
echo.
set /p NGROK_URL="Paste your ngrok URL here: "
echo.
echo Updating Backend\.env...
powershell -Command "(Get-Content Backend\.env) -replace 'NGROK_URL=.*', 'NGROK_URL=%NGROK_URL%' | Set-Content Backend\.env"
echo ✅ Backend\.env updated
echo.
echo Updating new frontend\.env.local...
powershell -Command "(Get-Content 'new frontend\.env.local') -replace 'VITE_NGROK_URL=.*', 'VITE_NGROK_URL=%NGROK_URL%' | Set-Content 'new frontend\.env.local'"
powershell -Command "(Get-Content 'new frontend\.env.local') -replace 'VITE_CHAT_API_BASE_URL=.*', 'VITE_CHAT_API_BASE_URL=%NGROK_URL%' | Set-Content 'new frontend\.env.local'"
powershell -Command "(Get-Content 'new frontend\.env.local') -replace 'VITE_CHATBOT_API_URL=.*', 'VITE_CHATBOT_API_URL=%NGROK_URL%' | Set-Content 'new frontend\.env.local'"
echo ✅ Frontend .env.local updated
echo.
echo ========================================
echo   STEP 4: Restart Backend (Pick up new URL)
echo ========================================
echo.
echo Please close the "Gurukul Backend Services" window
echo and press any key to restart it...
pause >nul
echo.
echo Restarting backend services...
start "Gurukul Backend Services (Restarted)" cmd /k "cd /d %~dp0Backend && start_all_services.bat"
echo ✅ Backend restarted with new ngrok URL
echo.
timeout /t 5 /nobreak >nul
echo.
echo ========================================
echo   STEP 5: Start Frontend
echo ========================================
echo.
echo Starting frontend dev server...
start "Gurukul Frontend" cmd /k "cd /d %~dp0new frontend && npm run dev"
echo ✅ Frontend starting...
echo.
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo   STEP 6: Verify Setup
echo ========================================
echo.
echo Running verification tests...
timeout /t 10 /nobreak >nul
call VERIFY_FIX.bat
echo.
echo ========================================
echo   🎉 SETUP COMPLETE!
echo ========================================
echo.
echo Your Gurukul platform is now running:
echo.
echo 🌐 Frontend:  http://localhost:5173
echo 🔧 Backend:   http://localhost:8000
echo 💬 Chatbot:   %NGROK_URL%
echo.
echo Open your browser and navigate to:
echo    http://localhost:5173
echo.
echo Test the chatbot to verify CORS is working!
echo.
echo ========================================
echo   Service Windows Open:
echo ========================================
echo.
echo 1. Gurukul Backend Services (Restarted)
echo 2. Ngrok Tunnel (Port 8001)
echo 3. Gurukul Frontend
echo.
echo To stop all services, close these windows.
echo.
pause
