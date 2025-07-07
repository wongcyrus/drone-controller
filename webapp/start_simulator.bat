@echo off
setlocal enabledelayedexpansion

REM Simple start script for drone simulator with working ports

echo 🚁 Starting Drone Simulator
echo ==========================

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%\.."

REM Check for and activate virtual environment
if exist "%PROJECT_DIR%\.venv-windows\" (
    call "%PROJECT_DIR%\.venv-windows\Scripts\activate.bat"
    echo ✅ Activated virtual environment ^(.venv-windows^)
) else if exist "%PROJECT_DIR%\.venv\" (
    call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
    echo ✅ Activated virtual environment ^(.venv^)
) else (
    echo ⚠️  Using system Python
)

REM Change to webapp directory
cd /d "%SCRIPT_DIR%"

REM Set default ports (can be overridden with command line arguments)
set "WEB_PORT=8000"
set "WEBAPP_PORT=8766"
set "DRONE_PORT=8889"
set "MULTIPLE=2"
set "HOST_ADDRESS=0.0.0.0"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="--web-port" (
    set "WEB_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--webapp-port" (
    set "WEBAPP_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--port" (
    set "DRONE_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--multiple" (
    set "MULTIPLE=%~2"
    shift
    shift
    goto :parse_args
)
shift
goto :parse_args

:done_parsing

echo.
echo 🔧 Configuration:
echo   Web Server: %HOST_ADDRESS%:%WEB_PORT%
echo   WebSocket: %HOST_ADDRESS%:%WEBAPP_PORT%
echo   Drone UDP: %HOST_ADDRESS%:%DRONE_PORT% ^(swarm mode^)
echo   Multiple Drones: %MULTIPLE%

echo.
echo 🌐 Access URLs:
echo   Local: http://localhost:%WEB_PORT%

echo.
echo 🚀 Starting simulator...

REM Start with single drone using multiple mode for proper networking
python mock_drone.py --host %HOST_ADDRESS% --ip %HOST_ADDRESS% --web-port %WEB_PORT% --webapp-port %WEBAPP_PORT% --port %DRONE_PORT% --multiple %MULTIPLE%
