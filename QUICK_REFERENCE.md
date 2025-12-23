# 🚀 Gurukul Platform - Quick Reference Card

## ⚡ Quick Start

```bash
# Start everything (services + ngrok)
START_ALL.bat

# Verify setup
VERIFY_NGROK.bat
```

## 🌐 Service URLs

| Service | Local | Ngrok |
|---------|-------|-------|
| Frontend | http://localhost:5173 | https://YOUR-URL.ngrok-free.app |
| Backend | http://localhost:8000 | https://YOUR-URL.ngrok-free.app |
| Chatbot | http://localhost:8001 | Via Backend |
| TTS | http://localhost:8007 | Via Backend |

## 🔧 Common Commands

### Check Services
```bash
netstat -ano | findstr ":8000 :8001 :8007 :5173"
```

### Test Endpoints
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8007/api/health
```

### Kill Process
```bash
netstat -ano | findstr :8001
taskkill /F /PID <PID>
```

### Restart Service
```bash
cd Backend\dedicated_chatbot_service
python chatbot_api.py
```

## 🐛 Quick Fixes

### CORS Error
```bash
# Restart services
START_ALL.bat
```

### ERR_BLOCKED_BY_CLIENT
```
1. Disable ad blocker
2. Test in Incognito mode
```

### Ngrok Not Working
```bash
# Check if tunnel is active
# Look for ngrok terminal windows
# Update .env.local with new URL
cd "new frontend"
npm run dev
```

### Clerk Not Signed In
```
1. Use HTTPS ngrok URL (not localhost)
2. Add ngrok URL to Clerk dashboard
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `START_ALL.bat` | Start all services + ngrok |
| `VERIFY_NGROK.bat` | Verify setup |
| `new frontend/.env` | Local dev config |
| `new frontend/.env.local` | Ngrok testing config |
| `Backend/main.py` | Backend gateway |
| `Backend/dedicated_chatbot_service/chatbot_api.py` | Chatbot service |

## ✅ Pre-Flight Checklist

Before testing:
- [ ] Run `START_ALL.bat`
- [ ] Check ngrok windows for URLs
- [ ] Update `.env.local` if needed
- [ ] Disable ad blocker
- [ ] Open http://localhost:5173

## 🔍 Troubleshooting

| Error | Solution |
|-------|----------|
| CORS preflight failure | Restart services |
| ERR_BLOCKED_BY_CLIENT | Disable ad blocker |
| Connection refused | Check service is running |
| Ngrok 502 | Restart backend service |
| Clerk error | Use HTTPS ngrok URL |
| Supabase DNS | Check system time, sync clock |

## 📊 Port Reference

| Port | Service |
|------|---------|
| 5173 | Frontend (Vite) |
| 8000 | Backend Gateway |
| 8001 | Chatbot Service |
| 8002 | Financial Simulator (mounted) |
| 8003 | Memory Management (mounted) |
| 8007 | TTS Service |

## 🔐 Environment Variables

### Local Testing (.env)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_CHAT_API_BASE_URL=http://localhost:8001
```

### Remote Testing (.env.local)
```env
VITE_API_BASE_URL=https://YOUR-URL.ngrok-free.app
VITE_CHAT_API_BASE_URL=https://YOUR-URL.ngrok-free.app/chat
```

## 📞 Support

- Full Guide: `NGROK_SETUP_GUIDE.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`
- Health Check: `python Backend\comprehensive_health_check.py`

---

**Quick Tip:** Always disable ad blocker when testing localhost!
