# Windows PowerShell script to run the IoT client
# This script handles Windows-specific configuration and environment setup

param(
    [string]$ConfigFile = "settings_windows.yaml",
    [switch]$Verbose,
    [switch]$Service
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set working directory to the IoT folder
Set-Location $ScriptDir

Write-Host "=== Windows IoT Client Launcher ===" -ForegroundColor Green
Write-Host "Working directory: $ScriptDir" -ForegroundColor Yellow
Write-Host "Config file: $ConfigFile" -ForegroundColor Yellow

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python is not installed or not in PATH. Please install Python first."
    exit 1
}

# Check if virtual environment exists
$venvPath = Join-Path $ScriptDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $activateScript
} else {
    Write-Error "Virtual environment activation script not found: $activateScript"
    exit 1
}

# Install/upgrade requirements
Write-Host "Installing/updating Python packages..." -ForegroundColor Yellow
pip install -r requirements.txt --upgrade

# Set Windows-specific environment variables
$env:PYTHONPATH = $ScriptDir
$env:IOT_CLIENT_OS = "Windows"
$env:IOT_CLIENT_PLATFORM = "win32"

# Configure logging for Windows
$logDir = Join-Path $ScriptDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$logFile = Join-Path $logDir "iot_client_$(Get-Date -Format 'yyyy-MM-dd').log"
$env:IOT_LOG_FILE = $logFile

Write-Host "Log file: $logFile" -ForegroundColor Yellow

# Check if config file exists
$configPath = Join-Path $ScriptDir $ConfigFile
if (-not (Test-Path $configPath)) {
    Write-Error "Configuration file not found: $configPath"
    exit 1
}

# Handle Windows certificate paths
Write-Host "Checking certificate files..." -ForegroundColor Yellow
$certDir = Join-Path $ScriptDir "certifications"
if (-not (Test-Path $certDir)) {
    Write-Warning "Certificate directory not found: $certDir"
    Write-Host "You may need to configure certificates for AWS IoT connectivity." -ForegroundColor Yellow
}

# Set Windows-specific timeout values
$env:IOT_CONNECTION_TIMEOUT = "10"
$env:IOT_RETRY_ATTEMPTS = "3"

if ($Verbose) {
    $env:PYTHONVERBOSE = "1"
    Write-Host "Verbose mode enabled" -ForegroundColor Yellow
}

if ($Service) {
    Write-Host "Running as Windows service mode..." -ForegroundColor Yellow
    # For service mode, redirect output and run without user interaction
    python pubsub.py --config $ConfigFile --service 2>&1 | Tee-Object -FilePath $logFile
} else {
    Write-Host "Running in interactive mode..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the client" -ForegroundColor Yellow

    try {
        python pubsub.py --config $ConfigFile 2>&1 | Tee-Object -FilePath $logFile
    } catch {
        Write-Host "IoT client stopped." -ForegroundColor Yellow
    }
}

Write-Host "=== IoT Client Finished ===" -ForegroundColor Green
