# Windows Service Management Script for IoT Client
# This script helps install, start, stop, and manage the IoT client as a Windows service

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "uninstall", "start", "stop", "restart", "status", "logs")]
    [string]$Action,

    [string]$ServiceName = "DroneIoTClient",
    [string]$ConfigFile = "settings_windows.yaml",
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServiceScript = Join-Path $ScriptDir "run_iot_service.py"
$LogDir = Join-Path $ScriptDir "logs"

# Ensure logs directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-ServiceLog {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARNING") { "Yellow" } else { "Green" })

    $logFile = Join-Path $LogDir "service_management.log"
    Add-Content -Path $logFile -Value $logMessage
}

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-IoTService {
    Write-ServiceLog "Installing IoT Client as Windows Service..."

    if (-not (Test-AdminRights)) {
        Write-ServiceLog "Administrator rights required to install service" "ERROR"
        throw "This operation requires administrator privileges. Please run PowerShell as Administrator."
    }

    # Create service wrapper script
    $serviceWrapperContent = @"
import sys
import os
import logging
import time
from pathlib import Path

# Add the IoT directory to Python path
iot_dir = Path(__file__).parent
sys.path.insert(0, str(iot_dir))

# Set working directory
os.chdir(iot_dir)

# Configure logging for service
log_file = iot_dir / "logs" / "service.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def run_service():
    try:
        logging.info("Starting IoT Client Service...")

        # Import and run the Windows IoT client
        from pubsub_windows import main
        import argparse

        # Override sys.argv for service mode
        sys.argv = [
            'pubsub_windows.py',
            '--config', '$ConfigFile',
            '--service',
            '--log-file', str(log_file)
        ]

        main()

    except Exception as e:
        logging.error(f"Service error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_service()
"@

    Set-Content -Path $ServiceScript -Value $serviceWrapperContent -Encoding UTF8

    # Create the service using New-Service or sc.exe
    $pythonPath = (Get-Command python).Path
    $serviceCommand = "`"$pythonPath`" `"$ServiceScript`""

    try {
        # Remove existing service if it exists
        $existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($existingService) {
            Write-ServiceLog "Removing existing service..."
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            & sc.exe delete $ServiceName
            Start-Sleep -Seconds 2
        }

        # Create new service
        Write-ServiceLog "Creating service: $ServiceName"
        & sc.exe create $ServiceName binPath= $serviceCommand start= demand DisplayName= "Drone IoT Client Service"

        if ($LASTEXITCODE -eq 0) {
            Write-ServiceLog "Service installed successfully"

            # Configure service description
            & sc.exe description $ServiceName "AWS IoT MQTT client for drone controller communication"

            # Configure service to restart on failure
            & sc.exe failure $ServiceName reset= 3600 actions= restart/5000/restart/10000/restart/30000

            Write-ServiceLog "Service configuration completed"
        } else {
            throw "Failed to create service"
        }

    } catch {
        Write-ServiceLog "Failed to install service: $_" "ERROR"
        throw
    }
}

function Uninstall-IoTService {
    Write-ServiceLog "Uninstalling IoT Client Service..."

    if (-not (Test-AdminRights)) {
        Write-ServiceLog "Administrator rights required to uninstall service" "ERROR"
        throw "This operation requires administrator privileges. Please run PowerShell as Administrator."
    }

    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-ServiceLog "Stopping service..."
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2

            Write-ServiceLog "Deleting service..."
            & sc.exe delete $ServiceName

            if ($LASTEXITCODE -eq 0) {
                Write-ServiceLog "Service uninstalled successfully"
            } else {
                Write-ServiceLog "Failed to delete service" "WARNING"
            }
        } else {
            Write-ServiceLog "Service not found" "WARNING"
        }

        # Clean up service script
        if (Test-Path $ServiceScript) {
            Remove-Item $ServiceScript -Force
            Write-ServiceLog "Service script removed"
        }

    } catch {
        Write-ServiceLog "Error during uninstall: $_" "ERROR"
        throw
    }
}

function Start-IoTService {
    Write-ServiceLog "Starting IoT Client Service..."

    try {
        Start-Service -Name $ServiceName
        Write-ServiceLog "Service started successfully"
    } catch {
        Write-ServiceLog "Failed to start service: $_" "ERROR"
        throw
    }
}

function Stop-IoTService {
    Write-ServiceLog "Stopping IoT Client Service..."

    try {
        Stop-Service -Name $ServiceName -Force
        Write-ServiceLog "Service stopped successfully"
    } catch {
        Write-ServiceLog "Failed to stop service: $_" "ERROR"
        throw
    }
}

function Restart-IoTService {
    Write-ServiceLog "Restarting IoT Client Service..."
    Stop-IoTService
    Start-Sleep -Seconds 3
    Start-IoTService
}

function Get-ServiceStatus {
    Write-ServiceLog "Getting service status..."

    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "Service Name: $($service.Name)" -ForegroundColor Green
            Write-Host "Display Name: $($service.DisplayName)" -ForegroundColor Green
            Write-Host "Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Yellow" })
            Write-Host "Start Type: $($service.StartType)" -ForegroundColor Green

            # Get additional service info
            $serviceInfo = & sc.exe query $ServiceName
            Write-Host "`nDetailed Status:" -ForegroundColor Cyan
            Write-Host $serviceInfo -ForegroundColor Gray
        } else {
            Write-Host "Service '$ServiceName' is not installed" -ForegroundColor Yellow
        }
    } catch {
        Write-ServiceLog "Error getting service status: $_" "ERROR"
        throw
    }
}

function Show-ServiceLogs {
    Write-ServiceLog "Showing recent service logs..."

    $serviceLogFile = Join-Path $LogDir "service.log"
    $iotLogFile = Join-Path $LogDir "iot_client_$(Get-Date -Format 'yyyy-MM-dd').log"

    Write-Host "`n=== Service Logs ===" -ForegroundColor Cyan
    if (Test-Path $serviceLogFile) {
        Get-Content $serviceLogFile -Tail 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    } else {
        Write-Host "No service log file found" -ForegroundColor Yellow
    }

    Write-Host "`n=== IoT Client Logs ===" -ForegroundColor Cyan
    if (Test-Path $iotLogFile) {
        Get-Content $iotLogFile -Tail 20 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    } else {
        Write-Host "No IoT client log file found for today" -ForegroundColor Yellow
    }
}

# Main script execution
Write-Host "=== Windows IoT Service Manager ===" -ForegroundColor Green
Write-Host "Action: $Action" -ForegroundColor Yellow
Write-Host "Service: $ServiceName" -ForegroundColor Yellow
Write-Host ""

try {
    switch ($Action.ToLower()) {
        "install" { Install-IoTService }
        "uninstall" { Uninstall-IoTService }
        "start" { Start-IoTService }
        "stop" { Stop-IoTService }
        "restart" { Restart-IoTService }
        "status" { Get-ServiceStatus }
        "logs" { Show-ServiceLogs }
        default {
            Write-Host "Invalid action: $Action" -ForegroundColor Red
            Write-Host "Valid actions: install, uninstall, start, stop, restart, status, logs" -ForegroundColor Yellow
            exit 1
        }
    }

    Write-Host "`nOperation completed successfully!" -ForegroundColor Green

} catch {
    Write-Host "`nOperation failed: $_" -ForegroundColor Red
    exit 1
}
