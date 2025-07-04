/**
 * UI.js - User Interface management and event handling
 */

class UI {
    constructor(simulator) {
        this.simulator = simulator;
        this.swarmManager = new SwarmManager(simulator);
        this.formationManager = new FormationManager(simulator);
        this.currentMode = 'single';
        this.selectedDroneId = 'drone_001';
        this.logEntries = [];

        this.initializeEventListeners();
        this.updateDisplay();

        // Auto-add first drone for single mode
        this.addDefaultDrone();
    }

    initializeEventListeners() {
        // Mode switching
        document.getElementById('singleMode').addEventListener('click', () => {
            this.switchMode('single');
        });

        document.getElementById('swarmMode').addEventListener('click', () => {
            this.switchMode('swarm');
        });

        // Single drone controls
        document.getElementById('connectBtn').addEventListener('click', () => {
            this.connectSingleDrone();
        });

        document.getElementById('takeoffBtn').addEventListener('click', () => {
            this.takeoffSingleDrone();
        });

        document.getElementById('landBtn').addEventListener('click', () => {
            this.landSingleDrone();
        });

        document.getElementById('emergencyBtn').addEventListener('click', () => {
            this.emergencyStopSingle();
        });

        // Movement controls
        document.querySelectorAll('.move-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const move = e.target.getAttribute('data-move').split(',').map(Number);
                this.moveSingleDrone(move[0], move[1], move[2]);
            });
        });

        document.getElementById('customMoveBtn').addEventListener('click', () => {
            this.customMoveSingleDrone();
        });

        document.getElementById('rotateBtn').addEventListener('click', () => {
            this.rotateSingleDrone();
        });

        // Swarm controls
        document.getElementById('addDroneBtn').addEventListener('click', () => {
            this.addDroneToSwarm();
        });

        document.getElementById('initSwarmBtn').addEventListener('click', () => {
            this.initializeSwarm();
        });

        document.getElementById('swarmTakeoffBtn').addEventListener('click', () => {
            this.takeoffSwarm();
        });

        document.getElementById('swarmLandBtn').addEventListener('click', () => {
            this.landSwarm();
        });

        document.getElementById('swarmEmergencyBtn').addEventListener('click', () => {
            this.emergencyStopSwarm();
        });

        // Formation controls
        document.getElementById('createFormationBtn').addEventListener('click', () => {
            this.createFormation();
        });

        document.getElementById('moveFormationBtn').addEventListener('click', () => {
            this.moveFormation();
        });

        // Utility controls
        document.getElementById('clearLogBtn').addEventListener('click', () => {
            this.clearLog();
        });

        // Update HUD periodically
        setInterval(() => this.updateHUD(), 100);
    }

    switchMode(mode) {
        this.currentMode = mode;
        this.simulator.setMode(mode);

        // Update UI
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(mode + 'Mode').classList.add('active');

        if (mode === 'single') {
            document.getElementById('singleControls').style.display = 'block';
            document.getElementById('swarmControls').style.display = 'none';
        } else {
            document.getElementById('singleControls').style.display = 'none';
            document.getElementById('swarmControls').style.display = 'block';

            // Create default swarm if none exists
            if (!this.swarmManager.getActiveSwarm()) {
                this.swarmManager.createSwarm('main_swarm');
            }
        }

        this.log(`Switched to ${mode} mode`, 'info');
    }

    addDefaultDrone() {
        const droneId = 'drone_001';
        this.simulator.addDrone(droneId);
        this.selectedDroneId = droneId;
        this.log(`Added default drone: ${droneId}`, 'info');
    }

    // Single drone methods
    connectSingleDrone() {
        if (this.simulator.connectDrone(this.selectedDroneId)) {
            document.getElementById('takeoffBtn').disabled = false;
            document.getElementById('landBtn').disabled = false;
            this.log(`Connected to ${this.selectedDroneId}`, 'success');
        } else {
            this.log(`Failed to connect to ${this.selectedDroneId}`, 'error');
        }
    }

    takeoffSingleDrone() {
        if (this.simulator.takeoffDrone(this.selectedDroneId)) {
            this.log(`${this.selectedDroneId} taking off`, 'success');
        } else {
            this.log(`Failed to takeoff ${this.selectedDroneId}`, 'error');
        }
    }

    landSingleDrone() {
        if (this.simulator.landDrone(this.selectedDroneId)) {
            this.log(`${this.selectedDroneId} landing`, 'success');
        } else {
            this.log(`Failed to land ${this.selectedDroneId}`, 'error');
        }
    }

    emergencyStopSingle() {
        this.simulator.emergencyStopDrone(this.selectedDroneId);
        this.log(`Emergency stop: ${this.selectedDroneId}`, 'warning');
    }

    moveSingleDrone(x, y, z) {
        if (this.simulator.moveDrone(this.selectedDroneId, x, y, z)) {
            this.log(`Moving ${this.selectedDroneId} by (${x}, ${y}, ${z})`, 'info');
        } else {
            this.log(`Failed to move ${this.selectedDroneId}`, 'error');
        }
    }

    customMoveSingleDrone() {
        const x = parseInt(document.getElementById('moveX').value) || 0;
        const y = parseInt(document.getElementById('moveY').value) || 0;
        const z = parseInt(document.getElementById('moveZ').value) || 0;

        this.moveSingleDrone(x, y, z);

        // Clear inputs
        document.getElementById('moveX').value = '';
        document.getElementById('moveY').value = '';
        document.getElementById('moveZ').value = '';
    }

    rotateSingleDrone() {
        const angle = parseInt(document.getElementById('rotationAngle').value) || 90;

        if (this.simulator.rotateDrone(this.selectedDroneId, angle)) {
            this.log(`Rotating ${this.selectedDroneId} by ${angle}°`, 'info');
        } else {
            this.log(`Failed to rotate ${this.selectedDroneId}`, 'error');
        }
    }

    // Swarm methods
    addDroneToSwarm() {
        const droneId = document.getElementById('newDroneId').value.trim();
        const ipAddress = document.getElementById('newDroneIp').value.trim() || null;

        if (!droneId) {
            this.log('Please enter a drone ID', 'error');
            return;
        }

        // Add drone to simulator
        const drone = this.simulator.addDrone(droneId, ipAddress);
        if (drone) {
            // Add to active swarm
            const activeSwarm = this.swarmManager.getActiveSwarm();
            if (activeSwarm) {
                this.swarmManager.addDroneToSwarm(activeSwarm.id, droneId);
            }

            this.updateSwarmDisplay();
            this.log(`Added ${droneId} to swarm`, 'success');

            // Clear inputs
            document.getElementById('newDroneId').value = '';
            document.getElementById('newDroneIp').value = '';
        } else {
            this.log(`Failed to add drone ${droneId}`, 'error');
        }
    }

    initializeSwarm() {
        const activeSwarm = this.swarmManager.getActiveSwarm();
        if (activeSwarm && this.swarmManager.initializeSwarm(activeSwarm.id)) {
            document.getElementById('swarmTakeoffBtn').disabled = false;
            document.getElementById('swarmLandBtn').disabled = false;
            this.log('Swarm initialized successfully', 'success');
        } else {
            this.log('Failed to initialize swarm', 'error');
        }
    }

    takeoffSwarm() {
        const activeSwarm = this.swarmManager.getActiveSwarm();
        if (activeSwarm && this.swarmManager.takeoffSwarm(activeSwarm.id)) {
            this.log('Swarm takeoff initiated', 'success');
        } else {
            this.log('Failed to takeoff swarm', 'error');
        }
    }

    landSwarm() {
        const activeSwarm = this.swarmManager.getActiveSwarm();
        if (activeSwarm && this.swarmManager.landSwarm(activeSwarm.id)) {
            this.log('Swarm landing initiated', 'success');
        } else {
            this.log('Failed to land swarm', 'error');
        }
    }

    emergencyStopSwarm() {
        const activeSwarm = this.swarmManager.getActiveSwarm();
        if (activeSwarm) {
            this.swarmManager.emergencyStopSwarm(activeSwarm.id);
            this.log('Emergency stop: All drones', 'warning');
        }
    }

    createFormation() {
        const formationType = document.getElementById('formationType').value;
        const activeSwarm = this.swarmManager.getActiveSwarm();

        if (!activeSwarm || activeSwarm.drones.size === 0) {
            this.log('No active swarm to create formation', 'error');
            return;
        }

        const droneIds = Array.from(activeSwarm.drones.keys());
        const formationId = 'formation_' + Date.now();

        // Create formation based on type
        let parameters = {};
        switch (formationType) {
            case 'line':
                parameters = { spacing: 150 };
                break;
            case 'circle':
                parameters = { radius: 200 };
                break;
            case 'diamond':
                parameters = { size: 200 };
                break;
            case 'v':
                parameters = { spacing: 150, angle: 45 };
                break;
        }

        const formation = this.formationManager.createFormation(
            formationId,
            droneIds,
            formationType,
            parameters
        );

        if (formation && this.formationManager.moveToFormation(formationId, 0, 30, 0)) {
            activeSwarm.formation = formation;
            this.log(`Created ${formationType} formation with ${droneIds.length} drones`, 'success');
        } else {
            this.log(`Failed to create ${formationType} formation`, 'error');
        }
    }

    moveFormation() {
        const x = parseInt(document.getElementById('formationX').value) || 0;
        const y = parseInt(document.getElementById('formationY').value) || 0;
        const z = parseInt(document.getElementById('formationZ').value) || 0;

        const activeSwarm = this.swarmManager.getActiveSwarm();
        if (activeSwarm && activeSwarm.formation) {
            if (this.formationManager.moveFormation(activeSwarm.formation.id, x, y, z)) {
                this.log(`Moving formation by (${x}, ${y}, ${z})`, 'info');
            } else {
                this.log('Failed to move formation', 'error');
            }
        } else {
            this.log('No active formation to move', 'error');
        }

        // Clear inputs
        document.getElementById('formationX').value = '';
        document.getElementById('formationY').value = '';
        document.getElementById('formationZ').value = '';
    }

    // Display updates
    updateDisplay() {
        this.updateHUD();
        this.updateSwarmDisplay();
    }

    updateHUD() {
        const stats = this.simulator.getStats();
        const hudElement = document.getElementById('droneStats');

        let hudContent = '';

        if (this.currentMode === 'single') {
            const drone = this.simulator.getDrone(this.selectedDroneId);
            if (drone) {
                const state = drone.getState();
                hudContent = `
                    <div class="status-item">
                        <span>Drone:</span>
                        <span>${state.id}</span>
                    </div>
                    <div class="status-item">
                        <span>Status:</span>
                        <span>${state.connected ? (state.flying ? 'Flying' : 'Connected') : 'Disconnected'}</span>
                    </div>
                    <div class="status-item">
                        <span>Battery:</span>
                        <span>${state.battery}%</span>
                    </div>
                    <div class="status-item">
                        <span>Altitude:</span>
                        <span>${state.altitude}cm</span>
                    </div>
                    <div class="status-item">
                        <span>Speed:</span>
                        <span>${state.speed} cm/s</span>
                    </div>
                    <div class="status-item">
                        <span>Position:</span>
                        <span>(${state.position.x.toFixed(0)}, ${state.position.y.toFixed(0)}, ${state.position.z.toFixed(0)})</span>
                    </div>
                `;
            }
        } else {
            hudContent = `
                <div class="status-item">
                    <span>Total Drones:</span>
                    <span>${stats.totalDrones}</span>
                </div>
                <div class="status-item">
                    <span>Connected:</span>
                    <span>${stats.connectedDrones}</span>
                </div>
                <div class="status-item">
                    <span>Flying:</span>
                    <span>${stats.flyingDrones}</span>
                </div>
                <div class="status-item">
                    <span>Avg Battery:</span>
                    <span>${stats.averageBattery.toFixed(1)}%</span>
                </div>
            `;
        }

        hudElement.innerHTML = hudContent;
    }

    updateSwarmDisplay() {
        const activeSwarm = this.swarmManager.getActiveSwarm();
        const droneListElement = document.getElementById('droneItems');

        if (!activeSwarm) {
            droneListElement.innerHTML = '<p>No active swarm</p>';
            return;
        }

        let content = '';
        activeSwarm.drones.forEach((drone, id) => {
            const state = drone.getState();
            content += `
                <div class="drone-item">
                    <h5>${id} ${id === activeSwarm.leader ? '👑' : ''}</h5>
                    <div class="drone-status">
                        Status: ${state.connected ? (state.flying ? 'Flying' : 'Connected') : 'Disconnected'}<br>
                        Battery: ${state.battery}%<br>
                        Position: (${state.position.x.toFixed(0)}, ${state.position.y.toFixed(0)}, ${state.position.z.toFixed(0)})
                    </div>
                </div>
            `;
        });

        droneListElement.innerHTML = content || '<p>No drones in swarm</p>';
    }

    // Logging
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const entry = {
            timestamp,
            message,
            type
        };

        this.logEntries.push(entry);

        // Keep only last 100 entries
        if (this.logEntries.length > 100) {
            this.logEntries.shift();
        }

        this.updateLogDisplay();
        console.log(`[${type.toUpperCase()}] ${timestamp}: ${message}`);
    }

    updateLogDisplay() {
        const logElement = document.getElementById('logOutput');
        const logContent = this.logEntries.map(entry =>
            `<div class="log-entry ${entry.type}">[${entry.timestamp}] ${entry.message}</div>`
        ).join('');

        logElement.innerHTML = logContent;
        logElement.scrollTop = logElement.scrollHeight;
    }

    clearLog() {
        this.logEntries = [];
        this.updateLogDisplay();
    }

    // Keyboard shortcuts info
    showKeyboardShortcuts() {
        const shortcuts = `
            Keyboard Controls (Single Mode):
            W/A/S/D - Move Forward/Left/Back/Right
            Q/E - Move Up/Down
            R/T - Rotate Left/Right
            Space - Takeoff/Land

            Click on a drone to select it for keyboard control.
        `;

        this.log(shortcuts.trim(), 'info');
    }
}
