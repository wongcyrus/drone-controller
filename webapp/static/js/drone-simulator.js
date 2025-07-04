/**
 * Drone Simulator Class
 * Manages drone states and integrates with the 3D scene
 */

class DroneSimulator {
    constructor() {
        this.drones = new Map(); // drone_id -> drone_data
        this.selectedDroneId = null;
        this.nextDroneId = 1;

        // Event callbacks
        this.onDroneListUpdate = null;
        this.onDroneSelect = null;
        this.onDroneStateUpdate = null;
    }

    addDrone(droneId, droneData = {}) {
        const defaultData = {
            id: droneId,
            name: droneData.name || `Drone-${droneId}`,
            ip: droneData.ip || '127.0.0.1',
            connected: droneData.connected || false,
            flying: false,
            state: {
                mid: -1,
                x: 0,
                y: 0,
                z: 0,
                pitch: 0,
                roll: 0,
                yaw: 0,
                vgx: 0,
                vgy: 0,
                vgz: 0,
                templ: 20,
                temph: 25,
                tof: 10,
                h: 0,
                bat: 100,
                baro: 1013.25,
                time: 0,
                agx: 0.0,
                agy: 0.0,
                agz: -1000.0
            },
            lastCommand: null,
            lastResponse: null,
            commandHistory: []
        };

        const drone = { ...defaultData, ...droneData };
        this.drones.set(droneId, drone);

        console.log(`Drone ${droneId} added to simulator`);

        if (this.onDroneListUpdate) {
            this.onDroneListUpdate();
        }

        return drone;
    }

    removeDrone(droneId) {
        if (this.drones.has(droneId)) {
            this.drones.delete(droneId);

            if (this.selectedDroneId === droneId) {
                this.selectedDroneId = null;
                if (this.onDroneSelect) {
                    this.onDroneSelect(null);
                }
            }

            console.log(`Drone ${droneId} removed from simulator`);

            if (this.onDroneListUpdate) {
                this.onDroneListUpdate();
            }
        }
    }

    getDrone(droneId) {
        return this.drones.get(droneId);
    }

    getAllDrones() {
        return Array.from(this.drones.values());
    }

    selectDrone(droneId) {
        if (this.drones.has(droneId)) {
            this.selectedDroneId = droneId;
            if (this.onDroneSelect) {
                this.onDroneSelect(this.drones.get(droneId));
            }
            console.log(`Selected drone: ${droneId}`);
        }
    }

    getSelectedDrone() {
        return this.selectedDroneId ? this.drones.get(this.selectedDroneId) : null;
    }

    updateDroneState(droneId, newState) {
        const drone = this.drones.get(droneId);
        if (drone) {
            // Merge new state with existing state
            drone.state = { ...drone.state, ...newState };

            // Update flying status based on height
            drone.flying = drone.state.h > 0;

            console.log(`Updated state for drone ${droneId}:`, newState);

            if (this.onDroneStateUpdate) {
                this.onDroneStateUpdate(droneId, drone.state);
            }

            // Update UI if this is the selected drone
            if (this.selectedDroneId === droneId && this.onDroneSelect) {
                this.onDroneSelect(drone);
            }
        }
    }

    updateDroneConnection(droneId, connected) {
        const drone = this.drones.get(droneId);
        if (drone) {
            drone.connected = connected;
            console.log(`Drone ${droneId} connection: ${connected}`);

            if (this.onDroneListUpdate) {
                this.onDroneListUpdate();
            }
        }
    }

    recordCommand(droneId, command, response) {
        const drone = this.drones.get(droneId);
        if (drone) {
            drone.lastCommand = command;
            drone.lastResponse = response;

            // Add to command history
            drone.commandHistory.push({
                command,
                response,
                timestamp: new Date().toISOString()
            });

            // Limit history size
            if (drone.commandHistory.length > 100) {
                drone.commandHistory.shift();
            }

            console.log(`Command recorded for drone ${droneId}: ${command} -> ${response}`);
        }
    }

    simulateMovement(droneId, direction, distance) {
        const drone = this.drones.get(droneId);
        if (!drone || !drone.flying) return;

        const state = drone.state;

        switch (direction) {
            case 'up':
                state.h = Math.min(state.h + distance, 500);
                break;
            case 'down':
                state.h = Math.max(state.h - distance, 0);
                if (state.h === 0) drone.flying = false;
                break;
            case 'forward':
                state.y += distance * 0.1; // Scale for 3D scene
                break;
            case 'back':
                state.y -= distance * 0.1;
                break;
            case 'left':
                state.x -= distance * 0.1;
                break;
            case 'right':
                state.x += distance * 0.1;
                break;
        }

        // Add some random variation
        state.pitch += (Math.random() - 0.5) * 4;
        state.roll += (Math.random() - 0.5) * 4;
        state.bat = Math.max(0, state.bat - Math.random());

        this.updateDroneState(droneId, state);
    }

    simulateRotation(droneId, direction, angle) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        const state = drone.state;

        if (direction === 'cw') {
            state.yaw = (state.yaw + angle) % 360;
        } else if (direction === 'ccw') {
            state.yaw = (state.yaw - angle + 360) % 360;
        }

        // Drain battery slightly
        state.bat = Math.max(0, state.bat - Math.random());

        this.updateDroneState(droneId, state);
    }

    simulateTakeoff(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone || drone.flying) return;

        drone.flying = true;
        drone.state.h = 50; // Default takeoff height

        this.updateDroneState(droneId, drone.state);
    }

    simulateLanding(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone || !drone.flying) return;

        drone.flying = false;
        drone.state.h = 0;

        this.updateDroneState(droneId, drone.state);
    }

    simulateEmergency(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        drone.flying = false;
        drone.state.h = 0;
        drone.state.pitch = 0;
        drone.state.roll = 0;

        this.updateDroneState(droneId, drone.state);
    }

    processCommand(droneId, command) {
        const drone = this.drones.get(droneId);
        if (!drone) {
            return 'error Drone not found';
        }

        const parts = command.toLowerCase().split(' ');
        const cmd = parts[0];
        const args = parts.slice(1);

        let response = 'ok';

        try {
            switch (cmd) {
                case 'command':
                    // Enable SDK mode
                    break;

                case 'takeoff':
                    if (!drone.flying) {
                        this.simulateTakeoff(droneId);
                    } else {
                        response = 'error Already flying';
                    }
                    break;

                case 'land':
                    if (drone.flying) {
                        this.simulateLanding(droneId);
                    } else {
                        response = 'error Not flying';
                    }
                    break;

                case 'emergency':
                    this.simulateEmergency(droneId);
                    break;

                case 'up':
                case 'down':
                case 'left':
                case 'right':
                case 'forward':
                case 'back':
                    if (args.length > 0 && !isNaN(args[0])) {
                        const distance = parseInt(args[0]);
                        if (distance >= 20 && distance <= 500) {
                            this.simulateMovement(droneId, cmd, distance);
                        } else {
                            response = 'error Out of range';
                        }
                    } else {
                        response = 'error Invalid argument';
                    }
                    break;

                case 'cw':
                case 'ccw':
                    if (args.length > 0 && !isNaN(args[0])) {
                        const angle = parseInt(args[0]);
                        if (angle >= 1 && angle <= 360) {
                            this.simulateRotation(droneId, cmd, angle);
                        } else {
                            response = 'error Out of range';
                        }
                    } else {
                        response = 'error Invalid argument';
                    }
                    break;

                case 'speed?':
                    response = '10';
                    break;

                case 'battery?':
                    response = drone.state.bat.toString();
                    break;

                case 'height?':
                    response = drone.state.h.toString();
                    break;

                case 'temp?':
                    response = `${Math.floor(drone.state.templ)}~${Math.floor(drone.state.temph)}`;
                    break;

                default:
                    response = 'error Unknown command';
            }
        } catch (error) {
            console.error('Error processing command:', error);
            response = 'error Command failed';
        }

        this.recordCommand(droneId, command, response);
        return response;
    }

    createVirtualDrone() {
        const droneId = `virtual_${this.nextDroneId++}`;
        const drone = this.addDrone(droneId, {
            name: `Virtual Drone ${this.nextDroneId - 1}`,
            connected: true,
            ip: 'virtual'
        });

        return drone;
    }

    // Simulate periodic state updates (like real drone state broadcasting)
    startStateSimulation() {
        setInterval(() => {
            this.drones.forEach((drone, droneId) => {
                if (drone.connected) {
                    // Simulate small state changes
                    const state = { ...drone.state };

                    // Increment flight time if flying
                    if (drone.flying) {
                        state.time += 1;
                    }

                    // Slowly drain battery
                    if (Math.random() < 0.01) { // 1% chance every update
                        state.bat = Math.max(0, state.bat - 1);
                    }

                    // Add sensor noise
                    state.baro += (Math.random() - 0.5) * 0.2;
                    state.templ += (Math.random() - 0.5) * 1.0;
                    state.temph += (Math.random() - 0.5) * 1.0;

                    // Keep temperature range realistic
                    state.templ = Math.max(10, Math.min(40, state.templ));
                    state.temph = Math.max(state.templ, Math.min(45, state.temph));

                    this.updateDroneState(droneId, state);
                }
            });
        }, 1000); // Update every second
    }
}

// Export for use in other scripts
window.DroneSimulator = DroneSimulator;
