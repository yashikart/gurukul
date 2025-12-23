# Render Deployment Configuration

## Backend Web Service Configuration

### Basic Settings
- **Name**: `gurukul-backend`
- **Environment**: `Python 3`
- **Region**: `Oregon` (or closest to your users)
- **Branch**: `main`
- **Root Directory**: `Gurukul_new-main/Backend` (or just `Backend` if root is already set)

### Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Start Command
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Alternative Start Command** (if uvicorn is not in PATH):
```bash
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Or using the main.py directly**:
```bash
python main.py
```
(Note: This will use `BASE_BACKEND_PORT` env var or default to 8000, but Render sets `$PORT` automatically)

---

## Environment Variables

Add these in Render Dashboard → Your Service → Environment:

### Required Environment Variables

```bash
# Server Configuration (Render sets PORT automatically)
PORT=10000
HOST=0.0.0.0

# Database
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
# OR
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

# API Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Environment
ENVIRONMENT=production
DEBUG=false
PYTHON_VERSION=3.11.0
```

### Optional Environment Variables

```bash
# Base Backend Port (if not using $PORT)
BASE_BACKEND_PORT=8000

# API Data Service Port
API_DATA_PORT=8011

# Ngrok URL (if using ngrok for local development)
NGROK_URL=https://your-ngrok-url.ngrok.io

# Arabic Model Checkpoint (if using local Arabic translation model)
LOCAL_MODEL_CHECKPOINT_PATH=/opt/render/checkpoints/checkpoint-100000
CHECKPOINT_DOWNLOAD_URL=https://your-checkpoint-url.com/checkpoint.zip
CHECKPOINT_S3_BUCKET=your-s3-bucket-name
CHECKPOINT_S3_PREFIX=checkpoint-100000
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Redis (if using Redis cache)
REDIS_URL=redis://your-redis-url:6379

# Other Services
ORCHESTRATION_ENABLED=true
MEMORY_API_ENABLED=true
```

---

## Frontend Static Site Configuration

### Basic Settings
- **Name**: `gurukul-frontend`
- **Environment**: `Static Site`
- **Region**: `Oregon`
- **Branch**: `main`
- **Root Directory**: `Gurukul_new-main/new frontend`

### Build Command
```bash
npm install && npm run build
```

### Publish Directory
```
dist
```
(Or `build` if your Vite config uses that)

### Environment Variables (for Frontend)

```bash
# Backend API URLs (update after backend deploys)
VITE_API_BASE_URL=https://gurukul-backend.onrender.com
VITE_CHAT_API_BASE_URL=https://gurukul-backend.onrender.com

# Other frontend variables
NODE_VERSION=18.0.0
```

---

## Step-by-Step Deployment

### 1. Deploy Backend

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository: `yashikart/gurukul`
4. Configure:
   - **Name**: `gurukul-backend`
   - **Root Directory**: `Gurukul_new-main/Backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (for testing) or Starter ($7/month)

5. Add Environment Variables (see list above)
6. Click **"Create Web Service"**
7. Wait for deployment to complete
8. Copy your backend URL (e.g., `https://gurukul-backend.onrender.com`)

### 2. Deploy Frontend

1. Click **"New +"** → **"Static Site"**
2. Connect GitHub repository: `yashikart/gurukul`
3. Configure:
   - **Name**: `gurukul-frontend`
   - **Root Directory**: `Gurukul_new-main/new frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. Add Environment Variables:
   - `VITE_API_BASE_URL` = Your backend URL from step 1
   - `VITE_CHAT_API_BASE_URL` = Your backend URL from step 1

5. Click **"Create Static Site"**

### 3. Update CORS Settings

After deployment, make sure your backend allows requests from your frontend domain. The backend should already have CORS configured, but verify it includes:
- `https://gurukul-frontend.onrender.com`
- Your frontend URL

---

## Quick Copy-Paste Commands

### Start Command (Backend)
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Build Command (Backend)
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Build Command (Frontend)
```bash
npm install && npm run build
```

---

## Troubleshooting

### Backend won't start
- Check that `requirements.txt` exists in `Backend/` directory
- Verify all environment variables are set
- Check Render logs for specific error messages
- Ensure `main.py` exists in the Backend directory

### Port issues
- Render automatically sets `$PORT` - use it in your start command
- Don't hardcode port numbers
- Use `0.0.0.0` as host (not `127.0.0.1`)

### Import errors
- Make sure all dependencies are in `requirements.txt`
- Check that Python path includes the Backend directory
- Verify all service modules are accessible

### Database connection fails
- Verify MongoDB connection string is correct
- Check MongoDB Atlas IP whitelist (allow all IPs: `0.0.0.0/0`)
- Ensure database user has proper permissions

---

## Health Check

Your backend has a health check endpoint at:
```
https://your-backend-url.onrender.com/health
```

Render will automatically use this for health monitoring.

---

## Notes

- Render sets `$PORT` automatically - always use it in your start command
- Free tier services spin down after 15 minutes of inactivity
- Starter plan ($7/month) keeps services always running
- Environment variables are case-sensitive
- Update frontend API URLs after backend deployment

