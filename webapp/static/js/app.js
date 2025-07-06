/**
 * Main Application Entry Point
 * Integrates WebSocket client, Three.js scene, and drone simulator
 */

class DroneSimulatorApp {
    constructor() {
        this.wsClient = null;
        this.threeScene = null;
        this.droneSimulator = null;
        this.console = null;

        this.selectedDroneId = null;

        this.init();
    }

    init() {
        console.log('Initializing Drone Simulator App...');

        // Initialize components
        this.initThreeScene();
        this.initDroneSimulator();
        this.initWebSocket();
        this.initConsole();
        this.initUI();

        // Start periodic updates
        this.droneSimulator.startStateSimulation();

        // Auto-connect to WebSocket
        setTimeout(() => {
            console.log("🔗 Auto-connecting to WebSocket...");
            this.wsClient.connect();
        }, 1000);

        console.log('Drone Simulator App initialized');
    }

    initThreeScene() {
        this.threeScene = new ThreeScene('three-canvas');

        // Bind viewport controls
        document.getElementById('reset-camera').addEventListener('click', () => {
            this.threeScene.resetCamera();
        });

        document.getElementById('toggle-grid').addEventListener('click', () => {
            this.threeScene.toggleGrid();
        });

        document.getElementById('toggle-axes').addEventListener('click', () => {
            this.threeScene.toggleAxes();
        });
    }

    initDroneSimulator() {
        this.droneSimulator = new DroneSimulator();

        // Set up event handlers
        this.droneSimulator.onDroneListUpdate = () => {
            this.updateDroneList();
        };

        this.droneSimulator.onDroneSelect = (drone) => {
            this.updateDroneInfo(drone);
        };

        this.droneSimulator.onDroneStateUpdate = (droneId, state) => {
            // Mark this as a JavaScript simulator update
            state._isJSUpdate = true;
            this.threeScene.updateDroneState(droneId, state);
        };
    }

    initWebSocket() {
        this.wsClient = new WebSocketClient();

        // Set up event handlers
        this.wsClient.onConnectionChange = (status) => {
            this.updateConnectionStatus(status);
        };

        this.wsClient.onDroneUpdate = (type, data) => {
            this.handleDroneUpdate(type, data);
        };

        this.wsClient.onCommandResult = (result) => {
            this.handleCommandResult(result);
        };

        // Start ping interval
        this.wsClient.startPingInterval();
    }

    initConsole() {
        this.console = {
            element: document.getElementById('console-content'),
            lines: [],
            maxLines: 100
        };

        document.getElementById('clear-console').addEventListener('click', () => {
            this.clearConsole();
        });
    }

    initUI() {
        // Connection button
        document.getElementById('connect-btn').addEventListener('click', () => {
            if (this.wsClient.connected) {
                this.wsClient.disconnect();
            } else {
                this.wsClient.connect();
            }
        });

        // Add virtual drone button
        document.getElementById('add-drone-btn').addEventListener('click', () => {
            this.addVirtualDrone();
        });

        // Reset button
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.resetDrone();
        });

        // Manual control buttons (no longer includes reset)
        document.querySelectorAll('.cmd-btn').forEach(button => {
            button.addEventListener('click', () => {
                const command = button.getAttribute('data-command');
                if (command) { // Only send if it has a data-command attribute
                    this.sendCommand(command);
                }
            });
        });

        // Custom command input
        const customCommandInput = document.getElementById('custom-command');
        const sendCommandBtn = document.getElementById('send-command-btn');

        sendCommandBtn.addEventListener('click', () => {
            const command = customCommandInput.value.trim();
            if (command) {
                this.sendCommand(command);
                customCommandInput.value = '';
            }
        });

        customCommandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommandBtn.click();
            }
        });

        // Disable manual controls initially
        this.updateManualControlsState(false);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        const connectBtn = document.getElementById('connect-btn');

        statusElement.className = '';
        statusElement.classList.add(status);

        switch (status) {
            case 'connected':
                statusElement.textContent = 'Connected';
                connectBtn.textContent = 'Disconnect';
                break;
            case 'connecting':
                statusElement.textContent = 'Connecting...';
                connectBtn.textContent = 'Cancel';
                break;
            case 'disconnected':
                statusElement.textContent = 'Disconnected';
                connectBtn.textContent = 'Connect';
                break;
            case 'error':
                statusElement.textContent = 'Error';
                connectBtn.textContent = 'Retry';
                break;
        }

        this.logToConsole(`Connection status: ${status}`, 'info');
    }

    handleDroneUpdate(type, data) {
        switch (type) {
            case 'list':
                // Handle initial drone list - data is now array of drone objects
                console.log("📋 Processing drone list:", data);
                data.forEach(drone => {
                    const droneId = drone.id || drone.name;
                    if (!this.droneSimulator.getDrone(droneId)) {
                        this.droneSimulator.addDrone(droneId, {
                            name: drone.name || droneId, // Ensure name is set
                            connected: drone.connected,
                            ip: drone.ip,
                            port: drone.port,
                            state: drone.state || {}
                        });
                        console.log(`🚁 Added drone: ${droneId} (${drone.ip}:${drone.port})`);
                        this.threeScene.addDrone(droneId);
                        // Update label with proper name
                        if (drone.name && drone.name !== droneId) {
                            this.threeScene.updateDroneLabelText(droneId, drone.name);
                        }
                    }
                });
                break;

            case 'added':
                if (!this.droneSimulator.getDrone(data.id)) {
                    this.droneSimulator.addDrone(data.id, data);
                    this.threeScene.addDrone(data.id);
                    // Update label with proper name
                    if (data.name && data.name !== data.id) {
                        this.threeScene.updateDroneLabelText(data.id, data.name);
                    }
                    this.logToConsole(`Drone ${data.id} connected`, 'info');
                }
                break;

            case 'removed':
                this.droneSimulator.removeDrone(data.id);
                this.threeScene.removeDrone(data.id);
                this.logToConsole(`Drone ${data.id} disconnected`, 'info');
                break;

            case 'state':
                // Filter out position data from server updates - only use non-position state
                const filteredState = { ...data.state };
                delete filteredState.x;
                delete filteredState.y;
                delete filteredState.h;
                this.droneSimulator.updateDroneState(data.id, filteredState);
                break;
        }
    }

    handleCommandResult(result) {
        const { drone_id, command, response, timestamp } = result;

        this.logToConsole(`[${drone_id}] ${command}`, 'command');

        // Handle undefined/null response
        const responseText = response || 'no response';
        const responseType = (response && response.startsWith && response.startsWith('error')) ? 'error' : 'response';

        this.logToConsole(`[${drone_id}] ${responseText}`, responseType);

        // If command was successful, also simulate it in the JavaScript simulator
        // This ensures position updates happen even when using WebSocket
        if (response === 'ok') {
            console.log(`🔄 Simulating command in JS: ${command} for drone ${drone_id}`);
            this.droneSimulator.processCommand(drone_id, command);
        }

        // Animate command in 3D scene if it's a movement command
        if (['takeoff', 'land', 'flip'].some(cmd => command.includes(cmd))) {
            this.threeScene.animateCommand(drone_id, command);
        }
    }

    updateDroneList() {
        const droneListElement = document.getElementById('drone-list');
        const drones = this.droneSimulator.getAllDrones();

        if (drones.length === 0) {
            droneListElement.innerHTML = '<p class="no-drones">No drones connected</p>';
            return;
        }

        droneListElement.innerHTML = '';

        drones.forEach(drone => {
            const droneElement = document.createElement('div');
            droneElement.className = 'drone-item';
            droneElement.dataset.droneId = drone.id;

            if (drone.id === this.selectedDroneId) {
                droneElement.classList.add('selected');
            }

            droneElement.innerHTML = `
                <div class="drone-name">
                    <span class="status-indicator ${drone.connected ? 'online' : 'offline'}"></span>
                    ${drone.name}
                </div>
                <div class="drone-status">
                    ${drone.flying ? 'Flying' : 'Landed'} |
                    Battery: ${Math.round(drone.state.bat)}% |
                    Height: ${Math.round(drone.state.h)}cm
                </div>
            `;

            droneElement.addEventListener('click', () => {
                this.selectDrone(drone.id);
            });

            droneListElement.appendChild(droneElement);
        });
    }

    updateDroneInfo(drone) {
        const droneInfoElement = document.getElementById('drone-info');

        if (!drone) {
            droneInfoElement.innerHTML = '<p class="no-selection">No drone selected</p>';
            this.updateManualControlsState(false);
            return;
        }

        droneInfoElement.innerHTML = `
            <div class="info-row">
                <span class="info-label">Name:</span>
                <span class="info-value">${drone.name}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value ${drone.flying ? 'flying' : ''}">${drone.flying ? 'Flying' : 'Landed'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Battery:</span>
                <span class="info-value">${Math.round(drone.state.bat)}%</span>
            </div>
            <div class="info-row">
                <span class="info-label">Height:</span>
                <span class="info-value">${Math.round(drone.state.h)} cm</span>
            </div>
            <div class="info-row">
                <span class="info-label">Temperature:</span>
                <span class="info-value">${Math.round(drone.state.templ)}°C ~ ${Math.round(drone.state.temph)}°C</span>
            </div>
            <div class="info-row">
                <span class="info-label">Yaw:</span>
                <span class="info-value">${Math.round(drone.state.yaw)}°</span>
            </div>
            <div class="info-row">
                <span class="info-label">Last Command:</span>
                <span class="info-value">${drone.lastCommand || 'None'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Last Response:</span>
                <span class="info-value">${drone.lastResponse || 'None'}</span>
            </div>
        `;

        this.updateManualControlsState(drone.connected);
    }

    updateManualControlsState(enabled) {
        const controlButtons = document.querySelectorAll('.cmd-btn');
        const customCommandInput = document.getElementById('custom-command');
        const sendCommandBtn = document.getElementById('send-command-btn');

        controlButtons.forEach(button => {
            // Don't disable the reset button - it should always be available
            if (button.id !== 'reset-btn') {
                button.disabled = !enabled;
            }
        });

        customCommandInput.disabled = !enabled;
        sendCommandBtn.disabled = !enabled;
    }

    selectDrone(droneId) {
        // Update UI selection
        document.querySelectorAll('.drone-item').forEach(item => {
            item.classList.remove('selected');
        });

        const selectedItem = document.querySelector(`[data-drone-id="${droneId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }

        // Update simulator selection
        this.selectedDroneId = droneId;
        this.droneSimulator.selectDrone(droneId);
    }

    sendCommand(command) {
        if (!this.selectedDroneId) {
            this.logToConsole('No drone selected', 'error');
            return;
        }

        const drone = this.droneSimulator.getDrone(this.selectedDroneId);
        if (!drone || !drone.connected) {
            this.logToConsole('Selected drone is not connected', 'error');
            return;
        }

        // Send command via WebSocket if connected
        if (this.wsClient.connected) {
            this.wsClient.sendCommand(this.selectedDroneId, command);
        } else {
            // Process command locally if WebSocket is not connected
            const response = this.droneSimulator.processCommand(this.selectedDroneId, command);
            this.handleCommandResult({
                drone_id: this.selectedDroneId,
                command: command,
                response: response,
                timestamp: Date.now()
            });
        }
    }

    addVirtualDrone() {
        const drone = this.droneSimulator.createVirtualDrone();
        this.threeScene.addDrone(drone.id);
        this.logToConsole(`Created virtual drone: ${drone.name}`, 'info');

        // Auto-select the new drone
        this.selectDrone(drone.id);
    }

    resetDrone() {
        if (!this.selectedDroneId) {
            this.logToConsole('No drone selected for reset', 'error');
            return;
        }

        this.logToConsole(`Resetting drone: ${this.selectedDroneId}`, 'info');

        // 1. Reset 3D position immediately
        this.threeScene.resetDroneToOrigin(this.selectedDroneId);

        // 2. Reset drone simulator state immediately
        const drone = this.droneSimulator.getDrone(this.selectedDroneId);
        if (drone) {
            this.droneSimulator.simulateReset(this.selectedDroneId);
        }

        // 3. Send reset command to backend (server no longer changes position)
        this.sendCommand('reset');

        this.logToConsole(`Drone ${this.selectedDroneId} reset complete`, 'success');
    }

    logToConsole(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const line = {
            message,
            type,
            timestamp
        };

        this.console.lines.push(line);

        // Limit console lines
        if (this.console.lines.length > this.console.maxLines) {
            this.console.lines.shift();
        }

        this.updateConsoleDisplay();
    }

    updateConsoleDisplay() {
        const content = this.console.lines.map(line => {
            return `<div class="console-line ${line.type}">
                <span class="timestamp">[${line.timestamp}]</span> ${line.message}
            </div>`;
        }).join('');

        this.console.element.innerHTML = content;
        this.console.element.scrollTop = this.console.element.scrollHeight;
    }

    clearConsole() {
        this.console.lines = [];
        this.updateConsoleDisplay();
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DroneSimulatorApp();
});
