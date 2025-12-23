# Quick Fix Guide - Get Real AI Responses

## Problem
Chatbot returns "fallback mode" or "technical difficulties" instead of real AI responses.

## Solution (3 Steps)

### Step 1: Verify Groq API Key
```bash
cd C:\Users\Microsoft\Documents\Gurukul_new-main\Gurukul_new-main
TEST_GROQ_DIRECT.bat
```

**Expected**:
```
Groq API Key: SET (gsk_...)
HTTP Status: 200
Response: Hello! How can I assist you today?
```

**If you see "NOT SET" or HTTP 401**:
1. Open `Backend\.env`
2. Add or update: `GROQ_API_KEY=your_key_here`
3. Get key from: https://console.groq.com/keys

### Step 2: Restart Chatbot Service
```bash
cd Backend\dedicated_chatbot_service
RESTART_CHATBOT_SERVICE.bat
```

**Watch for**:
```
🔧 LLM Service Configuration:
   Groq API Key: ✅ SET
   Groq Model: llama-3.1-70b-versatile
```

### Step 3: Test in Browser
1. Open: http://localhost:5173/chatbot
2. Type: "What is Pythagoras theorem?"
3. Send message

**Expected**: Real mathematical explanation
**NOT Expected**: "fallback mode" or "technical difficulties"

## Debugging

### Check Service Logs
Look at the "Chatbot Service" terminal window.

**When you send a message, you should see**:
```
============================================================
💬 CHAT REQUEST
   User: guest-user
   Model: grok
   Query: What is Pythagoras theorem?
============================================================
🔄 Calling Groq API: https://api.groq.com/openai/v1/chat/completions
   Model: llama-3.1-70b-versatile
📡 Groq API Response: HTTP 200
✅ Groq Success: The Pythagorean theorem states...
✅ Using Groq response
============================================================
```

### If You See Errors

**"Groq API Key: ❌ NOT SET"**
→ Add `GROQ_API_KEY` to `Backend\.env` and restart

**"HTTP 401: Unauthorized"**
→ API key is invalid, get new one from https://console.groq.com/keys

**"HTTP 429: Rate limit"**
→ Wait a minute and try again

**"All providers failed - using fallback"**
→ Check internet connection and API key

## Quick Test Commands

### Test Groq API
```bash
TEST_GROQ_DIRECT.bat
```

### Test Chatbot Endpoint
```bash
TEST_CHATBOT_ENDPOINT.bat
```

### Check Health
```bash
curl http://localhost:8001/health
```

## Configuration File

**Location**: `Backend\.env`

**Required**:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=llama-3.1-70b-versatile
```

## Success Checklist

- [ ] `TEST_GROQ_DIRECT.bat` shows HTTP 200
- [ ] Service logs show "Groq API Key: ✅ SET"
- [ ] Health check returns `"groq": true`
- [ ] Browser chat returns real AI responses
- [ ] No "fallback mode" messages

## Still Not Working?

1. **Check .env file exists**:
   ```bash
   dir Backend\.env
   ```

2. **Check API key is set**:
   ```bash
   type Backend\.env | findstr GROQ_API_KEY
   ```

3. **Restart everything**:
   - Close all terminal windows
   - Run `Backend\start_all_services.bat`
   - Run `Backend\dedicated_chatbot_service\RESTART_CHATBOT_SERVICE.bat`

4. **Check logs**:
   - Look at "Chatbot Service" window
   - Send a test message
   - Watch for "Groq Success" or error messages

---

**Need Help?**
- Check `GROQ_FIX_COMPLETE.md` for detailed documentation
- Review service logs in the terminal window
- Verify API key at https://console.groq.com/keys
