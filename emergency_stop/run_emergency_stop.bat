@echo off
echo Starting Emergency Stop GUI...
echo.
echo This GUI provides an emergency stop button for drone operations.
echo Keep this window open while running drone scripts.
echo.

REM Try to install psutil if needed (optional for better process detection)
pip install psutil >nul 2>&1

REM Run the emergency stop GUI
python emergency_stop_ui.py

echo.
echo Emergency Stop GUI closed.
pause
