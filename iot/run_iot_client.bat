@echo off
REM Windows Batch Script to run the IoT client
REM This script provides a simple way to start the IoT client on Windows

title Windows IoT Client for Drone Controller

echo =================================
echo Windows IoT Client Launcher
echo =================================
echo.

REM Get the directory where the batch file is located
cd /d "%~dp0"

echo Working directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and ensure it's added to your PATH
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade requirements
echo Installing/updating Python packages...
pip install -r requirements.txt --upgrade --quiet
if errorlevel 1 (
    echo WARNING: Some packages may have failed to install
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Set environment variables
set PYTHONPATH=%CD%
set IOT_CLIENT_OS=Windows
set IOT_CLIENT_PLATFORM=win32
set IOT_LOG_FILE=logs\iot_client_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%.log

echo.
echo Configuration:
echo - Config file: settings_windows.yaml
echo - Log file: %IOT_LOG_FILE%
echo - Platform: Windows
echo.

REM Check if Windows config exists, fallback to regular config
if exist "settings_windows.yaml" (
    set CONFIG_FILE=settings_windows.yaml
    echo Using Windows-specific configuration
) else (
    set CONFIG_FILE=settings.yaml
    echo Using default configuration
)

echo.
echo Starting IoT client...
echo Press Ctrl+C to stop the client
echo.

REM Run the client
python pubsub.py --config %CONFIG_FILE% --log-file "%IOT_LOG_FILE%"

REM Check exit code
if errorlevel 1 (
    echo.
    echo IoT client exited with error code %errorlevel%
) else (
    echo.
    echo IoT client stopped normally
)

echo.
pause
