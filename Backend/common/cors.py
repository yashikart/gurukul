import os
import logging
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

def configure_cors(app):
    origins = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '').split(',') if o.strip()]
    allow_regex = os.getenv('ALLOW_ORIGIN_REGEX', '') or None
    
    # Append NGROK_URL if present
    ngrok_url = os.getenv('NGROK_URL', '').strip()
    if ngrok_url and ngrok_url not in origins and not ngrok_url.startswith('https://YOUR_NGROK_URL'):
        origins.append(ngrok_url)
        logger.info(f"✅ Added NGROK_URL to allowed origins: {ngrok_url}")
    
    logger.info("="*60)
    logger.info("🔒 CORS CONFIGURATION")
    logger.info(f"Allowed origins: {origins}")
    logger.info(f"Regex pattern: {allow_regex}")
    logger.info(f"Credentials: True")
    logger.info(f"Methods: ALL")
    logger.info(f"Headers: ALL")
    logger.info("="*60)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=allow_regex,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['*']
    )
