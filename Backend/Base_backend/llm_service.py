"""
Enhanced LLM Service with multiple providers and fallback support
Supports: Groq, OpenAI, OpenRouter, Local Arabic Model, and local fallback responses
"""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import local model service (may fail if dependencies not installed)
try:
    from local_model_service import get_local_model
    LOCAL_MODEL_AVAILABLE = True
except ImportError as e:
    LOCAL_MODEL_AVAILABLE = False
    logger.warning(f"Local model service not available: {e}")

# Try to import YouTube helper
try:
    from youtube_helper import append_youtube_links
    YOUTUBE_HELPER_AVAILABLE = True
except ImportError as e:
    YOUTUBE_HELPER_AVAILABLE = False
    logger.warning(f"YouTube helper not available: {e}")

class LLMService:
    """Enhanced LLM service with multiple providers and fallback"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY', '').strip("'\"")
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '').strip("'\"")
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY', '').strip("'\"")
        
        # Initialize local model (lazy loaded, won't load until first use)
        self.local_model = None
        if LOCAL_MODEL_AVAILABLE:
            try:
                # Get checkpoint path from environment or use default
                checkpoint_path = os.getenv('LOCAL_MODEL_CHECKPOINT_PATH', None)
                self.local_model = get_local_model(checkpoint_path)
                logger.info("✅ Local Arabic model service initialized (lazy loading)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize local model: {e}")
                self.local_model = None
        
        # Provider priority order (local model after API providers, before fallback)
        self.providers = ['openrouter', 'groq', 'openai', 'local', 'fallback']
        
        # Model configurations - Updated for new ngrok endpoint
        self.models = {
            'openrouter': {
                'default': 'meta-llama/llama-3.1-8b-instruct:free',
                'alternatives': ['google/gemma-2-9b-it:free', 'mistralai/mistral-7b-instruct:free']
            },
            'groq': {
                'default': 'llama-3.3-70b-versatile',
                'alternatives': ['llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'llama3-8b-8192']
            },
            'openai': {
                'default': 'gpt-3.5-turbo',
                'alternatives': ['gpt-4', 'gpt-4-turbo-preview']
            }
        }
    
    def call_groq_api(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Call Groq API with improved error handling"""
        
        if not self.groq_api_key:
            return {"success": False, "error": "No Groq API key configured"}
        
        # Use real Groq API endpoint
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model = model or os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2048,  # Increased for in-depth content
            "top_p": 1.0
        }

        try:
            logger.info(f"Calling new ngrok API endpoint: {api_url}")
            logger.info(f"Model: {model}")
            logger.info(f"Prompt: {prompt[:100]}...")
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=180  # Increased timeout to 3 minutes for slow ngrok
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                logger.info("✅ Groq API call successful")
                return {
                    "success": True,
                    "content": content,
                    "provider": "groq",
                    "model": model
                }
            
            elif response.status_code == 401:
                logger.error("❌ Groq API: Invalid or expired API key")
                return {"success": False, "error": "Invalid Groq API key"}
            
            elif response.status_code == 429:
                logger.error("⚠️ Groq API: Rate limit exceeded")
                return {"success": False, "error": "Groq rate limit exceeded"}
            
            else:
                logger.error(f"❌ Groq API error: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Groq API error: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            logger.error("⏰ Groq API timeout")
            return {"success": False, "error": "Groq API timeout"}
            
        except requests.exceptions.ConnectionError:
            logger.error("🌐 Groq API connection error")
            return {"success": False, "error": "Groq API connection error"}
            
        except Exception as e:
            logger.error(f"❌ Groq API unexpected error: {e}")
            return {"success": False, "error": f"Groq API error: {str(e)}"}
    
    def call_openrouter_api(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Call OpenRouter API - supports free models"""
        
        if not self.openrouter_api_key:
            return {"success": False, "error": "No OpenRouter API key configured"}
        
        model = model or self.models['openrouter']['default']
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Gurukul Learning Platform"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            logger.info(f"Calling OpenRouter API with model: {model}")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                logger.info("✅ OpenRouter API call successful")
                return {
                    "success": True,
                    "content": content,
                    "provider": "openrouter",
                    "model": model
                }
            
            else:
                logger.error(f"❌ OpenRouter API error: {response.status_code}")
                return {"success": False, "error": f"OpenRouter API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ OpenRouter API error: {e}")
            return {"success": False, "error": f"OpenRouter API error: {str(e)}"}
    
    def call_openai_api(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Call OpenAI API as fallback"""
        
        if not self.openai_api_key:
            return {"success": False, "error": "No OpenAI API key configured"}
        
        model = model or self.models['openai']['default']
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        try:
            logger.info(f"Calling OpenAI API with model: {model}")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                logger.info("✅ OpenAI API call successful")
                return {
                    "success": True,
                    "content": content,
                    "provider": "openai",
                    "model": model
                }
            
            else:
                logger.error(f"❌ OpenAI API error: {response.status_code}")
                return {"success": False, "error": f"OpenAI API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return {"success": False, "error": f"OpenAI API error: {str(e)}"}
    
    def call_local_model(self, prompt: str) -> Dict[str, Any]:
        """Call local Arabic model for inference"""
        
        if not LOCAL_MODEL_AVAILABLE or self.local_model is None:
            return {
                "success": False,
                "error": "Local model not available (dependencies not installed or initialization failed)"
            }
        
        try:
            logger.info("🤖 Calling local Arabic model...")
            logger.info(f"Prompt: {prompt[:100]}...")
            
            # Generate response using local model
            # Optimized parameters for speed while maintaining quality
            # Match test script performance: 150 tokens, temp 0.7 for faster generation
            response_text = self.local_model.generate(
                prompt=prompt,
                max_new_tokens=200,   # Balanced: faster than 256, more complete than 150
                temperature=0.5,      # Balanced: faster than 0.3, still accurate
                top_p=0.9             # Match test script for consistency
            )
            
            # Post-process: Append YouTube links if requested
            if YOUTUBE_HELPER_AVAILABLE:
                try:
                    response_text = append_youtube_links(response_text, prompt)
                    logger.info("✅ YouTube links appended to response")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to append YouTube links: {e}")
            
            logger.info("✅ Local model inference successful")
            return {
                "success": True,
                "content": response_text,
                "provider": "local",
                "model": "arabic-llama-3.2-3b"
            }
            
        except RuntimeError as e:
            logger.error(f"❌ Local model runtime error: {e}")
            return {
                "success": False,
                "error": f"Local model error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Local model unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Local model error: {str(e)}"
            }
    
    def get_fallback_response(self, prompt: str) -> Dict[str, Any]:
        """Generate fallback response when APIs are unavailable"""
        
        # Simple keyword-based responses
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            content = "Hello! I'm your AI assistant. How can I help you today? (Note: I'm currently running in fallback mode as the main AI services are temporarily unavailable.)"
        
        elif any(word in prompt_lower for word in ['how are you', 'how do you do']):
            content = "I'm doing well, thank you for asking! I'm here to help you with any questions you might have. How can I assist you today?"
        
        elif any(word in prompt_lower for word in ['help', 'assist', 'support']):
            content = "I'm here to help! I can assist you with various topics including education, general questions, and guidance. What would you like to know about?"
        
        elif any(word in prompt_lower for word in ['thank', 'thanks']):
            content = "You're very welcome! I'm glad I could help. Is there anything else you'd like to know?"
        
        elif any(word in prompt_lower for word in ['bye', 'goodbye', 'see you']):
            content = "Goodbye! It was nice chatting with you. Feel free to come back anytime if you have more questions!"
        
        else:
            content = f"I understand you're asking about '{prompt[:50]}...'. While I'm currently in fallback mode, I'd be happy to help once our main AI services are restored. In the meantime, could you please rephrase your question or try again later?"
        
        logger.info("📝 Using fallback response")
        return {
            "success": True,
            "content": content,
            "provider": "fallback",
            "model": "rule-based"
        }
    
    def generate_response(self, prompt: str, preferred_provider: str = None) -> str:
        """
        Generate response with automatic fallback between providers
        
        Args:
            prompt: User input text
            preferred_provider: 'groq', 'openai', 'openrouter', 'local', or None for auto
            
        Returns:
            Generated response text
        """
        
        providers_to_try = [preferred_provider] if preferred_provider else self.providers
        
        for provider in providers_to_try:
            if provider == 'openrouter':
                result = self.call_openrouter_api(prompt)
                if result["success"]:
                    return result["content"]
                logger.warning(f"OpenRouter failed: {result.get('error', 'Unknown error')}")
            
            elif provider == 'groq':
                result = self.call_groq_api(prompt)
                if result["success"]:
                    return result["content"]
                logger.warning(f"Groq failed: {result.get('error', 'Unknown error')}")
            
            elif provider == 'openai':
                result = self.call_openai_api(prompt)
                if result["success"]:
                    return result["content"]
                logger.warning(f"OpenAI failed: {result.get('error', 'Unknown error')}")
            
            elif provider == 'local':
                result = self.call_local_model(prompt)
                if result["success"]:
                    return result["content"]
                logger.warning(f"Local model failed: {result.get('error', 'Unknown error')}")
            
            elif provider == 'fallback':
                result = self.get_fallback_response(prompt)
                return result["content"]
        
        # Final fallback if everything fails
        return "I apologize, but I'm experiencing technical difficulties right now. Please try again in a few moments, or contact support if the issue persists."
    
    def test_providers(self) -> Dict[str, bool]:
        """Test all available providers"""
        
        test_prompt = "Hello"
        results = {}
        
        # Test OpenRouter
        openrouter_result = self.call_openrouter_api(test_prompt)
        results['openrouter'] = openrouter_result["success"]
        
        # Test Groq
        groq_result = self.call_groq_api(test_prompt)
        results['groq'] = groq_result["success"]
        
        # Test OpenAI
        openai_result = self.call_openai_api(test_prompt)
        results['openai'] = openai_result["success"]
        
        # Test Local Model
        if LOCAL_MODEL_AVAILABLE and self.local_model is not None:
            local_result = self.call_local_model(test_prompt)
            results['local'] = local_result["success"]
        else:
            results['local'] = False
        
        # Fallback always works
        results['fallback'] = True
        
        return results

# Global instance
llm_service = LLMService()

# Backward compatibility function
def call_groq_llama3(prompt: str) -> str:
    """Backward compatible function with enhanced capabilities"""
    return llm_service.generate_response(prompt)

# Test function
if __name__ == "__main__":
    service = LLMService()
    
    print("🧪 Testing LLM Service...")
    test_results = service.test_providers()
    
    for provider, status in test_results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {provider.capitalize()}: {'Working' if status else 'Failed'}")
    
    print("\n🗣️ Testing response generation...")
    response = service.generate_response("Hello, how are you?")
    print(f"Response: {response}")
