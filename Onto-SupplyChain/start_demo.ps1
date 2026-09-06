$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

if ($args -contains "-Seed") {
    Write-Host "Seeding demo database..." -ForegroundColor Cyan
    Set-Location $backendPath
    python scripts/seed_demo_data.py
}

Write-Host "Starting backend on http://127.0.0.1:5000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; python app.py"

Write-Host "Starting frontend on http://127.0.0.1:5173" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev"

Write-Host "Demo startup commands launched." -ForegroundColor Yellow
