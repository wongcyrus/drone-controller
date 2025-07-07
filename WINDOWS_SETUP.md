# 🪟 Windows Environment Setup Guide

This guide provides comprehensive instructions for setting up and running the Drone Controller project on Windows.

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Windows-Specific Scripts](#-windows-specific-scripts)
- [Network Configuration](#-network-configuration)
- [Troubleshooting](#-troubleshooting)
- [Development Setup](#-development-setup)

## 🔧 Prerequisites

### Required Software

1. **Python 3.11 or higher**
   - Download from: https://www.python.org/downloads/
   - ✅ Add Python to PATH during installation
   - ✅ Install pip (included by default)

2. **PowerShell 5.1 or higher** (usually pre-installed)
   - Check version: `$PSVersionTable.PSVersion`
   - Upgrade if needed: https://docs.microsoft.com/en-us/powershell/

3. **Windows Terminal** (recommended)
   - Install from Microsoft Store
   - Better Unicode support for emojis in scripts

### Optional Software

- **Git for Windows** (for development)
- **Visual Studio Code** (recommended IDE)
- **Windows Subsystem for Linux (WSL)** (optional, for mixed environments)

## 🚀 Installation

### Method 1: PowerShell Setup (Recommended)

1. **Open PowerShell as Administrator**
   - Right-click Start button → "Windows PowerShell (Admin)"
   - Or search "PowerShell" → Right-click → "Run as administrator"

2. **Navigate to project directory**
   ```powershell
   cd "e:\working\drone-controller"
   ```

3. **Run setup script**
   ```powershell
   # Basic installation
   .\setup.ps1

   # Development installation
   .\setup.ps1 -Dev

   # Development with visualization tools
   .\setup.ps1 -Dev -Visualization

   # Force reinstall everything
   .\setup.ps1 -Dev -Force
   ```

### Method 2: Batch File Setup (Simple)

1. **Open Command Prompt as Administrator**
   - Press `Win + R`, type `cmd`, press `Ctrl + Shift + Enter`

2. **Navigate and run**
   ```cmd
   cd "e:\working\drone-controller"
   setup.bat
   ```

### Method 3: Manual Setup

```powershell
# Install uv package manager
Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1" | Invoke-Expression

# Install dependencies
uv sync

# For development
uv sync --dev
```

## 📜 Windows-Specific Scripts

The project includes several PowerShell and batch scripts for Windows users:

### 🚁 Simulator Scripts

#### `webapp\start_simulator.ps1`
PowerShell script to start the drone simulator with full parameter support:

```powershell
# Start with default settings
.\start_simulator.ps1

# Custom configuration
.\start_simulator.ps1 -WebPort 8080 -WebAppPort 8767 -Multiple 3

# Bind to specific host
.\start_simulator.ps1 -Host "192.168.1.100"
```

#### `webapp\start_simulator.bat`
Batch file equivalent for simpler usage:

```cmd
REM Start with default settings
start_simulator.bat

REM Custom configuration
start_simulator.bat --web-port 8080 --webapp-port 8767 --multiple 3
```

### 🔧 Configuration Scripts

#### `webapp\configure_ports.ps1`
Check port availability and find alternative ports:

```powershell
.\configure_ports.ps1
```

**Output:**
```
🔧 Port Configuration Helper
============================

📡 Current Port Status:
  Port 8000: ✅ Available
  Port 8765: ❌ In use
  Port 8766: ✅ Available

🔍 Finding Available Ports:
  Web Server: 8000
  WebSocket: 8766
  Drone UDP: 8889

🚀 Recommended Start Command:
  .\start_simulator.ps1 -WebPort 8000 -WebAppPort 8766 -DronePort 8889
```

#### `webapp\get_local_ip.ps1`
Get local IP address for network access:

```powershell
.\get_local_ip.ps1
```

**Output:**
```
🔍 Finding Local IP addresses...

📡 IP Detection Methods:
  Method 1 (Get-NetIPAddress): 192.168.1.100
  Method 2 (WMI): 192.168.1.100
  Method 3 (Test-Connection): 192.168.1.100

✅ Local IP Address Found: 192.168.1.100

🌐 Recommended URLs for network access:
  Web Interface: http://192.168.1.100:8000
  WebSocket: ws://192.168.1.100:8766
```

### 🛠️ Setup Scripts

#### `setup.ps1`
Main PowerShell setup script with advanced options:

```powershell
# Basic setup
.\setup.ps1

# Development setup with extra tools
.\setup.ps1 -Dev

# Include visualization libraries
.\setup.ps1 -Visualization

# Force clean install
.\setup.ps1 -Force
```

## 🌐 Network Configuration

### Local Development

For local development on a single Windows machine:

1. **Start the simulator:**
   ```powershell
   cd webapp
   .\start_simulator.ps1
   ```

2. **Access from browser:**
   - Local: http://localhost:8000
   - Network: http://YOUR_IP:8000 (get IP with `.\get_local_ip.ps1`)

### Network Access

To allow other devices to connect to your Windows machine:

1. **Check Windows Firewall:**
   ```powershell
   # Allow Python through firewall (run as Administrator)
   New-NetFirewallRule -DisplayName "Python Drone Simulator" -Direction Inbound -Program (Get-Command python).Source -Action Allow
   ```

2. **Get your IP address:**
   ```powershell
   .\webapp\get_local_ip.ps1
   ```

3. **Test connectivity:**
   ```powershell
   # From the same machine
   Test-NetConnection -ComputerName localhost -Port 8000

   # From another machine (replace with your IP)
   Test-NetConnection -ComputerName 192.168.1.100 -Port 8000
   ```

### Windows Firewall Configuration

If you encounter connection issues:

1. **Open Windows Defender Firewall**
   - Search "Windows Defender Firewall" in Start menu

2. **Allow an app through firewall**
   - Click "Allow an app or feature through Windows Defender Firewall"
   - Click "Change Settings" (requires admin)
   - Find Python or click "Allow another app..."
   - Browse to your Python installation (usually `C:\Users\USERNAME\AppData\Local\Programs\Python\Python311\python.exe`)
   - ✅ Check both "Private" and "Public" networks

3. **Or create a rule for the port:**
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "Drone Simulator Port 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   New-NetFirewallRule -DisplayName "Drone WebSocket Port 8766" -Direction Inbound -Protocol TCP -LocalPort 8766 -Action Allow
   New-NetFirewallRule -DisplayName "Drone UDP Port 8889" -Direction Inbound -Protocol UDP -LocalPort 8889 -Action Allow
   ```

## 🐛 Troubleshooting

### Common Issues

#### 1. PowerShell Execution Policy

**Error:** `cannot be loaded because running scripts is disabled on this system`

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Python Not Found

**Error:** `python : The term 'python' is not recognized`

**Solutions:**
```powershell
# Check if Python is installed
Get-Command python

# If not found, add to PATH or reinstall Python
# Or use full path:
C:\Users\USERNAME\AppData\Local\Programs\Python\Python311\python.exe -m pip --version
```

#### 3. Port Already in Use

**Error:** `OSError: [WinError 10048] Only one usage of each socket address`

**Solutions:**
```powershell
# Check what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID 1234 /F

# Or use the port configuration script
.\webapp\configure_ports.ps1
```

#### 4. Network Access Issues

**Symptoms:** Can't access from other devices on network

**Solutions:**
1. **Check firewall settings** (see Network Configuration section)
2. **Verify IP address:**
   ```powershell
   .\webapp\get_local_ip.ps1
   ```
3. **Test local connectivity:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 8000
   ```
4. **Check if server is binding to 0.0.0.0:**
   - The simulator should show `Web Server: 0.0.0.0:8000`
   - Not `127.0.0.1:8000`

#### 5. Virtual Environment Issues

**Error:** Issues with virtual environment activation

**Solutions:**
```powershell
# Manual activation
.\.venv\Scripts\Activate.ps1

# Or recreate environment
Remove-Item -Recurse -Force .venv
.\setup.ps1 -Force
```

### Performance Optimization

1. **Disable Windows Defender real-time scanning** for the project folder (temporarily)
2. **Use Windows Terminal** instead of Command Prompt for better performance
3. **Close unnecessary applications** to free up ports and resources

## 🔧 Development Setup

### Full Development Environment

For a complete development setup:

```powershell
# Install all development tools
.\setup.ps1 -Dev -Visualization

# This installs:
# - pytest (testing)
# - black (code formatting)
# - flake8 (linting)
# - mypy (type checking)
# - pre-commit (git hooks)
# - matplotlib (plotting)
# - plotly (interactive plots)
# - opencv-python (computer vision)
# - pillow (image processing)
```

### IDE Configuration

#### Visual Studio Code

1. **Install Python extension**
2. **Select interpreter:**
   - Press `Ctrl + Shift + P`
   - Type "Python: Select Interpreter"
   - Choose `.venv\Scripts\python.exe`

3. **Recommended extensions:**
   - Python
   - Python Docstring Generator
   - autoDocstring
   - GitLens

#### PyCharm

1. **Configure interpreter:**
   - File → Settings → Project → Python Interpreter
   - Add → Existing environment
   - Point to `.venv\Scripts\python.exe`

### Testing

```powershell
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=.

# Run specific test
uv run pytest tests/test_mock_drone.py
```

### Code Quality

```powershell
# Format code
uv run black .

# Lint code
uv run flake8 .

# Type checking
uv run mypy .
```

## 📚 Additional Resources

- [Python Windows Installation Guide](https://docs.python.org/3/using/windows.html)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)
- [Windows Firewall Configuration](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-firewall/)
- [uv Package Manager](https://docs.astral.sh/uv/)

## 💡 Tips

1. **Use Windows Terminal** for the best experience with Unicode characters and emojis
2. **Run PowerShell as Administrator** when installing or when you encounter permission issues
3. **Keep Windows Defender exceptions** for your development folder to improve performance
4. **Use the provided scripts** instead of manual commands for consistent results
5. **Check port availability** with `.\configure_ports.ps1` before starting the simulator
