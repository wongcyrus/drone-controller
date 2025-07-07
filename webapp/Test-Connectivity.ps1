# Test Windows connectivity for drone simulator

param(
    [string]$TargetIP = "localhost",
    [int]$WebPort = 8000,
    [int]$WebSocketPort = 8766,
    [int]$DronePort = 8889
)

Write-Host "🧪 Testing Drone Simulator Connectivity" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Get local IP if testing localhost
if ($TargetIP -eq "localhost") {
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" | Where-Object {$_.IPAddress -ne "127.0.0.1"})[0].IPAddress
    if ($LocalIP) {
        Write-Host "🌐 Local IP detected: $LocalIP" -ForegroundColor Yellow
        Write-Host "   You can also test with: .\Test-Connectivity.ps1 -TargetIP $LocalIP" -ForegroundColor Gray
        Write-Host ""
    }
}

Write-Host "🔍 Testing connectivity to: $TargetIP" -ForegroundColor Yellow
Write-Host ""

# Function to test port connectivity
function Test-PortConnectivity {
    param([string]$Host, [int]$Port, [string]$Protocol = "TCP", [string]$Description)

    Write-Host "Testing $Description ($Protocol $Port)... " -NoNewline -ForegroundColor Yellow

    try {
        if ($Protocol -eq "TCP") {
            $Connection = New-Object System.Net.Sockets.TcpClient
            $Connection.Connect($Host, $Port)
            $Connection.Close()
            Write-Host "✅ SUCCESS" -ForegroundColor Green
            return $true
        } else {
            # UDP test is more complex, just assume success for now
            Write-Host "⚠️  UDP (cannot test directly)" -ForegroundColor Yellow
            return $true
        }
    } catch {
        Write-Host "❌ FAILED" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
        return $false
    }
}

# Test HTTP Web Server
$WebOK = Test-PortConnectivity -Host $TargetIP -Port $WebPort -Protocol "TCP" -Description "Web Server"

# Test WebSocket Server
$WebSocketOK = Test-PortConnectivity -Host $TargetIP -Port $WebSocketPort -Protocol "TCP" -Description "WebSocket Server"

# Test Drone UDP Port (just check if something is listening)
$DroneOK = Test-PortConnectivity -Host $TargetIP -Port $DronePort -Protocol "UDP" -Description "Drone UDP"

Write-Host ""

# Test HTTP connectivity
if ($WebOK) {
    Write-Host "🌐 Testing HTTP connectivity..." -ForegroundColor Yellow
    try {
        $Response = Invoke-WebRequest -Uri "http://$($TargetIP):$WebPort" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ HTTP request successful (Status: $($Response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "❌ HTTP request failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Skipping HTTP test (port not accessible)" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "📋 Connectivity Summary:" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host "Target: $TargetIP" -ForegroundColor White
Write-Host "Web Server (TCP $WebPort): $(if ($WebOK) { '✅ OK' } else { '❌ FAIL' })" -ForegroundColor $(if ($WebOK) { 'Green' } else { 'Red' })
Write-Host "WebSocket (TCP $WebSocketPort): $(if ($WebSocketOK) { '✅ OK' } else { '❌ FAIL' })" -ForegroundColor $(if ($WebSocketOK) { 'Green' } else { 'Red' })
Write-Host "Drone UDP ($DronePort): $(if ($DroneOK) { '⚠️  Unknown' } else { '❌ FAIL' })" -ForegroundColor Yellow

Write-Host ""

# Recommendations
if (-not $WebOK -or -not $WebSocketOK) {
    Write-Host "🔧 Troubleshooting Recommendations:" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "1. 🚀 Start the simulator:" -ForegroundColor Yellow
    Write-Host "   cd webapp" -ForegroundColor White
    Write-Host "   .\start_simulator.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 🔍 Check available ports:" -ForegroundColor Yellow
    Write-Host "   .\configure_ports.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 🛡️ Check Windows Firewall:" -ForegroundColor Yellow
    Write-Host "   - Allow Python through Windows Defender Firewall" -ForegroundColor White
    Write-Host "   - Or temporarily disable firewall for testing" -ForegroundColor White
    Write-Host ""
    Write-Host "4. 🌐 Verify network configuration:" -ForegroundColor Yellow
    Write-Host "   .\get_local_ip.ps1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "🎉 All connectivity tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "  Web Interface: http://$($TargetIP):$WebPort" -ForegroundColor White
    Write-Host "  WebSocket: ws://$($TargetIP):$WebSocketPort" -ForegroundColor White
}

Write-Host ""
Write-Host "💡 Usage Examples:" -ForegroundColor Cyan
Write-Host "  Test localhost: .\Test-Connectivity.ps1" -ForegroundColor White
Write-Host "  Test specific IP: .\Test-Connectivity.ps1 -TargetIP 192.168.1.100" -ForegroundColor White
Write-Host "  Custom ports: .\Test-Connectivity.ps1 -WebPort 8080 -WebSocketPort 8767" -ForegroundColor White
