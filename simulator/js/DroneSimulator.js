/**
 * DroneSimulator.js - Main 3D Drone Simulation Engine
 */

class DroneSimulator {
    constructor(canvas) {
        this.canvas = canvas;
        this.drones = new Map();
        this.activeMode = 'single';
        this.selectedDroneId = null;

        // Initialize Three.js
        this.initializeRenderer();
        this.initializeScene();
        this.initializeCamera();
        this.initializeControls();

        // Initialize subsystems
        this.environment = new Environment(this.scene);
        this.physics = new PhysicsEngine();

        // Animation
        this.clock = new THREE.Clock();
        this.isRunning = false;

        // Event listeners
        this.setupEventListeners();

        // Start the simulation
        this.start();
    }

    initializeRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.setClearColor(0x87CEEB, 1);
    }

    initializeScene() {
        this.scene = new THREE.Scene();
    }

    initializeCamera() {
        this.camera = new THREE.PerspectiveCamera(
            75,
            this.canvas.clientWidth / this.canvas.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(50, 30, 50);
        this.camera.lookAt(0, 0, 0);
    }

    initializeControls() {
        try {
            if (typeof THREE.OrbitControls !== 'undefined') {
                this.controls = new THREE.OrbitControls(this.camera, this.canvas);
            } else {
                console.warn('OrbitControls not available, using fallback');
                // Create a simple fallback control system
                this.controls = {
                    enableDamping: true,
                    dampingFactor: 0.05,
                    minDistance: 10,
                    maxDistance: 200,
                    maxPolarAngle: Math.PI / 2.1,
                    update: () => {} // No-op for compatibility
                };
                return;
            }

            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
            this.controls.minDistance = 10;
            this.controls.maxDistance = 200;
            this.controls.maxPolarAngle = Math.PI / 2.1; // Prevent going below ground
        } catch (error) {
            console.error('Failed to initialize controls:', error);
            this.controls = { update: () => {} }; // Fallback
        }
    }

    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Keyboard controls
        document.addEventListener('keydown', (event) => this.onKeyDown(event));

        // Mouse controls for drone selection
        this.canvas.addEventListener('click', (event) => this.onCanvasClick(event));
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    onKeyDown(event) {
        if (!this.selectedDroneId) return;

        const drone = this.drones.get(this.selectedDroneId);
        if (!drone || !drone.isConnected) return;

        const moveDistance = 20;
        const rotationAngle = 45;

        switch (event.code) {
            case 'KeyW': // Forward
                drone.moveTo(0, moveDistance, 0);
                break;
            case 'KeyS': // Backward
                drone.moveTo(0, -moveDistance, 0);
                break;
            case 'KeyA': // Left
                drone.moveTo(-moveDistance, 0, 0);
                break;
            case 'KeyD': // Right
                drone.moveTo(moveDistance, 0, 0);
                break;
            case 'KeyQ': // Up
                drone.moveTo(0, 0, moveDistance);
                break;
            case 'KeyE': // Down
                drone.moveTo(0, 0, -moveDistance);
                break;
            case 'KeyR': // Rotate left
                drone.rotateTo(-rotationAngle);
                break;
            case 'KeyT': // Rotate right
                drone.rotateTo(rotationAngle);
                break;
            case 'Space': // Takeoff/Land
                event.preventDefault();
                if (drone.isFlying) {
                    drone.land();
                } else {
                    drone.takeoff();
                }
                break;
        }
    }

    onCanvasClick(event) {
        // Ray casting for drone selection
        const mouse = new THREE.Vector2();
        const rect = this.canvas.getBoundingClientRect();

        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);

        const intersectableObjects = [];
        this.drones.forEach(drone => {
            intersectableObjects.push(drone.group);
        });

        const intersects = raycaster.intersectObjects(intersectableObjects, true);

        if (intersects.length > 0) {
            // Find which drone was clicked
            for (const [id, drone] of this.drones) {
                if (intersects[0].object.parent === drone.group ||
                    intersects[0].object.parent.parent === drone.group) {
                    this.selectDrone(id);
                    break;
                }
            }
        }
    }

    selectDrone(droneId) {
        this.selectedDroneId = droneId;

        // Visual feedback for selected drone
        this.drones.forEach((drone, id) => {
            if (id === droneId) {
                // Add selection indicator
                this.addSelectionIndicator(drone);
            } else {
                // Remove selection indicator
                this.removeSelectionIndicator(drone);
            }
        });
    }

    addSelectionIndicator(drone) {
        this.removeSelectionIndicator(drone);

        const geometry = new THREE.RingGeometry(8, 10, 16);
        const material = new THREE.MeshBasicMaterial({
            color: 0xffff00,
            transparent: true,
            opacity: 0.7,
            side: THREE.DoubleSide
        });

        drone.selectionRing = new THREE.Mesh(geometry, material);
        drone.selectionRing.rotation.x = -Math.PI / 2;
        drone.selectionRing.position.y = -3;
        drone.group.add(drone.selectionRing);
    }

    removeSelectionIndicator(drone) {
        if (drone.selectionRing) {
            drone.group.remove(drone.selectionRing);
            drone.selectionRing = null;
        }
    }

    // Drone management methods
    addDrone(id, ipAddress = null) {
        if (this.drones.has(id)) {
            console.warn(`Drone ${id} already exists`);
            return null;
        }

        const position = this.getNextDronePosition();
        const drone = new DroneModel(id, this.scene, position);
        this.drones.set(id, drone);

        // Auto-select first drone in single mode
        if (this.activeMode === 'single' && this.drones.size === 1) {
            this.selectDrone(id);
        }

        return drone;
    }

    removeDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            drone.remove();
            this.drones.delete(id);

            if (this.selectedDroneId === id) {
                this.selectedDroneId = null;
            }
            return true;
        }
        return false;
    }

    getDrone(id) {
        return this.drones.get(id);
    }

    getAllDrones() {
        return Array.from(this.drones.values());
    }

    getNextDronePosition() {
        const spacing = 15;
        const count = this.drones.size;
        const row = Math.floor(count / 5);
        const col = count % 5;

        return {
            x: (col - 2) * spacing,
            y: 0,
            z: row * spacing
        };
    }

    // Control methods
    connectDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.connect();
        }
        return false;
    }

    disconnectDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.disconnect();
        }
        return false;
    }

    takeoffDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.takeoff();
        }
        return false;
    }

    landDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.land();
        }
        return false;
    }

    moveDrone(id, x, y, z) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.moveTo(x, y, z);
        }
        return false;
    }

    rotateDrone(id, angle) {
        const drone = this.drones.get(id);
        if (drone) {
            return drone.rotateTo(angle);
        }
        return false;
    }

    emergencyStopDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            drone.emergencyStop();
            return true;
        }
        return false;
    }

    emergencyStopAll() {
        this.drones.forEach(drone => {
            drone.emergencyStop();
        });
    }

    // Swarm methods
    connectAllDrones() {
        let success = true;
        this.drones.forEach(drone => {
            if (!drone.connect()) {
                success = false;
            }
        });
        return success;
    }

    takeoffAllDrones() {
        let success = true;
        this.drones.forEach(drone => {
            if (!drone.takeoff()) {
                success = false;
            }
        });
        return success;
    }

    landAllDrones() {
        let success = true;
        this.drones.forEach(drone => {
            if (!drone.land()) {
                success = false;
            }
        });
        return success;
    }

    // Camera controls
    focusOnDrone(id) {
        const drone = this.drones.get(id);
        if (drone) {
            const position = drone.position;
            this.controls.target.set(position.x, position.y, position.z);
            this.camera.position.set(
                position.x + 30,
                position.y + 20,
                position.z + 30
            );
        }
    }

    resetCamera() {
        this.controls.target.set(0, 0, 0);
        this.camera.position.set(50, 30, 50);
    }

    // Environmental controls
    setWind(x, y, z, strength) {
        this.physics.setWind(x, y, z, strength);
    }

    setWeather(type) {
        this.environment.addWeatherEffect(type);
    }

    // Simulation control
    start() {
        this.isRunning = true;
        this.animate();
    }

    stop() {
        this.isRunning = false;
    }

    animate() {
        if (!this.isRunning) return;

        requestAnimationFrame(() => this.animate());

        const deltaTime = this.clock.getDelta() * 1000; // Convert to milliseconds

        // Update controls
        this.controls.update();

        // Update physics
        const dronesArray = Array.from(this.drones.values());
        dronesArray.forEach(drone => {
            this.physics.applyPhysics(drone, deltaTime);
            drone.animate();
            drone.updateBattery();
        });

        // Collision detection for swarm mode
        if (this.activeMode === 'swarm' && dronesArray.length > 1) {
            this.physics.detectCollisions(dronesArray);
        }

        // Update environment
        this.environment.animate();

        // Render the scene
        this.renderer.render(this.scene, this.camera);
    }

    // Utility methods
    getStats() {
        const stats = {
            totalDrones: this.drones.size,
            connectedDrones: 0,
            flyingDrones: 0,
            averageBattery: 0
        };

        let totalBattery = 0;
        this.drones.forEach(drone => {
            if (drone.isConnected) stats.connectedDrones++;
            if (drone.isFlying) stats.flyingDrones++;
            totalBattery += drone.battery;
        });

        if (this.drones.size > 0) {
            stats.averageBattery = totalBattery / this.drones.size;
        }

        return stats;
    }

    setMode(mode) {
        this.activeMode = mode;

        if (mode === 'single') {
            // Auto-select first drone if available
            if (this.drones.size > 0 && !this.selectedDroneId) {
                this.selectDrone(Array.from(this.drones.keys())[0]);
            }
        }
    }
}
