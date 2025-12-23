#!/usr/bin/env python3
"""
Ollama Client for Local LLM Integration
Provides a simple interface to interact with Ollama models for wellness responses
"""

import requests
import json
import logging
from typing import Optional, Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama local LLM models"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.1:latest)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = 60  # 60 seconds timeout
        
        # Test connection on initialization
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test if Ollama server is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Check if the preferred model is available, otherwise use the first available
                if self.model in model_names:
                    logger.info(f"✅ Ollama connection successful. Model '{self.model}' is available.")
                    return True
                elif model_names:
                    # Use the first available model as fallback
                    self.model = model_names[0]
                    logger.info(f"✅ Ollama connection successful. Using available model: '{self.model}'")
                    return True
                else:
                    logger.warning("⚠️  No models found in Ollama")
                    return False
            else:
                logger.error(f"❌ Ollama server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to Ollama server. Make sure Ollama is running.")
            return False
        except Exception as e:
            logger.error(f"❌ Error testing Ollama connection: {e}")
            return False
    
    def generate_wellness_response(self, query: str, user_context: Optional[Dict[str, Any]] = None, language: str = "english") -> Dict[str, Any]:
        """
        Generate a wellness response using Ollama
        
        Args:
            query: User's wellness query
            user_context: Optional context (mood_score, stress_level, etc.)
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Build the prompt with context and language
            prompt = self._build_wellness_prompt(query, user_context, language)
            
            # Make request to Ollama
            start_time = time.time()
            response = self._make_ollama_request(prompt)
            response_time = time.time() - start_time
            
            if response:
                return {
                    "success": True,
                    "response": response,
                    "model": self.model,
                    "response_time": round(response_time, 2),
                    "source": "ollama_local",
                    "timestamp": time.time()
                }
            else:
                return self._get_fallback_response(query)
                
        except Exception as e:
            logger.error(f"Error generating wellness response: {e}")
            return self._get_fallback_response(query)
    
    def _build_wellness_prompt(self, query: str, user_context: Optional[Dict[str, Any]] = None, language: str = "english") -> str:
        """Build a comprehensive wellness prompt"""
        
        base_prompt = """You are a compassionate wellness counselor and mental health assistant. Your role is to provide supportive, practical, and empathetic guidance to help people manage stress, improve their well-being, and develop healthy coping strategies.

Guidelines for your responses:
- Be warm, empathetic, and non-judgmental
- Provide practical, actionable advice
- Keep responses concise but comprehensive (2-4 paragraphs)
- Focus on evidence-based wellness strategies
- Encourage professional help when appropriate
- Use a supportive and encouraging tone

"""
        
        # Add user context if available
        if user_context:
            context_info = []
            if user_context.get('mood_score'):
                context_info.append(f"Current mood level: {user_context['mood_score']}/10")
            if user_context.get('stress_level'):
                context_info.append(f"Stress level: {user_context['stress_level']}/10")
            if user_context.get('user_id'):
                context_info.append(f"User ID: {user_context['user_id']}")
            
            if context_info:
                base_prompt += f"\nUser Context: {', '.join(context_info)}\n"
        
        base_prompt += f"\nUser Query: {query}\n\n"
        
        # Add language instruction if Arabic is selected
        if language.lower() == "arabic":
            base_prompt += "LANGUAGE REQUIREMENT: Generate the ENTIRE response in Arabic (العربية). All content must be in Arabic using proper Arabic script and formatting.\n\n"
        
        base_prompt += "Please provide a helpful wellness response:"
        
        return base_prompt
    
    def _make_ollama_request(self, prompt: str) -> Optional[str]:
        """Make a request to Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            logger.info(f"🤖 Sending request to Ollama model: {self.model}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                if generated_text:
                    logger.info(f"✅ Ollama response generated successfully ({len(generated_text)} chars)")
                    return generated_text
                else:
                    logger.warning("⚠️  Ollama returned empty response")
                    return None
            else:
                logger.error(f"❌ Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Ollama request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to Ollama server")
            return None
        except Exception as e:
            logger.error(f"❌ Error making Ollama request: {e}")
            return None
    
    def _get_fallback_response(self, query: str) -> Dict[str, Any]:
        """Return a fallback response when Ollama fails"""
        fallback_text = f"Thank you for reaching out about '{query}'. I'm currently experiencing technical difficulties with my AI system, but I want to help. Here are some general wellness suggestions: Take time for self-care, practice deep breathing, stay connected with supportive people, and remember that small steps can lead to big improvements. If you're experiencing serious concerns, please consider speaking with a healthcare professional."
        
        return {
            "success": False,
            "response": fallback_text,
            "model": "fallback",
            "response_time": 0,
            "source": "fallback",
            "timestamp": time.time(),
            "error": "Ollama service unavailable"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of Ollama service"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                
                # Test model availability
                model_available = self.model in model_names
                
                # Test generation capability
                test_response = self._make_ollama_request("Hello, this is a test.")
                generation_working = test_response is not None
                
                return {
                    "status": "healthy" if model_available and generation_working else "degraded",
                    "server_accessible": True,
                    "model_available": model_available,
                    "generation_working": generation_working,
                    "available_models": model_names,
                    "current_model": self.model,
                    "base_url": self.base_url
                }
            else:
                return {
                    "status": "unhealthy",
                    "server_accessible": False,
                    "error": f"Server returned {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "server_accessible": False,
                "error": str(e)
            }

# Convenience function for easy import
def create_ollama_client(model: str = "llama3.2:3b") -> OllamaClient:
    """Create and return an Ollama client instance"""
    return OllamaClient(model=model)

# Test function
if __name__ == "__main__":
    print("🧪 Testing Ollama Client...")
    
    client = OllamaClient()
    
    # Health check
    health = client.health_check()
    print(f"Health Status: {health}")
    
    # Test wellness response
    test_query = "I'm feeling overwhelmed with work and need some guidance"
    test_context = {"mood_score": 4, "stress_level": 8}
    
    print(f"\nTesting with query: '{test_query}'")
    result = client.generate_wellness_response(test_query, test_context)
    
    print(f"Success: {result['success']}")
    print(f"Model: {result['model']}")
    print(f"Response Time: {result['response_time']}s")
    print(f"Response: {result['response'][:200]}...")
