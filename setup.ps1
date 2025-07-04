# ============================================================================
# Drone Controller Project Setup Script
# ============================================================================
# This script sets up the drone controller development environment
# Supports both development and production installations
# ============================================================================

param(
    [switch]$Dev,
    [switch]$Production,
    [switch]$Visualization,
    [switch]$Force,
    [switch]$Help
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProjectName = "drone-controller"
$PythonMinVersion = "3.11"

# Color output functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

function Show-Help {
    Write-Host @"
Drone Controller Project Setup Script

USAGE:
    .\setup.ps1 [OPTIONS]

OPTIONS:
    -Dev            Install development dependencies (pytest, black, flake8, mypy)
    -Production     Install only production dependencies (default)
    -Visualization  Install visualization dependencies (matplotlib)
    -Force          Force reinstall of all dependencies
    -Help           Show this help message

EXAMPLES:
    .\setup.ps1                     # Production setup
    .\setup.ps1 -Dev               # Development setup
    .\setup.ps1 -Dev -Visualization # Development + visualization
    .\setup.ps1 -Force             # Force reinstall everything

REQUIREMENTS:
    - Python $PythonMinVersion or higher
    - uv package manager (will be installed automatically if missing)
    - Administrative privileges may be required for some operations

"@ -ForegroundColor White
}

function Test-PythonVersion {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python is not installed or not in PATH"
            return $false
        }

        $versionString = $pythonVersion -replace "Python ", ""
        $version = [Version]$versionString
        $minVersion = [Version]$PythonMinVersion

        if ($version -lt $minVersion) {
            Write-Error "Python $PythonMinVersion or higher is required. Found: $versionString"
            return $false
        }

        Write-Success "✓ Python $versionString found"
        return $true
    }
    catch {
        Write-Error "Failed to check Python version: $_"
        return $false
    }
}

function Test-UvInstalled {
    try {
        $uvVersion = uv --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "uv is not installed, installing it..."
            return Install-Uv
        }
        Write-Success "✓ uv is available ($uvVersion)"
        return $true
    }
    catch {
        Write-Warning "uv not found, installing it..."
        return Install-Uv
    }
}

function Install-Uv {
    try {
        Write-Info "Installing uv package manager..."
        # Install uv using the official installer
        Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing | Invoke-Expression

        # Refresh PATH for current session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")

        # Test installation
        $uvVersion = uv --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ uv installed successfully ($uvVersion)"
            return $true
        } else {
            Write-Error "Failed to install uv"
            return $false
        }
    }
    catch {
        Write-Error "Failed to install uv: $_"
        return $false
    }
}

function Install-Dependencies {
    param([string[]]$Dependencies, [string]$Category = "")

    if ($Dependencies.Count -eq 0) {
        return
    }

    $categoryText = if ($Category) { " ($Category)" } else { "" }
    Write-Info "Installing dependencies$categoryText..."

    foreach ($dep in $Dependencies) {
        Write-Host "  Installing $dep..." -NoNewline
        try {
            if ($Force) {
                uv add --force $dep 2>&1 | Out-Null
            } else {
                uv add $dep 2>&1 | Out-Null
            }
            if ($LASTEXITCODE -eq 0) {
                Write-Success " ✓"
            } else {
                Write-Error " ✗"
                throw "uv add failed for $dep"
            }
        }
        catch {
            Write-Error " ✗"
            Write-Error "Failed to install $dep : $_"
            throw
        }
    }
}

function Install-ProjectDependencies {
    Write-Info "Installing project dependencies with uv..."
    try {
        # Initialize uv project if not already done
        if (-not (Test-Path "uv.lock")) {
            Write-Info "Initializing uv project..."
            uv init --no-readme 2>&1 | Out-Null
        }

        # Sync dependencies
        Write-Info "Syncing dependencies..."
        if ($Force) {
            uv sync --force 2>&1 | Out-Null
        } else {
            uv sync 2>&1 | Out-Null
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Project dependencies installed with uv"
        } else {
            throw "uv sync failed"
        }
    }
    catch {
        Write-Error "Failed to install project dependencies: $_"
        throw
    }
}

function Test-DroneControllerImport {
    Write-Info "Testing drone controller import..."
    try {
        uv run python -c "import src.drone_controller; print('Import successful')" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Drone controller import successful"
        } else {
            Write-Warning "⚠ Drone controller import failed (this may be normal if drones are not connected)"
        }
    }
    catch {
        Write-Warning "⚠ Could not test drone controller import: $_"
    }
}

function Initialize-ProjectStructure {
    Write-Info "Checking project structure..."

    $requiredDirs = @("src", "tests", "config", "logs", "examples")
    foreach ($dir in $requiredDirs) {
        if (-not (Test-Path $dir)) {
            Write-Warning "Creating missing directory: $dir"
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }

    # Ensure __init__.py files exist
    $initFiles = @(
        "src\__init__.py",
        "src\drone_controller\__init__.py",
        "src\drone_controller\core\__init__.py",
        "src\drone_controller\multi_robot\__init__.py",
        "src\drone_controller\utils\__init__.py"
    )

    foreach ($initFile in $initFiles) {
        if (-not (Test-Path $initFile)) {
            Write-Warning "Creating missing __init__.py: $initFile"
            New-Item -ItemType File -Path $initFile -Force | Out-Null
        }
    }

    Write-Success "✓ Project structure verified"
}

function Show-PostInstallInstructions {
    Write-Host @"

============================================================================
🎉 SETUP COMPLETE!
============================================================================

Your drone controller environment is ready! Here's what you can do next:

TESTING THE INSTALLATION:
    # Run basic tests
    uv run pytest tests/ -v

    # Run single drone demo (simulation mode)
    uv run python main.py --mode single --demo

    # Run swarm demo (simulation mode)
    uv run python main.py --mode swarm --demo

CONNECTING REAL DRONES:
    1. Turn on your Tello Talent drone(s)
    2. Connect to the drone's Wi-Fi network
    3. Run: uv run python main.py --mode single

DEVELOPMENT COMMANDS:
"@ -ForegroundColor Green    if ($Dev) {
        Write-Host @"
    # Run tests with coverage
    uv run pytest tests/ -v --cov=src

    # Code formatting
    uv run black src/ tests/ examples/

    # Linting
    uv run flake8 src/ tests/ examples/

    # Type checking
    uv run mypy src/

    # Add new dependencies
    uv add package-name
    uv add --dev package-name  # for dev dependencies
"@ -ForegroundColor Yellow
    }

    Write-Host @"

CONFIGURATION:
    - Edit config/drone_config.yaml for drone settings
    - Check logs/ directory for runtime logs
    - See examples/ for usage examples

DOCUMENTATION:
    - README.md for detailed documentation
    - examples/ directory for code samples

Happy flying! 🚁
============================================================================

"@ -ForegroundColor Green
}

# Main execution
function Main {
    if ($Help) {
        Show-Help
        return
    }

    Write-Host @"
============================================================================
🚁 DRONE CONTROLLER PROJECT SETUP
============================================================================
"@ -ForegroundColor Cyan

    # Default to production if no mode specified
    if (-not $Dev -and -not $Production) {
        $Production = $true
    }

    $mode = if ($Dev) { "Development" } else { "Production" }
    Write-Info "Setup mode: $mode"
    if ($Visualization) { Write-Info "Including visualization dependencies" }
    if ($Force) { Write-Info "Force reinstall enabled" }

    try {
        # Prerequisites check
        Write-Info "Checking prerequisites..."
        if (-not (Test-PythonVersion)) { exit 1 }
        if (-not (Test-UvInstalled)) { exit 1 }

        # Project structure
        Initialize-ProjectStructure

        # Install project dependencies with uv
        Install-ProjectDependencies

        # Add optional development dependencies
        if ($Dev) {
            Write-Info "Adding development dependencies..."
            $devDeps = @("pytest>=8.4.1", "black>=23.0.0", "flake8>=6.0.0", "mypy>=1.0.0")
            foreach ($dep in $devDeps) {
                Write-Host "  Adding $dep..." -NoNewline
                uv add --dev $dep 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success " ✓"
                } else {
                    Write-Warning " ⚠"
                }
            }
        }

        # Add visualization dependencies
        if ($Visualization) {
            Write-Info "Adding visualization dependencies..."
            uv add matplotlib 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ Visualization dependencies added"
            } else {
                Write-Warning "⚠ Failed to add visualization dependencies"
            }
        }

        # Test installation
        Test-DroneControllerImport

        # Success!
        Show-PostInstallInstructions

    }
    catch {
        Write-Error @"

============================================================================
❌ SETUP FAILED
============================================================================
Error: $_

Please check the error message above and try again.
You may need to:
1. Run as Administrator
2. Check your internet connection
3. Ensure Python and uv are properly installed
4. Try with -Force flag to reinstall dependencies

For help, run: .\setup.ps1 -Help
============================================================================
"@
        exit 1
    }
}

# Execute main function
Main
