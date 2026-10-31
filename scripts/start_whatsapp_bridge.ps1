# Starts the native AwaazLedger WhatsApp Bridge (Docker-free Evolution API drop-in)
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Starting Native WhatsApp Bridge (Zero Docker Required)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$bridgeDir = Join-Path $PSScriptRoot "..\whatsapp_bridge"
Set-Location $bridgeDir

Write-Host "Starting WhatsApp Gateway on port 8080..." -ForegroundColor Green
node server.js
