# Simple start script for drone simulator with working ports (with emojis)

param(
    [int]$WebPort = 8000,
    [int]$WebAppPort = 8766,
    [int]$DronePort = 8889,
    [int]$Multiple = 2,
    [string]$HostAddress = "0.0.0.0"
)

# Use UTF-8 encoding for proper emoji display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "$([char]0x1F681) Starting Drone Simulator" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Get the directory of this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Check for and activate virtual environment
$VenvPath = Join-Path $ProjectDir ".venv"
$VenvWindowsPath = Join-Path $ProjectDir ".venv-windows"

if (Test-Path $VenvWindowsPath) {
    $ActivateScript = Join-Path $VenvWindowsPath "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Host "$([char]0x2705) Activated virtual environment (.venv-windows)" -ForegroundColor Green
    }
} elseif (Test-Path $VenvPath) {
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        & $ActivateScript
        Write-Host "$([char]0x2705) Activated virtual environment (.venv)" -ForegroundColor Green
    }
} else {
    Write-Host "$([char]0x26A0)  Using system Python" -ForegroundColor Yellow
}

# Change to webapp directory
Set-Location $ScriptDir

# Get local IP address for Windows networking
try {
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*","Wi-Fi*" | Where-Object {$_.IPAddress -ne "127.0.0.1"})[0].IPAddress
} catch {
    $LocalIP = "localhost"
}

if (-not $LocalIP) {
    $LocalIP = "localhost"
}

Write-Host ""
Write-Host "$([char]0x1F527) Configuration:" -ForegroundColor Yellow
Write-Host "  Web Server: $($HostAddress):$WebPort"
Write-Host "  WebSocket: $($HostAddress):$WebAppPort"
Write-Host "  Drone UDP: $($HostAddress):$DronePort (swarm mode)"
Write-Host "  Local IP: $LocalIP"
Write-Host "  Multiple Drones: $Multiple"

Write-Host ""
Write-Host "$([char]0x1F310) Access URLs:" -ForegroundColor Yellow
Write-Host "  Local: http://localhost:$WebPort"
if ($LocalIP -ne "localhost") {
    Write-Host "  Network: http://$($LocalIP):$WebPort"
}

Write-Host ""
Write-Host "$([char]0x1F680) Starting simulator..." -ForegroundColor Green

# Start with single drone using multiple mode for proper networking
python mock_drone.py --host $HostAddress --ip $HostAddress --web-port $WebPort --webapp-port $WebAppPort --port $DronePort --multiple $Multiple
