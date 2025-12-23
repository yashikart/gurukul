@echo off
REM Setup script for downloading Arabic model checkpoint during deployment
REM Windows version for local testing

echo ==========================================
echo Arabic Model Checkpoint Setup
echo ==========================================

REM Check if checkpoint download is needed
if "%LOCAL_MODEL_CHECKPOINT_PATH%"=="" (
    set LOCAL_MODEL_CHECKPOINT_PATH=%TEMP%\checkpoints\checkpoint-100000
)

REM Check if checkpoint already exists
if exist "%LOCAL_MODEL_CHECKPOINT_PATH%\adapter_model.safetensors" (
    echo Checkpoint already exists at %LOCAL_MODEL_CHECKPOINT_PATH%
    exit /b 0
)

echo Checkpoint not found. Attempting download...

REM Navigate to Base_backend directory
cd /d "%~dp0Base_backend"

REM Run download script
python download_checkpoint.py

if %errorlevel% equ 0 (
    echo Checkpoint setup completed successfully
    exit /b 0
) else (
    echo Checkpoint download failed or not configured
    echo The Arabic model will use fallback providers (Groq/OpenAI)
    exit /b 0
)









