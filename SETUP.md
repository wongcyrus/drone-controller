# 🚁 Drone Controller - Setup Guide

This guide helps you set up the Drone Controller project on different operating systems.

## 📋 Quick Navigation

- **🪟 [Windows Users](WINDOWS_SETUP.md)** - Comprehensive Windows setup guide
- **🐧 Linux/macOS Users** - Continue with this guide
- **🔄 Mixed Environment (WSL + Windows)** - See both guides

## 🚀 Quick Setup Options

### Windows Users

**📖 For detailed Windows instructions, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md)**

#### Option 1: PowerShell Setup (Recommended)

Open PowerShell as Administrator and run:

```powershell
# For production use
.\setup.ps1

# For development
.\setup.ps1 -Dev

# For development with visualization tools
.\setup.ps1 -Dev -Visualization

# Force reinstall all dependencies
.\setup.ps1 -Dev -Force
```

#### Option 2: CMD/Batch Setup (Simple)

Open Command Prompt as Administrator and run:

```cmd
setup.bat
```

### Linux/macOS Users

For Linux and macOS, ensure you have Python 3.11+ and pip installed. Then, run:

```bash
# For production use
python3 -m pip install -r requirements.txt

# For development
python3 -m pip install -r requirements-dev.txt

# For development with visualization tools
python3 -m pip install -r requirements-visualization.txt
```

## 📁 What Gets Installed

### Core Dependencies (via uv)
- `djitellopy` - DJI Tello drone control library
- `numpy` - Numerical computing
- `opencv-python` - Computer vision and image processing
- `pyyaml` - YAML configuration file support

### Development Dependencies (with -Dev flag)
- `pytest` - Testing framework
- `black` - Code formatter
- `flake8` - Code linter
- `mypy` - Type checker
- `pytest-cov` - Coverage reporting
- `pre-commit` - Git hooks for code quality

### Visualization Dependencies (with -Visualization flag)
- `matplotlib` - Plotting and visualization

## 🧪 Testing the Installation

After setup, test your installation:

```powershell
# Run demo modes (no drones required)
uv run python main.py --mode single --demo
uv run python main.py --mode swarm --demo

# Run tests (if development setup)
uv run pytest tests/ -v

# Check drone controller import
uv run python -c "import src.drone_controller; print('✓ Import successful')"
```

## 🔗 Connecting Real Drones

1. **Power on** your Tello Talent drone(s)
2. **Connect** to the drone's Wi-Fi network (usually `TELLO-XXXXXX`)
3. **Run** the controller:
   ```powershell
   # Single drone
   uv run python main.py --mode single

   # Multiple drones
   uv run python main.py --mode swarm
   ```

## ⚙️ Configuration

- **Drone settings**: Configure directly in `main.py` or use webapp interface
- **Logging**: Check `logs/` directory for runtime logs
- **Examples**: See `examples/` directory for usage examples

## 🛠️ Development Workflow

If you installed the development environment:

```powershell
# Format code
uv run python scripts/format.py

# Run tests with coverage
uv run python scripts/test.py

# Run pre-commit hooks
uv run pre-commit run --all-files

# Add new dependencies
uv add package-name
uv add --dev package-name  # for development dependencies
```

## ❌ Troubleshooting

### Common Issues

1. **Python not found**
   - Ensure Python 3.11+ is installed and in PATH
   - Try `python --version` to verify

2. **Permission denied**
   - Run PowerShell/CMD as Administrator
   - Check Windows Execution Policy: `Set-ExecutionPolicy RemoteSigned`

3. **pip install fails**
   - Check internet connection
   - Try upgrading uv: `uv self update`
   - Use `-Force` flag to reinstall dependencies

4. **Import errors**
   - Ensure project dependencies are synced: `uv sync`
   - Check that all dependencies are installed

5. **uv not found**
   - The setup script should install uv automatically
   - Manual install: Visit https://docs.astral.sh/uv/getting-started/installation/

### Getting Help

- **Script help**: `.\setup.ps1 -Help`
- **Project documentation**: See `README.md`
- **Examples**: Check `examples/` directory

## 📚 Next Steps

1. **Read the documentation**: `README.md`
2. **Try examples**: Run scripts in `examples/`
3. **Configure drones**: Update IP addresses in `main.py` or use the webapp interface
4. **Start coding**: Begin with `examples/basic_flight.py`

Happy flying! 🚁✨
