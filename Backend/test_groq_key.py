"""Test script to verify GROQ_API_KEY is loaded correctly"""
import os
import sys
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Load shared config
from shared_config import load_shared_config

print("=" * 60)
print("Testing GROQ_API_KEY Configuration")
print("=" * 60)

# Load configuration
success = load_shared_config("test")

# Get API key
api_key = os.getenv('GROQ_API_KEY', '').strip()

print(f"\n✅ Configuration loaded: {success}")
print(f"📋 GROQ_API_KEY present: {bool(api_key)}")
print(f"📏 API Key length: {len(api_key)}")
print(f"🔑 First 15 chars: {api_key[:15] if api_key else 'N/A'}...")
print(f"🔑 Last 10 chars: ...{api_key[-10:] if api_key else 'N/A'}")

if api_key:
    # Test API call
    print("\n🧪 Testing API call...")
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": "Say 'Hello' if you can read this."}
            ],
            "max_tokens": 10,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ API Test SUCCESS!")
            print(f"📝 Response: {content}")
        else:
            print(f"❌ API Test FAILED!")
            print(f"📄 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ API Test ERROR: {str(e)}")
else:
    print("\n❌ GROQ_API_KEY is not set!")

print("\n" + "=" * 60)
