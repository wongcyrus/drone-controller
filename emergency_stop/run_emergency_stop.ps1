#!/usr/bin/env powershell
Write-Host "Starting Emergency Stop GUI..." -ForegroundColor Green
Write-Host ""
Write-Host "This GUI provides an emergency stop button for drone operations." -ForegroundColor Yellow
Write-Host "Keep this window open while running drone scripts." -ForegroundColor Yellow
Write-Host ""

# Try to install psutil if needed (optional for better process detection)
try {
    pip install psutil 2>$null
} catch {
    # Ignore errors
}

# Run the emergency stop GUI
python emergency_stop_ui.py

Write-Host ""
Write-Host "Emergency Stop GUI closed." -ForegroundColor Green
Read-Host "Press Enter to exit"
