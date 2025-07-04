# Clean WebApp Structure

## ✅ Files Kept (Essential)

### Core Application
- `mock_drone.py` - Main drone simulator
- `mock_tello_drone.py` - Core drone functionality
- `websocket_server.py` - WebSocket server for real-time communication
- `web_server.py` - Flask web server

### Scripts
- `start_simulator.sh` - **Main start script** (use this!)
- `get_wsl_ip.sh` - WSL IP detection and connectivity test
- `configure_ports.sh` - Port availability checker

### Configuration & Documentation
- `requirements.txt` - Python dependencies
- `README.md` - Main documentation
- `PORT_CONFIGURATION.md` - Port configuration guide

### Web Assets
- `static/` - CSS, JavaScript, images
- `templates/` - HTML templates

### Windows Support
- `Test-WSLConnectivity.ps1` - Windows PowerShell connectivity test

## 🗑️ Files Removed (Cleaned Up)

### Backup Files
- `mock_drone.py.bak` - Old backup
- `mock_drone_simple.py` - Alternative version

### Old Setup Scripts
- `setup.ps1`, `setup_windows.bat`, `setup_wsl.sh`
- `quick_setup.sh`, `fix_permissions.sh`

### Old Start Scripts
- `start.sh`, `start_mock_drone.sh`, `start_mock_drone_debug.sh`

### Test & Debug Files
- `test_setup.sh`, `test_websocket.py`, `test_windows_connectivity.bat`

### Redundant Documentation
- `SETUP_WSL.md`, `WINDOWS_CONNECTIVITY_TROUBLESHOOTING.md`
- `WINDOWS_WSL_FIX_SUMMARY.md`, `WINDOWS_WSL_SETUP.md`

### Cache & Virtual Environments
- `__pycache__/` - Python cache
- `venv/` - Old virtual environment

## 🚀 Quick Start (Simplified)

### 1. Setup (One Time)
```bash
cd /path/to/drone-controller
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r webapp/requirements.txt
```

### 2. Start Simulator
```bash
cd webapp
./start_simulator.sh
```

### 3. Access
- **WSL**: `http://localhost:8000`
- **Windows**: `http://172.28.3.205:8000` (get IP with `./get_wsl_ip.sh`)

## 📋 Current Configuration

### Ports
- **Web Server**: `0.0.0.0:8000`
- **WebSocket**: `0.0.0.0:8766`
- **Drones**: `127.0.0.1:8889+`

### Features
- ✅ 3 virtual drones by default
- ✅ Real-time WebSocket communication
- ✅ 3D visualization
- ✅ Windows-WSL connectivity
- ✅ Manual drone controls
- ✅ Command console

## 🔧 Customization

### Different Number of Drones
```bash
python3 mock_drone.py --multiple 5
```

### Custom Ports
```bash
python3 mock_drone.py --web-port 8080 --webapp-port 8767
```

### Check Available Ports
```bash
./configure_ports.sh
```

## 📁 Final Directory Structure

```
webapp/
├── mock_drone.py              # Main simulator
├── mock_tello_drone.py        # Core drone logic
├── websocket_server.py        # WebSocket server
├── web_server.py             # Flask server
├── start_simulator.sh        # 🚀 Main start script
├── get_wsl_ip.sh            # WSL IP detection
├── configure_ports.sh       # Port management
├── Test-WSLConnectivity.ps1 # Windows testing
├── requirements.txt         # Dependencies
├── README.md               # Documentation
├── PORT_CONFIGURATION.md   # Port guide
├── static/                # Web assets
│   ├── css/
│   ├── js/
│   └── images/
└── templates/             # HTML templates
    └── index.html
```

## ✅ Verification

The cleaned structure is working perfectly:
- ✅ All 3 drones start successfully
- ✅ WebSocket server on port 8766
- ✅ Web server accessible from Windows
- ✅ No conflicts or errors
- ✅ Simplified usage with one command

**Use `./start_simulator.sh` for everything!** 🎉
