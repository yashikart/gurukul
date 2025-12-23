"""
Centralized Environment Configuration Loader for Gurukul Platform
================================================================

This module provides a centralized way to load environment variables
for all backend services from the master .env file.

Usage:
    from shared_config import load_shared_config
    load_shared_config()
    
    # Now all environment variables are available via os.getenv()
    api_key = os.getenv("GROQ_API_KEY")
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_backend_root():
    """
    Get the Backend directory path regardless of where this function is called from.
    
    Returns:
        Path: Path to the Backend directory
    """
    # Get the current file's directory
    current_file = Path(__file__).resolve()
    
    # If we're already in Backend directory
    if current_file.parent.name == "Backend":
        return current_file.parent
    
    # Search upwards for Backend directory
    current_dir = current_file.parent
    while current_dir.parent != current_dir:  # Not at filesystem root
        if current_dir.name == "Backend":
            return current_dir
        # Check if Backend directory exists in current directory
        backend_path = current_dir / "Backend"
        if backend_path.exists() and backend_path.is_dir():
            return backend_path
        current_dir = current_dir.parent
    
    # If not found, assume we're in a subdirectory of Backend
    # and try to find it by going up
    current_dir = current_file.parent
    while current_dir.parent != current_dir:
        parent_backend = current_dir.parent / "Backend"
        if parent_backend.exists() and parent_backend.is_dir():
            return parent_backend
        current_dir = current_dir.parent
    
    # Fallback: assume Backend is the parent directory
    return current_file.parent.parent if current_file.parent.parent.name == "Backend" else current_file.parent

def load_shared_config(service_name=None, fallback_to_local=True):
    """
    Load environment variables from the centralized .env file.
    
    Args:
        service_name (str, optional): Name of the service loading config (for logging)
        fallback_to_local (bool): Whether to fallback to local .env if centralized not found
    
    Returns:
        bool: True if centralized config was loaded, False if fallback was used
    """
    if service_name:
        logger.info(f"🔧 Loading centralized configuration for {service_name}")
    else:
        logger.info("🔧 Loading centralized configuration")
    
    # Get the Backend root directory
    backend_root = get_backend_root()
    centralized_env_path = backend_root / ".env"
    
    # Try to load centralized .env file
    if centralized_env_path.exists():
        load_dotenv(centralized_env_path)
        logger.info(f"✅ Loaded centralized configuration from: {centralized_env_path}")
        
        # Verify critical variables are loaded
        critical_vars = ["GROQ_API_KEY", "MONGODB_URI", "MONGO_URI"]
        loaded_vars = []
        missing_vars = []
        
        for var in critical_vars:
            if os.getenv(var):
                loaded_vars.append(var)
            else:
                missing_vars.append(var)
        
        if loaded_vars:
            logger.info(f"✅ Loaded critical variables: {', '.join(loaded_vars)}")
        if missing_vars:
            logger.warning(f"⚠️  Missing variables: {', '.join(missing_vars)}")
        
        return True
    
    else:
        logger.warning(f"⚠️  Centralized .env file not found at: {centralized_env_path}")
        
        if fallback_to_local:
            # Try to load local .env file as fallback
            local_env_path = Path.cwd() / ".env"
            if local_env_path.exists():
                load_dotenv(local_env_path)
                logger.info(f"📁 Fallback: Loaded local .env from: {local_env_path}")
                return False
            else:
                logger.warning("⚠️  No local .env file found either")
                logger.info("💡 Services will use default values or environment variables")
                return False
        else:
            logger.error("❌ Centralized configuration required but not found")
            return False

def get_service_config(service_name):
    """
    Get service-specific configuration with centralized defaults.
    
    Args:
        service_name (str): Name of the service
    
    Returns:
        dict: Service configuration
    """
    # Load centralized config first
    load_shared_config(service_name)
    
    # Service-specific port mappings
    port_mapping = {
        "base_backend": int(os.getenv("BASE_BACKEND_PORT", "8000")),
        "api_data": int(os.getenv("API_DATA_PORT", "8001")),
        "financial_simulator": int(os.getenv("FINANCIAL_SIMULATOR_PORT", "8002")),
        "memory_management": int(os.getenv("MEMORY_MANAGEMENT_PORT", "8003")),
        "akash": int(os.getenv("AKASH_SERVICE_PORT", "8004")),
        "subject_generation": int(os.getenv("SUBJECT_GENERATION_PORT", "8005")),
        "orchestration": int(os.getenv("WELLNESS_API_PORT", "8006")),
        "tts_service": int(os.getenv("TTS_SERVICE_PORT", "8007"))
    }
    
    # Common configuration for all services
    # Default Google AI Studio API key
    default_gemini_key = "AIzaSyDSunIIg6InYPa4yaYhrXKGXO2HTWhi_wc"
    default_youtube_key = "AIzaSyCJhsvlm7aAhnOBM6oBl1d90s9l67ksfbc"
    
    config = {
        "service_name": service_name,
        "port": port_mapping.get(service_name, 8000),
        "host": os.getenv("HOST", "0.0.0.0"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        
        # API Keys
        "groq_api_key": os.getenv("GROQ_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", default_gemini_key),
        "agentops_api_key": os.getenv("AGENTOPS_API_KEY"),
        "llama_api_key": os.getenv("LLAMA_API_KEY"),
        "uniguru_api_key": os.getenv("UNIGURU_API_KEY"),
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY", default_youtube_key),
        
        # Database URLs
        "mongodb_uri": os.getenv("MONGODB_URI") or os.getenv("MONGO_URI"),
        "redis_url": os.getenv("REDIS_URL"),
        
        # Service URLs
        "agent_api_url": os.getenv("AGENT_API_URL"),
        "tutorbot_url": os.getenv("TUTORBOT_URL"),

        # Local LLM & Ollama Configuration
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model_primary": os.getenv("OLLAMA_MODEL_PRIMARY", "llama2"),
        "ollama_model_alternatives": os.getenv("OLLAMA_MODEL_ALTERNATIVES", "mistral,codellama,neural-chat").split(","),
        "groq_api_endpoint": os.getenv("GROQ_API_ENDPOINT"),
        "uniguru_ngrok_endpoint": os.getenv("UNIGURU_NGROK_ENDPOINT"),
        "uniguru_api_base_url": os.getenv("UNIGURU_API_BASE_URL"),
        "local_llama_api_url": os.getenv("LOCAL_LLAMA_API_URL", "http://localhost:8080/v1/chat/completions"),
        "local_ollama_api_url": os.getenv("LOCAL_OLLAMA_API_URL", "http://localhost:11434/api/generate"),
        "default_local_model": os.getenv("DEFAULT_LOCAL_MODEL", "llama3.1"),
        "fallback_local_model": os.getenv("FALLBACK_LOCAL_MODEL", "llama2"),

        # Memory Management Configuration
        "memory_api_keys": os.getenv("MEMORY_API_KEYS"),
        "memory_db_name": os.getenv("MEMORY_DB_NAME", "gurukul"),
        "memory_api_host": os.getenv("MEMORY_API_HOST", "0.0.0.0"),
        "memory_api_port": int(os.getenv("MEMORY_API_PORT", "8003")),
        "memory_rate_limit_requests": int(os.getenv("MEMORY_RATE_LIMIT_REQUESTS", "1000")),
        "memory_rate_limit_window": int(os.getenv("MEMORY_RATE_LIMIT_WINDOW", "3600")),

        # Supabase Configuration
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_KEY"),
        "supabase_jwt_secret": os.getenv("SUPABASE_JWT_SECRET"),

        # Agent API Configuration
        "agent_api_url": os.getenv("AGENT_API_URL"),
        "agent_api_key": os.getenv("AGENT_API_KEY"),

        # TTS Configuration
        "tts_enabled": os.getenv("TTS_ENABLED", "false").lower() == "true",
        "tts_api_url": os.getenv("TTS_API_URL"),

        # Service Thresholds
        "low_quiz_score_threshold": float(os.getenv("LOW_QUIZ_SCORE_THRESHOLD", "60")),
        "wellness_concern_threshold": float(os.getenv("WELLNESS_CONCERN_THRESHOLD", "3")),
        "inactivity_days_threshold": int(os.getenv("INACTIVITY_DAYS_THRESHOLD", "7")),

        # Sub-agent Service URLs
        "tutorbot_url": os.getenv("TUTORBOT_URL", "http://localhost:8001"),
        "emotional_wellness_bot_url": os.getenv("EMOTIONAL_WELLNESS_BOT_URL", "http://localhost:8002"),
        "financial_wellness_bot_url": os.getenv("FINANCIAL_WELLNESS_BOT_URL", "http://localhost:8003"),
        "quizbot_url": os.getenv("QUIZBOT_URL", "http://localhost:8004"),

        # External API Keys
        "alpha_vantage_api_key": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "opencage_api_key": os.getenv("OPENCAGE_API_KEY"),
        "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),

        # Vision API Configuration
        "vision_api_key": os.getenv("VISION_API_KEY"),
        "vision_api_url": os.getenv("VISION_API_URL"),

        # External Service URLs
        "gurukul_api_base": os.getenv("GURUKUL_API_BASE"),
        "external_server": os.getenv("EXTERNAL_SERVER"),

        # Database Additional Configuration
        "mongodb_database": os.getenv("MONGODB_DATABASE", "agent_memory"),
        "mongodb_url": os.getenv("MONGODB_URL", "mongodb://localhost:27017/"),
    }
    
    return config

def validate_config(required_vars=None):
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars (list): List of required variable names
    
    Returns:
        tuple: (is_valid, missing_vars)
    """
    if required_vars is None:
        required_vars = ["GROQ_API_KEY"]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    is_valid = len(missing_vars) == 0
    
    if not is_valid:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("💡 Please check the centralized .env file in the Backend directory")
    
    return is_valid, missing_vars

# Convenience function for backward compatibility
def load_dotenv_centralized():
    """Backward compatibility function"""
    return load_shared_config()

if __name__ == "__main__":
    # Test the configuration loader
    print("Testing centralized configuration loader...")
    success = load_shared_config("test_service")
    
    if success:
        print("\n📊 Configuration Summary:")
        print(f"   GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Missing'}")
        print(f"   MONGODB_URI: {'✅ Set' if os.getenv('MONGODB_URI') else '❌ Missing'}")
        print(f"   GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'Not set')}")
    else:
        print("❌ Failed to load centralized configuration")
