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
            name: droneData.name || `Tello-${droneId}`,
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

        console.log(`${drone.name} (${droneId}) added to simulator`);

        if (this.onDroneListUpdate) {
            this.onDroneListUpdate();
        }

        return drone;
    }

    removeDrone(droneId) {
        if (this.drones.has(droneId)) {
            const drone = this.drones.get(droneId);
            const droneName = drone.name;

            this.drones.delete(droneId);

            if (this.selectedDroneId === droneId) {
                this.selectedDroneId = null;
                if (this.onDroneSelect) {
                    this.onDroneSelect(null);
                }
            }

            console.log(`${droneName} (${droneId}) removed from simulator`);

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
            console.log(`Selected ${this.drones.get(droneId).name} (${droneId})`);
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

            console.log(`Updated state for ${drone.name} (${droneId}):`, newState);

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
            console.log(`${drone.name} (${droneId}) connection: ${connected}`);

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

            console.log(`Command recorded for ${drone.name} (${droneId}): ${command} -> ${response}`);
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

    simulateReset(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        // Reset drone to initial state - same as Python backend
        drone.flying = false;
        drone.state = {
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
        };

        console.log(`🔄 ${drone.name} (${droneId}) reset to initial state`);
        this.updateDroneState(droneId, drone.state);
    }

    processCommand(droneId, command) {
        const drone = this.drones.get(droneId);
        if (!drone) {
            return 'error Drone not found';
        }

        console.log(`📡 Processing command for ${drone.name} (${droneId}): ${command}`);

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
                        console.log(`🛫 ${drone.name} taking off...`);
                        this.simulateTakeoff(droneId);
                    } else {
                        response = 'error Already flying';
                    }
                    break;

                case 'land':
                    if (drone.flying) {
                        console.log(`🛬 ${drone.name} landing...`);
                        this.simulateLanding(droneId);
                    } else {
                        response = 'error Not flying';
                    }
                    break;

                case 'emergency':
                    console.log(`🚨 ${drone.name} emergency stop!`);
                    this.simulateEmergency(droneId);
                    break;

                case 'reset':
                    this.simulateReset(droneId);
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
                            console.log(`🚁 ${drone.name} moving ${cmd} ${distance}cm`);
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
                            console.log(`🔄 ${drone.name} rotating ${cmd} ${angle}°`);
                            this.simulateRotation(droneId, cmd, angle);
                        } else {
                            response = 'error Out of range';
                        }
                    } else {
                        response = 'error Invalid argument';
                    }
                    break;

                case 'flip':
                    if (args.length > 0) {
                        const direction = args[0].toLowerCase();
                        if (['f', 'b', 'l', 'r'].includes(direction)) {
                            if (drone.flying) {
                                console.log(`🤸 ${drone.name} performing flip ${direction}`);
                                this.simulateFlip(droneId, direction);
                            } else {
                                response = 'error Not flying';
                            }
                        } else {
                            response = 'error Invalid direction';
                        }
                    } else {
                        response = 'error Missing direction';
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
        const droneNumber = this.nextDroneId++;
        const droneId = `virtual_${droneNumber}`;
        const drone = this.addDrone(droneId, {
            name: `Virtual Tello ${droneNumber}`,
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
                    // Only update flight time - no random variations
                    const state = { ...drone.state };

                    // Increment flight time if flying
                    if (drone.flying) {
                        state.time += 1;
                    }

                    // No random battery drain - only command-based
                    // No sensor noise - keep values stable
                    // State updates come from the backend via WebSocket

                    // Only update if there are actual changes
                    if (state.time !== drone.state.time) {
                        this.updateDroneState(droneId, state);
                    }
                }
            });
        }, 1000); // Update every second
    }

    simulateFlip(droneId, direction) {
        const drone = this.drones.get(droneId);
        if (!drone || !drone.flying) return;

        const state = drone.state;

        // Perform a single flip animation without continuous updates
        console.log(`🔄 Starting flip animation for ${drone.name} (${droneId}) in direction: ${direction}`);

        // Trigger immediate 3D animation
        this.triggerFlipAnimation(droneId, direction);

        // Drain battery for flip maneuver
        state.bat = Math.max(0, state.bat - 2);

        this.updateDroneState(droneId, state);
    }

    triggerFlipAnimation(droneId, direction) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        console.log(`🚀 Sending flip trigger to 3D scene for ${drone.name} (${droneId}): direction=${direction}`);

        // Send a one-time flip trigger to the 3D scene
        const state = {
            ...drone.state,
            _flipTrigger: {
                direction: direction,
                timestamp: Date.now()
            }
        };

        console.log(`State update with flip trigger for ${drone.name}:`, state._flipTrigger);
        this.updateDroneState(droneId, state);

        // Clear the trigger after a short delay to prevent repeated triggers
        setTimeout(() => {
            const clearedState = { ...drone.state };
            delete clearedState._flipTrigger;
            console.log(`🧹 Clearing flip trigger for ${drone.name} (${droneId})`);
            this.updateDroneState(droneId, clearedState);
        }, 100);
    }

}

// Export for use in other scripts
window.DroneSimulator = DroneSimulator;
