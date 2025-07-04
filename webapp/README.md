# Drone Simulator WebApp

A comprehensive 3D drone simulator with real-time control and visualization using Three.js and WebSockets.

## Features

- **3D Visualization**: Real-time 3D representation of drones using Three.js
- **WebSocket Communication**: Real-time bidirectional communication between drones and webapp
- **Multiple Drone Support**: Control and monitor multiple drones simultaneously
- **Manual Controls**: Intuitive web interface for drone control
- **Command Console**: Real-time command and response logging
- **Virtual Drones**: Create virtual drones for testing without hardware
- **UDP Integration**: Compatible with existing Tello drone protocols

## Quick Start

### 1. Setup Virtual Environment
```bash
cd /path/to/drone-controller
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r webapp/requirements.txt
```

### 2. Start the Simulator
```bash
cd webapp
./start_simulator.sh
```

This starts a single drone simulator (WSL limitation - only one IP available for binding).

### 3. Access the WebApp
- **From WSL**: `http://localhost:8000`
- **From Windows**: `http://<WSL-IP>:8000` (get IP with `./get_wsl_ip.sh`)

## Port Configuration

### Default Ports
- **Web Server**: `8000`
- **WebSocket Server**: `8766`
- **Drone UDP**: `8889+` (sequential)

### Check Ports and WSL IP
```bash
# Check available ports
./configure_ports.sh

# Get WSL IP for Windows access
./get_wsl_ip.sh
```

## Usage Examples

### Basic Usage
```bash
# Start single drone (WSL default)
./start_simulator.sh

# Start with custom name
python3 mock_drone.py --name "MyDrone" --host 0.0.0.0 --ip 0.0.0.0

# Use custom ports
python3 mock_drone.py --web-port 8080 --webapp-port 8767 --host 0.0.0.0 --ip 0.0.0.0
```

### Multiple Drones (Linux only)
```bash
# Multiple drones only work on systems with multiple bindable IPs
# Not supported in WSL due to IP binding limitations
python3 mock_drone.py --multiple 3 --ip 127.0.0.1  # Linux only
```

### Integration with djitellopy
```python
from djitellopy import Tello

# Connect to a simulated drone
tello = Tello()
tello.connect('127.0.0.1')  # or other drone IP

# Commands will appear in the webapp
tello.takeoff()
tello.move_forward(50)
tello.land()
```

## Windows-WSL Connectivity

### From Windows
1. **Test connectivity**: Run `Test-WSLConnectivity.ps1` in PowerShell
2. **Get WSL IP**: `wsl ./get_wsl_ip.sh`
3. **Access webapp**: `http://<WSL-IP>:8000`

### Troubleshooting
- Ensure server binds to `0.0.0.0` (not `127.0.0.1`)
- Check Windows Firewall settings
- Try: `wsl --shutdown` then restart WSL

## File Structure

```
webapp/
├── mock_drone.py              # Main simulator
├── mock_tello_drone.py        # Core drone functionality
├── websocket_server.py        # WebSocket server
├── web_server.py             # Flask web server
├── start_simulator.sh        # Start script
├── get_wsl_ip.sh            # WSL IP detection
├── configure_ports.sh       # Port management
├── Test-WSLConnectivity.ps1 # Windows testing
├── requirements.txt         # Dependencies
├── PORT_CONFIGURATION.md    # Port guide
├── templates/              # HTML templates
│   └── index.html
└── static/                # CSS, JS, assets
    ├── css/
    ├── js/
    └── ...
```

## Command Line Options

```bash
python3 mock_drone.py --help
```

**Options:**
- `--host HOST`: Host to bind servers to (default: 0.0.0.0)
- `--ip IP`: IP address to bind drones to (default: 127.0.0.1)
- `--multiple N`: Number of drones to create (default: 1)
- `--name NAME`: Name for single drone instance
- `--port PORT`: Starting command port for drones (default: 8889)
- `--webapp-port PORT`: WebSocket server port (default: 8766)
- `--web-port PORT`: Web server port (default: 8000)
- `--no-webapp`: Disable webapp integration

## WebApp Interface

### Main Components
1. **3D Viewport**: Interactive 3D scene showing drones and environment
2. **Drone List**: Shows all connected drones with status indicators
3. **Control Panel**: Manual controls for selected drone
4. **Console**: Real-time command and response logging
5. **Connection Status**: WebSocket connection indicator

### Manual Controls
- **Basic Commands**: SDK Mode, Takeoff, Land, Emergency
- **Movement**: Up, Down, Left, Right, Forward, Back
- **Rotation**: Clockwise, Counter-clockwise
- **Custom Commands**: Send any Tello command directly

## API Reference

### WebSocket Messages

**Client → Server:**
```json
{
  "type": "drone_command",
  "drone_id": "Drone-1",
  "command": "takeoff"
}
```

**Server → Client:**
```json
{
  "type": "drone_state",
  "drone_id": "Drone-1",
  "data": {
    "h": 50,
    "bat": 85,
    "yaw": 45
  }
}
```

### REST API
- `GET /` - Main interface
- `GET /api/drones` - Get drone list
- `POST /api/command` - Send command to drone

## Development

### Adding New Features
1. **New Commands**: Add to `mock_tello_drone.py`
2. **3D Effects**: Extend `static/js/three-scene.js`
3. **UI Elements**: Modify `templates/index.html` and `static/css/style.css`
4. **WebSocket Events**: Add handlers in `static/js/websocket-client.js`

### Browser Compatibility
- Chrome/Chromium 60+
- Firefox 55+
- Safari 11+
- Edge 79+

WebGL and WebSocket support required.

## License

Same as the main project.
