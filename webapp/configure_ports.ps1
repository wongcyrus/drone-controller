# Configure and find available ports for the drone simulator

Write-Host "🔧 Port Configuration Helper" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# Function to check if port is available
function Test-Port {
    param([int]$Port)

    try {
        $Connection = New-Object System.Net.Sockets.TcpClient
        $Connection.Connect("localhost", $Port)
        $Connection.Close()
        return $false  # Port in use
    }
    catch {
        return $true   # Port available
    }
}

# Function to find next available port
function Find-AvailablePort {
    param([int]$StartPort)

    for ($port = $StartPort; $port -lt ($StartPort + 100); $port++) {
        if (Test-Port $port) {
            return $port
        }
    }

    Write-Host "No available port found starting from $StartPort" -ForegroundColor Red
    return $null
}

Write-Host ""
Write-Host "📡 Current Port Status:" -ForegroundColor Yellow

# Check common ports
$Ports = @(8000, 8765, 8766, 8767, 8768, 8889, 8890, 8891)
foreach ($port in $Ports) {
    if (Test-Port $port) {
        Write-Host "  Port $port`: ✅ Available" -ForegroundColor Green
    } else {
        Write-Host "  Port $port`: ❌ In use" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔍 Finding Available Ports:" -ForegroundColor Yellow

# Find available web port
$WebPort = Find-AvailablePort 8000
Write-Host "  Web Server: $WebPort"

# Find available websocket port
$WsPort = Find-AvailablePort 8766
Write-Host "  WebSocket: $WsPort"

# Find available drone port
$DronePort = Find-AvailablePort 8889
Write-Host "  Drone UDP: $DronePort"

Write-Host ""
Write-Host "🚀 Recommended Start Command:" -ForegroundColor Green
Write-Host "  .\start_simulator.ps1 -WebPort $WebPort -WebAppPort $WsPort -DronePort $DronePort"

Write-Host ""
Write-Host "🌐 Access URLs:" -ForegroundColor Yellow

# Get local IP address
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" | Where-Object {$_.IPAddress -ne "127.0.0.1"})[0].IPAddress
if (-not $LocalIP) {
    $LocalIP = "YOUR_LOCAL_IP"
}

Write-Host "  Local: http://localhost:$WebPort"
Write-Host "  Network: http://$($LocalIP):$WebPort"
Write-Host "  WebSocket: ws://$($LocalIP):$WsPort"

Write-Host ""
Write-Host "💡 Common Port Configurations:" -ForegroundColor Cyan
Write-Host "  Default: --web-port 8000 --webapp-port 8765"
Write-Host "  Alt 1:   --web-port 8001 --webapp-port 8766"
Write-Host "  Alt 2:   --web-port 8080 --webapp-port 8767"
Write-Host "  Alt 3:   --web-port 3000 --webapp-port 3001"
