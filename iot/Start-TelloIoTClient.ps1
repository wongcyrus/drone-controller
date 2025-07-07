# Tello Swarm IoT Client Startup Script for Windows
# This script helps start the Tello drone swarm IoT client with proper configuration

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = ".\tello_swarm_config.json",

    [Parameter(Mandatory=$false)]
    [switch]$ValidateOnly,

    [Parameter(Mandatory=$false)]
    [switch]$TestConnection,

    [Parameter(Mandatory=$false)]
    [switch]$CreateSampleConfig
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-PythonEnvironment {
    Write-ColorOutput "Checking Python environment..." $InfoColor

    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "Found: $pythonVersion" $SuccessColor
    }
    catch {
        Write-ColorOutput "Python not found. Please install Python 3.7 or later." $ErrorColor
        return $false
    }

    # Check required packages
    $requiredPackages = @("djitellopy", "AWSIoTPythonSDK", "jsonschema")

    foreach ($package in $requiredPackages) {
        try {
            $result = python -c "import $package" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ Package '$package' is installed" $SuccessColor
            } else {
                Write-ColorOutput "✗ Package '$package' is NOT installed" $ErrorColor
                Write-ColorOutput "Install with: pip install $package" $WarningColor
                return $false
            }
        }
        catch {
            Write-ColorOutput "✗ Package '$package' is NOT installed" $ErrorColor
            return $false
        }
    }

    return $true
}

function Create-SampleConfig {
    $sampleConfig = @{
        client_id = "tello_swarm_client_001"
        endpoint = "your-iot-endpoint.iot.region.amazonaws.com"
        root_ca_path = "./certifications/AmazonRootCA1.pem"
        private_key_path = "./certifications/drone_swarm.private.key"
        certificate_path = "./certifications/drone_swarm.cert.pem"
        swarm_id = "hkiit_demo_swarm"
        drone_ips = @("192.168.10.1", "192.168.10.2", "192.168.10.3", "192.168.10.4")
        schema_path = "./aws_iot_drone_schema.json"
        telemetry_interval = 10
        safety_settings = @{
            max_altitude = 300
            min_battery_level = 20
            collision_avoidance = $true
            auto_land_on_low_battery = $true
            emergency_land_on_signal_loss = $true
        }
        logging = @{
            level = "INFO"
            format = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
            file = "./logs/tello_swarm_iot.log"
        }
    }

    $configPath = ".\tello_swarm_config_sample.json"
    $sampleConfig | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath

    Write-ColorOutput "Sample configuration created at: $configPath" $SuccessColor
    Write-ColorOutput "Please edit this file with your actual AWS IoT endpoint and drone IPs." $WarningColor
}

function Test-ConfigFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        Write-ColorOutput "Configuration file not found: $Path" $ErrorColor
        return $false
    }

    try {
        $config = Get-Content $Path | ConvertFrom-Json
        Write-ColorOutput "Configuration file is valid JSON" $SuccessColor

        # Check required fields
        $requiredFields = @("client_id", "endpoint", "swarm_id", "drone_ips")

        foreach ($field in $requiredFields) {
            if (-not $config.$field) {
                Write-ColorOutput "Missing required field: $field" $ErrorColor
                return $false
            }
        }

        Write-ColorOutput "Swarm ID: $($config.swarm_id)" $InfoColor
        Write-ColorOutput "Drone count: $($config.drone_ips.Count)" $InfoColor

        return $true
    }
    catch {
        Write-ColorOutput "Invalid JSON in configuration file: $_" $ErrorColor
        return $false
    }
}

function Start-TelloIoTClient {
    param(
        [string]$ConfigPath,
        [switch]$ValidateOnly,
        [switch]$TestConnection
    )

    $arguments = @("run_tello_iot_client.py", "--config", $ConfigPath)

    if ($ValidateOnly) {
        $arguments += "--validate-only"
    }

    if ($TestConnection) {
        $arguments += "--test-connection"
    }

    Write-ColorOutput "Starting Tello IoT Client..." $InfoColor
    Write-ColorOutput "Command: python $($arguments -join ' ')" $InfoColor

    try {
        & python @arguments
    }
    catch {
        Write-ColorOutput "Failed to start IoT client: $_" $ErrorColor
        return $false
    }

    return $true
}

# Main execution
Write-ColorOutput "=== Tello Swarm IoT Client Setup ===" $InfoColor

if ($CreateSampleConfig) {
    Create-SampleConfig
    exit 0
}

# Check Python environment
if (-not (Test-PythonEnvironment)) {
    Write-ColorOutput "Please fix Python environment issues before continuing." $ErrorColor
    exit 1
}

# Check configuration file
if (-not (Test-ConfigFile $ConfigPath)) {
    Write-ColorOutput "Please fix configuration issues before continuing." $ErrorColor
    Write-ColorOutput "Run with -CreateSampleConfig to create a sample configuration file." $InfoColor
    exit 1
}

# Create logs directory
$logDir = ".\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    Write-ColorOutput "Created logs directory: $logDir" $InfoColor
}

# Start the IoT client
if (Start-TelloIoTClient -ConfigPath $ConfigPath -ValidateOnly:$ValidateOnly -TestConnection:$TestConnection) {
    Write-ColorOutput "IoT client completed successfully." $SuccessColor
} else {
    Write-ColorOutput "IoT client failed." $ErrorColor
    exit 1
}

Write-ColorOutput "Done." $SuccessColor
