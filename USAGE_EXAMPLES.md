# Drone Controller Usage Examples

This document provides examples of how to use the explicit simulator/real drone control features.

## Command Line Options

The drone controller now supports explicit control over whether to use real drones or the simulator:

- `--use-simulator`: Force use of simulator instead of real drones
- `--use-real`: Force use of real drones instead of simulator
- `--simulator`: Start the standalone 3D web simulator

## Examples

### 1. Force Simulator Demo (Single Drone)
```bash
python main.py --mode single --demo --use-simulator
```

### 2. Force Real Drone Demo (Single Drone)
```bash
python main.py --mode single --demo --use-real
```

### 3. Force Simulator Demo (Swarm)
```bash
python main.py --mode swarm --demo --use-simulator
```

### 4. Force Real Drone Demo (Swarm)
```bash
python main.py --mode swarm --demo --use-real
```

### 5. Interactive Mode with Real Drones (Default)
```bash
python main.py --mode single
```

### 6. Try to Use Simulator for Interactive Mode
```bash
python main.py --mode single --use-simulator
```
*Note: Interactive simulator mode is not yet implemented*

### 7. Start Standalone Simulator
```bash
python main.py --simulator
```

## Default Behavior

When neither `--use-simulator` nor `--use-real` is specified:

- **Demo mode**: Tries simulator first (if available), falls back to real drones
- **Interactive mode**: Defaults to real drones

## Error Handling

- If you specify both `--use-simulator` and `--use-real`, the program will show an error
- If simulator is requested but not available, it will fall back to real drones (with a warning)
- If interactive simulator mode is requested, it will show a message that it's not yet implemented

## VS Code Tasks

You can also use the predefined VS Code tasks:

- **Run Single Drone Demo**: Uses default behavior (simulator if available)
- **Run Swarm Demo**: Uses default behavior (simulator if available)
- **Simulator Basic Demo**: Forces simulator for single drone demo
- **Simulator Swarm Demo**: Forces simulator for swarm demo
