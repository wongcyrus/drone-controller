# Port Configuration Guide

## ✅ Working Configuration

The WebSocket server port has been changed to **8766** to avoid conflicts.

### Default Ports:
- **Web Server**: `8000`
- **WebSocket Server**: `8766` (changed from 8765)
- **Drone UDP**: `8889+` (sequential)

## 🚀 Quick Start Commands

### Simple Start (Recommended):
```bash
cd webapp
./start_simulator.sh
```

### Original Start Script:
```bash
./start_mock_drone.sh --multiple 3
```

### Manual Start:
```bash
python3 mock_drone.py --host 0.0.0.0 --web-port 8000 --webapp-port 8766 --multiple 3
```

## 🔧 Port Management

### Check Available Ports:
```bash
./configure_ports.sh
```

### Custom Port Configuration:
```bash
# Use different ports if needed
./start_mock_drone.sh --web-port 8080 --webapp-port 8767 --multiple 3

# Or with specific drone ports
python3 mock_drone.py --web-port 8001 --webapp-port 8766 --port 9000 --multiple 2
```

## 🌐 Access URLs

Replace `172.28.3.205` with your WSL IP (get it with `./get_wsl_ip.sh`):

### From WSL:
- **Web Interface**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8766`

### From Windows:
- **Web Interface**: `http://172.28.3.205:8000`
- **WebSocket**: `ws://172.28.3.205:8766`

## 🔍 Troubleshooting

### Check Current Ports:
```bash
# Check what's running
ss -tln | grep -E ":(8000|8766|8889)"

# Check specific port
ss -tln | grep :8766
```

### Kill Existing Processes:
```bash
# Kill all mock drone processes
pkill -f mock_drone.py

# Kill specific ports
lsof -ti:8000 | xargs kill -9
lsof -ti:8766 | xargs kill -9
```

### Find Alternative Ports:
```bash
# Get port recommendations
./configure_ports.sh

# Test connectivity
./get_wsl_ip.sh
```

## 📋 Port Conflict Solutions

### If Port 8000 is in use:
```bash
./start_simulator.sh --web-port 8080
```

### If Port 8766 is in use:
```bash
./start_simulator.sh --webapp-port 8767
```

### If Multiple Ports are in use:
```bash
# Use completely different port range
python3 mock_drone.py --web-port 3000 --webapp-port 3001 --port 9000 --multiple 3
```

## 🧪 Testing

### Test from WSL:
```bash
curl http://localhost:8000
```

### Test from Windows:
```powershell
# PowerShell
.\Test-WSLConnectivity.ps1

# Or manually
$WSL_IP = (wsl hostname -I).Trim()
Invoke-WebRequest "http://$WSL_IP:8000"
```

## 📁 Related Files

- `start_simulator.sh` - Simple start script with working ports
- `configure_ports.sh` - Port availability checker
- `get_wsl_ip.sh` - WSL IP detection and connectivity test
- `Test-WSLConnectivity.ps1` - Windows connectivity test

## 💡 Tips

1. **Always use `0.0.0.0` for host binding** to allow Windows access
2. **Check port availability** before starting with `./configure_ports.sh`
3. **Use consistent ports** across all components
4. **Test connectivity** with `./get_wsl_ip.sh` after starting
5. **Kill existing processes** if you get "port in use" errors
