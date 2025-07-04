/**
 * FormationManager.js - Drone formation management and patterns
 */

class FormationManager {
    constructor(simulator) {
        this.simulator = simulator;
        this.formations = new Map();
        this.patterns = this.initializePatterns();
    }

    initializePatterns() {
        return {
            line: {
                name: "Line Formation",
                description: "Drones arranged in a straight line",
                generate: (droneCount, spacing = 150) => this.generateLineFormation(droneCount, spacing)
            },
            circle: {
                name: "Circle Formation",
                description: "Drones arranged in a circle",
                generate: (droneCount, radius = 200) => this.generateCircleFormation(droneCount, radius)
            },
            diamond: {
                name: "Diamond Formation",
                description: "Drones arranged in a diamond shape",
                generate: (droneCount, size = 200) => this.generateDiamondFormation(droneCount, size)
            },
            v: {
                name: "V Formation",
                description: "Drones arranged in a V shape",
                generate: (droneCount, spacing = 150, angle = 45) => this.generateVFormation(droneCount, spacing, angle)
            },
            triangle: {
                name: "Triangle Formation",
                description: "Drones arranged in a triangle",
                generate: (droneCount, size = 200) => this.generateTriangleFormation(droneCount, size)
            },
            square: {
                name: "Square Formation",
                description: "Drones arranged in a square grid",
                generate: (droneCount, spacing = 150) => this.generateSquareFormation(droneCount, spacing)
            },
            arrow: {
                name: "Arrow Formation",
                description: "Drones arranged in an arrow shape",
                generate: (droneCount, length = 200) => this.generateArrowFormation(droneCount, length)
            },
            wedge: {
                name: "Wedge Formation",
                description: "Drones arranged in a wedge shape",
                generate: (droneCount, width = 200) => this.generateWedgeFormation(droneCount, width)
            }
        };
    }

    createFormation(formationId, droneIds, pattern, parameters = {}) {
        if (this.formations.has(formationId)) {
            console.warn(`Formation ${formationId} already exists`);
            return false;
        }

        const patternData = this.patterns[pattern];
        if (!patternData) {
            console.error(`Unknown formation pattern: ${pattern}`);
            return false;
        }

        // Generate formation positions
        const positions = patternData.generate(droneIds.length, ...Object.values(parameters));

        const formation = {
            id: formationId,
            pattern: pattern,
            droneIds: [...droneIds],
            positions: positions,
            parameters: parameters,
            isActive: false,
            centerPosition: { x: 0, y: 0, z: 0 }
        };

        this.formations.set(formationId, formation);
        return formation;
    }

    moveToFormation(formationId, centerX = 0, centerY = 30, centerZ = 0) {
        const formation = this.formations.get(formationId);
        if (!formation) return false;

        formation.centerPosition = { x: centerX, y: centerY, z: centerZ };

        let success = true;
        formation.droneIds.forEach((droneId, index) => {
            if (index < formation.positions.length) {
                const drone = this.simulator.getDrone(droneId);
                if (drone && drone.isConnected) {
                    const pos = formation.positions[index];
                    drone.targetPosition.x = centerX + pos.x;
                    drone.targetPosition.y = centerY + pos.y;
                    drone.targetPosition.z = centerZ + pos.z;
                } else {
                    success = false;
                }
            }
        });

        if (success) {
            formation.isActive = true;
        }

        return success;
    }

    moveFormation(formationId, deltaX, deltaY, deltaZ) {
        const formation = this.formations.get(formationId);
        if (!formation || !formation.isActive) return false;

        formation.centerPosition.x += deltaX;
        formation.centerPosition.y += deltaZ; // Z is up in our system
        formation.centerPosition.z += deltaY; // Y is forward

        formation.droneIds.forEach((droneId, index) => {
            if (index < formation.positions.length) {
                const drone = this.simulator.getDrone(droneId);
                if (drone && drone.isFlying) {
                    drone.targetPosition.x += deltaX;
                    drone.targetPosition.y += deltaZ;
                    drone.targetPosition.z += deltaY;
                }
            }
        });

        return true;
    }

    rotateFormation(formationId, angle) {
        const formation = this.formations.get(formationId);
        if (!formation || !formation.isActive) return false;

        const radians = (angle * Math.PI) / 180;
        const centerX = formation.centerPosition.x;
        const centerZ = formation.centerPosition.z;

        formation.droneIds.forEach((droneId, index) => {
            if (index < formation.positions.length) {
                const drone = this.simulator.getDrone(droneId);
                if (drone && drone.isFlying) {
                    // Get current position relative to formation center
                    const relativeX = drone.targetPosition.x - centerX;
                    const relativeZ = drone.targetPosition.z - centerZ;

                    // Rotate around center
                    const newX = relativeX * Math.cos(radians) - relativeZ * Math.sin(radians);
                    const newZ = relativeX * Math.sin(radians) + relativeZ * Math.cos(radians);

                    // Set new target position
                    drone.targetPosition.x = centerX + newX;
                    drone.targetPosition.z = centerZ + newZ;

                    // Rotate the drone itself
                    drone.rotateTo(angle);
                }
            }
        });

        return true;
    }

    scaleFormation(formationId, scaleFactor) {
        const formation = this.formations.get(formationId);
        if (!formation || !formation.isActive) return false;

        const centerX = formation.centerPosition.x;
        const centerY = formation.centerPosition.y;
        const centerZ = formation.centerPosition.z;

        formation.droneIds.forEach((droneId, index) => {
            if (index < formation.positions.length) {
                const drone = this.simulator.getDrone(droneId);
                if (drone && drone.isFlying) {
                    const pos = formation.positions[index];

                    // Scale position relative to center
                    drone.targetPosition.x = centerX + (pos.x * scaleFactor);
                    drone.targetPosition.y = centerY + (pos.y * scaleFactor);
                    drone.targetPosition.z = centerZ + (pos.z * scaleFactor);
                }
            }
        });

        // Update formation positions for future reference
        formation.positions.forEach(pos => {
            pos.x *= scaleFactor;
            pos.y *= scaleFactor;
            pos.z *= scaleFactor;
        });

        return true;
    }

    // Formation patterns
    generateLineFormation(droneCount, spacing = 150) {
        const positions = [];
        const startX = -(droneCount - 1) * spacing / 2;

        for (let i = 0; i < droneCount; i++) {
            positions.push({
                x: startX + i * spacing,
                y: 0,
                z: 0
            });
        }

        return positions;
    }

    generateCircleFormation(droneCount, radius = 200) {
        const positions = [];
        const angleStep = (2 * Math.PI) / droneCount;

        for (let i = 0; i < droneCount; i++) {
            const angle = i * angleStep;
            positions.push({
                x: Math.cos(angle) * radius,
                y: 0,
                z: Math.sin(angle) * radius
            });
        }

        return positions;
    }

    generateDiamondFormation(droneCount, size = 200) {
        const positions = [];

        if (droneCount === 1) {
            positions.push({ x: 0, y: 0, z: 0 });
        } else if (droneCount === 2) {
            positions.push({ x: -size/2, y: 0, z: 0 });
            positions.push({ x: size/2, y: 0, z: 0 });
        } else if (droneCount === 3) {
            positions.push({ x: 0, y: 0, z: -size/2 }); // Front
            positions.push({ x: -size/2, y: 0, z: size/2 }); // Back left
            positions.push({ x: size/2, y: 0, z: size/2 }); // Back right
        } else {
            // Diamond shape with 4 main points
            positions.push({ x: 0, y: 0, z: -size }); // Front
            positions.push({ x: -size, y: 0, z: 0 }); // Left
            positions.push({ x: size, y: 0, z: 0 }); // Right
            positions.push({ x: 0, y: 0, z: size }); // Back

            // Add additional drones between main points
            for (let i = 4; i < droneCount; i++) {
                const angle = (i - 4) * (2 * Math.PI) / (droneCount - 4);
                const radiusVariation = 0.7; // Closer to center
                positions.push({
                    x: Math.cos(angle) * size * radiusVariation,
                    y: 0,
                    z: Math.sin(angle) * size * radiusVariation
                });
            }
        }

        return positions;
    }

    generateVFormation(droneCount, spacing = 150, angle = 45) {
        const positions = [];
        const radians = (angle * Math.PI) / 180;

        // Leader at the front
        positions.push({ x: 0, y: 0, z: 0 });

        // Add drones to both sides
        for (let i = 1; i < droneCount; i++) {
            const side = i % 2 === 1 ? 1 : -1; // Alternate sides
            const row = Math.ceil(i / 2);

            const x = side * row * spacing * Math.sin(radians);
            const z = row * spacing * Math.cos(radians);

            positions.push({ x, y: 0, z });
        }

        return positions;
    }

    generateTriangleFormation(droneCount, size = 200) {
        const positions = [];

        if (droneCount === 1) {
            positions.push({ x: 0, y: 0, z: 0 });
        } else if (droneCount === 2) {
            positions.push({ x: -size/2, y: 0, z: 0 });
            positions.push({ x: size/2, y: 0, z: 0 });
        } else {
            // Equilateral triangle
            const height = size * Math.sqrt(3) / 2;

            positions.push({ x: 0, y: 0, z: -height/2 }); // Front
            positions.push({ x: -size/2, y: 0, z: height/2 }); // Back left
            positions.push({ x: size/2, y: 0, z: height/2 }); // Back right

            // Fill in additional drones
            for (let i = 3; i < droneCount; i++) {
                const angle = (i - 3) * (2 * Math.PI) / (droneCount - 3);
                const radius = size * 0.3; // Inner circle
                positions.push({
                    x: Math.cos(angle) * radius,
                    y: 0,
                    z: Math.sin(angle) * radius
                });
            }
        }

        return positions;
    }

    generateSquareFormation(droneCount, spacing = 150) {
        const positions = [];
        const gridSize = Math.ceil(Math.sqrt(droneCount));
        const startX = -(gridSize - 1) * spacing / 2;
        const startZ = -(gridSize - 1) * spacing / 2;

        for (let i = 0; i < droneCount; i++) {
            const row = Math.floor(i / gridSize);
            const col = i % gridSize;

            positions.push({
                x: startX + col * spacing,
                y: 0,
                z: startZ + row * spacing
            });
        }

        return positions;
    }

    generateArrowFormation(droneCount, length = 200) {
        const positions = [];

        // Arrow head (triangle)
        positions.push({ x: 0, y: 0, z: -length }); // Point
        if (droneCount > 1) {
            positions.push({ x: -length/3, y: 0, z: -length/2 }); // Left wing
        }
        if (droneCount > 2) {
            positions.push({ x: length/3, y: 0, z: -length/2 }); // Right wing
        }

        // Arrow shaft
        for (let i = 3; i < droneCount; i++) {
            const shaftPosition = (i - 2) * (length / (droneCount - 2));
            positions.push({
                x: 0,
                y: 0,
                z: -length/2 + shaftPosition
            });
        }

        return positions;
    }

    generateWedgeFormation(droneCount, width = 200) {
        const positions = [];

        // Leader at front
        positions.push({ x: 0, y: 0, z: 0 });

        // Create wedge shape
        for (let i = 1; i < droneCount; i++) {
            const row = Math.floor((i - 1) / 2) + 1;
            const side = (i - 1) % 2 === 0 ? -1 : 1;

            const x = side * row * width / 4;
            const z = row * width / 3;

            positions.push({ x, y: 0, z });
        }

        return positions;
    }

    // Dynamic formations
    morphFormation(fromFormationId, toPattern, parameters = {}, duration = 5000) {
        const formation = this.formations.get(fromFormationId);
        if (!formation || !formation.isActive) return false;

        const patternData = this.patterns[toPattern];
        if (!patternData) return false;

        const newPositions = patternData.generate(formation.droneIds.length, ...Object.values(parameters));

        // Animate transition
        this.animateFormationTransition(formation, newPositions, duration);

        // Update formation data
        formation.pattern = toPattern;
        formation.positions = newPositions;
        formation.parameters = parameters;

        return true;
    }

    animateFormationTransition(formation, newPositions, duration) {
        const startTime = Date.now();
        const originalPositions = formation.positions.map(pos => ({ ...pos }));

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-in-out)
            const easeProgress = progress < 0.5
                ? 2 * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 3) / 2;

            formation.droneIds.forEach((droneId, index) => {
                if (index < newPositions.length) {
                    const drone = this.simulator.getDrone(droneId);
                    if (drone && drone.isFlying) {
                        const original = originalPositions[index];
                        const target = newPositions[index];
                        const centerX = formation.centerPosition.x;
                        const centerY = formation.centerPosition.y;
                        const centerZ = formation.centerPosition.z;

                        // Interpolate between positions
                        const currentX = original.x + (target.x - original.x) * easeProgress;
                        const currentY = original.y + (target.y - original.y) * easeProgress;
                        const currentZ = original.z + (target.z - original.z) * easeProgress;

                        drone.targetPosition.x = centerX + currentX;
                        drone.targetPosition.y = centerY + currentY;
                        drone.targetPosition.z = centerZ + currentZ;
                    }
                }
            });

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        animate();
    }

    // Formation analysis
    getFormationCohesion(formationId) {
        const formation = this.formations.get(formationId);
        if (!formation || !formation.isActive) return 0;

        let totalDeviation = 0;
        let validDrones = 0;

        formation.droneIds.forEach((droneId, index) => {
            if (index < formation.positions.length) {
                const drone = this.simulator.getDrone(droneId);
                if (drone && drone.isFlying) {
                    const expectedPos = formation.positions[index];
                    const centerX = formation.centerPosition.x;
                    const centerY = formation.centerPosition.y;
                    const centerZ = formation.centerPosition.z;

                    const expectedX = centerX + expectedPos.x;
                    const expectedY = centerY + expectedPos.y;
                    const expectedZ = centerZ + expectedPos.z;

                    const deviation = Math.sqrt(
                        Math.pow(drone.position.x - expectedX, 2) +
                        Math.pow(drone.position.y - expectedY, 2) +
                        Math.pow(drone.position.z - expectedZ, 2)
                    );

                    totalDeviation += deviation;
                    validDrones++;
                }
            }
        });

        return validDrones > 0 ? (100 - Math.min(totalDeviation / validDrones, 100)) : 0;
    }

    // Utility methods
    getFormationInfo(formationId) {
        const formation = this.formations.get(formationId);
        if (!formation) return null;

        return {
            id: formation.id,
            pattern: formation.pattern,
            patternName: this.patterns[formation.pattern]?.name || formation.pattern,
            droneCount: formation.droneIds.length,
            isActive: formation.isActive,
            centerPosition: formation.centerPosition,
            cohesion: this.getFormationCohesion(formationId)
        };
    }

    getAllFormations() {
        return Array.from(this.formations.keys()).map(id => this.getFormationInfo(id));
    }

    removeFormation(formationId) {
        return this.formations.delete(formationId);
    }

    getAvailablePatterns() {
        return Object.keys(this.patterns).map(key => ({
            key,
            name: this.patterns[key].name,
            description: this.patterns[key].description
        }));
    }
}
