#!/usr/bin/env bash
set -e

echo "================================================================="
echo "  Starting AwaazLedger Real WhatsApp + Sarvam AI Stack"
echo "================================================================="

if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker daemon is not running. Please start Docker and retry."
    exit 1
fi

if [ ! -f ".env.real" ]; then
    echo "Copying .env.real.example to .env.real..."
    cp .env.real.example .env.real
    echo "[NOTE] Created .env.real. Please configure keys as needed."
fi

echo "Building and launching containers via Docker Compose..."
docker compose -f docker-compose.real.yml up --build -d

echo "Verifying backend health..."
python scripts/wait_for_backend.py

echo "Configuring Evolution API instance & webhooks..."
python scripts/setup_evolution_instance.py

echo "================================================================="
echo "  AwaazLedger Real Stack is Live!"
echo "  - Evolution API : http://localhost:8080"
echo "  - Backend API   : http://localhost:8000/docs"
echo "  - Admin UI      : http://localhost:5173"
echo "  - QR Code       : dist/evolution_qr.png"
echo "================================================================="
