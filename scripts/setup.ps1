$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "[1/2] Installing backend dependencies for Python 3.13..." -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "backend")
try {
    py -3.13 -m pip install -r requirements.txt
} finally {
    Pop-Location
}

Write-Host "[2/2] Installing frontend dependencies..." -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "frontend")
try {
    npm install
} finally {
    Pop-Location
}

Write-Host "Setup complete. Run scripts/start-dev.ps1 next." -ForegroundColor Green
