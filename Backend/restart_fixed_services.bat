@echo off
echo ========================================
echo    RESTARTING FIXED SERVICES
echo ========================================
echo.

echo 🔄 This script will help restart the backend services with the fixes applied
echo.

echo 💡 First, let's stop any existing services...
echo Press Ctrl+C in each service terminal window to stop them, then return here.
echo.
pause

echo.
echo 🚀 Starting services with the latest fixes...
echo.

echo 📝 Note: The following issues have been fixed:
echo   ✅ Created missing Financial Simulator service (langgraph_api.py)
echo   ✅ Fixed CORS configuration for frontend ports 5173 and 5174
echo   ✅ Added health endpoints to TTS and Subject Generation services
echo   ✅ Updated all services to allow proper frontend communication
echo.

echo 🏃‍♂️ Starting all services now...
call start_all_services.bat

echo.
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

echo.
echo 🏥 Running health check...
python health_check_services.py

echo.
echo 📋 If all services show as healthy:
echo   ✅ Your backend is ready!
echo   ✅ Frontend should now connect without CORS errors
echo   ✅ Financial simulation and agent features should work
echo.
echo 🔧 If any services are still unhealthy:
echo   1. Check the service terminal windows for error messages
echo   2. Ensure MongoDB and Redis are running
echo   3. Check for port conflicts
echo   4. Re-run this script
echo.
pause