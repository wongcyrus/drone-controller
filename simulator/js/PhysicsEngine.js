/**
 * PhysicsEngine.js - Simple physics simulation for drones
 */

class PhysicsEngine {
    constructor() {
        this.gravity = -9.81; // m/s²
        this.airResistance = 0.98;
        this.windSpeed = { x: 0, y: 0, z: 0 };
        this.windStrength = 0.1;
        this.turbulence = 0.05;
    }

    applyPhysics(drone, deltaTime) {
        if (!drone.isFlying) {
            return;
        }

        const dt = deltaTime * 0.001; // Convert to seconds

        // Apply gravity (very subtle for flying drones)
        if (drone.targetPosition.y > 0) {
            const gravityEffect = this.gravity * dt * 0.1; // Reduced gravity effect
            drone.position.y += gravityEffect;
        }

        // Apply wind effects
        this.applyWind(drone, dt);

        // Apply turbulence for realism
        this.applyTurbulence(drone, dt);

        // Apply air resistance to movement
        this.applyAirResistance(drone);

        // Update battery based on flight conditions
        this.updateBatteryDrain(drone, dt);

        // Check boundaries
        this.enforceFlightBoundaries(drone);
    }

    applyWind(drone, deltaTime) {
        // Simple wind simulation
        const windEffect = {
            x: this.windSpeed.x * this.windStrength * deltaTime,
            y: this.windSpeed.y * this.windStrength * deltaTime * 0.5,
            z: this.windSpeed.z * this.windStrength * deltaTime
        };

        drone.position.x += windEffect.x;
        drone.position.y += windEffect.y;
        drone.position.z += windEffect.z;

        // Update target position slightly to account for wind drift
        drone.targetPosition.x += windEffect.x * 0.5;
        drone.targetPosition.z += windEffect.z * 0.5;
    }

    applyTurbulence(drone, deltaTime) {
        // Add small random movements for realism
        const turbulenceEffect = {
            x: (Math.random() - 0.5) * this.turbulence,
            y: (Math.random() - 0.5) * this.turbulence * 0.5,
            z: (Math.random() - 0.5) * this.turbulence
        };

        drone.position.x += turbulenceEffect.x;
        drone.position.y += turbulenceEffect.y;
        drone.position.z += turbulenceEffect.z;

        // Add slight rotation turbulence
        drone.rotation.x += (Math.random() - 0.5) * 0.01;
        drone.rotation.z += (Math.random() - 0.5) * 0.01;
    }

    applyAirResistance(drone) {
        // Calculate velocity based on position difference
        const velocity = {
            x: drone.targetPosition.x - drone.position.x,
            y: drone.targetPosition.y - drone.position.y,
            z: drone.targetPosition.z - drone.position.z
        };

        // Calculate speed
        drone.speed = Math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2);

        // Apply air resistance to reduce oscillation
        drone.position.x += velocity.x * this.airResistance * 0.1;
        drone.position.y += velocity.y * this.airResistance * 0.1;
        drone.position.z += velocity.z * this.airResistance * 0.1;
    }

    updateBatteryDrain(drone, deltaTime) {
        if (!drone.isFlying) return;

        // Base battery drain
        let drainRate = 0.01; // Base drain per second

        // Increase drain based on speed
        drainRate += drone.speed * 0.001;

        // Increase drain in wind
        const windMagnitude = Math.sqrt(
            this.windSpeed.x ** 2 + this.windSpeed.y ** 2 + this.windSpeed.z ** 2
        );
        drainRate += windMagnitude * 0.005;

        // Apply battery drain
        drone.battery = Math.max(0, drone.battery - drainRate * deltaTime);

        // Emergency landing if battery is critically low
        if (drone.battery < 5 && drone.isFlying) {
            drone.emergencyStop();
        }
    }

    enforceFlightBoundaries(drone) {
        const maxDistance = 240; // Maximum distance from center
        const maxAltitude = 140;
        const minAltitude = 0;

        // Horizontal boundaries
        const distance = Math.sqrt(drone.position.x ** 2 + drone.position.z ** 2);
        if (distance > maxDistance) {
            const scale = maxDistance / distance;
            drone.position.x *= scale;
            drone.position.z *= scale;
            drone.targetPosition.x *= scale;
            drone.targetPosition.z *= scale;
        }

        // Vertical boundaries
        if (drone.position.y > maxAltitude) {
            drone.position.y = maxAltitude;
            drone.targetPosition.y = Math.min(drone.targetPosition.y, maxAltitude);
        }

        if (drone.position.y < minAltitude) {
            drone.position.y = minAltitude;
            drone.targetPosition.y = Math.max(drone.targetPosition.y, minAltitude);
            if (drone.targetPosition.y <= 0) {
                drone.isFlying = false;
            }
        }
    }

    setWind(x, y, z, strength = 0.1) {
        this.windSpeed = { x, y, z };
        this.windStrength = strength;
    }

    setTurbulence(level) {
        this.turbulence = Math.max(0, Math.min(1, level));
    }

    detectCollisions(drones) {
        const minDistance = 5; // Minimum safe distance between drones

        for (let i = 0; i < drones.length; i++) {
            for (let j = i + 1; j < drones.length; j++) {
                const drone1 = drones[i];
                const drone2 = drones[j];

                if (!drone1.isFlying || !drone2.isFlying) continue;

                const distance = Math.sqrt(
                    (drone1.position.x - drone2.position.x) ** 2 +
                    (drone1.position.y - drone2.position.y) ** 2 +
                    (drone1.position.z - drone2.position.z) ** 2
                );

                if (distance < minDistance) {
                    // Apply collision avoidance
                    this.avoidCollision(drone1, drone2, distance, minDistance);
                }
            }
        }
    }

    avoidCollision(drone1, drone2, currentDistance, minDistance) {
        // Calculate avoidance vector
        const avoidanceForce = (minDistance - currentDistance) / minDistance;

        const dx = drone1.position.x - drone2.position.x;
        const dy = drone1.position.y - drone2.position.y;
        const dz = drone1.position.z - drone2.position.z;

        const length = Math.sqrt(dx ** 2 + dy ** 2 + dz ** 2);
        if (length === 0) return;

        const normalizedDx = dx / length;
        const normalizedDy = dy / length;
        const normalizedDz = dz / length;

        // Apply avoidance force
        const force = avoidanceForce * 2;

        drone1.targetPosition.x += normalizedDx * force;
        drone1.targetPosition.y += normalizedDy * force * 0.5;
        drone1.targetPosition.z += normalizedDz * force;

        drone2.targetPosition.x -= normalizedDx * force;
        drone2.targetPosition.y -= normalizedDy * force * 0.5;
        drone2.targetPosition.z -= normalizedDz * force;
    }

    simulateSignalStrength(drone, distance = 0) {
        // Simulate WiFi signal strength based on distance and interference
        let strength = 100;

        // Distance-based degradation
        strength -= distance * 0.1;

        // Random interference
        strength -= Math.random() * 10;

        // Battery affects signal quality
        if (drone.battery < 20) {
            strength -= (20 - drone.battery) * 2;
        }

        // Wind affects signal stability
        const windEffect = Math.sqrt(
            this.windSpeed.x ** 2 + this.windSpeed.y ** 2 + this.windSpeed.z ** 2
        );
        strength -= windEffect * 5;

        return Math.max(0, Math.min(100, strength));
    }

    getEnvironmentalFactors() {
        return {
            wind: {
                speed: this.windSpeed,
                strength: this.windStrength
            },
            turbulence: this.turbulence,
            gravity: this.gravity
        };
    }
}
