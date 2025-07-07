# Get local IP address for Windows connectivity

Write-Host "🔍 Finding Local IP addresses..." -ForegroundColor Cyan
Write-Host ""

# Method 1: Get-NetIPAddress (most reliable for Windows)
try {
    $NetworkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -ne "127.0.0.1" -and
        $_.InterfaceAlias -match "Ethernet|Wi-Fi|Local Area Connection"
    }
    $LocalIP1 = $NetworkAdapters[0].IPAddress
} catch {
    $LocalIP1 = $null
}

# Method 2: WMI
try {
    $WmiNetworkAdapter = Get-WmiObject -Class Win32_NetworkAdapterConfiguration | Where-Object {
        $_.IPEnabled -eq $true -and $_.IPAddress -ne $null
    }
    $LocalIP2 = ($WmiNetworkAdapter.IPAddress | Where-Object { $_ -ne "127.0.0.1" })[0]
} catch {
    $LocalIP2 = $null
}

# Method 3: System.Net.NetworkInformation
try {
    $LocalIP3 = (Test-Connection -ComputerName $env:COMPUTERNAME -Count 1).IPv4Address.IPAddressToString
} catch {
    $LocalIP3 = $null
}

Write-Host "📡 IP Detection Methods:" -ForegroundColor Yellow
Write-Host "  Method 1 (Get-NetIPAddress): $(if ($LocalIP1) { $LocalIP1 } else { 'Failed' })"
Write-Host "  Method 2 (WMI): $(if ($LocalIP2) { $LocalIP2 } else { 'Failed' })"
Write-Host "  Method 3 (Test-Connection): $(if ($LocalIP3) { $LocalIP3 } else { 'Failed' })"
Write-Host ""

# Choose the best IP
$LocalIP = ""
if ($LocalIP1 -and $LocalIP1 -ne "127.0.0.1") {
    $LocalIP = $LocalIP1
} elseif ($LocalIP2 -and $LocalIP2 -ne "127.0.0.1") {
    $LocalIP = $LocalIP2
} elseif ($LocalIP3 -and $LocalIP3 -ne "127.0.0.1") {
    $LocalIP = $LocalIP3
}

Write-Host "🌐 Network Interface Details:" -ForegroundColor Yellow
try {
    Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.InterfaceAlias -match "Ethernet|Wi-Fi|Local Area Connection"
    } | ForEach-Object {
        Write-Host "  Interface: $($_.InterfaceAlias)"
        Write-Host "    IP: $($_.IPAddress)"
    }
} catch {
    Write-Host "  Network interface information not available"
}

Write-Host ""

if ($LocalIP -and $LocalIP -ne "127.0.0.1") {
    Write-Host "✅ Local IP Address Found: $LocalIP" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Recommended URLs for network access:" -ForegroundColor Yellow
    Write-Host "  Web Interface: http://$($LocalIP):8000"
    Write-Host "  WebSocket: ws://$($LocalIP):8766"
    Write-Host ""
    Write-Host "💡 Use these URLs from other devices on your network" -ForegroundColor Cyan
    Write-Host ""

    # Test if ports are accessible
    Write-Host "🔧 Port Accessibility Test:" -ForegroundColor Yellow

    function Test-Port {
        param([string]$Host, [int]$Port)
        try {
            $Connection = New-Object System.Net.Sockets.TcpClient
            $Connection.Connect($Host, $Port)
            $Connection.Close()
            return $true
        } catch {
            return $false
        }
    }

    if (Test-Port "localhost" 8000) {
        Write-Host "  Port 8000: ✅ In use (server likely running)" -ForegroundColor Green
    } else {
        Write-Host "  Port 8000: ⚠️  Not in use (start the server first)" -ForegroundColor Yellow
    }

    if (Test-Port "localhost" 8766) {
        Write-Host "  Port 8766: ✅ In use (WebSocket server likely running)" -ForegroundColor Green
    } else {
        Write-Host "  Port 8766: ⚠️  Not in use (start the server first)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "🧪 Quick Connectivity Test:" -ForegroundColor Yellow
    try {
        $Response = Invoke-WebRequest -Uri "http://$($LocalIP):8000" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✅ Server is accessible on $($LocalIP):8000" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Server not accessible (may not be running)" -ForegroundColor Red
    }

} else {
    Write-Host "❌ Could not determine local IP address" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check network adapter status:"
    Write-Host "     Get-NetAdapter | Where-Object Status -eq Up"
    Write-Host ""
    Write-Host "  2. Check IP configuration:"
    Write-Host "     ipconfig /all"
    Write-Host ""
    Write-Host "  3. Check Windows network profile:"
    Write-Host "     Get-NetConnectionProfile"
}

Write-Host ""
Write-Host "🔧 Manual IP Detection Commands:" -ForegroundColor Yellow
Write-Host "  PowerShell: (Get-NetIPAddress -AddressFamily IPv4).IPAddress"
Write-Host "  Command Prompt: ipconfig"
Write-Host "  Alternative: Get-WmiObject Win32_NetworkAdapterConfiguration"

Write-Host ""
Write-Host "🚨 Windows Connection Troubleshooting:" -ForegroundColor Red
Write-Host "  1. Ensure server binds to 0.0.0.0 (not 127.0.0.1)"
Write-Host "  2. Check Windows Firewall settings"
Write-Host "  3. Verify network discovery is enabled"
Write-Host "  4. Check if private/public network profile is correct"

# Show Windows version info
Write-Host ""
Write-Host "📋 Windows Environment Info:" -ForegroundColor Cyan
Write-Host "  $(([System.Environment]::OSVersion).VersionString)"
Write-Host "  PowerShell Version: $($PSVersionTable.PSVersion)"
