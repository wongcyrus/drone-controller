# ============================================================================
# Drone Controller Project Setup Script (PowerShell version)
# ============================================================================
# Enhanced setup script for drone controller project with Windows support
# ============================================================================

param(
    [switch]$Dev,
    [switch]$Visualization,
    [switch]$Force
)

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "🚁 DRONE CONTROLLER PROJECT SETUP" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $IsAdmin) {
    Write-Host "⚠️  Warning: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some features may require elevated privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $PythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python found: $PythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher and try again" -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check uv installation
Write-Host ""
Write-Host "Checking uv installation..." -ForegroundColor Yellow
try {
    $UvVersion = uv --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ uv found: $UvVersion" -ForegroundColor Green
    } else {
        throw "uv not found"
    }
} catch {
    Write-Host "Installing uv package manager..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression
        Write-Host "✓ uv installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install uv" -ForegroundColor Red
        Write-Host "Please install manually from: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Force reinstall if requested
if ($Force) {
    Write-Host ""
    Write-Host "🔄 Force reinstall requested - cleaning existing environment..." -ForegroundColor Yellow
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force ".venv"
        Write-Host "✓ Removed existing .venv directory" -ForegroundColor Green
    }
    if (Test-Path ".venv-windows") {
        Remove-Item -Recurse -Force ".venv-windows"
        Write-Host "✓ Removed existing .venv-windows directory" -ForegroundColor Green
    }
}

# Sync project dependencies
Write-Host ""
Write-Host "Installing project dependencies with uv..." -ForegroundColor Yellow
try {
    if ($Dev) {
        uv sync --dev
    } else {
        uv sync
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } else {
        throw "uv sync failed"
    }
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install additional development tools if requested
if ($Dev) {
    Write-Host ""
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow

    $DevPackages = @(
        "pytest",
        "black",
        "flake8",
        "mypy",
        "pre-commit"
    )

    foreach ($package in $DevPackages) {
        try {
            uv add --dev $package
            Write-Host "✓ Installed $package" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Failed to install $package" -ForegroundColor Yellow
        }
    }
}

# Install visualization tools if requested
if ($Visualization) {
    Write-Host ""
    Write-Host "Installing visualization dependencies..." -ForegroundColor Yellow

    $VizPackages = @(
        "matplotlib",
        "plotly",
        "opencv-python",
        "pillow"
    )

    foreach ($package in $VizPackages) {
        try {
            uv add $package
            Write-Host "✓ Installed $package" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Failed to install $package" -ForegroundColor Yellow
        }
    }
}

# Create Windows-specific virtual environment symlink
Write-Host ""
Write-Host "Setting up Windows-specific environment..." -ForegroundColor Yellow
if (Test-Path ".venv" -and -not (Test-Path ".venv-windows")) {
    try {
        if ($IsAdmin) {
            New-Item -ItemType SymbolicLink -Path ".venv-windows" -Target ".venv" -Force | Out-Null
            Write-Host "✓ Created .venv-windows symbolic link" -ForegroundColor Green
        } else {
            # Create a batch file to activate the environment instead
            $ActivateBat = @"
@echo off
call "%~dp0.venv\Scripts\activate.bat"
"@
            $ActivateBat | Out-File -FilePath ".venv-windows-activate.bat" -Encoding ASCII
            Write-Host "✓ Created .venv-windows-activate.bat (use this to activate environment)" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Could not create Windows environment link" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Green
Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your drone controller environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "TESTING THE INSTALLATION:" -ForegroundColor Yellow
Write-Host "  uv run python main.py --mode single --demo" -ForegroundColor White
Write-Host "  uv run python main.py --mode swarm --demo" -ForegroundColor White
Write-Host ""
Write-Host "STARTING THE WEB SIMULATOR:" -ForegroundColor Yellow
Write-Host "  cd webapp" -ForegroundColor White
Write-Host "  .\start_simulator.ps1" -ForegroundColor White
Write-Host "  # or" -ForegroundColor Gray
Write-Host "  .\start_simulator.bat" -ForegroundColor White
Write-Host ""
Write-Host "CONNECTING REAL DRONES:" -ForegroundColor Yellow
Write-Host "  1. Turn on your Tello Talent drone(s)" -ForegroundColor White
Write-Host "  2. Connect to the drone's Wi-Fi network" -ForegroundColor White
Write-Host "  3. Run: uv run python main.py --mode single" -ForegroundColor White
Write-Host ""
Write-Host "WINDOWS-SPECIFIC TOOLS:" -ForegroundColor Yellow
Write-Host "  .\webapp\configure_ports.ps1    # Check and configure ports" -ForegroundColor White
Write-Host "  .\webapp\get_local_ip.ps1       # Get local IP for network access" -ForegroundColor White
Write-Host ""
Write-Host "Happy flying! 🚁" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Green
Write-Host ""
