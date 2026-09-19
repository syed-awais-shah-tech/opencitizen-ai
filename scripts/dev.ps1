# OpenCitizen AI - Local Development Runner (PowerShell)
Write-Host "==> Launching OpenCitizen AI Development Services..." -ForegroundColor Cyan

Write-Host "Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "backend\.venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app", "--reload", "--port", "8000" -WorkingDirectory "backend" -PassThru

Write-Host "Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow
Push-Location frontend
npm run dev
Pop-Location

# Cleanup on exit
Stop-Process -Id $backendProcess.Id -Force
