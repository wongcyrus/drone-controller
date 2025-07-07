# Drone Controller ToolCall JSON Format Guide

This guide explains how to define JSON messages to trigger drone actions via the IoT messaging system.

## Overview

The system supports three different JSON formats for triggering drone actions, providing flexibility and backward compatibility:

1. **Simple Format**: Basic string-based commands
2. **Enhanced Format**: Object-based commands with drone targeting
3. **AWS IoT Schema Format**: Full schema-compliant messages

## Format 1: Simple ToolCall (Recommended for Basic Use)

```json
{
  "toolcall": "takeoff"
}
```

### Characteristics:
- ✅ Simple and easy to use
- ✅ Targets all drones in the swarm
- ✅ Default parameters for each action
- ❌ No fine-grained control over specific drones

### Example Messages:

```json
{"toolcall": "takeoff"}
{"toolcall": "land"}
{"toolcall": "move_forward"}
{"toolcall": "flip_left"}
{"toolcall": "formation_circle"}
{"toolcall": "dance_sequence_1"}
{"toolcall": "emergency"}
```

## Format 2: Enhanced ToolCall (Recommended for Advanced Use)

```json
{
  "toolcall": {
    "name": "move_forward",
    "drone_ids": [0, 1, 2]
  }
}
```

### Characteristics:
- ✅ Target specific drones or all drones
- ✅ More structured approach
- ✅ Ready for future parameter extensions
- ❌ Slightly more complex than simple format

### Drone Targeting Options:

```json
// Target all drones
{
  "toolcall": {
    "name": "takeoff",
    "drone_ids": "all"
  }
}

// Target specific drones by index (0, 1, 2, etc.)
{
  "toolcall": {
    "name": "flip_right",
    "drone_ids": [0, 2]
  }
}

// Target single drone
{
  "toolcall": {
    "name": "rotate_clockwise",
    "drone_ids": [1]
  }
}
```

## Format 3: AWS IoT Schema Format (Full Specification)

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
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

### Characteristics:
- ✅ Full schema compliance
- ✅ Message tracking and metadata
- ✅ Priority and timeout support
- ✅ Professional IoT messaging standard
- ❌ Most complex format

## Available Drone Actions

### Basic Flight Control
| Action | Description | Duration |
|--------|-------------|----------|
| `takeoff` | Take off all drones | 5.0s |
| `land` | Land all drones | 5.0s |
| `emergency` | Emergency stop | 0.5s |

### Movement Commands (50cm default)
| Action | Description | Duration |
|--------|-------------|----------|
| `move_up` | Move up 50cm | 3.0s |
| `move_down` | Move down 50cm | 3.0s |
| `move_left` | Move left 50cm | 3.0s |
| `move_right` | Move right 50cm | 3.0s |
| `move_forward` | Move forward 50cm | 3.0s |
| `move_back` | Move back 50cm | 3.0s |

### Rotation Commands (90° default)
| Action | Description | Duration |
|--------|-------------|----------|
| `rotate_clockwise` | Rotate 90° clockwise | 3.0s |
| `rotate_counter_clockwise` | Rotate 90° counter-clockwise | 3.0s |

### Aerial Maneuvers
| Action | Description | Duration |
|--------|-------------|----------|
| `flip_left` | Flip left | 4.0s |
| `flip_right` | Flip right | 4.0s |
| `flip_forward` | Flip forward | 4.0s |
| `flip_back` | Flip back | 4.0s |

### Speed Control
| Action | Description | Duration |
|--------|-------------|----------|
| `set_speed_slow` | Set speed to 10 | 1.0s |
| `set_speed_medium` | Set speed to 50 | 1.0s |
| `set_speed_fast` | Set speed to 100 | 1.0s |

### Formation Flying
| Action | Description | Duration |
|--------|-------------|----------|
| `formation_line` | Form line formation | 10.0s |
| `formation_circle` | Form circle formation | 10.0s |
| `formation_diamond` | Form diamond formation | 10.0s |

### Choreographed Sequences
| Action | Description | Duration |
|--------|-------------|----------|
| `dance_sequence_1` | Simple alternating up/down | 30.0s |
| `dance_sequence_2` | Circular movement pattern | 45.0s |
| `synchronized_flip` | All drones flip simultaneously | 8.0s |

### Video Control
| Action | Description | Duration |
|--------|-------------|----------|
| `stream_on` | Start video stream | 2.0s |
| `stream_off` | Stop video stream | 2.0s |

### Utility
| Action | Description | Duration |
|--------|-------------|----------|
| `hover` | Hover in place | 3.0s |

## Practical Examples

### Example 1: Basic Takeoff and Landing Sequence
```json
{"toolcall": "takeoff"}
// Wait 5 seconds
{"toolcall": "hover"}
// Wait 3 seconds
{"toolcall": "land"}
```

### Example 2: Formation Flying Demo
```json
{"toolcall": "takeoff"}
// Wait 5 seconds
{"toolcall": "formation_circle"}
// Wait 10 seconds
{"toolcall": "formation_line"}
// Wait 10 seconds
{"toolcall": "land"}
```

### Example 3: Drone-Specific Actions
```json
// Take off all drones
{"toolcall": {"name": "takeoff", "drone_ids": "all"}}

// Only drones 0 and 2 flip left
{"toolcall": {"name": "flip_left", "drone_ids": [0, 2]}}

// Only drone 1 rotates
{"toolcall": {"name": "rotate_clockwise", "drone_ids": [1]}}

// All drones land
{"toolcall": {"name": "land", "drone_ids": "all"}}
```

### Example 4: Dance Choreography
```json
{"toolcall": "takeoff"}
{"toolcall": "dance_sequence_1"}
{"toolcall": "synchronized_flip"}
{"toolcall": "dance_sequence_2"}
{"toolcall": "land"}
```

### Example 5: Emergency Stop
```json
{"toolcall": "emergency"}
```

## System Behavior

### Action Queueing
- Actions are queued and executed sequentially
- Each action has a predefined duration
- System waits for action completion before starting the next

### Error Handling
- Invalid action names are logged and ignored
- System continues processing valid actions
- Emergency stop immediately clears the queue

### Logging
- All received messages are logged
- Action execution status is tracked
- Errors and warnings are captured

## MQTT Topic Structure

The system subscribes to the topic defined in your `settings.yaml` file:
```yaml
input_topic: "drone/command/{robot_name}"
```

Send your JSON messages to this topic to trigger drone actions.

## Safety Considerations

1. **Always use emergency stop**: `{"toolcall": "emergency"}` in case of issues
2. **Test with simple actions first**: Start with basic movements
3. **Monitor drone battery levels**: Low battery may affect performance
4. **Ensure adequate space**: Some formations require significant space
5. **One action at a time**: Wait for completion before sending next action

## Troubleshooting

### Common Issues:
1. **Action not executing**: Check action name spelling
2. **Drone not responding**: Verify drone IP addresses and connectivity
3. **Partial swarm response**: Check individual drone battery and status
4. **Queue backup**: Use emergency stop to clear queue if needed

### Debug Information:
- Check logs for execution status
- Use the swarm status endpoint for real-time information
- Monitor MQTT message reception logs
