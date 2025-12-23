@echo off
echo ========================================
echo BACKEND-FRONTEND CONNECTION TEST
echo ========================================
echo.

echo Testing all backend services health endpoints...
echo.

echo [1/8] Base Backend (8000)
curl -s http://localhost:8000/health
echo.
echo.

echo [2/8] Chatbot Service (8001)
curl -s http://localhost:8001/health
echo.
echo.

echo [3/8] Financial Simulator (8002)
curl -s http://localhost:8002/health
echo.
echo.

echo [4/8] Memory Management (8003)
curl -s http://localhost:8003/health
echo.
echo.

echo [5/8] Agent Service (8004)
curl -s http://localhost:8004/health
echo.
echo.

echo [6/8] Subject Generation (8005)
curl -s http://localhost:8005/health
echo.
echo.

echo [7/8] Wellness API (8006)
curl -s http://localhost:8006/health
echo.
echo.

echo [8/8] TTS Service (8007)
curl -s http://localhost:8007/health
echo.
echo.

echo ========================================
echo CORS TEST - Chatbot Service
echo ========================================
echo.

echo Testing CORS from frontend origin...
echo.

echo [CORS 1] OPTIONS /chatpost
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" http://localhost:8001/chatpost
echo.
echo.

echo [CORS 2] OPTIONS /chatbot
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: GET" http://localhost:8001/chatbot
echo.
echo.

echo [CORS 3] POST /chatpost (actual request)
curl -i -X POST -H "Origin: http://192.168.0.77:5175" -H "Content-Type: application/json" -d "{\"message\":\"test\",\"llm\":\"uniguru\"}" "http://localhost:8001/chatpost?user_id=test-user"
echo.
echo.

echo ========================================
echo NGROK TEST
echo ========================================
echo.

echo [NGROK 1] Health check through ngrok
curl -s https://f08743e37e03.ngrok-free.app/health
echo.
echo.

echo [NGROK 2] OPTIONS /chatpost through ngrok
curl -i -X OPTIONS -H "Origin: http://192.168.0.77:5175" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type" https://f08743e37e03.ngrok-free.app/chatpost
echo.
echo.

echo ========================================
echo TEST SUMMARY
echo ========================================
echo.
echo Expected Results:
echo - All health endpoints return {"status":"healthy"} or similar
echo - All CORS OPTIONS return HTTP 200 with CORS headers
echo - POST /chatpost returns success response
echo - Ngrok endpoints work same as localhost
echo.
echo If any service fails:
echo 1. Check if service is running (netstat -ano ^| findstr :PORT)
echo 2. Check service logs for errors
echo 3. Verify .env configuration
echo 4. Restart the service
echo.
pause
