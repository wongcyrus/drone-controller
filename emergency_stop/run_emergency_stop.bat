@echo off
echo Starting Emergency Stop GUI...
echo.
echo This GUI provides an emergency stop button for drone operations.
echo Keep this window open while running drone scripts.
echo.

REM Check if virtual environment exists, if not create it
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt >nul 2>&1
) else (
    call .venv\Scripts\activate
)

REM Run the emergency stop GUI
python emergency_stop_ui.py

deactivate

echo.
echo Emergency Stop GUI closed.
pause
