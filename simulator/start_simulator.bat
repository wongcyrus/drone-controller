@echo off
title Drone Simulator 3D
echo.
echo 🚁 Drone Simulator 3D
echo ==================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.7 or higher.
    echo 📥 Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "index.html" (
    echo ❌ Simulator files not found!
    echo 📂 Please run this script from the simulator directory.
    pause
    exit /b 1
)

echo ✅ Starting simulator...
echo.

REM Try to start with Python bridge first
python start_simulator.py
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Python bridge failed. Opening simulator directly...
    echo.

    REM Fallback to opening HTML file directly
    start "" "index.html"
    echo 🌐 Simulator opened in your default browser.
    echo.
    echo 📝 Note: For full Python integration features, install:
    echo    pip install websockets
    echo.
)

echo.
echo ✨ Simulator started successfully!
echo 🎮 Use the controls in the web interface to fly drones.
echo.
pause
