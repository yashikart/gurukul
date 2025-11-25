@echo off
echo Stopping Gurukul Services...

echo Stopping Python processes...
taskkill /f /im python.exe >nul 2>&1

echo Stopping Node processes...
taskkill /f /im node.exe >nul 2>&1

echo Stopping any remaining processes on ports 3000 and 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo All Gurukul services stopped.
pause