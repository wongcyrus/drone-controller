/**
 * WebSocket Client for Drone Simulator
 * Handles real-time communication with the WebSocket server
 */

class WebSocketClient {
    constructor(url = 'ws://localhost:8766') {
        this.url = url;
        this.ws = null;
        this.connected = false;
        this.reconnectInterval = 5000; // 5 seconds
        this.reconnectTimer = null;
        this.messageHandlers = new Map();

        // Event handlers
        this.onConnectionChange = null;
        this.onDroneUpdate = null;
        this.onCommandResult = null;
    }

    connect() {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.connected = true;
                this.updateConnectionStatus('connected');

                if (this.reconnectTimer) {
                    clearInterval(this.reconnectTimer);
                    this.reconnectTimer = null;
                }

                // Request initial data
                this.send({ type: 'get_drones' });
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.connected = false;
                this.updateConnectionStatus('disconnected');
                this.scheduleReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('error');
            this.scheduleReconnect();
        }
    }

    disconnect() {
        if (this.reconnectTimer) {
            clearInterval(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.connected = false;
        this.updateConnectionStatus('disconnected');
    }

    scheduleReconnect() {
        if (this.reconnectTimer) return;

        console.log(`Attempting to reconnect in ${this.reconnectInterval / 1000} seconds...`);
        this.updateConnectionStatus('connecting');

        this.reconnectTimer = setInterval(() => {
            console.log('Attempting to reconnect...');
            this.connect();
        }, this.reconnectInterval);
    }

    send(message) {
        if (this.connected && this.ws) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        } else {
            console.warn('WebSocket not connected, cannot send message:', message);
            return false;
        }
    }

    handleMessage(message) {
        // Debug logging for all messages
        console.log("🔄 WebSocket Message Received:", {
            type: message.type,
            timestamp: new Date().toISOString(),
            data: message
        });
        const { type } = message;

        switch (type) {
            case 'drone_list':
                this.handleDroneList(message.drones);
                break;

            case 'drone_added':
                this.handleDroneAdded(message.drone_id, message.data);
                break;

            case 'drone_removed':
                this.handleDroneRemoved(message.drone_id);
                break;

            case 'drone_state':
                console.log("📡 Drone State Update:", message.drone_id, "Position:", {
                    x: message.data.x || 0, 
                    y: message.data.y || 0, 
                    z: message.data.z || 0, 
                    h: message.data.h || 0
                }, "Battery:", message.data.bat, "Full State:", message.data);
                this.handleDroneState(message.drone_id, message.data);
                break;

            case 'command_result':
                this.handleCommandResult(message);
                break;

            case 'command_executed':
                console.log("✅ UDP Command Executed:", message.drone_id, "Command:", message.command, "Response:", message.response);
                this.handleCommandExecuted(message);
                break;

            case 'pong':
                // Handle ping response
                break;

            default:
                console.log('Unknown message type:', type, message);
        }
    }

    handleDroneList(drones) {
        console.log('Drone list received:', drones);
        if (this.onDroneUpdate) {
            this.onDroneUpdate('list', drones);
        }
    }

    handleDroneAdded(droneId, data) {
        console.log('Drone added:', droneId, data);
        if (this.onDroneUpdate) {
            this.onDroneUpdate('added', { id: droneId, ...data });
        }
    }

    handleDroneRemoved(droneId) {
        console.log('Drone removed:', droneId);
        if (this.onDroneUpdate) {
            this.onDroneUpdate('removed', { id: droneId });
        }
    }

    handleDroneState(droneId, state) {
        console.log('Drone state update:', droneId, state);
        if (this.onDroneUpdate) {
            this.onDroneUpdate('state', { id: droneId, state });
        }
    }

    handleCommandResult(message) {
        console.log('Command result:', message);
        if (this.onCommandResult) {
            this.onCommandResult(message);
        }
    }

    handleCommandExecuted(message) {
        console.log('Command executed:', message);
        if (this.onCommandResult) {
            this.onCommandResult(message);
        }
    }

    updateConnectionStatus(status) {
        if (this.onConnectionChange) {
            this.onConnectionChange(status);
        }
    }

    sendCommand(droneId, command) {
        return this.send({
            type: 'drone_command',
            drone_id: droneId,
            command: command
        });
    }

    // Ping to keep connection alive
    ping() {
        this.send({ type: 'ping' });
    }

    startPingInterval(interval = 30000) {
        setInterval(() => {
            if (this.connected) {
                this.ping();
            }
        }, interval);
    }
}

// Export for use in other scripts
window.WebSocketClient = WebSocketClient;
