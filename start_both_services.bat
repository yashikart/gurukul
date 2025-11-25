@echo off
echo Starting Gurukul Backend and Frontend Services...

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main"

echo Starting Backend Services...
start "Backend Services" cmd /k "cd Backend && python main.py"

timeout /t 5 /nobreak >nul

echo Starting Frontend Development Server...
start "Frontend Dev Server" cmd /k "cd \"new frontend\" && npm run dev"

echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window (services will continue running)
pause