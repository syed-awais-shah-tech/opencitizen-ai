# OpenCitizen AI - Automated Setup Script (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==> Setting up OpenCitizen AI development environment..." -ForegroundColor Cyan

# 1. Backend virtual environment
Write-Host "==> Initializing Python virtual environment in backend/.venv..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.venv")) {
    uv venv backend\.venv
}

# 2. Install backend packages
Write-Host "==> Installing backend dependencies..." -ForegroundColor Yellow
uv pip install -e "backend[dev]" --python backend\.venv

# 3. Frontend packages
Write-Host "==> Installing frontend npm dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host "==> Setup complete! Run .\scripts\test.ps1 to verify." -ForegroundColor Green
