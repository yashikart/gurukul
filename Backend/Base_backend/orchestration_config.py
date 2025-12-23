"""
Orchestration Integration Configuration
Manages settings and environment variables for Base_backend + Orchestration integration
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OrchestrationConfig:
    """Configuration manager for orchestration integration"""
    
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        
        # Orchestration System Settings
        self.ORCHESTRATION_ENABLED = os.getenv("ORCHESTRATION_ENABLED", "true").lower() == "true"
        self.ORCHESTRATION_FALLBACK_ENABLED = os.getenv("ORCHESTRATION_FALLBACK_ENABLED", "true").lower() == "true"
        
        # API Keys for Orchestration
        # Default Google AI Studio API key
        default_gemini_key = "AIzaSyDSunIIg6InYPa4yaYhrXKGXO2HTWhi_wc"
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", default_gemini_key)
        self.GEMINI_API_KEY_BACKUP = os.getenv("GEMINI_API_KEY_BACKUP", "")
        
        # Sub-agent URLs (pointing to existing services)
        self.TUTORBOT_URL = os.getenv("TUTORBOT_URL", "http://localhost:8001")  # Karthikeya
        self.EMOTIONAL_WELLNESS_BOT_URL = os.getenv("EMOTIONAL_WELLNESS_BOT_URL", "http://localhost:8002")
        self.FINANCIAL_WELLNESS_BOT_URL = os.getenv("FINANCIAL_WELLNESS_BOT_URL", "http://localhost:8003")
        self.QUIZBOT_URL = os.getenv("QUIZBOT_URL", "http://localhost:8004")
        
        # Trigger Thresholds
        self.LOW_QUIZ_SCORE_THRESHOLD = float(os.getenv("LOW_QUIZ_SCORE_THRESHOLD", "60"))
        self.WELLNESS_CONCERN_THRESHOLD = float(os.getenv("WELLNESS_CONCERN_THRESHOLD", "3"))
        self.INACTIVITY_DAYS_THRESHOLD = int(os.getenv("INACTIVITY_DAYS_THRESHOLD", "7"))
        
        # Vector Store Settings
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
        self.MAX_DOCUMENTS_PER_QUERY = int(os.getenv("MAX_DOCUMENTS_PER_QUERY", "5"))
        
        # Integration Settings
        self.STORE_ENHANCED_LESSONS = os.getenv("STORE_ENHANCED_LESSONS", "true").lower() == "true"
        self.AUTO_TRIGGER_INTERVENTIONS = os.getenv("AUTO_TRIGGER_INTERVENTIONS", "true").lower() == "true"
        self.ENABLE_PROGRESS_TRACKING = os.getenv("ENABLE_PROGRESS_TRACKING", "true").lower() == "true"
        
        # Logging and Monitoring
        self.LOG_ORCHESTRATION_CALLS = os.getenv("LOG_ORCHESTRATION_CALLS", "true").lower() == "true"
        self.LOG_TRIGGER_EVENTS = os.getenv("LOG_TRIGGER_EVENTS", "true").lower() == "true"
        
    def get_sub_agent_config(self) -> Dict[str, str]:
        """Get sub-agent URL configuration"""
        return {
            "tutorbot": self.TUTORBOT_URL,
            "emotional_wellness": self.EMOTIONAL_WELLNESS_BOT_URL,
            "financial_wellness": self.FINANCIAL_WELLNESS_BOT_URL,
            "quizbot": self.QUIZBOT_URL
        }
    
    def get_trigger_thresholds(self) -> Dict[str, float]:
        """Get trigger threshold configuration"""
        return {
            "low_quiz_score": self.LOW_QUIZ_SCORE_THRESHOLD,
            "wellness_concern": self.WELLNESS_CONCERN_THRESHOLD,
            "inactivity_days": self.INACTIVITY_DAYS_THRESHOLD
        }
    
    def get_vector_store_config(self) -> Dict[str, int]:
        """Get vector store configuration"""
        return {
            "chunk_size": self.CHUNK_SIZE,
            "chunk_overlap": self.CHUNK_OVERLAP,
            "max_documents_per_query": self.MAX_DOCUMENTS_PER_QUERY
        }
    
    def is_orchestration_available(self) -> bool:
        """Check if orchestration system should be enabled"""
        return (
            self.ORCHESTRATION_ENABLED and 
            (self.GEMINI_API_KEY or self.GEMINI_API_KEY_BACKUP)
        )
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation_results = {
            "orchestration_enabled": self.ORCHESTRATION_ENABLED,
            "api_keys_available": bool(self.GEMINI_API_KEY or self.GEMINI_API_KEY_BACKUP),
            "sub_agents_configured": bool(self.TUTORBOT_URL),
            "thresholds_valid": self.LOW_QUIZ_SCORE_THRESHOLD > 0,
            "overall_valid": False
        }
        
        validation_results["overall_valid"] = all([
            validation_results["orchestration_enabled"],
            validation_results["api_keys_available"],
            validation_results["thresholds_valid"]
        ])
        
        return validation_results
    
    def get_environment_template(self) -> str:
        """Get template for .env file with orchestration settings"""
        return """
# Orchestration Integration Settings
ORCHESTRATION_ENABLED=true
ORCHESTRATION_FALLBACK_ENABLED=true

# Gemini API Keys for Orchestration
GEMINI_API_KEY=your_primary_gemini_key_here
GEMINI_API_KEY_BACKUP=your_backup_gemini_key_here

# Sub-agent URLs (point to your existing services)
TUTORBOT_URL=http://localhost:8001
EMOTIONAL_WELLNESS_BOT_URL=http://localhost:8002
FINANCIAL_WELLNESS_BOT_URL=http://localhost:8003
QUIZBOT_URL=http://localhost:8004

# Trigger Thresholds
LOW_QUIZ_SCORE_THRESHOLD=60
WELLNESS_CONCERN_THRESHOLD=3
INACTIVITY_DAYS_THRESHOLD=7

# Vector Store Settings
CHUNK_SIZE=500
CHUNK_OVERLAP=100
MAX_DOCUMENTS_PER_QUERY=5

# Integration Features
STORE_ENHANCED_LESSONS=true
AUTO_TRIGGER_INTERVENTIONS=true
ENABLE_PROGRESS_TRACKING=true

# Logging
LOG_ORCHESTRATION_CALLS=true
LOG_TRIGGER_EVENTS=true
"""

# Global configuration instance
config = OrchestrationConfig()

def get_config() -> OrchestrationConfig:
    """Get the global configuration instance"""
    return config

def validate_integration_setup() -> Dict[str, Any]:
    """Validate the complete integration setup"""
    config_validation = config.validate_config()
    
    # Additional checks
    integration_status = {
        **config_validation,
        "base_backend_ready": True,  # Assume Base_backend is ready
        "orchestration_path_exists": os.path.exists("../orchestration/unified_orchestration_system"),
        "mongodb_configured": bool(os.getenv("MONGO_URI")),
        "llm_service_available": bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"))
    }
    
    return integration_status

if __name__ == "__main__":
    # Test configuration
    print("🔧 Orchestration Integration Configuration")
    print("=" * 50)
    
    validation = validate_integration_setup()
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    print("\n📋 Environment Template:")
    print(config.get_environment_template())
