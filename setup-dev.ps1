# ============================================================================
# Drone Controller Development Environment Setup
# ============================================================================
# This script sets up a complete development environment with all tools
# ============================================================================

param(
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

function Show-Help {
    Write-Host @"
Drone Controller Development Environment Setup

USAGE:
    .\setup-dev.ps1 [OPTIONS]

OPTIONS:
    -Force          Force reinstall of all dependencies
    -Help           Show this help message

This script will install:
    - UV package manager (automatically if missing)
    - All core dependencies
    - Development tools (pytest, black, flake8, mypy)
    - Visualization tools (matplotlib)
    - Pre-commit hooks
    - VS Code extensions (if VS Code is available)

"@ -ForegroundColor White
}

function Install-PreCommitHooks {
    Write-Info "Setting up pre-commit hooks..."

    # Install pre-commit via uv
    uv add --dev pre-commit 2>&1 | Out-Null

    # Create .pre-commit-config.yaml
    $preCommitConfig = @"
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
"@

    if (-not (Test-Path ".pre-commit-config.yaml") -or $Force) {
        $preCommitConfig | Out-File -FilePath ".pre-commit-config.yaml" -Encoding UTF8
        Write-Success "✓ Created .pre-commit-config.yaml"
    }

    # Install the hooks
    uv run pre-commit install 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Pre-commit hooks installed"
    } else {
        Write-Warning "⚠ Failed to install pre-commit hooks"
    }
}

function Setup-VSCodeExtensions {
    # Check if VS Code is available
    try {
        code --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "VS Code not found in PATH, skipping extension setup"
            return
        }
    } catch {
        Write-Warning "VS Code not available, skipping extension setup"
        return
    }

    Write-Info "Installing recommended VS Code extensions..."

    $extensions = @(
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "ms-python.mypy-type-checker",
        "ms-python.pytest",
        "ms-vscode.test-adapter-converter",
        "ms-vscode.makefile-tools",
        "redhat.vscode-yaml",
        "ms-vscode.powershell"
    )

    foreach ($ext in $extensions) {
        Write-Host "  Installing $ext..." -NoNewline
        code --install-extension $ext 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success " ✓"
        } else {
            Write-Warning " ⚠"
        }
    }
}

function Create-DevScripts {
    Write-Info "Creating development scripts..."    # Create test script
    $testScript = @"
#!/usr/bin/env python3
"""
Development test runner with coverage and reporting
"""
import subprocess
import sys
import os

def run_tests():
    """Run tests with coverage"""
    cmd = [
        "uv", "run", "pytest",
        "tests/",
        "-v",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--tb=short"
    ]

    print("Running tests with coverage...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✓ All tests passed!")
        print("Coverage report generated in htmlcov/")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
"@

    $testScript | Out-File -FilePath "scripts\test.py" -Encoding UTF8 -Force    # Create format script
    $formatScript = @"
#!/usr/bin/env python3
"""
Code formatting and linting script
"""
import subprocess
import sys
import os

def format_code():
    """Format code with black"""
    print("Formatting code with black...")
    subprocess.run(["uv", "run", "black", "src/", "tests/", "examples/"])

def lint_code():
    """Lint code with flake8"""
    print("Linting code with flake8...")
    result = subprocess.run(["uv", "run", "flake8", "src/", "tests/", "examples/"])
    return result.returncode == 0

def type_check():
    """Type check with mypy"""
    print("Type checking with mypy...")
    result = subprocess.run(["uv", "run", "mypy", "src/"])
    return result.returncode == 0

def main():
    format_code()
    lint_passed = lint_code()
    type_passed = type_check()

    if lint_passed and type_passed:
        print("\n✓ All checks passed!")
    else:
        print("\n❌ Some checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
"@

    # Create scripts directory if it doesn't exist
    if (-not (Test-Path "scripts")) {
        New-Item -ItemType Directory -Path "scripts" -Force | Out-Null
    }

    $formatScript | Out-File -FilePath "scripts\format.py" -Encoding UTF8 -Force

    Write-Success "✓ Development scripts created in scripts/"
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
        Write-Info "This may take a few minutes..."

        # Install uv using the official installer
        $installResult = Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing | Invoke-Expression

        # Refresh PATH for current session
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "Machine")

        # Test installation
        Start-Sleep -Seconds 2  # Give time for PATH to refresh
        $uvVersion = uv --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ uv installed successfully ($uvVersion)"
            return $true
        } else {
            Write-Error "Failed to verify uv installation"
            Write-Warning "You may need to restart your terminal or run: refreshenv"
            return $false
        }
    }
    catch {
        Write-Error "Failed to install uv: $_"
        Write-Info "You can manually install uv from: https://docs.astral.sh/uv/getting-started/installation/"
        return $false
    }
}

function Test-UvFunctionality {
    Write-Info "Testing uv functionality..."
    try {
        # Test basic uv commands
        uv --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "uv --version failed"
            return $false
        }

        # Test uv in project context
        if (Test-Path "pyproject.toml") {
            uv info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ uv is working correctly with project"
            } else {
                Write-Warning "⚠ uv project context may need initialization"
            }
        }

        return $true
    }
    catch {
        Write-Error "uv functionality test failed: $_"
        return $false
    }
}

function Main {
    if ($Help) {
        Show-Help
        return
    }

    Write-Host @"
============================================================================
🛠️  DRONE CONTROLLER DEVELOPMENT ENVIRONMENT SETUP
============================================================================
"@ -ForegroundColor Cyan

    Write-Info "Setting up complete development environment..."
    if ($Force) { Write-Info "Force reinstall enabled" }

    try {
        # Check prerequisites
        Write-Info "Checking prerequisites..."
        if (-not (Test-UvInstalled)) {
            Write-Error "Failed to install uv package manager"
            exit 1
        }

        # Test uv functionality
        if (-not (Test-UvFunctionality)) {
            Write-Error "uv is not working correctly"
            exit 1
        }

        # Run main setup first
        Write-Info "Running main setup script..."
        if ($Force) {
            & ".\setup.ps1" -Dev -Visualization -Force
        } else {
            & ".\setup.ps1" -Dev -Visualization
        }

        if ($LASTEXITCODE -ne 0) {
            throw "Main setup failed"
        }

        # Additional development tools
        Write-Info "Installing additional development tools..."
        uv add --dev pytest-cov pytest-xdist coverage 2>&1 | Out-Null

        # Setup pre-commit hooks
        Install-PreCommitHooks

        # Setup VS Code extensions
        Setup-VSCodeExtensions

        # Create development scripts
        Create-DevScripts

        Write-Host @"

============================================================================
🎉 DEVELOPMENT ENVIRONMENT READY!
============================================================================

Your complete development environment is set up! Here's what's available:

DEVELOPMENT COMMANDS:
    uv run python scripts/test.py       # Run tests with coverage
    uv run python scripts/format.py     # Format and lint code
    uv run pre-commit run --all-files   # Run all pre-commit hooks

TESTING:
    uv run pytest tests/ -v             # Run tests
    uv run pytest tests/ -v --cov=src   # Run tests with coverage
    uv run pytest tests/ -x             # Stop on first failure

CODE QUALITY:
    uv run black src/ tests/ examples/  # Format code
    uv run flake8 src/ tests/ examples/ # Lint code
    uv run mypy src/                     # Type checking

PROJECT COMMANDS:
    uv run python main.py --mode single --demo    # Single drone demo
    uv run python main.py --mode swarm --demo     # Swarm demo

DEPENDENCY MANAGEMENT:
    uv add package-name                  # Add production dependency
    uv add --dev package-name            # Add development dependency
    uv sync                              # Sync all dependencies
    uv lock                              # Update lock file

VS CODE:
    - Recommended extensions installed
    - Python environment configured
    - Debugging ready

Happy coding! 🚁✨
============================================================================

"@ -ForegroundColor Green

    }
    catch {
        Write-Error @"

============================================================================
❌ DEVELOPMENT SETUP FAILED
============================================================================
Error: $_

Please check the error message above and try again.
============================================================================
"@
        exit 1
    }
}

Main
