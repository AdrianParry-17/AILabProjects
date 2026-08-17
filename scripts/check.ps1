$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$testTemp = Join-Path $projectRoot ".tmp\pytest"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $testTemp) | Out-Null

Write-Host "[1/4] Backend tests + coverage" -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "backend")
try {
    py -3.13 -m pytest -q -p no:cacheprovider --basetemp $testTemp --cov=app --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) {
        throw "Backend tests failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Write-Host "[2/4] Frontend contract tests" -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "frontend")
try {
    npm test
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend contract tests failed with exit code $LASTEXITCODE."
    }

    Write-Host "[3/4] TypeScript + production bundle" -ForegroundColor Cyan
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend production build failed with exit code $LASTEXITCODE."
    }

    Write-Host "[4/4] Microsoft Edge end-to-end smoke" -ForegroundColor Cyan
    npm run test:e2e
    if ($LASTEXITCODE -ne 0) {
        throw "End-to-end tests failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

Write-Host "All checks passed." -ForegroundColor Green
