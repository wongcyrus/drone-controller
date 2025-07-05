# Drone Simulator WebApp - Project Structure

## Core Application Files

### Python Backend
- `mock_drone.py` - Main application entry point and orchestrator
- `mock_tello_drone.py` - Core Tello drone simulation logic
- `websocket_server.py` - WebSocket server for real-time communication
- `web_server.py` - Flask web server for HTTP endpoints
- `requirements.txt` - Python dependencies

### Frontend (Static Files)
```
static/
├── css/
│   └── style.css - Main stylesheet
├── js/
│   ├── app.js - Main application controller
│   ├── drone-simulator.js - Drone simulation logic
│   ├── three-scene.js - 3D visualization with Three.js
│   └── websocket-client.js - WebSocket client communication
└── libs/ - Third-party JavaScript libraries
```

### Templates
```
templates/
└── index.html - Main web interface
```

## Utility Scripts

### Setup & Configuration
- `start_simulator.sh` - Main startup script for single drone
- `configure_ports.sh` - Port configuration and availability checker
- `get_wsl_ip.sh` - WSL IP address detection for Windows connectivity

### Windows Support
- `Test-WSLConnectivity.ps1` - PowerShell script for testing WSL connectivity

## Documentation
- `README.md` - Main documentation and usage guide
- `PORT_CONFIGURATION.md` - Detailed port configuration guide
- `PROJECT_STRUCTURE.md` - This file

## Key Features

### 3D Visualization
- Real-time 3D drone representation using Three.js
- Interactive camera controls (orbit, zoom, pan)
- Visual feedback for drone movements and status
- Trail visualization for flight paths

### Real-time Communication
- WebSocket server for bidirectional communication
- UDP simulation of Tello drone protocol
- State broadcasting and command execution
- Multiple drone support

### Web Interface
- Manual drone controls
- Command console with real-time logging
- Drone status monitoring
- Connection management

## Architecture

```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│   Web Browser   │◄──────────────►│  WebSocket       │
│   (Frontend)    │                 │  Server          │
└─────────────────┘                 └──────────────────┘
                                             │
                                             ▼
┌─────────────────┐    UDP Commands ┌──────────────────┐
│  djitellopy     │◄──────────────►│  Mock Tello      │
│  Client         │                 │  Drone           │
└─────────────────┘                 └──────────────────┘
```

## Development Guidelines

### File Organization
- Keep core logic in separate modules
- Maintain clear separation between frontend and backend
- Use descriptive file names and consistent structure

### Code Quality
- Follow Python PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for all public functions
- Keep functions focused and modular

### Testing
- Test files should be in a separate `tests/` directory (not in main webapp folder)
- Use descriptive test names
- Clean up test files after development

### Version Control
- Use `.gitignore` to exclude temporary files
- Commit logical, atomic changes
- Write clear commit messages
- Remove development/debug files before committing
