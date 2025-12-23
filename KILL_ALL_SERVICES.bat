@echo off
echo ========================================
echo KILLING ALL GURUKUL SERVICES
echo ========================================
echo.

REM Kill processes on common ports
echo [1/4] Killing processes on ports 8000, 8001, 8007...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 :8001 :8007" ^| findstr LISTENING') do (
    echo Killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM Kill Python processes
echo [2/4] Killing Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM Kill Node processes
echo [3/4] Killing Node processes...
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM Kill ngrok processes
echo [4/4] Killing ngrok processes...
taskkill /F /IM ngrok.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo.
echo ========================================
echo ALL SERVICES KILLED
echo ========================================
echo.
echo Ports 8000, 8001, 8007 should now be free.
echo Python, Node, and ngrok processes terminated.
echo.
pause

