# Drone Simulator 3D Launcher
# PowerShell script to start the drone simulator

Write-Host ""
Write-Host "🚁 Drone Simulator 3D" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.7 or higher." -ForegroundColor Red
    Write-Host "📥 Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "index.html")) {
    Write-Host "❌ Simulator files not found!" -ForegroundColor Red
    Write-Host "📂 Please run this script from the simulator directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "🚀 Starting simulator..." -ForegroundColor Cyan
Write-Host ""

# Try to start with Python bridge
try {
    python start_simulator.py
} catch {
    Write-Host ""
    Write-Host "⚠️  Python bridge failed. Opening simulator directly..." -ForegroundColor Yellow
    Write-Host ""

    # Fallback to opening HTML file directly
    Start-Process "index.html"
    Write-Host "🌐 Simulator opened in your default browser." -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Note: For full Python integration features, install:" -ForegroundColor Yellow
    Write-Host "   pip install websockets" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "✨ Simulator started successfully!" -ForegroundColor Green
Write-Host "🎮 Use the controls in the web interface to fly drones." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
