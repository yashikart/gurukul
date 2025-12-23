# Gurukul Platform - Ngrok URL Updater (PowerShell Version)

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   Gurukul Platform - Ngrok URL Updater" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "Running ngrok URL updater..." -ForegroundColor Yellow
python update_ngrok_url.py

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")