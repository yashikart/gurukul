@echo off
echo ========================================
echo    Gurukul Unified Agent Mind
echo    Starting All Backend Services
echo ========================================
echo.

REM Set the base directory
set BASE_DIR=%~dp0

REM Activate virtual environment
echo 🔧 Activating virtual environment...
if exist "%BASE_DIR%..\..\venv\Scripts\activate.bat" (
    call "%BASE_DIR%..\..\venv\Scripts\activate.bat"
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  Virtual environment not found at %BASE_DIR%..\..\venv
    echo    Services may fail if dependencies are not installed globally
)
echo.

echo 🚀 Starting all backend services with orchestration...
echo.

REM Check and install critical dependencies
echo 📦 Checking critical dependencies...
python -c "import fastapi" 2>nul || (
    echo ⚠️  Installing missing fastapi dependency...
    pip install fastapi>=0.95.0 uvicorn>=0.20.0 --quiet
)

python -c "import langchain_groq" 2>nul || (
    echo ⚠️  Installing missing langchain_groq dependency...
    pip install langchain>=0.1.0 langchain-groq>=0.1.0 langgraph>=0.0.30 --quiet
)

python -c "import prophet" 2>nul || (
    echo ⚠️  Installing missing prophet dependency...
    pip install prophet>=1.1.4 --quiet
)

echo ✅ Dependencies checked
echo.

REM Start Base Backend with Orchestration (Port 8000) - Main API using uvicorn
echo 🏠 Starting Base Backend with Orchestration on port 8000 (uvicorn)...
rem Run from project root so module path Backend.Base_backend.api resolves correctly
start "Base Backend (Main API)" cmd /k "cd /d %BASE_DIR%.. && python -m uvicorn Backend.Base_backend.api:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 4 /nobreak >nul

REM Start Dedicated Chatbot Service (Port 8001) - ONLY service on 8001
echo 🤖 Starting Dedicated Chatbot Service on port 8001...
start "Chatbot Service" cmd /k "cd /d %BASE_DIR%dedicated_chatbot_service && python chatbot_api.py"
timeout /t 3 /nobreak >nul

REM API Data Service disabled to avoid port conflict (was using 8001, now would use 8011)
REM Uncomment below if API Data service is needed on port 8011
REM echo 📊 Starting API Data Service on port 8011...
REM start "API Data Service" cmd /k "cd /d %BASE_DIR%api_data && set PORT=8011 && python api.py"
REM timeout /t 3 /nobreak >nul

REM Start Financial Simulator (Port 8002)
echo 💰 Starting Financial Simulator on port 8002...
start "Financial Simulator" cmd /k "cd /d %BASE_DIR%Financial_simulator\Financial_simulator && python langgraph_api.py"
timeout /t 3 /nobreak >nul

REM Start Memory Management API (Port 8003)
echo 📝 Starting Memory Management API on port 8003...
start "Memory Management API" cmd /k "cd /d %BASE_DIR%memory_management && python run_server.py"
timeout /t 3 /nobreak >nul

REM Start Akash Service (Port 8004)
echo 🧠 Starting Akash Service on port 8004...
start "Akash Service" cmd /k "cd /d %BASE_DIR%akash && python main.py"
timeout /t 3 /nobreak >nul

REM Start Subject Generation Service (Port 8005)
echo 📖 Starting Subject Generation Service on port 8005...
start "Subject Generation" cmd /k "cd /d %BASE_DIR%subject_generation && python app.py"
timeout /t 3 /nobreak >nul

REM Start Wellness API with Advanced Forecasting (Port 8006)
echo 🧘🔮 Starting Wellness API with Advanced Forecasting on port 8006...
start "Wellness API + Forecasting" cmd /k "cd /d %BASE_DIR%orchestration\unified_orchestration_system && python simple_api.py --port 8006"
timeout /t 4 /nobreak >nul

REM Start TTS Service (Port 8007)
echo 🔊 Starting TTS Service on port 8007...
start "TTS Service" cmd /k "cd /d %BASE_DIR%tts_service && python tts.py"
timeout /t 3 /nobreak >nul

echo.
echo ✅ All 7 backend services are starting...
echo.
echo 🌐 Service URLs:
echo    Base Backend (Main API):     http://localhost:8000/health
echo    Chatbot Service:             http://localhost:8001/health
echo    Financial Simulator:         http://localhost:8002/health
echo    Memory Management API:       http://localhost:8003/memory/health
echo    Akash Service:               http://localhost:8004/health
echo    Subject Generation:          http://localhost:8005/health
echo    Wellness API + Forecasting:  http://localhost:8006/
echo    TTS Service:                 http://localhost:8007/api/health
echo.
echo ⚠️  IMPORTANT: Do NOT start additional ngrok agents (free plan = 1 agent limit)
echo    Use START_NGROK_CORRECT_PORT.bat to start ngrok on port 8001
echo.
echo 📋 Next Steps:
echo    1. Wait 20-30 seconds for all services to start
echo    2. Run START_NGROK_CORRECT_PORT.bat in a separate window
echo    3. Copy ngrok URL and update Backend\.env NGROK_URL
echo    4. Update "new frontend\.env.local" with same ngrok URL
echo    5. Restart backend and frontend to pick up new URL
echo    6. Open http://localhost:5173 in your browser
echo.
echo 🔧 To stop all services: Close all the opened terminal windows
echo.
pause
