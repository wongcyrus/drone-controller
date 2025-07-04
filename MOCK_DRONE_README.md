# Mock Tello Drone Simulator

A UDP-based mock implementation of the DJI Tello drone that simulates real drone behavior for testing TelloSwarm and Tello applications without actual hardware.

## Features

- **Complete UDP Communication**: Responds to commands on port 8889 and broadcasts state on port 8890
- **Real Tello Command Support**: Supports all major Tello SDK commands (takeoff, land, move, rotate, flip, etc.)
- **State Broadcasting**: Continuously broadcasts realistic drone state information
- **Multiple Drone Support**: Can run multiple mock drones on different IP addresses
- **Battery Simulation**: Simulates battery drain and charging behavior
- **Flight State Tracking**: Tracks flight status, height, orientation, and movement
- **Error Responses**: Returns appropriate error messages for invalid commands

## Quick Start

### 1. Start a Single Mock Drone

```bash
python mock_tello_drone.py
```

This starts a mock drone listening on `127.0.0.1:8889` for commands.

### 2. Test with DJITelloPy

```python
from djitellopy import Tello

# Connect to mock drone
tello = Tello("127.0.0.1")
tello.connect()

# Test basic commands
print(f"Battery: {tello.get_battery()}%")
tello.takeoff()
tello.move_up(50)
tello.rotate_clockwise(90)
tello.land()
```

### 3. Multiple Drones for Swarm Testing

```bash
# Terminal 1: Start first drone
python mock_tello_drone.py --ip 192.168.1.10 --name Drone1

# Terminal 2: Start second drone
python mock_tello_drone.py --ip 192.168.1.11 --name Drone2
```

Then test with TelloSwarm:

```python
from djitellopy import TelloSwarm

swarm = TelloSwarm.fromIps([
    "192.168.1.10",
    "192.168.1.11"
])

swarm.connect()
swarm.takeoff()
swarm.move_up(100)
swarm.land()
swarm.end()
```

## Command Line Options

- `--ip IP_ADDRESS`: IP address to bind to (default: 127.0.0.1)
- `--name NAME`: Name for this drone instance (default: MockTello)
- `--multiple COUNT`: Create multiple drones on sequential IPs

### Examples

```bash
# Single drone on localhost
python mock_tello_drone.py

# Drone on specific IP
python mock_tello_drone.py --ip 192.168.1.100 --name MyDrone

# Multiple drones on sequential IPs
python mock_tello_drone.py --ip 192.168.1.10 --multiple 3
# Creates drones on 192.168.1.10, 192.168.1.11, 192.168.1.12
```

## Supported Tello Commands

### Basic Control
- `command` - Enter SDK mode
- `takeoff` - Automatic takeoff
- `land` - Automatic landing
- `emergency` - Emergency stop

### Movement (20-500cm)
- `up X`, `down X`, `left X`, `right X`, `forward X`, `back X`

### Rotation (1-360°)
- `cw X` - Clockwise rotation
- `ccw X` - Counter-clockwise rotation

### Advanced Movement
- `flip X` - Flip in direction (l/r/f/b)
- `go X Y Z speed` - Fly to coordinates
- `curve X1 Y1 Z1 X2 Y2 Z2 speed` - Curved flight

### Settings
- `speed X` - Set speed (10-100)
- `rc a b c d` - RC control
- `wifi SSID PASS` - Set WiFi credentials

### Video Streaming
- `streamon` - Start video stream
- `streamoff` - Stop video stream

### Status Queries
- `battery?` - Get battery percentage
- `speed?` - Get current speed
- `time?` - Get flight time
- `height?` - Get current height
- `temp?` - Get temperature range
- `attitude?` - Get pitch, roll, yaw
- `baro?` - Get barometer reading
- `tof?` - Get ToF distance
- `wifi?` - Get WiFi signal strength
- `sdk?` - Get SDK version
- `sn?` - Get serial number

## State Information

The mock drone broadcasts state information every 100ms containing:

```
mid:-1;x:0;y:0;z:0;pitch:0;roll:0;yaw:0;vgx:0;vgy:0;vgz:0;templ:20;
temph:25;tof:10;h:0;bat:100;baro:1013.25;time:0;agx:0.0;agy:0.0;agz:-1000.0;
```

## Architecture

The mock drone consists of two main components:

1. **Command Listener** (Port 8889): Receives and processes Tello commands
2. **State Broadcaster** (Port 8890): Continuously broadcasts drone state

### Network Protocol

- **Commands**: UDP packets sent TO the drone on port 8889
- **Responses**: UDP responses sent FROM the drone back to the client
- **State**: UDP broadcasts sent FROM the drone on port 8890

## Testing Your Swarm Code

1. Start multiple mock drones on different IPs
2. Update your swarm IP list to use the mock drone IPs
3. Run your swarm code - it will work exactly like with real drones
4. Monitor the console output to see command/response interactions

## Limitations

- Video streaming is not implemented (mock only)
- Mission pad detection is simulated with fixed values
- Physical constraints are not enforced (can "fly" through walls)
- Network latency is minimal compared to real WiFi connections

## Integration with Existing Code

The mock drone is fully compatible with existing DJITelloPy code. Simply change the IP addresses in your drone/swarm initialization to point to the mock drones.

No code changes are needed - the mock responds to the exact same UDP protocol as real Tello drones.
