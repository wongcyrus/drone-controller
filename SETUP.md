# 🚁 Drone Controller - Quick Setup Guide

This guide will help you quickly set up the drone controller project on Windows.

## 📋 Prerequisites

- **Python 3.11 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **uv package manager** - Will be installed automatically by setup scripts
- **Git** (optional) - For cloning the repository
- **Administrator privileges** (may be required for some installations)

## 🚀 Quick Setup Options

### Option 1: PowerShell Setup (Recommended)

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

### Option 2: CMD/Batch Setup (Simple)

Open Command Prompt as Administrator and run:

```cmd
setup.bat
```

### Option 3: Complete Development Environment

For a full development setup with all tools:

```powershell
.\setup-dev.ps1
```

This includes:
- All dependencies
- Development tools (pytest, black, flake8, mypy)
- Pre-commit hooks
- VS Code extensions
- Development scripts

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

- **Drone settings**: Edit `config/drone_config.yaml`
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
3. **Configure drones**: Edit `config/drone_config.yaml`
4. **Start coding**: Begin with `examples/basic_flight.py`

Happy flying! 🚁✨
