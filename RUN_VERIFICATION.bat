@echo off
echo ========================================
echo Running Verification Tests
echo ========================================
echo.

cd /d "%~dp0"

echo [1] Port Status:
netstat -ano | findstr ":8000 :8001 :8007"
echo.

echo [2] CORS Preflight Test (Chatbot):
powershell -Command "$h=@{'Origin'='https://c7d82cf2656d.ngrok-free.app';'Access-Control-Request-Method'='GET'};try{$r=Invoke-WebRequest -Uri 'http://localhost:8001/chatbot' -Method Options -Headers $h -UseBasicParsing -TimeoutSec 15;Write-Host 'Status:'$r.StatusCode;Write-Host 'Allow-Origin:'$r.Headers['Access-Control-Allow-Origin'];Write-Host 'Allow-Methods:'$r.Headers['Access-Control-Allow-Methods'];Write-Host 'Allow-Credentials:'$r.Headers['Access-Control-Allow-Credentials']}catch{Write-Host 'FAILED:'$_.Exception.Message}"
echo.

echo [3] TTS Health:
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8007/api/health' -TimeoutSec 10|ConvertTo-Json -Compress}catch{Write-Host 'FAILED:'$_.Exception.Message}"
echo.

echo [4] Chatbot Health:
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8001/health' -TimeoutSec 15|ConvertTo-Json -Compress}catch{Write-Host 'FAILED:'$_.Exception.Message}"
echo.

echo [5] Gateway Health:
powershell -Command "try{Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 10|ConvertTo-Json -Compress}catch{Write-Host 'FAILED:'$_.Exception.Message}"
echo.

echo ========================================
echo Verification Complete
echo ========================================
pause
