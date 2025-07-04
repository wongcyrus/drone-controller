# Signal Handling Fix for Swarm Mode

## Problem
Previously, when running in swarm mode, pressing Ctrl+C would not properly stop the application and could leave drones in an unsafe state without performing emergency landing.

## Solution
Added comprehensive signal handling to both single drone and swarm modes:

### Features Added:
1. **Graceful Ctrl+C Handling**: Pressing Ctrl+C now triggers emergency landing before exiting
2. **Emergency Stop Protocol**: All drones perform emergency landing when signal is received
3. **Proper Cleanup**: Swarm connections are properly closed and resources cleaned up
4. **Cross-Platform Support**: Works on both Windows and Unix-like systems
5. **Backup Signal Handler**: Additional signal handler for Windows (SIGBREAK)

### How It Works:

#### Swarm Mode:
- Ctrl+C triggers emergency landing for all drones in the swarm
- Performs proper swarm shutdown and cleanup
- Restores default signal handlers before exit

#### Single Drone Mode:
- Ctrl+C triggers emergency landing for the connected drone
- Properly disconnects from the drone
- Restores default signal handlers before exit

### Usage:
```bash
# Start swarm mode - Ctrl+C will now work properly
python main.py --mode swarm --verbose

# Start single drone mode - Ctrl+C will now work properly
python main.py --mode single --drone-id drone_001
```

### Safety Improvements:
- No more orphaned drone connections
- Guaranteed emergency landing on forced exit
- Proper resource cleanup prevents system resource leaks
- Clear user feedback during emergency procedures

### User Interface Updates:
- Added "Ctrl+C - Emergency landing and exit" to help text
- Status messages during emergency landing process
- Visual indicators (🛑, ✅, ❌) for better user feedback

This fix ensures that interrupting the drone controller application will always attempt to safely land drones before exiting.
