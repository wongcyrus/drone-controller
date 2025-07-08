# Emergency Stop GUI for Drone Controller

## Overview
This is a simple emergency stop GUI that provides a big red button to immediately stop drone operations from your `main.py` script.

## Features
- **Always-on-top window** - Stays visible above other windows
- **Single button interface** - Large emergency stop button
- **Multiple stop methods**:
  - Sends interrupt signals to Python processes
  - Attempts direct emergency commands to drones
  - Kills drone-related processes as backup
- **No process monitoring** - Lightweight, doesn't continuously monitor processes

## How to Use

### Method 1: Run directly
```bash
python emergency_stop_ui.py
```

### Method 2: Use batch file (Windows)
```bash
run_emergency_stop.bat
```

### Method 3: Use PowerShell script
```powershell
.\run_emergency_stop.ps1
```

## Usage Instructions

1. **Start the Emergency Stop GUI** before running your drone scripts
2. **Keep the GUI window open** while your `main.py` or other drone scripts are running
3. **Click the emergency stop button** if you need to immediately halt drone operations
4. **Confirm the action** when prompted
5. The GUI will:
   - Send interrupt signals to stop Python processes
   - Try to send emergency/land commands directly to drones
   - Kill any remaining drone-related processes
6. **Check your drones manually** after emergency stop to ensure they are safe

## What the Emergency Stop Does

When you click the emergency stop button, it performs these actions in order:

1. **Interrupt Signals**: Sends Ctrl+C equivalent to running Python processes
2. **Direct Drone Commands**: Attempts to connect to drones and send emergency/land commands
3. **Process Termination**: Kills Python processes related to drone control as a backup

## Drone IP Addresses

The emergency stop will try to send commands to these IP addresses:
- `172.28.3.205` (WSL IP from your main.py)
- `192.168.10.1` (Common Tello IP)
- `192.168.4.1` (Alternative Tello IP)

## Safety Notes

- ⚠️ **Use only in emergencies** - This forcefully stops all operations
- ⚠️ **Manual check required** - Always verify drone status after emergency stop
- ⚠️ **Keep GUI visible** - Don't minimize or close the emergency stop window
- ⚠️ **Test before flight** - Make sure the emergency stop works with your setup

## Troubleshooting

### GUI doesn't start
- Make sure Python is installed and in your PATH
- Check that tkinter is available (usually included with Python)

### Emergency stop doesn't work
- Verify the GUI can see your Python processes
- Check that drone IP addresses are correct
- Try running as administrator on Windows

### Process monitoring errors
- The GUI will work without `psutil` but won't show process status
- Install psutil for better functionality: `pip install psutil`

## Files Included

- `emergency_stop_ui.py` - Main GUI application
- `run_emergency_stop.bat` - Windows batch file to run GUI
- `run_emergency_stop.ps1` - PowerShell script to run GUI
- `emergency_stop_requirements.txt` - Optional dependencies

## Integration with main.py

Your `main.py` already has signal handlers for Ctrl+C, so the emergency stop GUI will work by sending interrupt signals. The GUI also tries direct drone commands as a backup.

The emergency stop is designed to work with your existing safety features in `main.py`:
- Signal handlers
- Emergency landing functions
- Timeout mechanisms
- Force exit protection
