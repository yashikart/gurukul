@echo off
title Gurukul Platform - Setup Verification
color 0B

echo ========================================
echo   GURUKUL PLATFORM SETUP VERIFICATION
echo ========================================
echo.

set PASS=0
set FAIL=0

echo [1/10] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
    python --version
    set /a PASS+=1
) else (
    echo [FAIL] Python not found
    set /a FAIL+=1
)
echo.

echo [2/10] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js is installed
    node --version
    set /a PASS+=1
) else (
    echo [FAIL] Node.js not found
    set /a FAIL+=1
)
echo.

echo [3/10] Checking npm installation...
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] npm is installed
    npm --version
    set /a PASS+=1
) else (
    echo [FAIL] npm not found
    set /a FAIL+=1
)
echo.

echo [4/10] Checking Backend directory...
if exist "Gurukul_new-main\Backend\main.py" (
    echo [OK] Backend directory found
    set /a PASS+=1
) else (
    echo [FAIL] Backend directory not found
    set /a FAIL+=1
)
echo.

echo [5/10] Checking Frontend directory...
if exist "Gurukul_new-main\new frontend\package.json" (
    echo [OK] Frontend directory found
    set /a PASS+=1
) else (
    echo [FAIL] Frontend directory not found
    set /a FAIL+=1
)
echo.

echo [6/10] Checking Backend .env file...
if exist "Gurukul_new-main\Backend\.env" (
    echo [OK] Backend .env exists
    set /a PASS+=1
) else (
    echo [FAIL] Backend .env not found
    set /a FAIL+=1
)
echo.

echo [7/10] Checking Frontend .env file...
if exist "Gurukul_new-main\new frontend\.env" (
    echo [OK] Frontend .env exists
    findstr "VITE_CLERK_PUBLISHABLE_KEY" "Gurukul_new-main\new frontend\.env" >nul
    if %errorlevel% equ 0 (
        echo [OK] Clerk key configured
        set /a PASS+=1
    ) else (
        echo [WARN] Clerk key not found
        set /a PASS+=1
    )
) else (
    echo [FAIL] Frontend .env not found
    set /a FAIL+=1
)
echo.

echo [8/10] Checking Frontend node_modules...
if exist "Gurukul_new-main\new frontend\node_modules" (
    echo [OK] Frontend dependencies installed
    set /a PASS+=1
) else (
    echo [FAIL] Frontend dependencies not installed
    echo Run: cd "new frontend" ^&^& npm install
    set /a FAIL+=1
)
echo.

echo [9/10] Checking Clerk package...
cd "Gurukul_new-main\new frontend"
npm list @clerk/clerk-react >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Clerk package installed
    set /a PASS+=1
) else (
    echo [FAIL] Clerk package not installed
    echo Run: npm install @clerk/clerk-react
    set /a FAIL+=1
)
cd ..\..
echo.

echo [10/10] Checking documentation files...
if exist "QUICK_START.md" (
    echo [OK] Documentation files present
    set /a PASS+=1
) else (
    echo [WARN] Some documentation missing
    set /a PASS+=1
)
echo.

echo ========================================
echo   VERIFICATION RESULTS
echo ========================================
echo.
echo Tests Passed: %PASS%/10
echo Tests Failed: %FAIL%/10
echo.

if %FAIL% equ 0 (
    echo [SUCCESS] All checks passed!
    echo.
    echo You are ready to start the platform:
    echo 1. Run: START_DEMO.bat
    echo 2. Open: http://localhost:5173
    echo 3. Click: "Continue in Demo Mode"
    echo.
) else (
    echo [WARNING] Some checks failed
    echo Please fix the issues above before starting
    echo.
)

echo ========================================
echo   QUICK REFERENCE
echo ========================================
echo.
echo Start Platform: START_DEMO.bat
echo Test Services: test_full_stack.bat
echo Quick Start: See QUICK_START.md
echo Auth Guide: See CLERK_AUTH_FIX.md
echo.
pause
