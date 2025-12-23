# CORS Error Fix - Complete Instructions

## Problem
CORS error when accessing chatbot API through ngrok:
```
Access to fetch at 'https://69f21cfd502a.ngrok-free.app/chatpost?user_id=guest-user' from origin 'http://localhost:5173' has been blocked by CORS policy
```

## Root Cause
Ngrok is currently forwarding to **port 8000** (Gateway service) instead of **port 8001** (Chatbot service).

## Solution Steps

### Step 1: Stop Current Ngrok Tunnel
1. Find and close any running ngrok windows
2. Or run: `taskkill /F /IM ngrok.exe`

### Step 2: Start Ngrok with Correct Port
```bash
ngrok http 8001 --region=in --host-header=localhost
```

**CRITICAL**: Ngrok MUST point to port **8001** (Chatbot service), NOT port 8000!

### Step 3: Update Configuration Files

#### A. Backend/.env
Update these lines with your NEW ngrok URL:
```env
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://192.168.0.77:5173,http://192.168.0.77:5174,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:3000,https://YOUR-NEW-NGROK-URL.ngrok-free.app
ALLOW_ORIGIN_REGEX=https://.*\.ngrok-free\.app
NGROK_URL=https://YOUR-NEW-NGROK-URL.ngrok-free.app
```

#### B. new frontend/.env.local
Update these lines:
```env
VITE_CHAT_API_BASE_URL=https://YOUR-NEW-NGROK-URL.ngrok-free.app
VITE_CHATBOT_API_URL=https://YOUR-NEW-NGROK-URL.ngrok-free.app
```

### Step 4: Restart Chatbot Service
```bash
cd Backend\dedicated_chatbot_service
python chatbot_api.py
```

Watch the logs for CORS configuration output:
```
============================================================
🔒 CORS CONFIGURATION
Allowed origins: ['http://localhost:5173', ..., 'https://YOUR-NGROK-URL.ngrok-free.app']
Regex pattern: https://.*\.ngrok-free\.app
Credentials: True
Methods: ALL
Headers: ALL
============================================================
```

### Step 5: Clear Ngrok Warning Page
1. Open your ngrok URL in a browser: `https://YOUR-NGROK-URL.ngrok-free.app`
2. Click "Visit Site" button
3. You should see the FastAPI docs page

### Step 6: Verify CORS Configuration

#### Test 1: Health Check
```bash
curl -i "https://YOUR-NGROK-URL.ngrok-free.app/health"
```
Expected: HTTP 200 with JSON response

#### Test 2: CORS Preflight for /chatpost
```bash
curl -i -X OPTIONS "https://YOUR-NGROK-URL.ngrok-free.app/chatpost" ^
  -H "Origin: http://localhost:5173" ^
  -H "Access-Control-Request-Method: POST" ^
  -H "Access-Control-Request-Headers: content-type"
```
Expected response headers:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
```

#### Test 3: CORS Preflight for /chatbot
```bash
curl -i -X OPTIONS "https://YOUR-NGROK-URL.ngrok-free.app/chatbot" ^
  -H "Origin: http://localhost:5173" ^
  -H "Access-Control-Request-Method: GET"
```
Expected: Same CORS headers as above

#### Test 4: Actual GET Request
```bash
curl -i "https://YOUR-NGROK-URL.ngrok-free.app/chatbot?user_id=test-user" ^
  -H "Origin: http://localhost:5173"
```
Expected: HTTP 200 with `Access-Control-Allow-Origin: http://localhost:5173` header

### Step 7: Test from Frontend
1. Start frontend: `cd "new frontend" && npm run dev`
2. Open: http://localhost:5173/chatbot
3. Send a test message
4. Check browser console - should see NO CORS errors

## Verification Checklist

- [ ] Ngrok is running on port 8001 (not 8000)
- [ ] Backend/.env has correct ngrok URL in ALLOWED_ORIGINS
- [ ] new frontend/.env.local has correct ngrok URL
- [ ] Chatbot service is running on port 8001
- [ ] Ngrok warning page has been cleared
- [ ] CORS preflight returns 200 with correct headers
- [ ] Actual requests include Access-Control-Allow-Origin header
- [ ] Frontend can send messages without CORS errors

## Common Issues

### Issue 1: Still Getting CORS Errors
**Solution**: Make sure you restarted the chatbot service AFTER updating .env

### Issue 2: Getting HTML Instead of JSON
**Solution**: Visit the ngrok URL in browser first to clear the warning page

### Issue 3: Connection Refused
**Solution**: Verify chatbot service is running on port 8001:
```bash
netstat -ano | findstr :8001
```

### Issue 4: Wrong Port in Ngrok
**Solution**: Kill ngrok and restart with correct command:
```bash
taskkill /F /IM ngrok.exe
ngrok http 8001 --region=in --host-header=localhost
```

## Quick Start Script

Use the provided batch file:
```bash
START_CHATBOT_NGROK.bat
```

This will:
1. Clean up port 8001
2. Start chatbot service
3. Start ngrok tunnel
4. Show instructions for updating URLs

## Testing Script

Use the provided batch file:
```bash
TEST_CORS_NGROK.bat
```

This will run all verification tests automatically.

## Architecture

```
Frontend (localhost:5173)
    ↓
    ↓ HTTPS
    ↓
Ngrok (https://YOUR-URL.ngrok-free.app)
    ↓
    ↓ HTTP (port 8001)
    ↓
Chatbot Service (localhost:8001)
    ↓
    ↓ MongoDB, LLM APIs
    ↓
Backend Services
```

## Important Notes

1. **Port 8001 is the chatbot service** - This is what ngrok should forward to
2. **Port 8000 is the gateway service** - This is optional and not needed for chat
3. **CORS is configured centrally** - All services use Backend/common/cors.py
4. **Ngrok URL changes** - Update both Backend/.env and frontend/.env.local when it changes
5. **Restart required** - Always restart chatbot service after changing .env

## Support

If issues persist:
1. Check chatbot service logs for CORS configuration
2. Check browser Network tab for actual request/response headers
3. Verify ngrok is forwarding to correct port (8001)
4. Ensure .env files are loaded correctly
