#!/usr/bin/env python3
"""
Drone Controller Installation Validator

This script validates that the drone controller project is properly installed
and all dependencies are working correctly.
"""

import sys
import importlib
import subprocess
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print("=" * len(message))


def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version >= (3, 11):
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        return False


def check_package_import(package_name, optional=False):
    """Check if a package can be imported"""
    try:
        importlib.import_module(package_name)
        print_success(f"{package_name} import")
        return True
    except ImportError as e:
        if optional:
            print_warning(f"{package_name} import (optional): {e}")
        else:
            print_error(f"{package_name} import: {e}")
        return not optional


def check_project_structure():
    """Check if project structure is correct"""
    required_dirs = [
        "src",
        "src/drone_controller",
        "src/drone_controller/core",
        "src/drone_controller/multi_robot",
        "src/drone_controller/utils",
        "tests",
        "config",
        "examples"
    ]

    all_good = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"Directory: {dir_path}")
        else:
            print_error(f"Missing directory: {dir_path}")
            all_good = False

    return all_good


def check_config_files():
    """Check if configuration files exist"""
    config_files = [
        "config/drone_config.yaml",
        "pyproject.toml",
        "README.md"
    ]

    all_good = True
    for config_file in config_files:
        if Path(config_file).exists():
            print_success(f"Config file: {config_file}")
        else:
            print_error(f"Missing config file: {config_file}")
            all_good = False

    return all_good


def check_drone_controller_modules():
    """Check if drone controller modules can be imported"""
    modules = [
        "src.drone_controller",
        "src.drone_controller.core.tello_drone",
        "src.drone_controller.multi_robot.swarm_controller",
        "src.drone_controller.multi_robot.formation_manager",
        "src.drone_controller.utils.config_manager",
        "src.drone_controller.utils.logging_utils"
    ]

    all_good = True
    for module in modules:
        if check_package_import(module):
            pass  # Success already printed
        else:
            all_good = False

    return all_good


def run_basic_tests():
    """Run basic functionality tests"""
    try:
        # Test main.py help
        result = subprocess.run(["uv", "run", "python", "main.py", "--help"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print_success("main.py --help")
        else:
            print_error("main.py --help failed")
            return False

        # Test demo mode (if available)
        try:
            result = subprocess.run(["uv", "run", "python", "main.py",
                                   "--mode", "single", "--demo"],
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                print_success("Demo mode execution")
            else:
                print_warning("Demo mode failed (this may be normal)")
        except subprocess.TimeoutExpired:
            print_warning("Demo mode timeout (this may be normal)")

        return True
    except Exception as e:
        print_error(f"Basic tests failed: {e}")
        return False


def main():
    """Main validation function"""
    print_header("🚁 Drone Controller Installation Validator")

    all_checks_passed = True

    # Check Python version
    print_header("Python Environment")
    if not check_python_version():
        all_checks_passed = False

    # Check core dependencies
    print_header("Core Dependencies")
    core_packages = [
        "djitellopy",
        "numpy",
        "cv2",  # opencv-python
        "yaml"  # pyyaml
    ]

    for package in core_packages:
        if not check_package_import(package):
            all_checks_passed = False

    # Check optional dependencies
    print_header("Optional Dependencies")
    optional_packages = [
        ("pytest", True),
        ("black", True),
        ("flake8", True),
        ("mypy", True),
        ("matplotlib", True)
    ]

    for package, optional in optional_packages:
        check_package_import(package, optional)

    # Check project structure
    print_header("Project Structure")
    if not check_project_structure():
        all_checks_passed = False

    # Check config files
    print_header("Configuration Files")
    if not check_config_files():
        all_checks_passed = False

    # Check drone controller modules
    print_header("Drone Controller Modules")
    if not check_drone_controller_modules():
        all_checks_passed = False

    # Run basic tests
    print_header("Basic Functionality Tests")
    if not run_basic_tests():
        all_checks_passed = False

    # Final result
    print_header("Validation Results")
    if all_checks_passed:
        print_success("All critical checks passed! 🎉")
        print_info("Your drone controller installation is ready to use.")
        print_info("Try running: uv run python main.py --mode single --demo")
    else:
        print_error("Some checks failed! ❌")
        print_info("Please review the errors above and run setup again.")
        print_info("Run: .\\setup.ps1 -Force to reinstall dependencies")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
