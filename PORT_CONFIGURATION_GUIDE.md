# Enhanced Port Configuration for DJI Tello

This enhanced version of djitellopy now supports configurable UDP ports for better flexibility when working with multiple drones or custom network setups.

## New Features

### 1. Configurable Ports During Initialization

You can now specify custom ports when creating a Tello instance:

```python
from djitellopy import Tello

# Create Tello with custom ports
tello = Tello(
    host='192.168.10.1',
    control_udp=8890,     # Custom control port (default: 8889)
    state_udp=8891,       # Custom state port (default: 8890)
    vs_udp=11112          # Custom video port (default: 11111)
)
```

### 2. Dynamic Port Configuration

Set ports after initialization:

```python
# Set individual ports
tello.set_control_port(8892)
tello.set_state_port(8893)
tello.set_video_port(11113)

# Get current port configuration
config = tello.get_port_configuration()
print(config)
# Output: {'control_port': 8892, 'state_port': 8893, 'video_port': 11113}
```

### 3. Backward Compatibility

All existing code continues to work without modification:

```python
# Original initialization still works
tello = Tello()

# Original video port change method still works
tello.change_vs_udp(11114)
```

## API Reference

### Constructor Parameters

- `host` (str): IP address of the Tello drone (default: '192.168.10.1')
- `retry_count` (int): Number of command retries (default: 3)
- `vs_udp` (int): Video stream UDP port (default: 11111)
- `control_udp` (int): Control command UDP port (default: 8889)
- `state_udp` (int): State information UDP port (default: 8890)

### New Methods

#### `set_control_port(port: int)`
Set the control UDP port for sending commands to the drone.

#### `set_state_port(port: int)`
Set the state UDP port for receiving state information from the drone.

#### `set_video_port(port: int)`
Set the video UDP port for receiving video stream from the drone.

#### `get_port_configuration() -> dict`
Get the current port configuration as a dictionary.

## Use Cases

### Multiple Drones
When working with multiple drones, you can assign different ports to avoid conflicts:

```python
# Drone 1 with default ports
tello1 = Tello(host='192.168.10.1')

# Drone 2 with custom ports
tello2 = Tello(
    host='192.168.10.2',
    control_udp=8899,
    state_udp=8900,
    vs_udp=11121
)
```

### Network Restrictions
If certain ports are blocked or in use, you can easily configure alternatives:

```python
# Use alternative ports if defaults are blocked
tello = Tello(
    control_udp=9889,
    state_udp=9890,
    vs_udp=12111
)
```

## Important Notes

1. **Global Port Architecture**: The current implementation uses a global socket architecture, so the first Tello instance's ports become the global ports for the session.

2. **Port Changes**: Control and state port changes affect the global UDP receivers. Video port changes are sent as commands to the drone.

3. **Backward Compatibility**: All existing djitellopy code will continue to work unchanged.

## Testing

Run the test script to verify the enhanced port configuration features:

```bash
python test_port_config.py
```

This will test default initialization, custom port initialization, dynamic port configuration, and backward compatibility.
