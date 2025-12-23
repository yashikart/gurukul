@echo off
echo Starting All Gurukul Services...
echo.

echo Starting Backend...
start "Backend" cmd /k "cd Backend && python main.py"

timeout /t 5 /nobreak >nul

echo Starting Frontend...
start "Frontend" cmd /k "cd \"new frontend\" && npm run dev"

timeout /t 3 /nobreak >nul

echo Starting AnimateDiff API Server (Port 8501)...
if exist "TTV\start_api_server.bat" (
    start "AnimateDiff-API" cmd /k "cd /d %~dp0TTV && start_api_server.bat"
    echo ✅ AnimateDiff API Server starting...
) else (
    echo ⚠️  TTV folder not found. AnimateDiff will not start.
    echo    Expected location: TTV\start_api_server.bat
)
timeout /t 5 /nobreak >nul
echo.

echo.
echo Services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo AnimateDiff API: http://localhost:8501
echo.
echo NOTE: AnimateDiff will download models on first startup (may take 10-15 minutes)
echo       Check the AnimateDiff-API window for progress
echo.
pause
