@echo off
echo ========================================
echo CORS PREFLIGHT TEST SCRIPT
echo ========================================
echo.

echo Testing localhost:8001 endpoints...
echo.

echo [1/4] OPTIONS /chatpost (localhost)
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" http://localhost:8001/chatpost
echo.
echo.

echo [2/4] OPTIONS /chatbot (localhost)
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: GET" http://localhost:8001/chatbot
echo.
echo.

echo [3/4] OPTIONS /chatpost (ngrok)
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" https://541633dcfdba.ngrok-free.app/chatpost
echo.
echo.

echo [4/4] OPTIONS /chatbot (ngrok)
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: GET" https://541633dcfdba.ngrok-free.app/chatbot
echo.
echo.

echo ========================================
echo TEST COMPLETE
echo ========================================
echo.
echo Expected: All requests should return HTTP 200
echo Expected: All responses should include CORS headers
echo.
pause
