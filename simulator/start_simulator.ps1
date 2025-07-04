# Tello UDP Simulator Launcher
# PowerShell script to start the UDP-based drone simulator

Write-Host ""
Write-Host "🚁 Tello UDP Simulator" -ForegroundColor Green
Write-Host "=====================" -ForegroundColor Green
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
if (-not (Test-Path "udp_simulator.py")) {
    Write-Host "❌ Simulator files not found!" -ForegroundColor Red
    Write-Host "📂 Please run this script from the simulator directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "🚀 Starting UDP simulator..." -ForegroundColor Cyan
Write-Host ""

# Start the UDP simulator
try {
    python start_udp_simulator.py
} catch {
    Write-Host ""
    Write-Host "❌ Failed to start simulator: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
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
