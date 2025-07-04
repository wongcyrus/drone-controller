#!/bin/bash
# Configure and find available ports for the drone simulator

echo "🔧 Port Configuration Helper"
echo "============================"

# Function to check if port is available
check_port() {
    local port=$1
    if ss -tln | grep -q ":$port "; then
        return 1  # Port in use
    else
        return 0  # Port available
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while [ $port -lt $((start_port + 100)) ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    
    echo "No available port found starting from $start_port"
    return 1
}

echo
echo "📡 Current Port Status:"

# Check common ports
PORTS=(8000 8765 8766 8767 8768 8889 8890 8891)
for port in "${PORTS[@]}"; do
    if check_port $port; then
        echo "  Port $port: ✅ Available"
    else
        echo "  Port $port: ❌ In use"
    fi
done

echo
echo "🔍 Finding Available Ports:"

# Find available web port
WEB_PORT=$(find_available_port 8000)
echo "  Web Server: $WEB_PORT"

# Find available websocket port
WS_PORT=$(find_available_port 8766)
echo "  WebSocket: $WS_PORT"

# Find available drone port
DRONE_PORT=$(find_available_port 8889)
echo "  Drone UDP: $DRONE_PORT"

echo
echo "🚀 Recommended Start Command:"
echo "  ./start_mock_drone.sh --multiple 3 --web-port $WEB_PORT --webapp-port $WS_PORT --port $DRONE_PORT"

echo
echo "🌐 Access URLs (replace with your WSL IP):"
WSL_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "YOUR_WSL_IP")
echo "  From WSL: http://localhost:$WEB_PORT"
echo "  From Windows: http://$WSL_IP:$WEB_PORT"
echo "  WebSocket: ws://$WSL_IP:$WS_PORT"

echo
echo "💡 Common Port Configurations:"
echo "  Default: --web-port 8000 --webapp-port 8765"
echo "  Alt 1:   --web-port 8001 --webapp-port 8766"
echo "  Alt 2:   --web-port 8080 --webapp-port 8767"
echo "  Alt 3:   --web-port 3000 --webapp-port 3001"
