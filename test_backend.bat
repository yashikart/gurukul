@echo off
echo Testing Backend Services...
echo.

echo Testing Port 8000 (Base Backend):
curl -s http://localhost:8000/health || echo Not responding

echo.
echo Testing Port 8006 (Wellness API):
curl -s http://localhost:8006/ || echo Not responding

echo.
echo Testing Port 8002 (Financial Simulator):
curl -s http://localhost:8002/health || echo Not responding

echo.
pause
