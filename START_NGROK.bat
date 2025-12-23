@echo off
echo Starting Ngrok Tunnels...
start "Ngrok-8001" cmd /k "ngrok http 8001 --region=in --host-header=localhost"
timeout /t 2 /nobreak >nul
start "Ngrok-8007" cmd /k "ngrok http 8007 --region=in --host-header=localhost"
echo Ngrok tunnels starting... Check windows for URLs
