# AWS IoT Message Examples for Tello Drone Swarm Control

This document provides example AWS IoT messages for controlling multiple Tello drones using the defined JSON schema.

## Example 1: Basic Action - Takeoff All Drones

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
  "safety": {
    "max_altitude": 200,
    "min_battery_level": 25,
    "collision_avoidance": true
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 2: Movement with Parameters - Specific Drones

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2025-07-07T10:31:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "action",
  "target_drones": [0, 1, 2],
  "action": {
    "name": "move_forward",
    "parameters": {
      "distance": 100,
      "speed": 50
    },
    "priority": "normal",
    "timeout": 5.0
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 3: Formation Flying - Circle Formation

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2025-07-07T10:32:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "formation",
  "target_drones": "all",
  "formation": {
    "type": "circle",
    "spacing": 150,
    "height": 100,
    "orientation": 0
  },
  "safety": {
    "collision_avoidance": true,
    "max_altitude": 300
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 4: Custom Formation with Specific Positions

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440004",
  "timestamp": "2025-07-07T10:33:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "formation",
  "target_drones": [0, 1, 2, 3],
  "formation": {
    "type": "custom",
    "height": 150,
    "custom_positions": [
      {"drone_id": 0, "x": 0, "y": 0, "z": 150},
      {"drone_id": 1, "x": 100, "y": 0, "z": 150},
      {"drone_id": 2, "x": 100, "y": 100, "z": 150},
      {"drone_id": 3, "x": 0, "y": 100, "z": 150}
    ]
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 5: Choreographed Dance Sequence

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440005",
  "timestamp": "2025-07-07T10:34:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "choreography",
  "target_drones": [0, 1, 2, 3],
  "choreography": {
    "sequence_name": "spiral_dance",
    "steps": [
      {
        "step_number": 1,
        "duration": 3.0,
        "actions": [
          {"drone_id": 0, "action": "rotate_clockwise", "parameters": {"angle": 90}},
          {"drone_id": 1, "action": "rotate_counter_clockwise", "parameters": {"angle": 90}},
          {"drone_id": 2, "action": "move_up", "parameters": {"distance": 50}},
          {"drone_id": 3, "action": "move_down", "parameters": {"distance": 50}}
        ]
      },
      {
        "step_number": 2,
        "duration": 4.0,
        "actions": [
          {"drone_id": 0, "action": "flip_forward"},
          {"drone_id": 1, "action": "flip_back"},
          {"drone_id": 2, "action": "flip_left"},
          {"drone_id": 3, "action": "flip_right"}
        ]
      },
      {
        "step_number": 3,
        "duration": 2.0,
        "actions": [
          {"drone_id": 0, "action": "move_forward", "parameters": {"distance": 100}},
          {"drone_id": 1, "action": "move_back", "parameters": {"distance": 100}},
          {"drone_id": 2, "action": "move_left", "parameters": {"distance": 100}},
          {"drone_id": 3, "action": "move_right", "parameters": {"distance": 100}}
        ]
      }
    ],
    "repeat_count": 2
  },
  "safety": {
    "max_altitude": 250,
    "collision_avoidance": true
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 6: Emergency Stop

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440006",
  "timestamp": "2025-07-07T10:35:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "emergency_stop",
  "target_drones": "all",
  "action": {
    "name": "emergency",
    "priority": "emergency",
    "timeout": 1.0
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Example 7: Status Request

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440007",
  "timestamp": "2025-07-07T10:36:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "status_request",
  "target_drones": "all",
  "response_topic": "drone/swarm/hkiit_demo_swarm/status"
}
```

## Example 8: Video Stream Control

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440008",
  "timestamp": "2025-07-07T10:37:00Z",
  "swarm_id": "hkiit_demo_swarm",
  "command_type": "stream_control",
  "target_drones": [0, 1],
  "action": {
    "name": "stream_on",
    "priority": "normal",
    "timeout": 3.0
  },
  "response_topic": "drone/swarm/hkiit_demo_swarm/response"
}
```

## Response Message Format

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440001",
  "response_id": "550e8400-e29b-41d4-a716-446655440009",
  "timestamp": "2025-07-07T10:30:05Z",
  "swarm_id": "hkiit_demo_swarm",
  "status": "success",
  "execution_time": 4.2,
  "drone_responses": [
    {
      "drone_id": 0,
      "ip": "192.168.10.1",
      "status": "success",
      "battery": 85,
      "height": 120,
      "temperature": 32.5,
      "is_flying": true
    },
    {
      "drone_id": 1,
      "ip": "192.168.10.2",
      "status": "success",
      "battery": 78,
      "height": 118,
      "temperature": 31.8,
      "is_flying": true
    }
  ],
  "errors": [],
  "warnings": [
    "Drone 1 battery level below 80%"
  ]
}
```

## Error Response Example

```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440002",
  "response_id": "550e8400-e29b-41d4-a716-446655440010",
  "timestamp": "2025-07-07T10:31:08Z",
  "swarm_id": "hkiit_demo_swarm",
  "status": "partial_failure",
  "execution_time": 2.1,
  "drone_responses": [
    {
      "drone_id": 0,
      "ip": "192.168.10.1",
      "status": "success",
      "battery": 84,
      "height": 150,
      "temperature": 33.1,
      "is_flying": true
    },
    {
      "drone_id": 1,
      "ip": "192.168.10.2",
      "status": "error",
      "error": "Low battery - action aborted",
      "battery": 15,
      "height": 0,
      "temperature": 29.2,
      "is_flying": false
    }
  ],
  "errors": [
    "Drone 1: Command failed due to low battery"
  ],
  "warnings": []
}
```

## MQTT Topic Structure

- **Command Topic**: `drone/swarm/{swarm_id}/command`
- **Response Topic**: `drone/swarm/{swarm_id}/response`
- **Status Topic**: `drone/swarm/{swarm_id}/status`
- **Emergency Topic**: `drone/swarm/{swarm_id}/emergency`
- **Telemetry Topic**: `drone/swarm/{swarm_id}/telemetry`

## Safety Considerations

1. **Battery Monitoring**: Always check battery levels before executing actions
2. **Collision Avoidance**: Maintain safe distances between drones
3. **Emergency Procedures**: Implement immediate stop and land procedures
4. **Signal Loss**: Auto-land if connection is lost
5. **Weather Conditions**: Monitor wind and weather before operations
6. **Flight Restrictions**: Respect no-fly zones and altitude limits
