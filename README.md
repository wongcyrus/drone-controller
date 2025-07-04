# 🚁 Drone Controller Project

A simple but powerful multi-drone control system for DJI Tello drones with swarm coordination and mock drone simulation capabilities.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Mock Drone Testing](#-mock-drone-testing)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## ✨ Features

- **Multi-drone Swarm Control**: Control multiple Tello drones simultaneously using djitellopy
- **Mock Drone Simulation**: Test without real hardware using the built-in mock drone simulator
- **Cross-Platform Support**: Works on Windows, macOS, and Linux (including WSL)
- **Safety Features**: Emergency landing, graceful shutdown with Ctrl+C handling
- **Real-time Communication**: UDP-based command and state communication
- **Debug Logging**: Detailed packet tracing and network debugging

## 🚀 Quick Start

### Prerequisites

- **Python 3.11 or higher**
- **uv package manager** (installed automatically by setup script)

### 1. Setup

```bash
# Windows
.\setup.bat

# Or manual setup
uv sync
```

### 2. Test with Mock Drone
Change the code in main.py with WSL IP.
```bash
# Terminal 1 in WSL: Start mock drone
python mock_tello_drone.py --ip <WSL IP>

# Terminal 2: Run swarm controller
python main.py
```

### 3. Use with Real Drones

1. Power on your Tello drone(s)
2. Connect to drone Wi-Fi network (`TELLO-XXXXXX`)
3. Update IP address in `main.py` (line 31)
4. Run: `python main.py`

## 📦 Installation

### Option 1: Automated Setup (Windows)

```bash
.\setup.bat
```

### Option 2: Manual Installation

```bash
# Install uv package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# For development
uv sync --dev
```

## 🎮 Usage

### Basic Usage

The main controller (`main.py`) demonstrates a simple swarm mission:

```python
from djitellopy import TelloSwarm

# Create swarm with drone IP addresses
swarm = TelloSwarm.fromIps([
    "172.28.3.205"  # Update with your drone's IP
])

# Connect and fly
swarm.connect()
swarm.takeoff()
swarm.move_up(100)
swarm.land()
swarm.end()
```

### Running the Demo

```bash
# Make sure to update the IP address in main.py first
python main.py
```

The demo performs:
1. ✈️  **Takeoff** - All drones take off
2. ⬆️  **Move Up** - Fly 100cm higher (parallel)
3. ➡️  **Move Forward** - Sequential movement with spacing
4. ⬅️  **Move Left** - Parallel movement with individual spacing
5. 🛬 **Landing** - Safe landing

### Safety Features

- **Ctrl+C Handling**: Graceful emergency landing
- **Exception Handling**: Automatic landing on errors
- **Signal Handling**: Proper cleanup on interruption

## 🧪 Mock Drone Testing

The project includes a sophisticated mock drone simulator for testing without real hardware.

### Starting Mock Drones

```bash
# Single mock drone (default: 127.0.0.1:8889)
python mock_tello_drone.py

# Custom IP
python mock_tello_drone.py --ip 172.28.3.205

# Multiple drones on sequential IPs
python mock_tello_drone.py --multiple 3 --ip 127.0.0.1

# Custom port
python mock_tello_drone.py --port 8890
```

### Mock Drone Features

- ✅ **Full Tello SDK Support**: All major commands (takeoff, land, move, etc.)
- ✅ **Realistic State Simulation**: Battery, height, orientation, temperature
- ✅ **Network Communication**: Real UDP communication on ports 8889/8890
- ✅ **Cross-Platform**: Works between Windows ↔ WSL
- ✅ **Debug Logging**: Detailed packet tracing with emojis
  - 📥 **RAW UDP**: Incoming packets
  - ✅ **PROCESSING**: Commands being processed
  - 📤 **RESPONSE**: Responses being sent
  - ⛔ **IGNORED**: Filtered/loop packets

### Testing Communication

```bash
# Test basic UDP communication
python test_udp_communication.py

# Test full Tello API
python test_mock_different_port.py
```

### WSL/Windows Testing

**WSL Terminal:**
```bash
python mock_tello_drone.py --ip 172.28.3.205
```

**Windows Terminal:**
```cmd
# Update IP in main.py to 172.28.3.205
python main.py
```

## 📁 Project Structure

```
drone-controller/
├── main.py                    # Main swarm controller script
├── mock_tello_drone.py        # Mock drone simulator
├── test_udp_communication.py  # Basic UDP test script
├── test_mock_different_port.py # Full API test script
├── config/
│   └── drone_config.yaml      # Drone configuration (future use)
├── pyproject.toml             # Project dependencies and metadata
├── setup.bat                  # Windows setup script
├── SETUP.md                   # Detailed setup instructions
├── MOCK_DRONE_README.md       # Mock drone documentation
└── README.md                  # This file
```

### Key Files

- **`main.py`**: Main entry point - simple swarm demo
- **`mock_tello_drone.py`**: Full mock drone implementation
- **`pyproject.toml`**: Dependencies (djitellopy, numpy, opencv-python, pyyaml)
- **`config/drone_config.yaml`**: Configuration file (for future features)

## ⚙️ Configuration

### Updating Drone IP Addresses

Edit `main.py` line 31 to change drone IPs:

```python
swarm = TelloSwarm.fromIps([
    "192.168.10.1",  # First drone
    "192.168.10.2",  # Second drone
    # Add more drones as needed
])
```

### Mock Drone Configuration

```bash
# Different IP
python mock_tello_drone.py --ip 192.168.1.100

# Different port (if 8889 is busy)
python mock_tello_drone.py --port 8890

# Multiple mock drones
python mock_tello_drone.py --multiple 3
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Command timeout" or "No response"

```bash
# Check if mock drone is running
python mock_tello_drone.py --ip 127.0.0.1

# Test communication
python test_udp_communication.py

# Check Windows Firewall
# Allow Python through Windows Defender Firewall
```

#### 2. "Port already in use" (Port 8889 busy)

```bash
# Find process using port 8889
netstat -ano | findstr :8889

# Kill the process
taskkill /PID <process_id> /F

# Or use different port
python mock_tello_drone.py --port 8890
```

#### 3. WSL Network Issues

```bash
# Get WSL IP
ip addr show eth0

# Use WSL IP in main.py
# Test connectivity: ping 172.28.3.205
```

#### 4. Real Drone Connection Issues

```bash
# Check Wi-Fi connection to drone
# Drone network usually: TELLO-XXXXXX
# Default drone IP: 192.168.10.1

# Test ping to drone
ping 192.168.10.1
```

### Debug Mode

The mock drone provides detailed logging:

```bash
# Run with debug output
python mock_tello_drone.py --ip 127.0.0.1

# Look for these log patterns:
# 📥 RAW UDP: Shows all incoming packets
# ✅ PROCESSING: Commands being handled
# 📤 RESPONSE: Responses sent back
# ⛔ IGNORED: Filtered out packets (normal for loops)
```

### Network Diagnostics

```bash
# Test network connectivity
ping <drone_ip>

# Check UDP ports
netstat -an | findstr :8889
netstat -an | findstr :8890

# Windows: Check if Python is allowed through firewall
```

## 🛠️ Development

### Dependencies

- **djitellopy**: Tello drone control library
- **numpy**: Numerical computing
- **opencv-python**: Computer vision (for future features)
- **pyyaml**: Configuration file support

### Adding New Drones

```python
# In main.py, update the IP list:
swarm = TelloSwarm.fromIps([
    "192.168.10.1",
    "192.168.10.2",
    "192.168.10.3",  # Add new drone IP
])
```

### Creating New Flight Patterns

```python
# Example: Circle formation
def circle_formation(swarm):
    swarm.parallel(lambda i, tello: (
        tello.move_forward(100) if i == 0 else
        tello.move_right(100) if i == 1 else
        tello.move_back(100) if i == 2 else
        tello.move_left(100)
    ))
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with mock drones
5. Submit a pull request

### Development Guidelines

- Test with mock drones before real hardware
- Follow the existing code style
- Add logging for debugging
- Handle exceptions gracefully

## 📜 License

MIT License - see pyproject.toml for details.

## 🆘 Support

- **Setup Issues**: See [SETUP.md](SETUP.md)
- **Mock Drone Help**: See [MOCK_DRONE_README.md](MOCK_DRONE_README.md)
- **Network Issues**: Check the troubleshooting section above

## 🎯 Current Limitations

- Basic swarm coordination (no advanced formations)
- No web interface (command-line only)
- No video streaming integration
- Configuration via code editing (no GUI)

---

**Ready to fly? Start with the mock drone testing!** 🚁✨

## 🧪 Mock Drone Testing

## 🐛 Troubleshooting

### Common Issues

#### 1. "Command timeout" or "No response"

```bash
# Check mock drone is running
python mock_tello_drone.py --ip 127.0.0.1

# Test basic communication
python test_udp_communication.py

# Check firewall settings (Windows)
# Allow Python through Windows Firewall
```

#### 2. "Port already in use"

```bash
# Kill processes using port 8889
netstat -ano | findstr :8889
taskkill /PID <process_id> /F

# Or use different port
python mock_tello_drone.py --port 8890
```

#### 3. WSL Network Issues

```bash
# Get WSL IP address
ip addr show eth0

# Update IP in test scripts
# Use WSL IP for mock drone, Windows IP for client
```

#### 4. Python/uv not found

```powershell
# Reinstall Python 3.11+
# Add Python to PATH
# Install uv: https://docs.astral.sh/uv/getting-started/installation/

# Manual uv install
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Debug Mode

Enable verbose logging:

```bash
# Set debug level in mock drone
python mock_tello_drone.py --ip 127.0.0.1

# Check logs for detailed packet information:
# 📥 RAW UDP: Incoming packets
# ✅ PROCESSING: Commands being processed
# 📤 RESPONSE: Responses being sent
# ⛔ IGNORED: Filtered packets
```

### Network Diagnostics

```bash
# Test network connectivity
ping 172.28.3.205

# Check UDP port accessibility
telnet 172.28.3.205 8889

# Monitor network traffic (Linux/WSL)
sudo tcpdump -i any port 8889
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Use type hints where possible
- Test with both real and mock drones

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See [SETUP.md](SETUP.md) for detailed setup instructions
- **Mock Drone Guide**: See [MOCK_DRONE_README.md](MOCK_DRONE_README.md)
- **Issues**: Open an issue on GitHub for bug reports or feature requests

## 🎯 Roadmap

- [ ] Web-based control interface
- [ ] GPS-based outdoor navigation
- [ ] Computer vision integration
- [ ] Mission planning and waypoints
- [ ] Real-time video streaming
- [ ] Formation flying algorithms
- [ ] Mobile app controller

---

Happy flying! 🚁✨

*Built with ❤️ for the drone community*
