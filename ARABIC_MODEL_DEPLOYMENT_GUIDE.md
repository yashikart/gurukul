# Arabic Model Deployment Guide for Cloud Services (Render, etc.)

## Overview

Your Arabic checkpoint model is currently loaded from local files. When deploying to cloud services like Render, you have several options for making the model available.

## Current Setup

- **Checkpoint Location**: `checkpoints/checkpoint-100000/`
- **Required Files**:
  - `adapter_model.safetensors` (LoRA adapter weights)
  - `adapter_config.json` (LoRA configuration)
  - `tokenizer.json` (Tokenizer)
  - `tokenizer_config.json` (Tokenizer config)
  - `special_tokens_map.json` (Special tokens)
  - `chat_template.jinja` (Chat template)

## Deployment Options

### Option 1: Cloud Storage (Recommended for Production)

**Best for**: Production deployments with large checkpoints

#### Steps:

1. **Upload Checkpoint to Cloud Storage**:
   - Upload `checkpoints/checkpoint-100000/` folder to:
     - AWS S3
     - Google Cloud Storage
     - Azure Blob Storage
     - Or any object storage service

2. **Create Download Script**:
   ```python
   # Backend/Base_backend/download_checkpoint.py
   import os
   import boto3  # or google-cloud-storage, azure-storage-blob
   from pathlib import Path
   
   def download_checkpoint_from_s3(bucket_name, checkpoint_path, local_path):
       """Download checkpoint from S3"""
       s3 = boto3.client('s3')
       checkpoint_dir = Path(local_path)
       checkpoint_dir.mkdir(parents=True, exist_ok=True)
       
       # List and download all files
       files = [
           'adapter_model.safetensors',
           'adapter_config.json',
           'tokenizer.json',
           'tokenizer_config.json',
           'special_tokens_map.json',
           'chat_template.jinja'
       ]
       
       for file in files:
           s3_key = f"{checkpoint_path}/{file}"
           local_file = checkpoint_dir / file
           print(f"Downloading {file}...")
           s3.download_file(bucket_name, s3_key, str(local_file))
       
       print(f"Checkpoint downloaded to {local_path}")
   ```

3. **Update local_model_service.py**:
   ```python
   def _get_default_checkpoint_path(self) -> str:
       checkpoint_dir = Path("/tmp/checkpoints/checkpoint-100000")
       
       # Check if checkpoint exists locally
       if (checkpoint_dir / "adapter_model.safetensors").exists():
           return str(checkpoint_dir)
       
       # Download from cloud storage if not exists
       if os.getenv('CHECKPOINT_S3_BUCKET'):
           download_checkpoint_from_s3(
               os.getenv('CHECKPOINT_S3_BUCKET'),
               'checkpoint-100000',
               str(checkpoint_dir)
           )
           return str(checkpoint_dir)
       
       # Fallback to environment variable
       env_path = os.getenv('LOCAL_MODEL_CHECKPOINT_PATH')
       if env_path:
           return env_path
       
       # ... rest of existing code
   ```

4. **Set Environment Variables on Render**:
   ```
   CHECKPOINT_S3_BUCKET=your-bucket-name
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   LOCAL_MODEL_CHECKPOINT_PATH=/tmp/checkpoints/checkpoint-100000
   ```

### Option 2: Include in Git Repository (Not Recommended)

**Best for**: Small checkpoints (< 100MB) or development

⚠️ **Warning**: Checkpoint files are large and shouldn't be committed to Git.

If you must include them:
1. Add checkpoint files to repository
2. Set `LOCAL_MODEL_CHECKPOINT_PATH` to relative path
3. Ensure files are included in deployment

### Option 3: Render Persistent Disk (If Available)

**Best for**: Render services with persistent storage

1. Upload checkpoint files to Render's persistent disk
2. Set `LOCAL_MODEL_CHECKPOINT_PATH` to disk path
3. Files persist across deployments

### Option 4: Download During Build (Render Build Script)

**Best for**: Render deployments with build scripts

1. **Create `render.yaml`**:
   ```yaml
   services:
     - type: web
       name: gurukul-backend
       env: python
       buildCommand: |
         pip install -r requirements.txt
         python download_checkpoint.py  # Download checkpoint during build
       startCommand: python -m uvicorn api:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: LOCAL_MODEL_CHECKPOINT_PATH
           value: /opt/render/checkpoints/checkpoint-100000
   ```

2. **Create `download_checkpoint.py`**:
   ```python
   import os
   import requests
   from pathlib import Path
   
   def download_checkpoint():
       checkpoint_url = os.getenv('CHECKPOINT_DOWNLOAD_URL')
       if not checkpoint_url:
           print("No CHECKPOINT_DOWNLOAD_URL set, skipping download")
           return
       
       checkpoint_dir = Path("/opt/render/checkpoints/checkpoint-100000")
       checkpoint_dir.mkdir(parents=True, exist_ok=True)
       
       files = [
           'adapter_model.safetensors',
           'adapter_config.json',
           'tokenizer.json',
           'tokenizer_config.json',
           'special_tokens_map.json',
           'chat_template.jinja'
       ]
       
       for file in files:
           url = f"{checkpoint_url}/{file}"
           local_file = checkpoint_dir / file
           print(f"Downloading {file}...")
           response = requests.get(url)
           local_file.write_bytes(response.content)
       
       print("Checkpoint downloaded successfully")
   
   if __name__ == "__main__":
       download_checkpoint()
   ```

### Option 5: Make Model Optional (Fallback to API)

**Best for**: When model hosting is complex

Update the code to gracefully handle missing checkpoints:

```python
# In llm_service.py
if LOCAL_MODEL_AVAILABLE:
    try:
        checkpoint_path = os.getenv('LOCAL_MODEL_CHECKPOINT_PATH', None)
        self.local_model = get_local_model(checkpoint_path)
        logger.info("✅ Local Arabic model service initialized")
    except Exception as e:
        logger.warning(f"⚠️ Local model not available: {e}")
        logger.info("💡 Falling back to API-based models (Groq/OpenAI)")
        self.local_model = None
```

The system will automatically fallback to Groq/OpenAI when the local model isn't available.

## Recommended Approach for Render

### Step 1: Upload to Cloud Storage

1. **Create S3 bucket** (or equivalent):
   ```bash
   aws s3 mb s3://your-gurukul-checkpoints
   ```

2. **Upload checkpoint files**:
   ```bash
   aws s3 sync checkpoints/checkpoint-100000/ s3://your-gurukul-checkpoints/checkpoint-100000/
   ```

### Step 2: Create Download Utility

Create `Backend/Base_backend/download_checkpoint.py`:

```python
"""
Download checkpoint from cloud storage for deployment
"""
import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def download_checkpoint():
    """Download checkpoint from configured storage"""
    checkpoint_dir = Path(os.getenv('LOCAL_MODEL_CHECKPOINT_PATH', '/tmp/checkpoints/checkpoint-100000'))
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    if (checkpoint_dir / "adapter_model.safetensors").exists():
        logger.info(f"Checkpoint already exists at {checkpoint_dir}")
        return str(checkpoint_dir)
    
    # Try S3
    if os.getenv('CHECKPOINT_S3_BUCKET'):
        try:
            import boto3
            s3 = boto3.client('s3')
            bucket = os.getenv('CHECKPOINT_S3_BUCKET')
            prefix = os.getenv('CHECKPOINT_S3_PREFIX', 'checkpoint-100000')
            
            files = [
                'adapter_model.safetensors',
                'adapter_config.json',
                'tokenizer.json',
                'tokenizer_config.json',
                'special_tokens_map.json',
                'chat_template.jinja'
            ]
            
            for file in files:
                s3_key = f"{prefix}/{file}"
                local_file = checkpoint_dir / file
                logger.info(f"Downloading {file} from S3...")
                s3.download_file(bucket, s3_key, str(local_file))
            
            logger.info(f"✅ Checkpoint downloaded to {checkpoint_dir}")
            return str(checkpoint_dir)
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
    
    # Try direct URL download
    if os.getenv('CHECKPOINT_DOWNLOAD_URL'):
        try:
            import requests
            base_url = os.getenv('CHECKPOINT_DOWNLOAD_URL')
            
            files = [
                'adapter_model.safetensors',
                'adapter_config.json',
                'tokenizer.json',
                'tokenizer_config.json',
                'special_tokens_map.json',
                'chat_template.jinja'
            ]
            
            for file in files:
                url = f"{base_url}/{file}"
                local_file = checkpoint_dir / file
                logger.info(f"Downloading {file} from {url}...")
                response = requests.get(url, timeout=300)
                response.raise_for_status()
                local_file.write_bytes(response.content)
            
            logger.info(f"✅ Checkpoint downloaded to {checkpoint_dir}")
            return str(checkpoint_dir)
        except Exception as e:
            logger.error(f"Failed to download from URL: {e}")
    
    logger.warning("No checkpoint download method configured")
    return None

if __name__ == "__main__":
    download_checkpoint()
```

### Step 3: Update local_model_service.py

Add checkpoint download on initialization:

```python
def _get_default_checkpoint_path(self) -> str:
    """Get default checkpoint path, downloading if needed"""
    # Try environment variable first
    env_path = os.getenv('LOCAL_MODEL_CHECKPOINT_PATH')
    if env_path and Path(env_path).exists():
        return env_path
    
    # Try to download checkpoint if configured
    try:
        from download_checkpoint import download_checkpoint
        downloaded_path = download_checkpoint()
        if downloaded_path:
            return downloaded_path
    except ImportError:
        pass
    
    # ... rest of existing path detection code
```

### Step 4: Render Environment Variables

Set these in Render dashboard:

```
# Checkpoint Configuration
LOCAL_MODEL_CHECKPOINT_PATH=/tmp/checkpoints/checkpoint-100000

# Option A: S3 Storage
CHECKPOINT_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
CHECKPOINT_S3_PREFIX=checkpoint-100000

# Option B: Direct URL (if hosting checkpoint files elsewhere)
CHECKPOINT_DOWNLOAD_URL=https://your-cdn.com/checkpoints/checkpoint-100000
```

### Step 5: Update Requirements

Add to `Backend/requirements.txt`:

```
boto3>=1.28.0  # For S3 downloads
requests>=2.31.0  # For URL downloads
```

## Alternative: Use Model Hosting Service

Instead of hosting the checkpoint yourself, consider:

1. **Hugging Face Model Hub**: Upload your checkpoint to Hugging Face
2. **Replicate**: Host your model on Replicate
3. **Modal**: Serverless model hosting
4. **RunPod**: GPU instances for model hosting

Then update the code to load from Hugging Face:

```python
base_model_name = "your-username/your-arabic-model"  # Hugging Face model ID
```

## Performance Considerations

1. **First Load**: Model download and loading takes time (5-10 minutes)
   - Consider lazy loading (current implementation)
   - Cache checkpoint files in persistent storage

2. **Memory**: Model requires ~4-8GB RAM
   - Ensure Render instance has sufficient memory
   - Consider using GPU instances for faster inference

3. **Storage**: Checkpoint files are large (~500MB-2GB)
   - Use persistent storage or download on startup
   - Consider model quantization for smaller size

## Testing Deployment

1. **Test Locally First**:
   ```bash
   # Set environment variables
   export CHECKPOINT_S3_BUCKET=your-bucket
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export LOCAL_MODEL_CHECKPOINT_PATH=/tmp/test-checkpoint
   
   # Run download script
   python Backend/Base_backend/download_checkpoint.py
   
   # Test model loading
   python Backend/Base_backend/test_local_model.py
   ```

2. **Deploy to Render**:
   - Set environment variables in Render dashboard
   - Deploy and check logs for checkpoint download
   - Test Arabic model endpoint

## Troubleshooting

### Model Not Loading
- Check checkpoint files exist at specified path
- Verify environment variables are set correctly
- Check Render logs for download errors

### Out of Memory
- Increase Render instance RAM
- Use model quantization (4-bit/8-bit)
- Consider using API-based models instead

### Slow Inference
- Use GPU instances if available
- Enable model caching
- Consider using API-based models for faster response

## Summary

**Recommended Flow**:
1. Upload checkpoint to S3/cloud storage
2. Use download script during Render build/startup
3. Cache checkpoint in persistent storage
4. Fallback to API models if checkpoint unavailable

This ensures your Arabic model works in production while maintaining flexibility.









