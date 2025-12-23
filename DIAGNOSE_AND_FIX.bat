@echo off
echo ========================================
echo GURUKUL PLATFORM - COMPREHENSIVE DIAGNOSTIC
echo ========================================
echo.

echo [STEP 1] Checking Python Installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo.

echo [STEP 2] Checking Node.js Installation...
node --version
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found!
    pause
    exit /b 1
)
echo.

echo [STEP 3] Checking Backend Dependencies...
cd Backend
pip install -r requirements.txt --quiet
echo.

echo [STEP 4] Checking Frontend Dependencies...
cd "..\new frontend"
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)
echo.

echo [STEP 5] Checking Port Availability...
cd ..\..
netstat -ano | findstr ":8000 :8001 :8002 :5173"
echo.

echo [STEP 6] Creating Diagnostic Report...
python Backend\health_check_services.py
echo.

echo ========================================
echo DIAGNOSTIC COMPLETE
echo ========================================
echo.
echo Press any key to start all services...
pause >nul

echo.
echo Starting all services...
call START_ALL.bat
