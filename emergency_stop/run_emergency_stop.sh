#!/bin/bash

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 to run this script."
    exit 1
fi

# Check if Homebrew is available
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Please install Homebrew to proceed."
    exit 1
fi

# Check if tkinter is available
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Tkinter not found. Installing python-tk via Homebrew..."
    brew install python-tk
fi

echo "Starting Emergency Stop GUI..."
echo ""
echo "This GUI provides an emergency stop button for drone operations."
echo "Keep this window open while running drone scripts."
echo ""

# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing requirements..."
    pip install -r requirements.txt > /dev/null 2>&1
else
    source .venv/bin/activate
fi

# Run the emergency stop GUI
python3 emergency_stop_ui.py

deactivate

echo ""
echo "Emergency Stop GUI closed."
read -p "Press enter to continue"
