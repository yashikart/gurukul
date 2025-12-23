@echo off
cd /d "%~dp0"
start "Chatbot-8001" cmd /k "cd Backend\dedicated_chatbot_service && python chatbot_api.py"
timeout /t 5 /nobreak >nul
start "Gateway-8000" cmd /k "cd Backend && python main.py"
timeout /t 10 /nobreak >nul
echo [Port Status]
netstat -ano | findstr ":8000 :8001 :8007"
echo.
echo [CORS Test]
powershell -Command "$h=@{'Origin'='https://c7d82cf2656d.ngrok-free.app';'Access-Control-Request-Method'='GET'};try{$r=Invoke-WebRequest -Uri 'http://localhost:8001/chatbot' -Method Options -Headers $h -UseBasicParsing;Write-Host 'Status:'$r.StatusCode;$r.Headers['Access-Control-Allow-Origin']}catch{Write-Host 'Error:'$_.Exception.Message}"
echo.
echo [Health Tests]
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8001/health'|ConvertTo-Json -Compress}catch{Write-Host '8001 Error:'$_.Exception.Message}"
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8000/health'|ConvertTo-Json -Compress}catch{Write-Host '8000 Error:'$_.Exception.Message}"
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8007/api/health'|ConvertTo-Json -Compress}catch{Write-Host '8007 Error:'$_.Exception.Message}"
pause
