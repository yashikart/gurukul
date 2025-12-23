@echo off
setlocal enabledelayedexpansion

echo ========================================
echo GURUKUL CORS + NGROK VERIFICATION
echo ========================================
echo.

REM Read ngrok URL from .env
set "NGROK_URL="
for /f "tokens=1,* delims==" %%a in ('type "Backend\.env" ^| findstr "^NGROK_URL="') do (
    set "NGROK_URL=%%b"
)

if "%NGROK_URL%"=="" (
    echo ERROR: NGROK_URL not found in Backend\.env
    echo Please update Backend\.env with your current ngrok URL
    pause
    exit /b 1
)

echo Using ngrok URL: %NGROK_URL%
echo.

echo [1/5] Testing local chatbot service...
curl -s -o nul -w "HTTP %%{http_code}" http://localhost:8001/health
echo.
echo.

echo [2/5] Testing ngrok health endpoint...
curl -s -o nul -w "HTTP %%{http_code}" %NGROK_URL%/health
echo.
echo.

echo [3/5] Testing CORS preflight for /chatpost...
curl -i -X OPTIONS "%NGROK_URL%/chatpost" ^
  -H "Origin: http://localhost:5173" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: content-type"
echo.

echo [4/5] Testing CORS preflight for /chatbot...
curl -i -X OPTIONS "%NGROK_URL%/chatbot" ^
  -H "Origin: http://localhost:5173" ^
  -H "Access-Control-Request-Method: GET"
echo.

echo [5/5] Testing actual GET request with Origin header...
curl -i "%NGROK_URL%/chatbot?user_id=test-user" ^
  -H "Origin: http://localhost:5173"
echo.

echo.
echo ========================================
echo VERIFICATION COMPLETE
echo ========================================
echo.
echo Check the responses above for:
echo   - HTTP 200 status codes
echo   - Access-Control-Allow-Origin: http://localhost:5173
echo   - Access-Control-Allow-Methods including POST/GET
echo.
echo If you see HTML instead of JSON, visit %NGROK_URL% in browser first
echo to clear the ngrok warning page.
echo.
pause
