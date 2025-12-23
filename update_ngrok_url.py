#!/usr/bin/env python3
"""
Script to automatically update ngrok URLs in configuration files
and ensure Ollama integration works properly
"""

import os
import re
import sys
import requests
from pathlib import Path
from datetime import datetime
import argparse

def get_ngrok_url(auto_mode=False):
    """Get current ngrok URL from ngrok API or user input"""
    print("Getting current ngrok URL...")
    
    # Option 1: Try to get from ngrok API (if running locally)
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                # Get the first HTTPS tunnel
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        ngrok_url = tunnel.get('public_url')
                        print(f"Found ngrok URL from API: {ngrok_url}")
                        return ngrok_url
    except Exception as e:
        print(f"Could not get ngrok URL from API: {e}")
    
    # If in auto mode, return None to indicate failure
    if auto_mode:
        print("Auto mode: Could not detect ngrok URL automatically")
        return None
    
    # Option 2: Ask user for URL
    print("\nPlease enter your current ngrok URL (e.g., https://abcd1234.ngrok-free.app):")
    ngrok_url = input("Ngrok URL: ").strip()
    
    # Validate URL format
    if not ngrok_url.startswith('https://') or '.ngrok' not in ngrok_url:
        print("Invalid URL format. Please use format: https://abcd1234.ngrok-free.app")
        return None
    
    return ngrok_url

def update_frontend_env(ngrok_url):
    """Update frontend .env files with new ngrok URL"""
    frontend_path = Path("new frontend")
    
    # Update .env file
    env_file = frontend_path / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
        
        # Update all ngrok-related variables
        patterns = [
            (r'GROQ_API_ENDPOINT=(.*)', f'GROQ_API_ENDPOINT={ngrok_url}'),
            (r'UNIGURU_NGROK_ENDPOINT=(.*)', f'UNIGURU_NGROK_ENDPOINT={ngrok_url}'),
            (r'UNIGURU_API_BASE_URL=(.*)', f'UNIGURU_API_BASE_URL={ngrok_url}'),
            (r'ANIMATEDIFF_NGROK_ENDPOINT=(.*)', f'ANIMATEDIFF_NGROK_ENDPOINT={ngrok_url}'),
            (r'VITE_CHATBOT_API_URL=(.*)', f'VITE_CHATBOT_API_URL={ngrok_url}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        env_file.write_text(content, encoding='utf-8')
        print(f"✅ Updated {env_file}")
    
    # Update .env.local file
    env_local_file = frontend_path / ".env.local"
    if env_local_file.exists():
        content = env_local_file.read_text(encoding='utf-8')
        
        # Update all ngrok-related variables
        patterns = [
            (r'VITE_NGROK_URL=(.*)', f'VITE_NGROK_URL={ngrok_url}'),
            (r'VITE_CHAT_API_BASE_URL=(.*)', f'VITE_CHAT_API_BASE_URL={ngrok_url}'),
            (r'VITE_CHATBOT_API_URL=(.*)', f'VITE_CHATBOT_API_URL={ngrok_url}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        env_local_file.write_text(content, encoding='utf-8')
        print(f"✅ Updated {env_local_file}")

def update_backend_env(ngrok_url):
    """Update backend .env file with new ngrok URL"""
    backend_env_file = Path("Backend/.env")
    
    if backend_env_file.exists():
        content = backend_env_file.read_text(encoding='utf-8')
        
        # Update ngrok-related variables
        patterns = [
            (r'NGROK_URL=(.*)', f'NGROK_URL={ngrok_url}'),
            (r'UNIGURU_NGROK_ENDPOINT=\$\{NGROK_URL\}', 'UNIGURU_NGROK_ENDPOINT=${NGROK_URL}'),
            (r'UNIGURU_API_BASE_URL=\$\{NGROK_URL\}', 'UNIGURU_API_BASE_URL=${NGROK_URL}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        backend_env_file.write_text(content, encoding='utf-8')
        print(f"✅ Updated {backend_env_file}")

def test_ollama_connection():
    """Test Ollama connection and ensure it's working"""
    print("\n🧪 Testing Ollama connection...")
    
    try:
        # Try to import and test Ollama client
        sys.path.append(str(Path("Backend/orchestration/unified_orchestration_system").resolve()))
        from ollama_client import OllamaClient
        
        client = OllamaClient()
        health = client.health_check()
        
        print(f"Ollama Health Status: {health.get('status', 'unknown')}")
        print(f"Server Accessible: {health.get('server_accessible', False)}")
        print(f"Model Available: {health.get('model_available', False)}")
        print(f"Generation Working: {health.get('generation_working', False)}")
        
        if health.get('status') == 'healthy':
            print("✅ Ollama is working properly!")
            return True
        else:
            print("⚠️  Ollama has issues. Please check:")
            print("  1. Make sure Ollama is installed and running")
            print("  2. Check if the required model is pulled")
            print("  3. Verify the Ollama URL in config files")
            return False
            
    except ImportError:
        print("⚠️  Ollama client not found. Skipping Ollama test.")
        return False
    except Exception as e:
        print(f"❌ Error testing Ollama: {e}")
        return False

def main():
    """Main function to update ngrok URLs and test Ollama"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update ngrok URLs and test Ollama integration')
    parser.add_argument('--auto', action='store_true', help='Run in auto mode without user interaction')
    args = parser.parse_args()
    
    print("🔄 Ngrok URL Updater and Ollama Tester")
    print("=" * 50)
    
    # Get current ngrok URL
    ngrok_url = get_ngrok_url(auto_mode=args.auto)
    if not ngrok_url:
        if args.auto:
            print("❌ Could not get valid ngrok URL in auto mode")
            return 1
        else:
            print("❌ Could not get valid ngrok URL")
            return 1
    
    print(f"\nUsing ngrok URL: {ngrok_url}")
    
    # Update configuration files
    print("\n📝 Updating configuration files...")
    try:
        update_frontend_env(ngrok_url)
        update_backend_env(ngrok_url)
        print("✅ Configuration files updated successfully!")
    except Exception as e:
        print(f"❌ Error updating configuration files: {e}")
        return 1
    
    # Test Ollama connection
    test_ollama_connection()
    
    # Print summary
    print(f"\n📋 Summary:")
    print(f"  • Ngrok URL updated to: {ngrok_url}")
    print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  • Configuration files updated in both frontend and backend")
    print(f"\n🚀 You can now restart your services to use the new configuration!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())