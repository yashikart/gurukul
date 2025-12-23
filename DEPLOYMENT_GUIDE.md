# Deployment Guide for Gurukul Application

This guide explains how to deploy your Gurukul application to Render using GitHub.

## Prerequisites

1. GitHub account with your repository pushed
2. Render account (sign up at https://render.com)
3. MongoDB Atlas account (or use Render's MongoDB)
4. API keys for:
   - Groq API
   - OpenAI API
   - Google/Gemini API

## Step-by-Step Deployment

### Option 1: Deploy Using Render Dashboard (Recommended)

#### 1. Deploy Backend Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account and select the `yashikart/gurukul` repository
4. Configure the service:
   - **Name**: `gurukul-backend`
   - **Region**: Oregon (or closest to your users)
   - **Branch**: `main`
   - **Root Directory**: `Gurukul_new-main/Backend` (or just `Backend` if using render.yaml)
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     python main.py
     ```
   - **Plan**: Starter (or Free for testing)

5. Add Environment Variables:
   - `PORT` = `10000` (Render sets this automatically, but good to have)
   - `HOST` = `0.0.0.0`
   - `MONGODB_URL` = Your MongoDB connection string
   - `GROQ_API_KEY` = Your Groq API key
   - `OPENAI_API_KEY` = Your OpenAI API key
   - `GOOGLE_API_KEY` = Your Google API key
   - `GEMINI_API_KEY` = Your Gemini API key
   - `ENVIRONMENT` = `production`
   - `DEBUG` = `false`

6. Click **"Create Web Service"**

#### 2. Deploy Frontend (Static Site)

1. In Render Dashboard, click **"New +"** → **"Static Site"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `gurukul-frontend`
   - **Branch**: `main`
   - **Root Directory**: `Gurukul_new-main/new frontend`
   - **Build Command**: 
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist` (or `build` depending on your Vite config)
   - **Environment Variables**:
     - `VITE_API_BASE_URL` = `https://gurukul-backend.onrender.com`
     - `VITE_CHAT_API_BASE_URL` = `https://gurukul-backend.onrender.com`

4. Click **"Create Static Site"**

#### 3. Create MongoDB Database (Optional - if not using external MongoDB)

1. Click **"New +"** → **"Postgres"** (or use MongoDB Atlas)
2. Configure:
   - **Name**: `gurukul-mongodb`
   - **Plan**: Starter
3. Copy the connection string and add it to your backend environment variables

### Option 2: Deploy Using render.yaml (Blueprints)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the `render.yaml` file from the root directory
5. Render will automatically:
   - Create the backend web service
   - Create the frontend static site
   - Create the MongoDB database
   - Link all services together

6. Add your API keys in the Environment Variables section for the backend service

## Post-Deployment Steps

### 1. Update Frontend API URLs

After deployment, update your frontend environment variables to point to your Render backend URL:
- `VITE_API_BASE_URL` = `https://your-backend-service.onrender.com`
- `VITE_CHAT_API_BASE_URL` = `https://your-backend-service.onrender.com`

### 2. Configure CORS

Make sure your backend allows requests from your frontend domain. Update CORS settings in your backend code to include:
```python
origins = [
    "https://gurukul-frontend.onrender.com",
    "http://localhost:5173",  # For local development
]
```

### 3. Test Your Deployment

1. Visit your frontend URL: `https://gurukul-frontend.onrender.com`
2. Test the backend health endpoint: `https://gurukul-backend.onrender.com/health`
3. Test API endpoints through the frontend

## Environment Variables Reference

### Backend Required Variables:
- `MONGODB_URL` - MongoDB connection string
- `GROQ_API_KEY` - Groq API key for LLM
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_API_KEY` - Google API key
- `GEMINI_API_KEY` - Gemini API key
- `PORT` - Server port (usually auto-set by Render)
- `HOST` - Server host (0.0.0.0)

### Frontend Required Variables:
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_CHAT_API_BASE_URL` - Chat API URL

## Troubleshooting

### Backend won't start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` includes all dependencies
- Check that `main.py` exists and is executable

### Frontend build fails
- Check Node.js version (should be 18+)
- Verify `package.json` has correct build scripts
- Check that all dependencies are listed in `package.json`

### CORS errors
- Update backend CORS settings to include frontend URL
- Verify frontend environment variables point to correct backend URL

### Database connection issues
- Verify MongoDB connection string is correct
- Check MongoDB Atlas IP whitelist (if using Atlas)
- Ensure database user has proper permissions

## Continuous Deployment

Render automatically deploys when you push to the `main` branch. To disable auto-deploy:
1. Go to your service settings
2. Under "Auto-Deploy", select "No"

## Monitoring

- View logs in Render dashboard
- Set up health checks (already configured in `render.yaml`)
- Monitor service uptime in Render dashboard

## Cost Estimation

- **Free Tier**: Good for testing (spins down after inactivity)
- **Starter Plan**: $7/month per service (always on)
- **MongoDB**: Free tier available on MongoDB Atlas

## Support

For issues:
1. Check Render logs
2. Review GitHub Actions (if using CI/CD)
3. Check application logs in Render dashboard

