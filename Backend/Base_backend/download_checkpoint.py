"""
Download checkpoint from cloud storage for deployment
Supports S3, direct URL downloads, and local paths
"""
import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def download_from_s3(bucket_name: str, prefix: str, local_path: Path) -> bool:
    """Download checkpoint from AWS S3"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        s3 = boto3.client('s3')
        
        files = [
            'adapter_model.safetensors',
            'adapter_config.json',
            'tokenizer.json',
            'tokenizer_config.json',
            'special_tokens_map.json',
            'chat_template.jinja'
        ]
        
        for file in files:
            s3_key = f"{prefix}/{file}" if prefix else file
            local_file = local_path / file
            
            # Skip if file already exists
            if local_file.exists():
                logger.info(f"File {file} already exists, skipping download")
                continue
            
            logger.info(f"Downloading {file} from S3 (s3://{bucket_name}/{s3_key})...")
            try:
                s3.download_file(bucket_name, s3_key, str(local_file))
                logger.info(f"✅ Downloaded {file}")
            except ClientError as e:
                logger.error(f"Failed to download {file}: {e}")
                return False
        
        return True
    except ImportError:
        logger.error("boto3 not installed. Install with: pip install boto3")
        return False
    except Exception as e:
        logger.error(f"S3 download failed: {e}")
        return False

def download_from_url(base_url: str, local_path: Path) -> bool:
    """Download checkpoint from direct URL"""
    try:
        import requests
        
        files = [
            'adapter_model.safetensors',
            'adapter_config.json',
            'tokenizer.json',
            'tokenizer_config.json',
            'special_tokens_map.json',
            'chat_template.jinja'
        ]
        
        for file in files:
            url = f"{base_url.rstrip('/')}/{file}"
            local_file = local_path / file
            
            # Skip if file already exists
            if local_file.exists():
                logger.info(f"File {file} already exists, skipping download")
                continue
            
            logger.info(f"Downloading {file} from {url}...")
            try:
                response = requests.get(url, timeout=300, stream=True)
                response.raise_for_status()
                
                # Write file in chunks for large files
                with open(local_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"✅ Downloaded {file} ({local_file.stat().st_size / (1024*1024):.2f} MB)")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download {file}: {e}")
                return False
        
        return True
    except ImportError:
        logger.error("requests not installed. Install with: pip install requests")
        return False
    except Exception as e:
        logger.error(f"URL download failed: {e}")
        return False

def download_checkpoint() -> str:
    """
    Download checkpoint from configured storage source
    
    Returns:
        Path to checkpoint directory if successful, None otherwise
    """
    # Get checkpoint directory from environment or use default
    checkpoint_dir = Path(
        os.getenv('LOCAL_MODEL_CHECKPOINT_PATH', '/tmp/checkpoints/checkpoint-100000')
    )
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if checkpoint already exists
    if (checkpoint_dir / "adapter_model.safetensors").exists():
        logger.info(f"✅ Checkpoint already exists at {checkpoint_dir}")
        return str(checkpoint_dir)
    
    logger.info(f"📥 Checkpoint not found. Attempting to download to {checkpoint_dir}...")
    
    # Try S3 download
    s3_bucket = os.getenv('CHECKPOINT_S3_BUCKET')
    if s3_bucket:
        logger.info(f"Attempting S3 download from bucket: {s3_bucket}")
        s3_prefix = os.getenv('CHECKPOINT_S3_PREFIX', 'checkpoint-100000')
        if download_from_s3(s3_bucket, s3_prefix, checkpoint_dir):
            logger.info(f"✅ Checkpoint downloaded successfully to {checkpoint_dir}")
            return str(checkpoint_dir)
        else:
            logger.warning("S3 download failed, trying other methods...")
    
    # Try direct URL download
    download_url = os.getenv('CHECKPOINT_DOWNLOAD_URL')
    if download_url:
        logger.info(f"Attempting URL download from: {download_url}")
        if download_from_url(download_url, checkpoint_dir):
            logger.info(f"✅ Checkpoint downloaded successfully to {checkpoint_dir}")
            return str(checkpoint_dir)
        else:
            logger.warning("URL download failed")
    
    # No download method configured or all failed
    logger.warning(
        "⚠️ No checkpoint download method configured or download failed.\n"
        "Set one of:\n"
        "  - CHECKPOINT_S3_BUCKET (with AWS credentials)\n"
        "  - CHECKPOINT_DOWNLOAD_URL (direct URL to checkpoint files)\n"
        "  - LOCAL_MODEL_CHECKPOINT_PATH (local path to checkpoint)\n"
        "\n"
        "The Arabic model will not be available until checkpoint is provided."
    )
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = download_checkpoint()
    if result:
        print(f"\n✅ Checkpoint ready at: {result}")
        sys.exit(0)
    else:
        print("\n❌ Checkpoint download failed")
        sys.exit(1)









