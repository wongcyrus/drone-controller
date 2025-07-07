# Tello Drone Swarm IoT Integration

This module provides AWS IoT integration for controlling multiple Tello drones via MQTT messages. It replaces the humanoid robot action executor with a drone-specific implementation using the TelloSwarm library.

## Features

- **Multi-drone Control**: Control multiple Tello drones simultaneously through TelloSwarm
- **AWS IoT Integration**: Full MQTT-based communication with AWS IoT Core
- **Formation Flying**: Support for predefined formations (line, circle, diamond)
- **Choreographed Sequences**: Execute synchronized dance routines
- **Safety Features**: Battery monitoring, collision avoidance, emergency stops
- **Real-time Telemetry**: Continuous status reporting and monitoring
- **JSON Schema Validation**: Ensure message integrity and format compliance

## Architecture

```
AWS IoT Core
     ↓ (MQTT)
TelloSwarmIoTClient
     ↓
TelloSwarmActionExecutor
     ↓
DJITelloPy TelloSwarm
     ↓
Individual Tello Drones
```

## File Structure

```
iot/
├── tello_action_executor.py      # Core action executor for TelloSwarm
├── tello_swarm_iot_client.py     # AWS IoT MQTT client
├── aws_iot_drone_schema.json     # JSON schema for message validation
├── aws_iot_examples.md           # Example messages and usage
├── tello_swarm_config.json       # Configuration template
└── README_TELLO.md              # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install djitellopy AWSIoTPythonSDK jsonschema
   ```

2. **Configure AWS IoT**:
   - Create an AWS IoT Thing for your drone swarm
   - Download certificates and place them in `./certifications/`
   - Update the configuration file with your endpoint and certificate paths

3. **Configure Drones**:
   - Ensure all Tello drones are connected to the same WiFi network
   - Update the `drone_ips` list in the configuration file

## Configuration

Copy and modify `tello_swarm_config.json`:

```json
{
  "client_id": "tello_swarm_client_001",
  "endpoint": "your-iot-endpoint.iot.region.amazonaws.com",
  "swarm_id": "hkiit_demo_swarm",
  "drone_ips": [
    "192.168.10.1",
    "192.168.10.2",
    "192.168.10.3",
    "192.168.10.4"
  ]
}
```

## Usage

### Starting the IoT Client

```bash
python tello_swarm_iot_client.py --config tello_swarm_config.json
```

### Sending Commands via MQTT

#### Basic Takeoff Command
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-07-07T10:30:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "action",
  "target_drones": "all",
  "action": {
    "name": "takeoff",
    "priority": "high",
    "timeout": 10.0
  }
}
```

#### Formation Flying
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2025-07-07T10:31:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "formation",
  "target_drones": "all",
  "formation": {
    "type": "circle",
    "spacing": 150,
    "height": 100
  }
}
```

## Available Actions

### Basic Movement
- `takeoff`: Take off all drones
- `land`: Land all drones
- `move_up`, `move_down`, `move_left`, `move_right`, `move_forward`, `move_back`
- `rotate_clockwise`, `rotate_counter_clockwise`

### Aerobatics
- `flip_left`, `flip_right`, `flip_forward`, `flip_back`

### Formation Flying
- `formation_line`: Arrange drones in a line
- `formation_circle`: Arrange drones in a circle
- `formation_diamond`: Arrange drones in a diamond pattern

### Choreography
- `dance_sequence_1`: Simple alternating movement
- `dance_sequence_2`: Circular movement pattern
- `synchronized_flip`: All drones flip simultaneously

### Control
- `emergency`: Emergency stop all drones
- `hover`: Hold position
- `stream_on`, `stream_off`: Control video streaming

## MQTT Topics

- **Commands**: `drone/swarm/{swarm_id}/command`
- **Responses**: `drone/swarm/{swarm_id}/response`
- **Status**: `drone/swarm/{swarm_id}/status`
- **Emergency**: `drone/swarm/{swarm_id}/emergency`
- **Telemetry**: `drone/swarm/{swarm_id}/telemetry`

## Safety Features

### Battery Monitoring
- Automatic low battery warnings
- Optional auto-land when battery is critically low
- Battery status in telemetry data

### Collision Avoidance
- Maintain safe distances during formation flying
- Emergency stop capability
- Height and position monitoring

### Emergency Procedures
- Immediate emergency stop via dedicated MQTT topic
- Auto-land on signal loss
- Graceful shutdown procedures

## Error Handling

The system provides comprehensive error handling:

```json
{
  "status": "error",
  "error": "Drone 1: Command failed due to low battery",
  "drone_responses": [
    {
      "drone_id": 1,
      "status": "error",
      "error": "Low battery - action aborted",
      "battery": 15
    }
  ]
}
```

## Monitoring and Telemetry

Real-time telemetry includes:
- Battery levels for each drone
- Current altitude and position
- Temperature readings
- Flight status (flying/grounded)
- Action queue status
- Connection status

## Development

### Adding New Actions

1. Add action definition to `tello_actions` in `tello_action_executor.py`:
```python
"new_action": {
    "duration": 3.0,
    "description": "Description of new action",
    "method": "tello_method_name",
    "args": []
}
```

2. Update the JSON schema in `aws_iot_drone_schema.json`

3. Add example usage to `aws_iot_examples.md`

### Custom Formations

Implement custom formation logic in `_execute_formation()`:

```python
elif formation_type == "custom_formation":
    # Custom formation logic here
    for i, tello in enumerate(self.swarm.tellos):
        x, y, z = calculate_position(i)
        tello.go_xyz_speed(x, y, z, 50)
```

## Troubleshooting

### Connection Issues
1. Verify WiFi connectivity to all drones
2. Check IP addresses in configuration
3. Ensure drones are powered on and in SDK mode

### AWS IoT Issues
1. Verify certificate paths and permissions
2. Check endpoint URL and region
3. Validate MQTT topics and permissions

### Performance Issues
1. Reduce telemetry frequency
2. Limit number of simultaneous actions
3. Monitor network bandwidth

## Integration with Existing Systems

This implementation is designed to be compatible with the existing drone controller project structure. It can be integrated with:

- Web interface (`webapp/` directory)
- Existing IoT infrastructure
- Simulation environments
- External control systems

## License

This project is part of the HKIIT drone controller system.
