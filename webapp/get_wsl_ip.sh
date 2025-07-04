#!/bin/bash
# Get WSL IP address for Windows connectivity

echo "🔍 Finding WSL IP addresses..."
echo

# Method 1: ip route (most reliable)
WSL_IP1=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null)

# Method 2: hostname -I
WSL_IP2=$(hostname -I 2>/dev/null | awk '{print $1}')

# Method 3: ip addr show
WSL_IP3=$(ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)

echo "📡 IP Detection Methods:"
echo "  Method 1 (ip route): ${WSL_IP1:-'Failed'}"
echo "  Method 2 (hostname -I): ${WSL_IP2:-'Failed'}"
echo "  Method 3 (ip addr eth0): ${WSL_IP3:-'Failed'}"
echo

# Choose the best IP
WSL_IP=""
if [ -n "$WSL_IP1" ] && [ "$WSL_IP1" != "127.0.0.1" ]; then
    WSL_IP="$WSL_IP1"
elif [ -n "$WSL_IP2" ] && [ "$WSL_IP2" != "127.0.0.1" ]; then
    WSL_IP="$WSL_IP2"
elif [ -n "$WSL_IP3" ] && [ "$WSL_IP3" != "127.0.0.1" ]; then
    WSL_IP="$WSL_IP3"
fi

echo "🌐 Network Interface Details:"
if command -v ip >/dev/null 2>&1; then
    ip addr show | grep -E "^[0-9]+:|inet " | while IFS= read -r line; do
        if [[ $line =~ ^[0-9]+: ]]; then
            echo "  Interface: $(echo "$line" | awk '{print $2}' | sed 's/:$//')"
        elif [[ $line =~ inet.*eth|inet.*wsl ]] && [[ ! $line =~ 127.0.0.1 ]]; then
            ip=$(echo "$line" | awk '{print $2}' | cut -d'/' -f1)
            echo "    IP: $ip"
        fi
    done
else
    echo "  ip command not available"
fi

echo

if [ -n "$WSL_IP" ] && [ "$WSL_IP" != "127.0.0.1" ]; then
    echo "✅ WSL IP Address Found: $WSL_IP"
    echo
    echo "🌐 Recommended URLs for Windows access:"
    echo "  Web Interface: http://$WSL_IP:8000"
    echo "  WebSocket: ws://$WSL_IP:8766"
    echo
    echo "💡 Use these URLs from Windows browsers/applications"
    echo
    
    # Test if ports are accessible
    echo "🔧 Port Accessibility Test:"
    if command -v ss >/dev/null 2>&1; then
        if ss -tln | grep -q ":8000 "; then
            echo "  Port 8000: ✅ In use (server likely running)"
        else
            echo "  Port 8000: ⚠️  Not in use (start the server first)"
        fi
        
        if ss -tln | grep -q ":8766 "; then
            echo "  Port 8766: ✅ In use (WebSocket server likely running)"
        else
            echo "  Port 8766: ⚠️  Not in use (start the server first)"
        fi
    else
        echo "  Cannot check port status (ss command not available)"
    fi
    
    echo
    echo "🧪 Quick Connectivity Test:"
    if command -v curl >/dev/null 2>&1; then
        echo "  Testing http://$WSL_IP:8000..."
        if curl -s -o /dev/null -w "" --connect-timeout 2 "http://$WSL_IP:8000" 2>/dev/null; then
            echo "  ✅ Server is accessible on $WSL_IP:8000"
        else
            echo "  ❌ Server not accessible (may not be running)"
        fi
    else
        echo "  curl not available for testing"
    fi
    
else
    echo "❌ Could not determine WSL IP address"
    echo
    echo "🔧 Troubleshooting:"
    echo "  1. Check if you're running in WSL:"
    echo "     cat /proc/version | grep -i microsoft"
    echo
    echo "  2. Check network interfaces manually:"
    echo "     ip addr show"
    echo
    echo "  3. Try alternative commands:"
    echo "     hostname -I"
    echo "     ip route get 8.8.8.8"
fi

echo
echo "🔧 Manual IP Detection Commands:"
echo "  From WSL: hostname -I"
echo "  From Windows PowerShell: wsl hostname -I"
echo "  From Windows CMD: wsl ip addr show eth0"

echo
echo "🚨 Windows Connection Troubleshooting:"
echo "  1. Ensure WSL server binds to 0.0.0.0 (not 127.0.0.1)"
echo "  2. Check Windows Firewall settings"
echo "  3. Try: wsl --shutdown (then restart WSL)"
echo "  4. Verify WSL version: wsl --list --verbose"

# Show WSL version info if available
if [ -f "/proc/version" ]; then
    echo
    echo "📋 WSL Environment Info:"
    echo "  $(cat /proc/version | head -1)"
fi
