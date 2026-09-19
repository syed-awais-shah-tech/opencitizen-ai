# OpenCitizen AI - Test & Validation Script (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==> Running OpenCitizen AI Test Suite..." -ForegroundColor Cyan

# 1. Backend Tests
Write-Host "`n[1/2] Running Backend Unit & Integration Tests..." -ForegroundColor Yellow
& "backend\.venv\Scripts\pytest" backend/tests tests/backend -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend tests failed!" -ForegroundColor Red
    exit 1
}

# 2. Frontend Validation
Write-Host "`n[2/2] Running Frontend Validation (TypeScript / Build Check)..." -ForegroundColor Yellow
Push-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "Frontend build validation failed!" -ForegroundColor Red
    exit 1
}
Pop-Location

Write-Host "`n==> All checks passed successfully!" -ForegroundColor Green
