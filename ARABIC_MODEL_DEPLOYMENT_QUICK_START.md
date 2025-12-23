# Arabic Model Deployment - Quick Start Guide

## 🚀 Quick Deployment Options

### Option 1: Upload to S3 (Recommended)

**Steps:**

1. **Upload checkpoint to S3**:
   ```bash
   aws s3 sync checkpoints/checkpoint-100000/ s3://your-bucket-name/checkpoint-100000/
   ```

2. **Set Render Environment Variables**:
   ```
   CHECKPOINT_S3_BUCKET=your-bucket-name
   CHECKPOINT_S3_PREFIX=checkpoint-100000
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   LOCAL_MODEL_CHECKPOINT_PATH=/opt/render/checkpoints/checkpoint-100000
   ```

3. **Deploy** - The checkpoint will download automatically during build!

### Option 2: Host on CDN/Web Server

**Steps:**

1. **Upload checkpoint files to your web server/CDN**
   - Upload all files from `checkpoints/checkpoint-100000/` to a public URL

2. **Set Render Environment Variables**:
   ```
   CHECKPOINT_DOWNLOAD_URL=https://your-cdn.com/checkpoints/checkpoint-100000
   LOCAL_MODEL_CHECKPOINT_PATH=/opt/render/checkpoints/checkpoint-100000
   ```

3. **Deploy** - Files will download automatically!

### Option 3: Skip Local Model (Use API Fallback)

**If you don't want to host the checkpoint:**

1. **Don't set any checkpoint environment variables**
2. **The system will automatically use Groq/OpenAI APIs** for Arabic queries
3. **No additional setup needed!**

## 📋 Required Checkpoint Files

The following files must be available:

- `adapter_model.safetensors` (~500MB-2GB)
- `adapter_config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- `chat_template.jinja`

## ⚙️ How It Works

1. **During Build**: `setup_checkpoint.sh` runs and downloads checkpoint if configured
2. **On Startup**: Model service checks for checkpoint, downloads if missing
3. **Fallback**: If checkpoint unavailable, uses Groq/OpenAI APIs automatically

## 🔍 Testing Locally

```bash
# Set environment variables
export CHECKPOINT_S3_BUCKET=your-bucket
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export LOCAL_MODEL_CHECKPOINT_PATH=/tmp/test-checkpoint

# Test download
cd Backend
python Base_backend/download_checkpoint.py

# Test model loading
python Base_backend/test_local_model.py
```

## 💡 Tips

- **First deployment**: Checkpoint download takes 5-10 minutes
- **Subsequent deployments**: Checkpoint is cached, faster startup
- **Memory**: Ensure Render instance has 8GB+ RAM for model
- **Storage**: Checkpoint needs ~2GB disk space

## 🆘 Troubleshooting

**Model not loading?**
- Check Render logs for download errors
- Verify environment variables are set correctly
- Check S3 bucket permissions (if using S3)

**Out of memory?**
- Upgrade Render instance to higher RAM plan
- Or use API fallback (don't set checkpoint env vars)

**Slow inference?**
- Consider using GPU instances
- Or use API-based models (Groq/OpenAI) for faster responses

## 📚 Full Documentation

See `ARABIC_MODEL_DEPLOYMENT_GUIDE.md` for detailed instructions.









