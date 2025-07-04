@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Drone Controller Project Setup Script (CMD version)
REM ============================================================================
REM Simple setup script for drone controller project
REM ============================================================================

echo.
echo ============================================================================
echo 🚁 DRONE CONTROLLER PROJECT SETUP
echo ============================================================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11 or higher and try again
    pause
    exit /b 1
)

python --version
echo ✓ Python found

REM Check uv installation
echo.
echo Checking uv installation...
uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv package manager...
    powershell -Command "Invoke-WebRequest -Uri 'https://astral.sh/uv/install.ps1' -UseBasicParsing | Invoke-Expression"
    if errorlevel 1 goto :error
    echo ✓ uv installed
) else (
    echo ✓ uv found
)

REM Sync project dependencies
echo.
echo Installing project dependencies with uv...
uv sync
if errorlevel 1 goto :error

echo.
echo ============================================================================
echo 🎉 SETUP COMPLETE!
echo ============================================================================
echo.
echo Your drone controller environment is ready!
echo.
echo TESTING THE INSTALLATION:
echo   uv run python main.py --mode single --demo
echo   uv run python main.py --mode swarm --demo
echo.
echo CONNECTING REAL DRONES:
echo   1. Turn on your Tello Talent drone(s)
echo   2. Connect to the drone's Wi-Fi network
echo   3. Run: uv run python main.py --mode single
echo.
echo Happy flying! 🚁
echo ============================================================================
echo.
pause
exit /b 0

:error
echo.
echo ============================================================================
echo ❌ SETUP FAILED
echo ============================================================================
echo.
echo Installation failed. Please check the error messages above.
echo You may need to:
echo   1. Run as Administrator
echo   2. Check your internet connection
echo   3. Ensure Python and uv are properly installed
echo.
pause
exit /b 1
