#!/bin/bash
# Simple start script for drone simulator with working ports

echo "🚁 Starting Drone Simulator"
echo "=========================="

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
if [ -d "$PROJECT_DIR/.venv-linux" ]; then
    source "$PROJECT_DIR/.venv-linux/bin/activate"
    echo "✅ Activated virtual environment"
else
    echo "⚠️  Using system Python"
fi

# Change to webapp directory
cd "$SCRIPT_DIR"

# Get WSL IP for drone UDP binding
WSL_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")

echo
echo "🔧 Configuration:"
echo "  Web Server: 0.0.0.0:8000"
echo "  WebSocket: 0.0.0.0:8766"
echo "  Drone UDP: 0.0.0.0:8889 (swarm mode)"
echo "  WSL IP: $WSL_IP"

echo
echo "🌐 Access URLs:"
echo "  From WSL: http://localhost:8000"
if [ "$WSL_IP" != "localhost" ]; then
    echo "  From Windows: http://$WSL_IP:8000"
fi

echo
echo "🚀 Starting simulator..."

# Start with single drone using multiple mode for proper WSL networking
python3 mock_drone.py --host 0.0.0.0 --ip 0.0.0.0 --web-port 8000 --webapp-port 8766 --multiple 1
