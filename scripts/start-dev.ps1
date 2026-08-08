$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "backend"
$frontendRoot = Join-Path $projectRoot "frontend"
$runtimeRoot = Join-Path $projectRoot ".runtime"
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

$backendOut = Join-Path $runtimeRoot "backend.stdout.log"
$backendErr = Join-Path $runtimeRoot "backend.stderr.log"
$backend = Start-Process `
    -FilePath "py" `
    -ArgumentList "-3.13", "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $backendRoot `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendErr `
    -WindowStyle Hidden `
    -PassThru

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($backend.HasExited) {
            throw "FastAPI exited early. See $backendErr"
        }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 1
            if ($health.status -eq "ok") {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 300
        }
    }
    if (-not $ready) {
        throw "FastAPI did not become healthy. See $backendErr"
    }

    Write-Host "Backend ready: http://127.0.0.1:8000/docs" -ForegroundColor Green
    Write-Host "Starting React: http://localhost:5173 (Ctrl+C stops both)" -ForegroundColor Green
    Push-Location $frontendRoot
    try {
        npm run dev
    } finally {
        Pop-Location
    }
} finally {
    if (-not $backend.HasExited) {
        Stop-Process -Id $backend.Id -Force
    }
}
