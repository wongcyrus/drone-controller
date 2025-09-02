#!/bin/bash
# macOS Shell Script to run the IoT client
# This script provides a simple way to start the IoT client on macOS

echo "================================="
echo "macOS IoT Client Launcher"
echo "================================="
echo

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $PWD"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and ensure it's added to your PATH"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Python found:"
python3 --version
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    read -p "Press Enter to exit..."
    exit 1
fi

# Install/upgrade requirements
echo "Installing/updating Python packages..."
pip install -r requirements.txt --upgrade --quiet
if [ $? -ne 0 ]; then
    echo "WARNING: Some packages may have failed to install"
fi

# Create logs directory
mkdir -p logs

# Set environment variables
export PYTHONPATH="$PWD"
export IOT_CLIENT_OS="macOS"
export IOT_CLIENT_PLATFORM="darwin"

# Generate log file name with current date
LOG_DATE=$(date +"%Y-%m-%d")
export IOT_LOG_FILE="logs/iot_client_${LOG_DATE}.log"

echo
echo "Configuration:"
echo "- Config file: settings.yaml"
echo "- Log file: $IOT_LOG_FILE"
echo "- Platform: macOS"
echo

# Use default configuration
CONFIG_FILE="settings.yaml"
echo "Using default configuration"

echo
echo "Starting IoT client..."
echo "Press Ctrl+C to stop the client"
echo

# Run the client
python3 pubsub.py --config "$CONFIG_FILE" --log-file "$IOT_LOG_FILE"

# Check exit code
if [ $? -ne 0 ]; then
    echo
    echo "IoT client exited with error code $?"
else
    echo
    echo "IoT client stopped normally"
fi

echo
read -p "Press Enter to exit..."
