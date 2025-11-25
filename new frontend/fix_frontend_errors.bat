@echo off
echo Fixing Frontend Errors...

cd "c:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\new frontend"

echo 1. Clearing node_modules and package-lock.json...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

echo 2. Installing dependencies...
npm install

echo 3. Checking for peer dependency issues...
npm ls --depth=0

echo 4. Fixing React Router compatibility...
npm install react-router-dom@^6.26.2

echo 5. Updating Clerk dependencies...
npm install @clerk/clerk-react@latest

echo 6. Installing missing dependencies...
npm install @types/uuid

echo 7. Running build to check for errors...
npm run build

echo Frontend error fixes completed!
pause