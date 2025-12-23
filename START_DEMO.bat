@echo off
title Gurukul Platform - Demo Launcher
color 0A

echo ========================================
echo   GURUKUL LEARNING PLATFORM
echo   Demo Environment Launcher
echo ========================================
echo.

echo Checking prerequisites...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python found

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 20+ from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found

echo.
echo ========================================
echo Starting Services...
echo ========================================
echo.

REM Start Backend
echo [1/2] Starting Backend Server...
cd "Gurukul_new-main\Backend"
start "Gurukul Backend" cmd /k "python main.py"
timeout /t 5 /nobreak >nul
echo Backend started on http://localhost:8000
echo.

REM Start Frontend
echo [2/2] Starting Frontend Server...
cd "..\new frontend"
start "Gurukul Frontend" cmd /k "npm run dev"
timeout /t 5 /nobreak >nul
echo Frontend starting on http://localhost:5173
echo.

echo ========================================
echo   SERVICES LAUNCHED
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Demo Login Options:
echo 1. Click "Continue in Demo Mode" (No auth required)
echo 2. Create account via Clerk (Email verification required)
echo 3. Sign in with Google OAuth
echo.
echo Press any key to open browser...
pause >nul

start http://localhost:5173

echo.
echo Services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause
