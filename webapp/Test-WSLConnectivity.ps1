# Test WSL connectivity from Windows PowerShell
param(
    [int]$WebPort = 8000,
    [int]$WebSocketPort = 8766
)

Write-Host "Testing WSL Connectivity from Windows" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Get WSL IP
Write-Host "1. Getting WSL IP address..." -ForegroundColor Yellow
try {
    $WSL_IP = (wsl hostname -I).Trim()
    if ($WSL_IP -and $WSL_IP -ne "127.0.0.1") {
        Write-Host "   WSL IP: $WSL_IP" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Could not get valid WSL IP" -ForegroundColor Red
        Write-Host "   Try: wsl --shutdown, then restart WSL" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ✗ Failed to get WSL IP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test network connectivity
Write-Host "2. Testing network connectivity..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $WSL_IP -Count 1 -Quiet
    if ($ping) {
        Write-Host "   ✓ Network connectivity: OK" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Network connectivity: FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Network test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test Web Server
Write-Host "3. Testing port $WebPort (Web Server)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "http://${WSL_IP}:${WebPort}" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   ✓ Web Server: OK (Status: $($response.StatusCode))" -ForegroundColor Green
    $webServerOK = $true
} catch {
    Write-Host "   ✗ Web Server: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    $webServerOK = $false
}

Write-Host ""

# Test WebSocket Port
Write-Host "4. Testing port $WebSocketPort (WebSocket)..." -ForegroundColor Yellow
try {
    $connection = Test-NetConnection -ComputerName $WSL_IP -Port $WebSocketPort -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "   ✓ WebSocket Port: OK" -ForegroundColor Green
        $webSocketOK = $true
    } else {
        Write-Host "   ✗ WebSocket Port: FAILED" -ForegroundColor Red
        $webSocketOK = $false
    }
} catch {
    Write-Host "   ✗ WebSocket Port test failed: $($_.Exception.Message)" -ForegroundColor Red
    $webSocketOK = $false
}

Write-Host ""

# Show URLs
Write-Host "5. Browser URLs:" -ForegroundColor Yellow
Write-Host "   Web Interface: http://${WSL_IP}:${WebPort}" -ForegroundColor Cyan
Write-Host "   WebSocket: ws://${WSL_IP}:${WebSocketPort}" -ForegroundColor Cyan

Write-Host ""

# Summary
Write-Host "6. Summary:" -ForegroundColor Yellow
if ($webServerOK -and $webSocketOK) {
    Write-Host "   ✓ All tests passed! You can access the webapp from Windows." -ForegroundColor Green
    Write-Host "   Open your browser to: http://${WSL_IP}:${WebPort}" -ForegroundColor Green
} else {
    Write-Host "   ✗ Some tests failed. Troubleshooting needed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Start WSL server: wsl cd /mnt/e/working/drone-controller/webapp && ./start_mock_drone.sh --multiple 3" -ForegroundColor White
    Write-Host "2. Check server binding: wsl ss -tln | grep -E ':(8000|8765)'" -ForegroundColor White
    Write-Host "3. Check Windows Firewall settings" -ForegroundColor White
    Write-Host "4. Try restarting WSL: wsl --shutdown" -ForegroundColor White
    Write-Host "5. Verify WSL version: wsl --list --verbose" -ForegroundColor White
}

Write-Host ""

# Offer to open browser
if ($webServerOK) {
    $openBrowser = Read-Host "Open browser to webapp? (y/n)"
    if ($openBrowser -eq 'y' -or $openBrowser -eq 'Y') {
        Start-Process "http://${WSL_IP}:${WebPort}"
    }
}
