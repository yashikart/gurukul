# 🎯 Backend CORS & Service Configuration - COMPLETE FIX

## ✅ What Was Fixed

### 1. **LangChain Dependencies**
- ✅ Installed `langchain-classic`, `langchain-groq`, `faiss-cpu`, `statsmodels`
- ✅ Both `Backend/Base_backend/rag.py` and `Backend/api_data/rag.py` now import correctly
- ✅ No more `ModuleNotFoundError` for langchain_classic

### 2. **Unified NGROK Configuration**
- ✅ Single source of truth: `Backend/.env` → `NGROK_URL=https://YOUR_NGROK_URL.ngrok-free.app`
- ✅ All services read from this centralized variable
- ✅ Frontend reads from `new frontend/.env.local` → `VITE_CHATBOT_API_URL`

### 3. **Centralized CORS Configuration**
- ✅ `Backend/common/cors.py` now automatically appends `NGROK_URL` to allowed origins
- ✅ All services use `configure_cors(app)` helper
- ✅ CORS configuration logged on startup for debugging

### 4. **Port Conflict Resolution**
- ✅ **Port 8001**: Dedicated Chatbot Service ONLY
- ✅ **Port 8011**: API Data Service (moved from 8001)
- ✅ **Port 8000**: Base Backend (Main API)
- ✅ No more port conflicts!

### 5. **Generic OPTIONS Handlers**
- ✅ All FastAPI services now have `@app.options("/{path:path}")` handler
- ✅ CORS preflight requests return 200 with correct headers
- ✅ Middleware automatically adds CORS headers

### 6. **Service Startup Script**
- ✅ `Backend/start_all_services.bat` updated to:
  - Start chatbot service on port 8001
  - Disable API Data service by default (avoid conflicts)
  - Add warning about ngrok free plan (1 agent limit)
  - Provide clear next steps

### 7. **Frontend Configuration**
- ✅ `new frontend/.env.local` uses placeholder `https://YOUR_NGROK_URL.ngrok-free.app`
- ✅ All service URLs point to correct localhost ports
- ✅ Chatbot URLs point to ngrok (for external access)

### 8. **Verification Script**
- ✅ Created `VERIFY_FIX.bat` to test:
  - All service health endpoints
  - CORS preflight for /chatbot and /chatpost
  - Both localhost and ngrok origins

---

## 🚀 How to Use

### Step 1: Start Backend Services
```bash
cd C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\Backend
start_all_services.bat
```

**Services Started:**
- Port 8000: Base Backend (Main API)
- Port 8001: Chatbot Service
- Port 8002: Financial Simulator
- Port 8003: Memory Management
- Port 8004: Akash Service
- Port 8005: Subject Generation
- Port 8006: Wellness API
- Port 8007: TTS Service

### Step 2: Start Ngrok (Separate Terminal)
```bash
cd C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main
START_NGROK_CORRECT_PORT.bat
```

**This will:**
- Kill any existing ngrok sessions
- Start ngrok forwarding to port 8001 (chatbot service)
- Display the public URL (e.g., `https://abc123.ngrok-free.app`)

### Step 3: Update Configuration with Ngrok URL

**Copy the ngrok URL** from the terminal, then update:

**Backend/.env:**
```env
NGROK_URL=https://abc123.ngrok-free.app
```

**new frontend/.env.local:**
```env
VITE_NGROK_URL=https://abc123.ngrok-free.app
VITE_CHAT_API_BASE_URL=https://abc123.ngrok-free.app
VITE_CHATBOT_API_URL=https://abc123.ngrok-free.app
```

### Step 4: Restart Services
**Restart backend** (close all service windows and run `start_all_services.bat` again)

**Restart frontend:**
```bash
cd "C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main\new frontend"
npm run dev
```

### Step 5: Verify Everything Works
```bash
cd C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main
VERIFY_FIX.bat
```

**Expected Output:**
- ✅ All services return 200 OK
- ✅ CORS preflight tests pass
- ✅ Access-Control-Allow-Origin headers present

### Step 6: Test in Browser
1. Open `http://localhost:5173`
2. Navigate to chatbot page
3. Send a test message
4. **Expected:** Message sends successfully, AI responds, no CORS errors in console

---

## 📋 Service Port Map

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Base Backend | 8000 | http://localhost:8000 | Main API, lessons, subjects |
| Chatbot Service | 8001 | http://localhost:8001 | Chat messages, AI responses |
| Financial Simulator | 8002 | http://localhost:8002 | Financial simulations |
| Memory Management | 8003 | http://localhost:8003 | User memory, agent data |
| Akash Service | 8004 | http://localhost:8004 | Akash agent |
| Subject Generation | 8005 | http://localhost:8005 | Subject/lesson generation |
| Wellness API | 8006 | http://localhost:8006 | Wellness forecasting |
| TTS Service | 8007 | http://localhost:8007 | Text-to-speech |
| API Data (disabled) | 8011 | http://localhost:8011 | Legacy data service |

---

## 🔧 CORS Configuration

### Allowed Origins (Backend/.env)
```env
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://192.168.0.77:5173,http://192.168.0.77:5174
ALLOW_ORIGIN_REGEX=https://.*\.ngrok-free\.app
NGROK_URL=https://YOUR_NGROK_URL.ngrok-free.app
```

### How CORS Works Now
1. Service starts → reads `ALLOWED_ORIGINS` from `.env`
2. `configure_cors(app)` reads `NGROK_URL` and appends it to origins list
3. Logs final CORS configuration on startup
4. Middleware adds headers to all responses
5. Generic OPTIONS handler returns 200 for preflight requests

---

## 🐛 Troubleshooting

### Issue: "Port 8001 already in use"
**Solution:**
```bash
# Kill process using port 8001
netstat -ano | findstr :8001
taskkill /F /PID <PID>

# Or restart computer
```

### Issue: "CORS error: No 'Access-Control-Allow-Origin' header"
**Solution:**
1. Check `Backend/.env` has correct `NGROK_URL`
2. Restart backend services to pick up new config
3. Check browser console for actual origin being sent
4. Run `VERIFY_FIX.bat` to test CORS

### Issue: "Ngrok warning page instead of JSON"
**Solution:**
- Frontend already includes `ngrok-skip-browser-warning: true` header
- Visit ngrok URL in browser once to clear warning
- Or use paid ngrok plan

### Issue: "ModuleNotFoundError: No module named 'langchain_classic'"
**Solution:**
```bash
cd C:\Users\Microsoft\Documents\Gurukul_new-main
venv\Scripts\activate
pip install langchain-classic langchain-groq faiss-cpu statsmodels
```

### Issue: "Service won't start - import error"
**Solution:**
1. Check `Backend/.env` exists and has all required variables
2. Activate venv before running: `venv\Scripts\activate`
3. Check logs in service terminal window
4. Ensure `Backend/common/cors.py` exists

---

## 🧪 Testing CORS Manually

### Test 1: Health Check
```bash
curl -i http://localhost:8001/health
```
**Expected:** 200 OK with JSON response

### Test 2: CORS Preflight (localhost)
```bash
curl -i -X OPTIONS http://localhost:8001/chatbot ^
  -H "Origin: http://localhost:5173" ^
  -H "Access-Control-Request-Method: GET"
```
**Expected:** 200 OK with `Access-Control-Allow-Origin: http://localhost:5173`

### Test 3: CORS Preflight (ngrok)
```bash
curl -i -X OPTIONS http://localhost:8001/chatpost ^
  -H "Origin: https://YOUR_NGROK_URL.ngrok-free.app" ^
  -H "Access-Control-Request-Method: POST"
```
**Expected:** 200 OK with `Access-Control-Allow-Origin: https://YOUR_NGROK_URL.ngrok-free.app`

### Test 4: Actual POST Request
```bash
curl -i -X POST http://localhost:8001/chatpost ^
  -H "Content-Type: application/json" ^
  -H "Origin: http://localhost:5173" ^
  -d "{\"message\":\"test\",\"type\":\"chat_message\"}"
```
**Expected:** 200 OK with response data and CORS headers

---

## 📊 Final Configuration Summary

### Backend Services
- ✅ All services use centralized CORS via `common/cors.py`
- ✅ All services have generic OPTIONS handler
- ✅ All services read from `Backend/.env`
- ✅ No port conflicts (chatbot=8001, api_data=8011)

### CORS Origins
- ✅ `http://localhost:5173` (main frontend)
- ✅ `http://127.0.0.1:5173` (IP variant)
- ✅ `http://localhost:3000` (alternative port)
- ✅ `http://localhost:5174-5176` (dev ports)
- ✅ `http://192.168.0.77:5173-5174` (network access)
- ✅ `${NGROK_URL}` (dynamically added from .env)
- ✅ Regex: `https://.*\.ngrok-free\.app` (all ngrok domains)

### Frontend Configuration
- ✅ `VITE_API_BASE_URL=http://localhost:8000` (main API)
- ✅ `VITE_CHAT_API_BASE_URL=${NGROK_URL}` (chatbot via ngrok)
- ✅ `VITE_CHATBOT_API_URL=${NGROK_URL}` (chatbot via ngrok)
- ✅ All other services point to localhost

### Ngrok Setup
- ✅ Single tunnel on port 8001 (chatbot service)
- ✅ Region: India (`--region=in`)
- ✅ Host header preserved (`--host-header=localhost`)
- ✅ Free plan compatible (1 agent limit respected)

---

## ✨ Success Criteria

When everything is working correctly, you should see:

1. **Backend Startup:**
   ```
   🔒 CORS CONFIGURATION
   Allowed origins: ['http://localhost:5173', ..., 'https://abc123.ngrok-free.app']
   Regex pattern: https://.*\.ngrok-free\.app
   ```

2. **Ngrok Startup:**
   ```
   Forwarding  https://abc123.ngrok-free.app -> http://localhost:8001
   ```

3. **Frontend Console (No Errors):**
   ```
   ✅ Message sent successfully
   ✅ Response received from chatbot
   ```

4. **VERIFY_FIX.bat Output:**
   ```
   ✅ Base Backend is running
   ✅ Chatbot Service is running
   ✅ CORS preflight passed for /chatbot
   ✅ CORS preflight passed for /chatpost
   ```

5. **Browser Network Tab:**
   - OPTIONS request: 200 OK
   - POST /chatpost: 200 OK with CORS headers
   - GET /chatbot: 200 OK with CORS headers
   - No CORS errors in console

---

## 🎉 You're Done!

All backend services are now properly configured with:
- ✅ Unified NGROK_URL configuration
- ✅ Centralized CORS handling
- ✅ No port conflicts
- ✅ Proper OPTIONS handlers
- ✅ Clean service startup
- ✅ Comprehensive verification

**Test the chatbot at:** `http://localhost:5173/chatbot`

**Services running on:**
- Base Backend: `http://localhost:8000`
- Chatbot (via ngrok): `https://YOUR_NGROK_URL.ngrok-free.app`

**No CORS errors. Clean communication. Happy coding! 🚀**
