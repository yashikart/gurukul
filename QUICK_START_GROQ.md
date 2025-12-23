# Quick Start - Groq Integration

## 🚨 URGENT: Security Issue
Your Groq API key was shared publicly in chat. **You MUST revoke it immediately:**

1. Visit: https://console.groq.com/keys
2. Find key: `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`
3. Click "Revoke"
4. Generate new key
5. Update `Backend\.env` with new key

## ✅ What Was Fixed

1. **Groq API Endpoint**: Changed from ngrok to real Groq API
2. **Model Names**: Updated to `llama-3.1-70b-versatile`
3. **Authorization**: Added proper Bearer token headers
4. **Error Handling**: TTS errors now silent, fallback only when needed
5. **Health Check**: Shows provider configuration status

## 🚀 Quick Start (3 Steps)

### Step 1: Verify Configuration
```bash
VERIFY_GROQ_CONFIG.bat
```
All checks should show ✅

### Step 2: Restart Chatbot Service
```bash
RESTART_CHATBOT.bat
```
Wait for "Starting Dedicated Chatbot Service on port 8001..."

### Step 3: Test Chat
1. Open: http://localhost:5173/chatbot
2. Send message: "Explain quantum physics"
3. Verify: Response should NOT say "fallback mode"

## 🧪 Testing

### Test Groq API Directly
```bash
TEST_GROQ_INTEGRATION.bat
```

### Test via curl
```bash
# Send message
curl -X POST "https://85f3d18a29fe.ngrok-free.app/chatpost?user_id=test" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"Hello\",\"model\":\"grok\"}"

# Get response
curl "https://85f3d18a29fe.ngrok-free.app/chatbot?user_id=test"
```

### Check Health
```bash
curl http://localhost:8001/health
```

Expected:
```json
{
  "status": "healthy",
  "groq": true,
  "openai": true
}
```

## 🔧 Troubleshooting

### Still Getting Fallback Messages?

**Check 1: API Key**
```bash
cd Backend
type .env | findstr GROQ_API_KEY
```
Should show: `GROQ_API_KEY=gsk_...`

**Check 2: Service Running**
- Look for "Chatbot Service" window
- Should see: `✅ Groq API call successful`

**Check 3: Restart Service**
```bash
RESTART_CHATBOT.bat
```

### CORS Errors?
Already fixed! Ngrok URL is in ALLOWED_ORIGINS.

### TTS Errors?
Normal! Ad blockers block port 8007. Doesn't affect chat.

## 📁 Files Modified

- `Backend/.env` - Groq configuration
- `Backend/Base_backend/llm_service.py` - Real Groq API
- `Backend/dedicated_chatbot_service/chatbot_api.py` - Better routing
- `new frontend/src/services/*.js` - Silent TTS errors

## 🎯 Model Mapping

| Frontend | Backend Provider | Actual Model |
|----------|-----------------|--------------|
| `uniguru` | Groq | llama-3.1-70b-versatile |
| `grok` | Groq | llama-3.1-70b-versatile |
| `llama` | Groq | llama-3.1-70b-versatile |
| `chatgpt` | OpenAI | gpt-3.5-turbo |

## 📞 Support

If chat still shows "fallback mode":
1. Check chatbot service terminal for errors
2. Run `TEST_GROQ_INTEGRATION.bat`
3. Verify API key is valid at https://console.groq.com/keys
4. Restart chatbot service

---

**Status**: ✅ Fixed and ready to use
**Action Required**: Revoke exposed API key and restart service
