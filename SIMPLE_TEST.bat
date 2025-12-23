@echo off
echo Testing Services...
netstat -ano | findstr ":8000 :8001 :8007"
echo.
powershell -Command "$h=@{'Origin'='https://c7d82cf2656d.ngrok-free.app';'Access-Control-Request-Method'='GET'};$r=Invoke-WebRequest -Uri 'http://localhost:8001/chatbot' -Method Options -Headers $h -UseBasicParsing -TimeoutSec 10;Write-Host 'Status:'$r.StatusCode;Write-Host 'CORS:'$r.Headers['Access-Control-Allow-Origin']"
pause
