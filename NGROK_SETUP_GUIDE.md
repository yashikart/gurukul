# 🌐 Ngrok Setup Guide - Gurukul Platform

Complete guide for setting up ngrok tunnels for local dev + public testing.

## 📋 Prerequisites

- ✅ Ngrok installed and authtoken configured
- ✅ All backend services running (8000, 8001, 8007)
- ✅ Frontend running (5173)

## 🚀 Quick Start

### Option 1: Automated Start (Recommended)
```bash
START_ALL.bat
```
This will:
- Start Backend Gateway (8000)
- Start Chatbot Service (8001)
- Start TTS Service (8007)
- Start Frontend (5173)
- Start Ngrok tunnels automatically

### Option 2: Manual Start

**Step 1: Start Services**
```bash
# Terminal 1 - Backend
cd Backend
python main.py

# Terminal 2 - Chatbot
cd Backend\dedicated_chatbot_service
python chatbot_api.py

# Terminal 3 - TTS
cd Backend\tts_service
python tts.py

# Terminal 4 - Frontend
cd "new frontend"
npm run dev
```

**Step 2: Start Ngrok Tunnels**
```bash
# Terminal 5 - Ngrok for Backend
ngrok http 8000 --region=in --host-header=localhost

# Terminal 6 - Ngrok for Chatbot
ngrok http 8001 --region=in --host-header=localhost
```

## 🔧 Configuration

### 1. Get Ngrok URLs

After starting ngrok, you'll see output like:
```
Forwarding  https://c7d82cf2656d.ngrok-free.app -> http://localhost:8000
```

Copy these URLs!

### 2. Update Frontend Environment

**For Local Testing:**
Use `new frontend\.env` (already configured for localhost)

**For Remote Testing via Ngrok:**
Update `new frontend\.env.local`:

```env
# Update with your actual ngrok URLs
VITE_API_BASE_URL=https://YOUR-NGROK-URL.ngrok-free.app
VITE_CHAT_API_BASE_URL=https://YOUR-NGROK-URL.ngrok-free.app/chat
VITE_FINANCIAL_API_BASE_URL=https://YOUR-NGROK-URL.ngrok-free.app/api/v1/financial
```

### 3. Restart Frontend
```bash
cd "new frontend"
npm run dev
```

## ✅ Verification Steps

### 1. Check Services Running
```bash
netstat -ano | findstr :8000
netstat -ano | findstr :8001
netstat -ano | findstr :8007
```

### 2. Test Local Endpoints
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8007/api/health
```

### 3. Test CORS Preflight
```bash
curl -i -X OPTIONS http://localhost:8001/chatbot ^
  -H "Origin: https://c7d82cf2656d.ngrok-free.app" ^
  -H "Access-Control-Request-Method: GET"
```

Expected response:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://c7d82cf2656d.ngrok-free.app
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
```

### 4. Test Ngrok Forwarding
```bash
curl https://YOUR-NGROK-URL.ngrok-free.app/health
```

### 5. Browser Test
1. Open: `https://YOUR-NGROK-URL.ngrok-free.app`
2. Open DevTools → Network tab
3. Send a chat message
4. Verify:
   - ✅ No CORS errors
   - ✅ Status 200 responses
   - ✅ No ERR_BLOCKED_BY_CLIENT

## 🐛 Troubleshooting

### Issue 1: ERR_BLOCKED_BY_CLIENT

**Cause:** Browser ad blocker or privacy extension

**Solution:**
1. Open Incognito mode with extensions disabled
2. OR disable ad blocker for:
   - `localhost`
   - `127.0.0.1`
   - `192.168.0.77`
   - `*.ngrok-free.app`

### Issue 2: CORS Preflight Failures

**Cause:** Origin not whitelisted in backend

**Solution:**
Backend CORS is already configured for:
- `http://localhost:5173-5176`
- `http://127.0.0.1:5173-5174`
- `http://192.168.0.77:5173-5174`
- `https://c7d82cf2656d.ngrok-free.app`

If using a different ngrok URL, update:
- `Backend/main.py` (line 40-50)
- `Backend/dedicated_chatbot_service/chatbot_api.py` (line 140-150)
- `Backend/tts_service/tts.py` (line 30-40)

### Issue 3: Ngrok "Not Found" or 502

**Cause:** Backend service not running or wrong port

**Solution:**
```bash
# Check if service is running
netstat -ano | findstr :8000

# Restart service
cd Backend
python main.py
```

### Issue 4: Clerk "Not signed in" Error

**Cause:** Clerk requires HTTPS for secure cookies

**Solution:**
1. Use ngrok HTTPS URL (not HTTP localhost)
2. Add ngrok URL to Clerk dashboard:
   - Go to: https://dashboard.clerk.com
   - Settings → Allowed Origins
   - Add: `https://YOUR-NGROK-URL.ngrok-free.app`

### Issue 5: Supabase DNS Errors

**Cause:** Network DNS issues or system time incorrect

**Solution:**
```bash
# Test DNS
nslookup qjriwcvexqvqvtegeokv.supabase.co

# Test connection
curl -v https://qjriwcvexqvqvtegeokv.supabase.co/rest/v1

# Fix system time
# Windows: Settings → Time & Language → Sync now
```

### Issue 6: Slow LLM Responses

**Cause:** Ngrok endpoint running Ollama locally

**Current Status:**
- Timeout increased to 180 seconds
- Using ngrok: `https://c7d82cf2656d.ngrok-free.app`
- Expected response time: 7-10 seconds

**Solution:**
- Wait for response (timeout is 180s)
- OR switch to Groq API (faster, cloud-based)

## 📊 Service Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Vite)                                │
│  Port: 5173                                     │
│  Ngrok: https://YOUR-URL.ngrok-free.app        │
└────────────────┬────────────────────────────────┘
                 │
                 ├──────────────────────────────────┐
                 │                                  │
┌────────────────▼──────────┐    ┌─────────────────▼──────────┐
│  Backend Gateway          │    │  Chatbot Service           │
│  Port: 8000               │    │  Port: 8001                │
│  Ngrok: Optional          │    │  Ngrok: Optional           │
│                           │    │                            │
│  Mounts:                  │    │  Features:                 │
│  - /api/v1/base          │    │  - Chat messages           │
│  - /api/v1/memory        │    │  - LLM integration         │
│  - /api/v1/financial     │    │  - PDF/Image processing    │
│  - /api/v1/subjects      │    │  - TTS streaming           │
│  - /api/v1/akash         │    │                            │
│  - /api/v1/tts           │    │                            │
└───────────────────────────┘    └────────────────────────────┘
                                              │
                                 ┌────────────▼────────────┐
                                 │  TTS Service            │
                                 │  Port: 8007             │
                                 │  Features:              │
                                 │  - Text-to-Speech       │
                                 │  - Audio generation     │
                                 └─────────────────────────┘
```

## 🔒 Security Notes

### CORS Configuration
All services are configured with CORS to allow:
- Local development (localhost, 127.0.0.1)
- LAN access (192.168.0.77)
- Ngrok public access (c7d82cf2656d.ngrok-free.app)

### Environment Variables
- ✅ API keys stored in `.env` files
- ✅ `.env` files in `.gitignore`
- ⚠️ Never commit secrets to git
- ⚠️ Rotate ngrok URLs regularly

### Clerk Authentication
- Requires HTTPS for secure cookies
- Use ngrok HTTPS URL for remote testing
- Add ngrok URL to Clerk dashboard allowed origins

## 📝 Developer Notes

### Port Allocation
- 8000: Backend Gateway (main entry point)
- 8001: Chatbot Service (dedicated)
- 8002: Financial Simulator (mounted in gateway)
- 8003: Memory Management (mounted in gateway)
- 8004: Akash Service (mounted in gateway)
- 8005: Subject Generation (mounted in gateway)
- 8006: Wellness API (optional)
- 8007: TTS Service (standalone)
- 5173: Frontend (Vite dev server)

### Ngrok Best Practices
1. Use `--host-header=localhost` to preserve Host header
2. Use `--region=in` for India region (lower latency)
3. Keep ngrok windows open while testing
4. Update frontend .env.local with new URLs
5. Restart frontend after changing URLs

### Testing Checklist
- [ ] All services running (8000, 8001, 8007)
- [ ] Ngrok tunnels active
- [ ] Frontend .env.local updated
- [ ] Frontend restarted
- [ ] Browser ad blocker disabled
- [ ] CORS preflight test passed
- [ ] Chat message test successful
- [ ] No console errors

## 🆘 Support

### Quick Diagnostics
```bash
# Run comprehensive health check
python Backend\comprehensive_health_check.py

# Check all ports
netstat -ano | findstr ":8000 :8001 :8007 :5173"

# Test all endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8007/api/health
```

### Common Commands
```bash
# Kill process on port
netstat -ano | findstr :8001
taskkill /F /PID <PID>

# Restart service
cd Backend\dedicated_chatbot_service
python chatbot_api.py

# Clear npm cache
cd "new frontend"
npm cache clean --force
npm install
```

## ✨ Status

- ✅ Backend Gateway: Configured
- ✅ Chatbot Service: Configured
- ✅ TTS Service: Configured
- ✅ CORS: Configured for ngrok
- ✅ Frontend: Ready for ngrok
- ✅ START_ALL.bat: Updated with ngrok
- ✅ GlassButton: Fixed (forwardRef)

---

**Last Updated:** 2024-11-25
**Ngrok URL:** https://c7d82cf2656d.ngrok-free.app
**Status:** ✅ Ready for Testing
