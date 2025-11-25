@echo off
echo Starting Gurukul Frontend Development Server...

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\new frontend"

echo Checking if dependencies are installed...
if not exist node_modules (
    echo Installing dependencies...
    npm install
)

echo Starting development server...
npm run dev

pause