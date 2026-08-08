$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$testTemp = Join-Path $projectRoot ".tmp\pytest"

Write-Host "[1/4] Backend tests + coverage" -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "backend")
try {
    py -3.13 -m pytest -q -p no:cacheprovider --basetemp $testTemp --cov=app --cov-report=term-missing
} finally {
    Pop-Location
}

Write-Host "[2/4] Frontend contract tests" -ForegroundColor Cyan
Push-Location (Join-Path $projectRoot "frontend")
try {
    npm test
    Write-Host "[3/4] TypeScript + production bundle" -ForegroundColor Cyan
    npm run build
    Write-Host "[4/4] Microsoft Edge end-to-end smoke" -ForegroundColor Cyan
    npm run test:e2e
} finally {
    Pop-Location
}

Write-Host "All checks passed." -ForegroundColor Green
