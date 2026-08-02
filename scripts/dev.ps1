# scripts/dev.ps1
param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "backend/.env") -and (Test-Path "backend/.env.example")) {
    Write-Host "--> Copying backend/.env.example to backend/.env" -ForegroundColor Cyan
    Copy-Item "backend/.env.example" "backend/.env"
}

if (-not (Test-Path "frontend/.env") -and (Test-Path "frontend/.env.example")) {
    Write-Host "--> Copying frontend/.env.example to frontend/.env" -ForegroundColor Cyan
    Copy-Item "frontend/.env.example" "frontend/.env"
}

$pnpmCmd = if (Get-Command pnpm -ErrorAction SilentlyContinue) { "pnpm" } else { "npx -y pnpm" }

if ($Check) {
    Write-Host "==> Checking backend (ruff lint)..." -ForegroundColor Green
    Push-Location backend
    try {
        uv run --locked --no-sync ruff check .
    } finally {
        Pop-Location
    }

    Write-Host "==> Checking frontend (typecheck & production build)..." -ForegroundColor Green
    Push-Location frontend
    try {
        if ($pnpmCmd -eq "pnpm") { pnpm run build } else { npx -y pnpm run build }
    } finally {
        Pop-Location
    }

    Write-Host "==> All checks passed!" -ForegroundColor Green
    exit 0
}

Write-Host "==> Starting Backend (FastAPI)..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD/backend"
    uv run --locked --no-sync uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}

Write-Host "==> Starting Frontend (Vite)..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PWD/frontend"
    if ($using:pnpmCmd -eq "pnpm") { pnpm dev } else { npx -y pnpm dev }
}

Write-Host "==> Both backend and frontend services are running." -ForegroundColor Green
Write-Host "==> Press Ctrl+C to stop services." -ForegroundColor Yellow

try {
    while ($true) {
        Receive-Job -Job $backendJob -ErrorAction SilentlyContinue
        Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`n==> Stopping background jobs..." -ForegroundColor Red
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "==> Services stopped." -ForegroundColor Red
}
