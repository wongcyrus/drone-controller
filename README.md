# Drone Controller - Multi-Robot Tello Talent System

A comprehensive Python package for controlling multiple DJI Tello Talent drones simultaneously using djitellopy. This project provides advanced multi-robot coordination, formation flying, and swarm intelligence capabilities.

## Features

### Core Capabilities
- **Individual Drone Control**: Complete control of single Tello Talent drones
- **Multi-Robot Swarm Management**: Coordinate multiple drones simultaneously
- **Formation Flying**: Predefined and custom formation patterns
- **Real-time Coordination**: Synchronized takeoff, landing, and movement
- **Safety Systems**: Collision avoidance, battery monitoring, emergency procedures
- **Video Streaming**: Live video feeds from drone cameras
- **Configuration Management**: YAML-based configuration system

### Supported Formations
- Line Formation
- Circle Formation  
- Diamond Formation
- V Formation
- Grid Formation
- Custom Formations

### Safety Features
- Minimum distance enforcement between drones
- Collision risk detection and avoidance
- Battery level monitoring with automatic warnings
- Emergency stop capabilities
- Connection loss handling
- Automatic emergency landing for critical situations

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Prerequisites
- Python 3.11+
- DJI Tello Talent drones
- WiFi network for drone communication

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd drone-controller

# Install with uv (uv will automatically create virtual environment)
uv sync

# Or install dependencies manually
uv add djitellopy opencv-python numpy pyyaml
```

## Quick Start

### Single Drone Control
```python
from drone_controller.core.tello_drone import TelloDrone

# Create and connect to drone
drone = TelloDrone("my_drone")
drone.connect()

# Basic flight operations
drone.takeoff()
drone.move(100, 0, 50)  # Forward 100cm, up 50cm
drone.rotate(90)        # Rotate 90 degrees
drone.land()
drone.disconnect()
```

### Multi-Robot Swarm Control
```python
from drone_controller.multi_robot.swarm_controller import SwarmController
from drone_controller.multi_robot.formation_manager import FormationManager

# Create swarm and formation managers
swarm = SwarmController("my_swarm")
formation = FormationManager("my_formation")

# Add drones to swarm
swarm.add_drone("drone_1", "192.168.10.1")
swarm.add_drone("drone_2", "192.168.10.2")
swarm.add_drone("drone_3", "192.168.10.3")

# Add drones to formation
for drone in swarm.drones.values():
    formation.add_drone(drone)

# Initialize and takeoff
swarm.initialize_swarm()
swarm.takeoff_all()

# Create and execute formation
formation.create_circle_formation(radius=200)
formation.move_to_formation()

# Move formation around
formation.move_formation(100, 0, 0)  # Move forward
formation.rotate_formation(45)       # Rotate formation

# Land and shutdown
swarm.land_all()
swarm.shutdown_swarm()
```

## Command Line Interface

### Single Drone Mode
```bash
# Interactive single drone control
uv run main.py --mode single --drone-id drone_001

# With specific IP address
uv run main.py --mode single --drone-id drone_001 --ip 192.168.10.1

# Run basic flight demonstration
uv run main.py --mode single --demo
```

### Swarm Mode
```bash
# Interactive swarm control
uv run main.py --mode swarm

# With custom configuration
uv run main.py --mode swarm --config config/my_config.yaml

# Run swarm formation demonstration
uv run main.py --mode swarm --demo
```

## Configuration

The system uses YAML configuration files for drone and swarm settings. See `config/drone_config.yaml` for examples:

```yaml
drones:
  default:
    connection_timeout: 10.0
    max_speed: 50
    video_enabled: false
  
  drone_001:
    ip_address: "192.168.10.1"
    video_enabled: true

formations:
  circle:
    radius: 200
  line:
    spacing: 150
    orientation: 0

safety:
  min_distance: 100
  collision_threshold: 80
  max_altitude: 300
```

## Project Structure

```
drone-controller/
├── src/drone_controller/           # Main package
│   ├── core/                       # Core drone control
│   │   └── tello_drone.py         # Individual drone controller
│   ├── multi_robot/               # Multi-robot coordination
│   │   ├── swarm_controller.py    # Swarm management
│   │   └── formation_manager.py   # Formation control
│   └── utils/                     # Utility modules
│       ├── logging_utils.py       # Logging configuration
│       └── config_manager.py      # Configuration management
├── examples/                      # Example scripts
│   ├── basic_flight.py           # Single drone example
│   └── swarm_formation_demo.py   # Multi-robot example
├── config/                       # Configuration files
│   └── drone_config.yaml        # Main configuration
├── tests/                        # Test suite
└── main.py                      # Command line interface
```

## Examples

### Basic Flight Example
```bash
uv run examples/basic_flight.py
```

### Swarm Formation Demo
```bash
# Full demonstration with multiple formations
uv run examples/swarm_formation_demo.py

# Simple two-drone demo
uv run examples/swarm_formation_demo.py --simple
```

## API Reference

### TelloDrone Class
- `connect()` - Connect to drone
- `takeoff()` - Take off
- `land()` - Land drone
- `move(x, y, z, speed)` - Move drone
- `rotate(angle)` - Rotate drone
- `get_state()` - Get drone status

### SwarmController Class
- `add_drone(drone_id, ip)` - Add drone to swarm
- `initialize_swarm()` - Connect all drones
- `takeoff_all()` - Takeoff all drones
- `land_all()` - Land all drones
- `move_swarm_formation(offsets)` - Move swarm in formation

### FormationManager Class
- `create_line_formation(spacing)` - Create line formation
- `create_circle_formation(radius)` - Create circle formation
- `create_diamond_formation(size)` - Create diamond formation
- `move_to_formation()` - Move drones to formation positions
- `move_formation(dx, dy, dz)` - Move entire formation
- `rotate_formation(angle)` - Rotate formation

## Safety Guidelines

1. **Pre-flight Checks**
   - Ensure adequate battery levels (>30%)
   - Check for obstacles in flight area
   - Verify drone connectivity
   - Test emergency stop procedures

2. **Flight Operations**
   - Maintain visual contact with drones
   - Monitor battery levels continuously
   - Keep emergency stop ready
   - Respect minimum distance between drones

3. **Emergency Procedures**
   - Use `emergency_stop_all()` for immediate landing
   - Have manual controller ready as backup
   - Know local emergency contacts

## Development

### Running Tests
```bash
uv run -m pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

**Connection Problems**
- Verify drone IP addresses
- Check WiFi connectivity
- Ensure drones are powered on
- Try connecting to individual drones first

**Formation Issues**
- Check minimum distance settings
- Verify all drones are flying before formation
- Monitor collision warnings
- Adjust formation parameters for your space

**Battery Issues**
- Always check battery levels before flight
- Set appropriate warning thresholds
- Plan for reduced performance at low battery

### Logging
Logs are automatically saved to the `logs/` directory with detailed information about:
- Connection events
- Flight operations
- Error conditions
- Formation movements

## Acknowledgments

- Built on top of [djitellopy](https://github.com/damiafuentes/DJITelloPy)
- Uses OpenCV for video processing
- Configuration management with PyYAML
