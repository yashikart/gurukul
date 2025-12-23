@echo off
REM Export to Core Telemetry Bridge Script (Windows Version)
REM This script exports daily audit snapshots for verifiable telemetry

REM Set variables
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR:~0,-9%
set EXPORT_DIR=%PROJECT_ROOT%\exports

REM Create exports directory if it doesn't exist
if not exist "%EXPORT_DIR%" mkdir "%EXPORT_DIR%"

REM Log start time
echo [%date% %time%] Starting daily telemetry export...

REM Run the export script
cd /d "%PROJECT_ROOT%"
python -c "import sys; import os; sys.path.append(os.path.join(os.path.dirname(__file__), '.')); from utils.audit_enhancer import auto_export_telemetry_feed; try: filepath = auto_export_telemetry_feed(); print(f'Export completed successfully: {filepath}'); except Exception as e: print(f'Error during export: {e}'); sys.exit(1)"

REM Check if the export was successful
if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Daily telemetry export completed successfully
    
    REM Show file info
    set EXPORT_FILE=%EXPORT_DIR%\core_telemetry_bridge.json
    if exist "%EXPORT_FILE%" (
        for %%A in ("%EXPORT_FILE%") do set FILE_SIZE=%%~zA
        echo Export file: %EXPORT_FILE%
        echo File size: %FILE_SIZE% bytes
        echo Entries exported: Check file content
    )
) else (
    echo [%date% %time%] Daily telemetry export failed
    exit /b 1
)

echo [%date% %time%] Export process finished