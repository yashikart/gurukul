# Render Deployment - Quick Reference

## Backend Configuration

### Start Command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Root Directory
```
Gurukul_new-main/Backend
```

---

## Essential Environment Variables

Copy and paste these into Render Dashboard → Environment Variables:

```bash
# Database (Required)
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database

# API Keys (Required)
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
GEMINI_API_KEY=your_gemini_key

# Server (Render sets PORT automatically)
HOST=0.0.0.0
ENVIRONMENT=production
DEBUG=false
```

---

## Frontend Configuration

### Build Command
```bash
npm install && npm run build
```

### Publish Directory
```
dist
```

### Root Directory
```
Gurukul_new-main/new frontend
```

### Environment Variables
```bash
VITE_API_BASE_URL=https://gurukul-backend.onrender.com
VITE_CHAT_API_BASE_URL=https://gurukul-backend.onrender.com
```
*(Update with your actual backend URL after deployment)*

---

## Quick Steps

1. **Backend**: New + → Web Service → Use commands above
2. **Frontend**: New + → Static Site → Use commands above
3. **Update**: Frontend env vars with backend URL
4. **Done!** 🎉

