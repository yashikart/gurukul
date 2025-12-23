@echo off
echo ════════════════════════════════════════════════════════════════
echo   TESTING GROQ API DIRECTLY
echo ════════════════════════════════════════════════════════════════
echo.

cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat

cd Gurukul_new-main\Backend\dedicated_chatbot_service

echo 🧪 Testing Groq API integration...
echo.

python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); import requests; key = os.getenv('GROQ_API_KEY', '').strip(); print(f'Groq API Key: {\"SET (\" + key[:10] + \"...)\" if key else \"NOT SET\"}'); print(f'Model: {os.getenv(\"GROQ_MODEL_NAME\", \"llama-3.1-70b-versatile\")}'); print(); print('Testing API call...'); resp = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}, json={'model': os.getenv('GROQ_MODEL_NAME', 'llama-3.1-70b-versatile'), 'messages': [{'role': 'user', 'content': 'Say hello in one sentence'}], 'max_tokens': 50}, timeout=30); print(f'HTTP Status: {resp.status_code}'); print(f'Response: {resp.json()[\"choices\"][0][\"message\"][\"content\"] if resp.status_code == 200 else resp.text[:200]}')"

echo.
echo ════════════════════════════════════════════════════════════════
echo   TEST COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
pause
