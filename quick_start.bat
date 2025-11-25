@echo off
title Gurukul Quick Start
color 0A

echo ========================================
echo    GURUKUL LEARNING PLATFORM
echo ========================================
echo.

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main"

echo [1/4] Checking Backend Dependencies...
cd Backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt >nul 2>&1

echo [2/4] Checking Frontend Dependencies...
cd "..\new frontend"
if not exist node_modules (
    echo Installing frontend dependencies...
    npm install >nul 2>&1
)

echo [3/4] Starting Backend Services...
cd ..\Backend
start "Gurukul Backend" cmd /k "call venv\Scripts\activate && python main.py"

echo [4/4] Starting Frontend Server...
cd "..\new frontend"
timeout /t 3 /nobreak >nul
start "Gurukul Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Services Started Successfully!
echo ========================================
echo Backend API: http://localhost:8000
echo Frontend App: http://localhost:3000
echo.
echo Both services are running in separate windows.
echo Close this window when done.
pause