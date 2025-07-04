/**
 * SwarmManager.js - Swarm coordination and management
 */

class SwarmManager {
    constructor(simulator) {
        this.simulator = simulator;
        this.swarms = new Map();
        this.activeSwarmId = null;
    }

    createSwarm(swarmId) {
        if (this.swarms.has(swarmId)) {
            console.warn(`Swarm ${swarmId} already exists`);
            return this.swarms.get(swarmId);
        }

        const swarm = {
            id: swarmId,
            drones: new Map(),
            leader: null,
            formation: null,
            isActive: false
        };

        this.swarms.set(swarmId, swarm);
        this.activeSwarmId = swarmId;
        return swarm;
    }

    addDroneToSwarm(swarmId, droneId) {
        const swarm = this.swarms.get(swarmId);
        const drone = this.simulator.getDrone(droneId);

        if (!swarm || !drone) {
            return false;
        }

        swarm.drones.set(droneId, drone);

        // Set first drone as leader
        if (swarm.drones.size === 1) {
            swarm.leader = droneId;
        }

        return true;
    }

    removeDroneFromSwarm(swarmId, droneId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        swarm.drones.delete(droneId);

        // Reassign leader if necessary
        if (swarm.leader === droneId && swarm.drones.size > 0) {
            swarm.leader = Array.from(swarm.drones.keys())[0];
        }

        return true;
    }

    initializeSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        let success = true;
        swarm.drones.forEach((drone, id) => {
            if (!this.simulator.connectDrone(id)) {
                success = false;
            }
        });

        if (success) {
            swarm.isActive = true;
        }

        return success;
    }

    takeoffSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm || !swarm.isActive) return false;

        let success = true;
        let delay = 0;

        // Staggered takeoff for safety
        swarm.drones.forEach((drone, id) => {
            setTimeout(() => {
                if (!this.simulator.takeoffDrone(id)) {
                    success = false;
                }
            }, delay);
            delay += 500; // 500ms between each takeoff
        });

        return success;
    }

    landSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        let success = true;
        swarm.drones.forEach((drone, id) => {
            if (!this.simulator.landDrone(id)) {
                success = false;
            }
        });

        return success;
    }

    emergencyStopSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        swarm.drones.forEach((drone, id) => {
            this.simulator.emergencyStopDrone(id);
        });

        return true;
    }

    // Coordinated movements
    moveSwarmRelative(swarmId, deltaX, deltaY, deltaZ) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm || !swarm.formation) return false;

        swarm.drones.forEach((drone, id) => {
            this.simulator.moveDrone(id, deltaX, deltaY, deltaZ);
        });

        return true;
    }

    rotateSwarm(swarmId, angle) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return false;

        const centerX = leader.position.x;
        const centerZ = leader.position.z;
        const radians = (angle * Math.PI) / 180;

        swarm.drones.forEach((drone, id) => {
            // Calculate position relative to leader
            const relativeX = drone.position.x - centerX;
            const relativeZ = drone.position.z - centerZ;

            // Rotate around leader
            const newX = relativeX * Math.cos(radians) - relativeZ * Math.sin(radians);
            const newZ = relativeX * Math.sin(radians) + relativeZ * Math.cos(radians);

            // Set new target position
            drone.targetPosition.x = centerX + newX;
            drone.targetPosition.z = centerZ + newZ;

            // Rotate the drone itself
            this.simulator.rotateDrone(id, angle);
        });

        return true;
    }

    // Advanced swarm behaviors
    maintainFormation(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm || !swarm.formation) return;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return;

        const leaderPos = leader.position;

        swarm.formation.positions.forEach((formationPos, index) => {
            const droneIds = Array.from(swarm.drones.keys());
            if (index < droneIds.length) {
                const drone = swarm.drones.get(droneIds[index]);
                if (drone && drone.isFlying) {
                    // Calculate desired position relative to leader
                    const desiredX = leaderPos.x + formationPos.x;
                    const desiredY = leaderPos.y + formationPos.y;
                    const desiredZ = leaderPos.z + formationPos.z;

                    // Smooth adjustment to formation position
                    const currentX = drone.position.x;
                    const currentY = drone.position.y;
                    const currentZ = drone.position.z;

                    const adjustmentFactor = 0.1;
                    const deltaX = (desiredX - currentX) * adjustmentFactor;
                    const deltaY = (desiredY - currentY) * adjustmentFactor;
                    const deltaZ = (desiredZ - currentZ) * adjustmentFactor;

                    drone.targetPosition.x += deltaX;
                    drone.targetPosition.y += deltaY;
                    drone.targetPosition.z += deltaZ;
                }
            }
        });
    }

    followLeader(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return;

        swarm.drones.forEach((drone, id) => {
            if (id === swarm.leader) return; // Skip leader

            const leaderPos = leader.position;
            const followDistance = 15;
            const heightOffset = Math.random() * 10 - 5; // Random height variation

            // Calculate follow position behind leader
            const angle = leader.rotation.y + Math.PI; // Opposite direction
            const followX = leaderPos.x + Math.cos(angle) * followDistance;
            const followZ = leaderPos.z + Math.sin(angle) * followDistance;
            const followY = leaderPos.y + heightOffset;

            drone.targetPosition.x = followX;
            drone.targetPosition.y = followY;
            drone.targetPosition.z = followZ;
        });
    }

    disperseSwarm(swarmId, radius = 30) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return false;

        const centerX = leader.position.x;
        const centerZ = leader.position.z;
        const centerY = leader.position.y;

        const droneIds = Array.from(swarm.drones.keys());
        droneIds.forEach((id, index) => {
            if (id === swarm.leader) return;

            const angle = (index / droneIds.length) * 2 * Math.PI;
            const distance = radius * (0.5 + Math.random() * 0.5); // Random distance within radius

            const newX = centerX + Math.cos(angle) * distance;
            const newZ = centerZ + Math.sin(angle) * distance;
            const newY = centerY + (Math.random() - 0.5) * 20; // Random height variation

            const drone = swarm.drones.get(id);
            if (drone) {
                drone.targetPosition.x = newX;
                drone.targetPosition.y = newY;
                drone.targetPosition.z = newZ;
            }
        });

        return true;
    }

    gatherSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return false;

        const centerX = leader.position.x;
        const centerZ = leader.position.z;
        const centerY = leader.position.y;

        swarm.drones.forEach((drone, id) => {
            if (id === swarm.leader) return;

            // Move towards leader with small random offset
            const offsetX = (Math.random() - 0.5) * 10;
            const offsetZ = (Math.random() - 0.5) * 10;
            const offsetY = (Math.random() - 0.5) * 5;

            drone.targetPosition.x = centerX + offsetX;
            drone.targetPosition.y = centerY + offsetY;
            drone.targetPosition.z = centerZ + offsetZ;
        });

        return true;
    }

    // Swarm search patterns
    searchPattern(swarmId, pattern = 'grid') {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return false;

        const leader = swarm.drones.get(swarm.leader);
        if (!leader) return false;

        const centerX = leader.position.x;
        const centerZ = leader.position.z;
        const centerY = leader.position.y;

        const droneIds = Array.from(swarm.drones.keys());

        switch (pattern) {
            case 'grid':
                this.createGridSearch(droneIds, swarm, centerX, centerY, centerZ);
                break;
            case 'spiral':
                this.createSpiralSearch(droneIds, swarm, centerX, centerY, centerZ);
                break;
            case 'line':
                this.createLineSearch(droneIds, swarm, centerX, centerY, centerZ);
                break;
        }

        return true;
    }

    createGridSearch(droneIds, swarm, centerX, centerY, centerZ) {
        const spacing = 25;
        const columns = Math.ceil(Math.sqrt(droneIds.length));

        droneIds.forEach((id, index) => {
            const row = Math.floor(index / columns);
            const col = index % columns;

            const x = centerX + (col - columns / 2) * spacing;
            const z = centerZ + (row - columns / 2) * spacing;

            const drone = swarm.drones.get(id);
            if (drone) {
                drone.targetPosition.x = x;
                drone.targetPosition.y = centerY;
                drone.targetPosition.z = z;
            }
        });
    }

    createSpiralSearch(droneIds, swarm, centerX, centerY, centerZ) {
        const baseRadius = 20;
        const angleStep = (2 * Math.PI) / droneIds.length;

        droneIds.forEach((id, index) => {
            const angle = index * angleStep;
            const radius = baseRadius + (index * 5);

            const x = centerX + Math.cos(angle) * radius;
            const z = centerZ + Math.sin(angle) * radius;

            const drone = swarm.drones.get(id);
            if (drone) {
                drone.targetPosition.x = x;
                drone.targetPosition.y = centerY;
                drone.targetPosition.z = z;
            }
        });
    }

    createLineSearch(droneIds, swarm, centerX, centerY, centerZ) {
        const spacing = 20;
        const startX = centerX - ((droneIds.length - 1) * spacing) / 2;

        droneIds.forEach((id, index) => {
            const x = startX + index * spacing;

            const drone = swarm.drones.get(id);
            if (drone) {
                drone.targetPosition.x = x;
                drone.targetPosition.y = centerY;
                drone.targetPosition.z = centerZ;
            }
        });
    }

    // Status and monitoring
    getSwarmStatus(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (!swarm) return null;

        const status = {
            id: swarmId,
            droneCount: swarm.drones.size,
            leader: swarm.leader,
            isActive: swarm.isActive,
            connectedDrones: 0,
            flyingDrones: 0,
            averageBattery: 0,
            formation: swarm.formation ? swarm.formation.type : null
        };

        let totalBattery = 0;
        swarm.drones.forEach(drone => {
            if (drone.isConnected) status.connectedDrones++;
            if (drone.isFlying) status.flyingDrones++;
            totalBattery += drone.battery;
        });

        if (swarm.drones.size > 0) {
            status.averageBattery = totalBattery / swarm.drones.size;
        }

        return status;
    }

    getAllSwarms() {
        return Array.from(this.swarms.keys()).map(id => this.getSwarmStatus(id));
    }

    setActiveSwarm(swarmId) {
        if (this.swarms.has(swarmId)) {
            this.activeSwarmId = swarmId;
            return true;
        }
        return false;
    }

    getActiveSwarm() {
        return this.swarms.get(this.activeSwarmId);
    }

    // Cleanup
    removeSwarm(swarmId) {
        const swarm = this.swarms.get(swarmId);
        if (swarm) {
            // Land all drones first
            this.landSwarm(swarmId);
            this.swarms.delete(swarmId);

            if (this.activeSwarmId === swarmId) {
                this.activeSwarmId = null;
            }

            return true;
        }
        return false;
    }
}
