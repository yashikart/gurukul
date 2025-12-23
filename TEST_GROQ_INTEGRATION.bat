@echo off
echo ════════════════════════════════════════════════════════════════
echo   TESTING GROQ INTEGRATION
echo ════════════════════════════════════════════════════════════════
echo.
echo This script will test if Groq API is working correctly
echo.

cd /d C:\Users\Microsoft\Documents\Gurukul_new-main
call venv\Scripts\activate.bat

cd Gurukul_new-main\Backend\Base_backend

echo 🧪 Testing LLM Service...
echo.
python -c "from llm_service import LLMService; service = LLMService(); print('Groq API Key:', 'SET' if service.groq_api_key else 'NOT SET'); result = service.call_groq_api('Hello'); print('Groq Test:', 'PASSED' if result['success'] else 'FAILED -', result.get('error', 'Unknown error'))"

echo.
echo ════════════════════════════════════════════════════════════════
echo   TEST COMPLETE
echo ════════════════════════════════════════════════════════════════
echo.
pause
