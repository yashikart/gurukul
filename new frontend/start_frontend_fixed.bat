@echo off
echo Starting Gurukul Frontend with Authentication Fixes...
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
    echo.
)

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy ".env.example" ".env"
    echo.
    echo Please update the .env file with your actual API keys and configuration.
    echo.
)

REM Start the development server
echo Starting development server...
echo Frontend will be available at: http://localhost:5173
echo.
echo Authentication Status:
echo - Clerk authentication is configured with fallback
echo - If Clerk keys are missing, development mode will be used
echo - Check the debug panel in bottom-left corner for auth status
echo.

npm run dev

pause