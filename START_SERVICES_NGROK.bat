@echo off
echo Starting Gurukul Services with Logging...
cd /d "%~dp0"

start "Gateway-8000" powershell -NoExit -Command "cd '%CD%\Backend'; pip install -r requirements.txt 2>&1 | Out-Null; python main.py 2>&1 | Tee-Object -FilePath '%CD%\logs\gateway.log'"

start "Chatbot-8001" powershell -NoExit -Command "cd '%CD%\Backend\dedicated_chatbot_service'; pip install -r requirements.txt 2>&1 | Out-Null; python chatbot_api.py 2>&1 | Tee-Object -FilePath '%CD%\logs\chatbot.log'"

start "TTS-8007" powershell -NoExit -Command "cd '%CD%\Backend\tts_service'; pip install -r requirements.txt 2>&1 | Out-Null; python tts.py 2>&1 | Tee-Object -FilePath '%CD%\logs\tts.log'"

echo Services starting... Check individual windows for status
echo Logs: logs\gateway.log, logs\chatbot.log, logs\tts.log
