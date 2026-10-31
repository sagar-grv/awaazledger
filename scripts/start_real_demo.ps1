# Start AwaazLedger in Real WhatsApp + Real Sarvam AI Mode
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Starting AwaazLedger Real WhatsApp + Sarvam AI Stack" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Verify Docker is running
try {
    docker info > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker is not running. Please start Docker Desktop and retry." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Docker command not found. Please install/start Docker." -ForegroundColor Red
    exit 1
}

# 2. Prepare .env.real
if (-not (Test-Path ".env.real")) {
    Write-Host "Copying .env.real.example to .env.real..." -ForegroundColor Yellow
    Copy-Item ".env.real.example" ".env.real"
    Write-Host "[NOTE] Created .env.real. Update credentials if you have live Sarvam/Evolution keys." -ForegroundColor Yellow
}

# 3. Spin up Docker containers
Write-Host "Building and launching containers via Docker Compose..." -ForegroundColor Green
docker compose -f docker-compose.real.yml up --build -d

# 4. Wait for backend to be healthy
Write-Host "Verifying backend health..." -ForegroundColor Green
python scripts/wait_for_backend.py

# 5. Setup Evolution WhatsApp Instance & Webhooks
Write-Host "Configuring Evolution API instance & webhooks..." -ForegroundColor Green
python scripts/setup_evolution_instance.py

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  AwaazLedger Real Stack is Live!" -ForegroundColor Green
Write-Host "  - Evolution API : http://localhost:8080" -ForegroundColor White
Write-Host "  - Backend API   : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Admin UI      : http://localhost:5173" -ForegroundColor White
Write-Host "  - QR Code       : dist/evolution_qr.png" -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan
