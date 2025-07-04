# Drone Simulator 3D

A comprehensive 3D web-based drone simulator built with Three.js for testing and visualizing drone operations without physical hardware.

## Features

### 🚁 Realistic Drone Simulation
- **3D Drone Models**: Detailed quadcopter models with animated propellers
- **Physics Engine**: Realistic movement, gravity, wind effects, and collision detection
- **Battery Simulation**: Battery drain based on flight conditions
- **Status Indicators**: LED lights showing drone status (connected, flying, etc.)

### 🎮 Interactive Controls
- **Single Drone Mode**: Direct control of individual drones
- **Swarm Mode**: Coordinate multiple drones simultaneously
- **Keyboard Controls**: WASD movement, Space for takeoff/land
- **Mouse Controls**: Click to select drones, camera orbit controls

### 🌟 Formation Flying
- **Multiple Patterns**: Line, Circle, Diamond, V, Triangle, Square, Arrow, Wedge
- **Dynamic Formations**: Morph between different patterns smoothly
- **Formation Management**: Move, rotate, and scale entire formations
- **Collision Avoidance**: Automatic drone spacing and safety

### 🌍 3D Environment
- **Realistic World**: Ground plane, buildings, trees, and landmarks
- **Weather Effects**: Rain, fog, and wind simulation
- **Day/Night Cycle**: Dynamic lighting and skybox
- **Flight Boundaries**: Safe flying zones with automatic enforcement

### 📊 Real-time Monitoring
- **HUD Display**: Real-time drone status and telemetry
- **Command Log**: History of all commands and events
- **Performance Metrics**: Battery levels, speeds, positions
- **Formation Analysis**: Cohesion and accuracy metrics

## Quick Start

### Option 1: Direct Web Access
1. Open `index.html` in a web browser
2. The simulator will load automatically
3. Use the control panel on the right to operate drones

### Option 2: Python Integration
```python
# Run with Python for advanced features
python simulator_bridge.py

# Run demonstrations
python simulator_bridge.py basic    # Single drone demo
python simulator_bridge.py swarm    # Swarm formation demo
```

### Option 3: Integration with Main Drone Controller
```python
# In your main.py
from simulator.simulator_bridge import DroneSimulatorBridge

# Start simulator alongside your drone controller
bridge = DroneSimulatorBridge()
await bridge.start()

# Mirror real drone operations
bridge.add_drone('drone_001')
bridge.connect_drone('drone_001')
bridge.takeoff_drone('drone_001')
```

## Controls

### Keyboard (Single Mode)
- **W/A/S/D**: Move Forward/Left/Back/Right
- **Q/E**: Move Up/Down
- **R/T**: Rotate Left/Right
- **Space**: Takeoff/Land
- **Click**: Select drone for keyboard control

### Mouse
- **Left Click + Drag**: Rotate camera
- **Right Click + Drag**: Pan camera
- **Scroll**: Zoom in/out
- **Click Drone**: Select for control

### Control Panel
- **Single Mode**: Direct drone control with movement buttons
- **Swarm Mode**: Multi-drone coordination and formations
- **Formation Controls**: Create and manage drone formations
- **Status Display**: Real-time telemetry and logs

## File Structure

```
simulator/
├── index.html              # Main simulator page
├── styles.css              # Styling and UI layout
├── simulator_bridge.py     # Python integration bridge
└── js/
    ├── main.js             # Application entry point
    ├── DroneModel.js       # 3D drone models and animation
    ├── DroneSimulator.js   # Main simulation engine
    ├── Environment.js      # 3D world and environment
    ├── PhysicsEngine.js    # Physics and collision detection
    ├── SwarmManager.js     # Swarm coordination
    ├── FormationManager.js # Formation patterns and control
    └── UI.js               # User interface management
```

## API Integration

The simulator provides a Python bridge for seamless integration with your drone controller:

### Basic Operations
```python
bridge = DroneSimulatorBridge()

# Drone management
bridge.add_drone('drone_001', '192.168.1.100')
bridge.connect_drone('drone_001')
bridge.takeoff_drone('drone_001')
bridge.move_drone('drone_001', 100, 0, 50)  # x, y, z in cm
bridge.rotate_drone('drone_001', 90)        # degrees
bridge.land_drone('drone_001')

# Status monitoring
state = bridge.get_drone_state('drone_001')
print(f"Battery: {state['battery']}%")
```

### Swarm Operations
```python
# Create swarm
drone_ids = ['alpha', 'beta', 'gamma', 'delta']
for drone_id in drone_ids:
    bridge.add_drone(drone_id)
    bridge.connect_drone(drone_id)

bridge.create_swarm('test_swarm', drone_ids)

# Formation flying
bridge.create_formation('formation_1', drone_ids, 'circle', {'radius': 200})
```

### Real-time Updates
```python
# Send log messages to simulator
bridge.log_to_simulator('Mission started', 'info')

# Update drone states from real hardware
bridge.update_drone_state('drone_001', {
    'battery': 85,
    'position': {'x': 150, 'y': 30, 'z': 75}
})
```

## Formation Patterns

The simulator supports multiple formation patterns:

1. **Line Formation**: Drones arranged in a straight line
2. **Circle Formation**: Drones arranged in a circle
3. **Diamond Formation**: 4-point diamond with additional drones inside
4. **V Formation**: Classic V-shape with leader at point
5. **Triangle Formation**: Equilateral triangle arrangement
6. **Square Formation**: Grid-based square formation
7. **Arrow Formation**: Arrow shape pointing forward
8. **Wedge Formation**: Wedge shape for tactical movement

## Environmental Features

### Weather Effects
- **Clear**: Normal flying conditions
- **Rain**: Reduced visibility and increased battery drain
- **Fog**: Limited visibility range
- **Wind**: Affects drone stability and movement

### Physics Simulation
- **Gravity**: Subtle downward force on flying drones
- **Air Resistance**: Smooth movement damping
- **Turbulence**: Realistic micro-movements
- **Collision Detection**: Automatic avoidance between drones
- **Boundary Enforcement**: Keeps drones within safe flying area

## Customization

### Adding New Formation Patterns
```javascript
// In FormationManager.js
generateCustomFormation(droneCount, parameters) {
    const positions = [];
    // Your custom formation logic here
    return positions;
}
```

### Modifying Drone Appearance
```javascript
// In DroneModel.js - createDroneModel()
// Customize colors, materials, and geometry
const bodyMaterial = new THREE.MeshPhongMaterial({
    color: 0x2196F3,  // Change drone color
    shininess: 100
});
```

### Environmental Modifications
```javascript
// In Environment.js
// Add custom landmarks, lighting, or effects
createCustomLandmark() {
    // Your custom 3D objects
}
```

## Performance Optimization

- **LOD System**: Level-of-detail for distant drones
- **Efficient Rendering**: Optimized Three.js rendering pipeline
- **Smart Updates**: Only update changed drone states
- **Configurable Quality**: Adjust visual quality for performance

## Browser Compatibility

- **Chrome/Edge**: Full support with hardware acceleration
- **Firefox**: Full support
- **Safari**: Full support with some WebGL limitations
- **Mobile**: Basic support (touch controls)

## Dependencies

### Web Dependencies (CDN)
- Three.js r128 (3D graphics engine)
- OrbitControls (camera controls)

### Python Dependencies (Optional)
- websockets (for real-time communication)
- asyncio (async/await support)

## Troubleshooting

### Common Issues

1. **Simulator won't load**
   - Check browser console for WebGL support
   - Ensure internet connection for CDN resources
   - Try a different browser

2. **Python bridge connection fails**
   - Check if port 8000/8001 are available
   - Install required Python packages: `pip install websockets`
   - Check firewall settings

3. **Poor performance**
   - Reduce number of drones
   - Disable weather effects
   - Use hardware acceleration

4. **Drones not responding**
   - Check if drone is connected (blue/green lights)
   - Verify drone is selected (yellow ring)
   - Check command log for errors

## License

This simulator is part of the Drone Controller project and follows the same licensing terms.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional formation patterns
- New environmental effects
- Enhanced physics simulation
- Mobile interface improvements
- VR/AR integration
