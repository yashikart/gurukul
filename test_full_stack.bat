@echo off
echo ========================================
echo GURUKUL FULL STACK TEST
echo ========================================
echo.

echo [1/5] Testing Backend Health...
curl -s http://localhost:8000/health
if %errorlevel% neq 0 (
    echo ERROR: Backend not responding on port 8000
    echo Please start backend first: cd Backend ^&^& python main.py
) else (
    echo SUCCESS: Backend is running
)
echo.

echo [2/5] Testing Chat API...
curl -s http://localhost:8001/health
if %errorlevel% neq 0 (
    echo WARNING: Chat API not responding on port 8001
) else (
    echo SUCCESS: Chat API is running
)
echo.

echo [3/5] Testing Financial API...
curl -s http://localhost:8002/health
if %errorlevel% neq 0 (
    echo WARNING: Financial API not responding on port 8002
) else (
    echo SUCCESS: Financial API is running
)
echo.

echo [4/5] Testing Memory API...
curl -s http://localhost:8003/health
if %errorlevel% neq 0 (
    echo WARNING: Memory API not responding on port 8003
) else (
    echo SUCCESS: Memory API is running
)
echo.

echo [5/5] Checking Frontend Configuration...
cd "Gurukul_new-main\new frontend"
if exist ".env" (
    echo SUCCESS: Frontend .env file exists
    findstr "VITE_CLERK_PUBLISHABLE_KEY" .env >nul
    if %errorlevel% equ 0 (
        echo SUCCESS: Clerk key configured
    ) else (
        echo WARNING: Clerk key not found in .env
    )
) else (
    echo ERROR: Frontend .env file missing
)
echo.

echo ========================================
echo TEST COMPLETE
echo ========================================
echo.
echo Next Steps:
echo 1. Start Backend: cd Backend ^&^& python main.py
echo 2. Start Frontend: cd "new frontend" ^&^& npm run dev
echo 3. Open browser: http://localhost:5173
echo 4. Use Demo Mode or create Clerk test user
echo.
pause
