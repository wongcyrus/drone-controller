# Tello UDP Simulator

This directory contains a standalone UDP-based simulator that mocks the actual Tello drone protocol. Unlike the old web-based simulator, this one properly simulates the low-level UDP communication that real Tello drones use.

## Architecture

The simulator consists of:

1. **UDP Simulator** (`udp_simulator.py`) - Core simulator that implements the Tello UDP protocol
2. **Startup Scripts** - Easy launchers for the simulator
3. **Web Visualizer** (legacy) - Optional 3D visualization (kept for reference)

## How It Works

The simulator creates virtual drones that:
- Listen on UDP port 8889 for commands (just like real Tello drones)
- Send state data on UDP port 8890 (just like real Tello drones)
- Respond to all standard Tello commands (`takeoff`, `land`, `move`, etc.)
- Simulate realistic movement, battery drain, and sensor data

## Quick Start

### Option 1: Use the Startup Scripts (Recommended)

**Windows:**
```bash
# Run from simulator directory
start_simulator.bat
# or
start_simulator.ps1
```

**Manual:**
```bash
cd simulator
python start_udp_simulator.py
```

### Option 2: Custom Configuration

```bash
# Start with specific drones
python udp_simulator.py --drones 3
python udp_simulator.py --drone-ids alpha beta gamma
python udp_simulator.py --base-ip 192.168.20 --start-host 10
```

## Default Drone IPs

When using `start_udp_simulator.py`, these drones are available:

- `drone_001` at `192.168.10.1`
- `drone_002` at `192.168.10.2`
- `drone_003` at `192.168.10.3`
- `alpha` at `192.168.10.4`
- `beta` at `192.168.10.5`
- `gamma` at `192.168.10.6`
- `delta` at `192.168.10.7`

## Usage with Main Application

1. **Start the simulator first:**
   ```bash
   cd simulator
   python start_udp_simulator.py
   ```

2. **In another terminal, run your drone application:**
   ```bash
   # Single drone mode
   python main.py --mode single --drone-id drone_001 --ip 192.168.10.1

   # Swarm mode (auto-loads from config)
   python main.py --mode swarm
   ```

## Supported Commands

The simulator supports all standard Tello commands:

- **Basic**: `command`, `takeoff`, `land`, `emergency`
- **Movement**: `up X`, `down X`, `left X`, `right X`, `forward X`, `back X`
- **Rotation**: `cw X`, `ccw X`
- **Complex**: `go X Y Z SPEED`
- **Queries**: `battery?`, `speed?`, `time?`, `height?`, `temp?`, `attitude?`, `baro?`, `acceleration?`, `tof?`, `wifi?`
- **Video**: `streamon`, `streamoff`

## Features

- **Realistic Movement**: Smooth interpolated movement with physics-based easing
- **State Simulation**: Battery drain, temperature, altitude, orientation
- **Multi-Drone Support**: Simulate multiple drones simultaneously
- **Protocol Accurate**: Matches real Tello UDP protocol exactly
- **Configurable**: Custom IP ranges, drone counts, and IDs

## Differences from Real Drones

- **No Video Stream**: Video commands are accepted but no actual stream is provided
- **Simplified Physics**: Basic movement simulation (no wind, momentum, etc.)
- **Instant Response**: Commands execute immediately (no physical motor delays)
- **Perfect Conditions**: No communication errors or interference simulation

## Legacy Web Simulator

The original web-based 3D simulator is still available in this directory but is not used by the main application. It can be accessed by opening `index.html` in a browser for visualization purposes.

## Troubleshooting

**"Address already in use" error:**
- Another instance of the simulator is already running
- Kill existing Python processes: `taskkill /f /im python.exe` (Windows)

**"No drone found" in main app:**
- Ensure simulator is running first
- Check that IP addresses match between simulator and main app
- Verify Windows Firewall isn't blocking UDP ports 8889/8890

**Connection timeouts:**
- The simulator may need a moment to fully start
- Try connecting to the drone after seeing "Simulator ready!" message
