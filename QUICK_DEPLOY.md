# Quick Deployment Guide

## Deploy to Render in 5 Steps

### Step 1: Prepare Your Repository
✅ Your code is already on GitHub at: `https://github.com/yashikart/gurukul.git`

### Step 2: Sign Up for Render
1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### Step 3: Deploy Backend (Web Service)
1. Click **"New +"** → **"Web Service"**
2. Select your repository: `yashikart/gurukul`
3. Configure:
   - **Name**: `gurukul-backend`
   - **Root Directory**: `Gurukul_new-main/Backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free (for testing) or Starter ($7/month)

4. Add Environment Variables:
   ```
   MONGODB_URL=your_mongodb_connection_string
   GROQ_API_KEY=your_groq_key
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   GEMINI_API_KEY=your_gemini_key
   PORT=10000
   HOST=0.0.0.0
   ```

5. Click **"Create Web Service"**

### Step 4: Deploy Frontend (Static Site)
1. Click **"New +"** → **"Static Site"**
2. Select your repository: `yashikart/gurukul`
3. Configure:
   - **Name**: `gurukul-frontend`
   - **Root Directory**: `Gurukul_new-main/new frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. Add Environment Variables:
   ```
   VITE_API_BASE_URL=https://gurukul-backend.onrender.com
   VITE_CHAT_API_BASE_URL=https://gurukul-backend.onrender.com
   ```
   (Replace with your actual backend URL after deployment)

5. Click **"Create Static Site"**

### Step 5: Update Frontend URLs
After backend deploys, copy the backend URL and update frontend environment variables:
- Go to Frontend service → Environment
- Update `VITE_API_BASE_URL` with your backend URL
- Redeploy frontend

## Alternative: Use Blueprint (Easier!)

1. Click **"New +"** → **"Blueprint"**
2. Select repository: `yashikart/gurukul`
3. Render will auto-detect `render.yaml` and create everything
4. Just add your API keys in Environment Variables

## Your URLs Will Be:
- Backend: `https://gurukul-backend.onrender.com`
- Frontend: `https://gurukul-frontend.onrender.com`

## Need Help?
See `DEPLOYMENT_GUIDE.md` for detailed instructions.

