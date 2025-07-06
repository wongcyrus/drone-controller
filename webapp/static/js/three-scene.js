/**
 * Three.js Scene Manager for Drone Simulator
 * Handles 3D visualization of drones and environment
 */

class ThreeScene {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.animationId = null;

        // Scene objects
        this.drones = new Map(); // drone_id -> drone_object
        this.droneLabels = new Map(); // drone_id -> label_element
        this.grid = null;
        this.axes = null;
        this.lights = [];

        // Settings
        this.showGrid = true;
        this.showAxes = true;

        this.init();
    }

    init() {
        this.createScene();
        this.createCamera();
        this.createRenderer();
        this.createControls();
        this.createLights();
        this.createEnvironment();
        this.startRenderLoop();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        console.log('Three.js scene initialized');
    }

    createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0a);
        this.scene.fog = new THREE.Fog(0x0a0a0a, 1000, 20000); // Extended fog range for infinite world
    }

    createCamera() {
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 50000); // Increased far plane for infinite world
        this.camera.position.set(50, 50, 50);
        this.camera.lookAt(0, 0, 0);
    }

    createRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: true
        });

        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.0;
    }

    createControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.1;
        this.controls.screenSpacePanning = false;
        this.controls.maxPolarAngle = Math.PI / 2;
        this.controls.minDistance = 10;
        this.controls.maxDistance = 10000; // Increased max distance for infinite world
    }

    createLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        this.lights.push(ambientLight);

        // Main directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
        directionalLight.position.set(100, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 10000; // Increased shadow distance for infinite world
        directionalLight.shadow.camera.left = -1000;
        directionalLight.shadow.camera.right = 1000;
        directionalLight.shadow.camera.top = 1000;
        directionalLight.shadow.camera.bottom = -1000;
        this.scene.add(directionalLight);
        this.lights.push(directionalLight);

        // Fill light
        const fillLight = new THREE.DirectionalLight(0x4080ff, 0.3);
        fillLight.position.set(-50, 50, -50);
        this.scene.add(fillLight);
        this.lights.push(fillLight);
    }

    createEnvironment() {
        // Infinite grid - much larger size
        this.grid = new THREE.GridHelper(10000, 100, 0x444444, 0x222222);
        this.scene.add(this.grid);

        // Larger axes helper for infinite world
        this.axes = new THREE.AxesHelper(100);
        this.scene.add(this.axes);

        // Load HKIIT logo texture for the floor
        const textureLoader = new THREE.TextureLoader();
        textureLoader.load(
            './static/img/HKIIT_logo_RGB_vertical.jpg',
            (texture) => {
                // Configure texture settings for infinite world
                texture.wrapS = THREE.RepeatWrapping;
                texture.wrapT = THREE.RepeatWrapping;
                texture.repeat.set(200, 200); // Repeat the logo 200x200 times across the infinite floor
                texture.minFilter = THREE.LinearFilter;
                texture.magFilter = THREE.LinearFilter;

                // Create infinite ground plane with logo texture
                const groundGeometry = new THREE.PlaneGeometry(10000, 10000);
                const groundMaterial = new THREE.MeshLambertMaterial({
                    map: texture,
                    transparent: true,
                    opacity: 0.6,
                    side: THREE.DoubleSide
                });

                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                ground.name = 'logoFloor';
                this.scene.add(ground);

                console.log('HKIIT logo texture loaded and applied to floor');
            },
            (progress) => {
                console.log('Loading HKIIT logo texture:', (progress.loaded / progress.total * 100) + '%');
            },
            (error) => {
                console.error('Error loading HKIIT logo texture:', error);

                // Fallback: create a simple infinite colored ground plane
                const groundGeometry = new THREE.PlaneGeometry(10000, 10000);
                const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.3 });
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                ground.name = 'fallbackFloor';
                this.scene.add(ground);

                console.log('Fallback floor created due to texture loading error');
            }
        );
    }

    createDroneModel(droneId) {
        const group = new THREE.Group();
        group.name = `drone_${droneId}`;

        // Main body - upper half sphere (dome)
        const bodyGeometry = new THREE.SphereGeometry(2, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2);
        const bodyMaterial = new THREE.MeshLambertMaterial({
            color: 0x2196F3,
            side: THREE.DoubleSide
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);

        // Propellers
        const propellerPositions = [
            { x: 2.5, z: 2.5 },   // Front right
            { x: -2.5, z: 2.5 },  // Front left
            { x: 2.5, z: -2.5 },  // Back right
            { x: -2.5, z: -2.5 }  // Back left
        ];

        propellerPositions.forEach((pos, index) => {
            // Motor
            const motorGeometry = new THREE.CylinderGeometry(0.2, 0.2, 0.5);
            const motorMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
            const motor = new THREE.Mesh(motorGeometry, motorMaterial);
            motor.position.set(pos.x, 0.25, pos.z);
            motor.castShadow = true;
            group.add(motor);

            // Propeller blades
            const bladeGeometry = new THREE.BoxGeometry(3, 0.05, 0.2);
            const bladeMaterial = new THREE.MeshLambertMaterial({
                color: 0x666666,
                transparent: true,
                opacity: 0.7
            });
            const blade = new THREE.Mesh(bladeGeometry, bladeMaterial);
            blade.position.set(pos.x, 0.5, pos.z);
            blade.name = `propeller_${index}`;
            blade.castShadow = true;
            group.add(blade);
        });

        // Simple LED indicator on top
        const ledGeometry = new THREE.SphereGeometry(0.2, 8, 8);
        const ledMaterial = new THREE.MeshLambertMaterial({
            color: 0x00ff00,
            emissive: 0x004400
        });
        const led = new THREE.Mesh(ledGeometry, ledMaterial);
        led.position.set(0, 2, 0); // On top of the dome
        led.name = 'status_led';
        group.add(led);



        return group;
    }

    addDrone(droneId, initialPosition = { x: 0, y: 0, z: 0 }) {
        if (this.drones.has(droneId)) {
            console.warn(`Drone ${droneId} already exists`);
            return;
        }

        const droneModel = this.createDroneModel(droneId);
        droneModel.position.set(initialPosition.x, initialPosition.y, initialPosition.z);

        // Initialize userData for animation tracking
        droneModel.userData = {
            animationId: null,
            isStable: true,
            isFlipping: false
        };

        this.scene.add(droneModel);
        this.drones.set(droneId, droneModel);

        // Create and store drone label
        // Try to get drone name from simulator if available
        let droneName = droneId;
        if (window.app && window.app.droneSimulator) {
            const drone = window.app.droneSimulator.getDrone(droneId);
            if (drone && drone.name) {
                droneName = drone.name;
            }
        }

        const label = this.createDroneLabel(droneId, droneName);
        this.droneLabels.set(droneId, label);

        console.log(`Added drone ${droneId} to scene`);
    }

    removeDrone(droneId) {
        const drone = this.drones.get(droneId);
        if (drone) {
            this.scene.remove(drone);
            this.drones.delete(droneId);

            // Remove and dispose drone label
            const label = this.droneLabels.get(droneId);
            if (label) {
                label.parentNode.removeChild(label);
                this.droneLabels.delete(droneId);
                console.log(`Removed label for drone ${droneId}`);
            }

            console.log(`Removed drone ${droneId} from scene`);
        }
    }

    createDroneLabel(droneId, droneName) {
        // Create a label element
        const label = document.createElement('div');
        label.className = 'drone-label';
        label.textContent = droneName || droneId;

        // Append to the canvas container
        const canvasContainer = this.canvas.parentElement;
        canvasContainer.style.position = 'relative';
        canvasContainer.appendChild(label);

        return label;
    }

    updateDroneLabel(droneId) {
        const drone = this.drones.get(droneId);
        const label = this.droneLabels.get(droneId);

        if (!drone || !label) return;

        // Get drone position in world coordinates
        const dronePosition = new THREE.Vector3();
        drone.getWorldPosition(dronePosition);

        // Add offset above the drone
        dronePosition.y += 8; // Label appears above drone

        // Convert to screen coordinates
        const screenPosition = dronePosition.clone();
        screenPosition.project(this.camera);

        // Convert normalized device coordinates to screen coordinates
        const canvasRect = this.canvas.getBoundingClientRect();
        const x = (screenPosition.x * 0.5 + 0.5) * canvasRect.width;
        const y = (-screenPosition.y * 0.5 + 0.5) * canvasRect.height;

        // Update label position
        label.style.left = `${x - (label.offsetWidth / 2)}px`;
        label.style.top = `${y - label.offsetHeight}px`;

        // Hide label if drone is behind camera or too far away
        const isVisible = screenPosition.z < 1 && dronePosition.distanceTo(this.camera.position) < 1000;
        label.style.display = isVisible ? 'block' : 'none';
    }

    updateAllDroneLabels() {
        this.droneLabels.forEach((label, droneId) => {
            this.updateDroneLabel(droneId);
        });
    }

    updateDroneState(droneId, state) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        // Cancel any ongoing animations
        if (drone.userData && drone.userData.animationId) {
            cancelAnimationFrame(drone.userData.animationId);
            drone.userData.animationId = null;
        }

        // Check if this is a JavaScript simulator update vs server update
        const isJSUpdate = state._isJSUpdate === true;

        if (isJSUpdate) {
            // Handle position updates from JavaScript simulator
            // No range constraints - infinite world allows any position
            const targetPosition = {
                x: state.x !== undefined ? state.x : drone.position.x,
                y: state.h !== undefined ? state.h * 0.1 : drone.position.y, // Height scaling
                z: state.y !== undefined ? state.y : drone.position.z
            };

            // Animate to target position smoothly (no bounds checking)
            this.animateToPosition(drone, targetPosition);

            console.log(`JS Update: Moving drone ${droneId} to position:`, targetPosition);
        }

        // Handle one-time flip animation trigger
        if (state._flipTrigger && !drone.userData.isFlipping) {
            const flipData = state._flipTrigger;
            const direction = flipData.direction;

            // Mark drone as currently flipping to prevent repeated triggers
            drone.userData.isFlipping = true;

            console.log(`🎬 Triggering 3D flip animation for direction: ${direction}`);
            console.log(`Drone current rotation:`, {
                x: THREE.MathUtils.radToDeg(drone.rotation.x),
                y: THREE.MathUtils.radToDeg(drone.rotation.y),
                z: THREE.MathUtils.radToDeg(drone.rotation.z)
            });

            switch (direction) {
                case 'f': // forward flip - pitch forward (around x-axis)
                    this.animateFlip(drone, 'x', 360, 'forward');
                    break;
                case 'b': // backward flip - pitch backward (around x-axis)
                    this.animateFlip(drone, 'x', -360, 'backward');
                    break;
                case 'l': // left flip - roll left (around z-axis)
                    this.animateFlip(drone, 'z', 360, 'left');
                    break;
                case 'r': // right flip - roll right (around z-axis)
                    this.animateFlip(drone, 'z', -360, 'right');
                    break;
            }
        } else if (state._flipTrigger && drone.userData.isFlipping) {
            console.log(`⚠️ Flip trigger ignored - drone already flipping`);
        } else {
            // Normal rotation animations (from both server and JS)
            if (state.yaw !== undefined) {
                this.animateToRotation(drone, 'y', THREE.MathUtils.degToRad(state.yaw));
            }
            if (state.pitch !== undefined) {
                this.animateToRotation(drone, 'x', THREE.MathUtils.degToRad(state.pitch));
            }
            if (state.roll !== undefined) {
                this.animateToRotation(drone, 'z', THREE.MathUtils.degToRad(state.roll));
            }
        }

        // Update LED color based on battery
        const battery = state.bat || 100;
        const statusLed = drone.children.find(child => child.name === 'status_led');

        if (statusLed) {
            if (battery > 50) {
                statusLed.material.color.setHex(0x00ff00); // Green
                statusLed.material.emissive.setHex(0x004400);
            } else if (battery > 20) {
                statusLed.material.color.setHex(0xffff00); // Yellow
                statusLed.material.emissive.setHex(0x444400);
            } else {
                statusLed.material.color.setHex(0xff0000); // Red
                statusLed.material.emissive.setHex(0x440000);
            }
        }

        // Animate propellers based on height (flying state)
        this.animatePropellers(drone, state.h > 0);
    }

    animatePropellers(drone, isFlying) {
        drone.children.forEach(child => {
            if (child.name && child.name.startsWith('propeller_')) {
                if (isFlying) {
                    child.rotation.y += 0.5; // Fast rotation when flying
                    child.material.opacity = 0.3; // More transparent when spinning fast
                } else {
                    child.rotation.y += 0.02; // Very slow rotation when idle
                    child.material.opacity = 0.7; // More visible when not spinning fast
                }
            }
        });
    }

    animateToPosition(drone, targetPosition) {
        const startPosition = {
            x: drone.position.x,
            y: drone.position.y,
            z: drone.position.z
        };

        // Check if we need to animate (if position changed significantly)
        const threshold = 0.01;
        const needsAnimation =
            Math.abs(targetPosition.x - startPosition.x) > threshold ||
            Math.abs(targetPosition.y - startPosition.y) > threshold ||
            Math.abs(targetPosition.z - startPosition.z) > threshold;

        if (!needsAnimation) {
            // Set position directly if change is minimal
            drone.position.set(targetPosition.x, targetPosition.y, targetPosition.z);
            return;
        }

        // Smooth animation to target position
        let progress = 0;
        const duration = 0.8; // Animation duration in seconds
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = (currentTime - startTime) / 1000; // Convert to seconds
            progress = Math.min(elapsed / duration, 1);

            // Use easing function for smooth animation
            const easeProgress = this.easeInOutCubic(progress);

            // Interpolate position
            drone.position.x = THREE.MathUtils.lerp(startPosition.x, targetPosition.x, easeProgress);
            drone.position.y = THREE.MathUtils.lerp(startPosition.y, targetPosition.y, easeProgress);
            drone.position.z = THREE.MathUtils.lerp(startPosition.z, targetPosition.z, easeProgress);

            if (progress < 1) {
                drone.userData.animationId = requestAnimationFrame(animate);
            } else {
                // Ensure final position is exact
                drone.position.set(targetPosition.x, targetPosition.y, targetPosition.z);
                drone.userData.animationId = null;
            }
        };

        drone.userData.animationId = requestAnimationFrame(animate);
    }

    animateToRotation(drone, axis, targetRotation) {
        const currentRotation = drone.rotation[axis];

        // Check if we need to animate
        const threshold = 0.01;
        if (Math.abs(targetRotation - currentRotation) < threshold) {
            drone.rotation[axis] = targetRotation;
            return;
        }

        // Smooth rotation animation
        let progress = 0;
        const duration = 0.5; // Faster rotation animation
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = (currentTime - startTime) / 1000;
            progress = Math.min(elapsed / duration, 1);

            const easeProgress = this.easeInOutCubic(progress);
            drone.rotation[axis] = THREE.MathUtils.lerp(currentRotation, targetRotation, easeProgress);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                drone.rotation[axis] = targetRotation;
            }
        };

        requestAnimationFrame(animate);
    }

    animateFlip(drone, axis, totalRotation, direction) {
        // Store the current rotation as the original position
        const originalRotation = {
            x: drone.rotation.x,
            y: drone.rotation.y,
            z: drone.rotation.z
        };

        const startRotation = drone.rotation[axis];
        const targetRotation = startRotation + THREE.MathUtils.degToRad(totalRotation);

        console.log(`🎬 Starting flip animation: ${direction}, axis: ${axis}, rotation: ${totalRotation}°`);
        console.log(`Original rotation:`, {
            x: THREE.MathUtils.radToDeg(originalRotation.x),
            y: THREE.MathUtils.radToDeg(originalRotation.y),
            z: THREE.MathUtils.radToDeg(originalRotation.z)
        });

        const duration = 2.0; // Slower 2 second flip for complete visibility
        let progress = 0;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = (currentTime - startTime) / 1000;
            progress = Math.min(elapsed / duration, 1);

            // Use LINEAR progression for consistent rotation speed (no easing)
            // This ensures we see the full 360-degree rotation clearly
            const currentRotation = startRotation + (THREE.MathUtils.degToRad(totalRotation) * progress);
            drone.rotation[axis] = currentRotation;

            // Add some visual effects during flip
            if (progress > 0.1 && progress < 0.9) {
                // Add slight position bobbing during flip
                const bobAmount = Math.sin(progress * Math.PI * 4) * 0.2;
                drone.position.y += bobAmount * 0.03;
            }

            // Debug logging every 10% progress to see the full rotation
            if (Math.floor(progress * 10) !== Math.floor((progress - 0.1) * 10)) {
                console.log(`Flip progress: ${Math.floor(progress * 100)}%, ${axis} rotation: ${THREE.MathUtils.radToDeg(currentRotation)}°`);
            }

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Return ALL rotations to horizontal position (0,0,0)
                drone.rotation.x = 0;
                drone.rotation.y = 0;
                drone.rotation.z = 0;

                drone.userData.isFlipping = false; // Reset flipping flag
                console.log(`✅ 3D flip animation completed for direction: ${direction}`);
                console.log(`Total rotation completed: ${totalRotation}°, final rotation reset to horizontal: (0°, 0°, 0°)`);
            }
        };

        requestAnimationFrame(animate);
    }

    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }



    animateCommand(droneId, command) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        // Visual feedback for commands - but don't interfere with position updates
        if (command === 'takeoff') {
            // Just visual effect, no position changes
            this.showTakeoffEffect(drone);
        } else if (command === 'land') {
            // Just visual effect, no position changes
            this.showLandingEffect(drone);
        } else if (command.includes('flip')) {
            this.animateFlip(drone);
        }
    }

    showTakeoffEffect(drone) {
        // Brief visual effect without changing position
        const originalScale = drone.scale.clone();
        drone.scale.multiplyScalar(1.1);

        setTimeout(() => {
            drone.scale.copy(originalScale);
        }, 200);
    }

    showLandingEffect(drone) {
        // Brief visual effect without changing position
        const originalScale = drone.scale.clone();
        drone.scale.multiplyScalar(0.9);

        setTimeout(() => {
            drone.scale.copy(originalScale);
        }, 200);
    }

    animateFlip(drone) {
        // Quick rotation animation
        const startRotation = drone.rotation.x;
        const targetRotation = startRotation + Math.PI * 2;
        let progress = 0;

        const animate = () => {
            progress += 0.1;
            drone.rotation.x = THREE.MathUtils.lerp(startRotation, targetRotation,
                Math.min(progress, 1));

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                drone.rotation.x = startRotation; // Reset to original
            }
        };
        animate();
    }

    toggleGrid() {
        this.showGrid = !this.showGrid;
        this.grid.visible = this.showGrid;
    }

    toggleAxes() {
        this.showAxes = !this.showAxes;
        this.axes.visible = this.showAxes;
    }

    resetCamera() {
        this.camera.position.set(50, 50, 50);
        this.camera.lookAt(0, 0, 0);
        this.controls.reset();
    }

    resetDronePosition(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone) {
            console.warn(`Drone ${droneId} not found for reset`);
            return;
        }

        // Cancel any ongoing animations
        if (drone.userData && drone.userData.animationId) {
            cancelAnimationFrame(drone.userData.animationId);
            drone.userData.animationId = null;
        }

        // Animate drone back to origin position
        this.animateToPosition(drone, { x: 0, y: 0, z: 0 });

        // Reset rotation smoothly
        this.animateToRotation(drone, 'x', 0);
        this.animateToRotation(drone, 'y', 0);
        this.animateToRotation(drone, 'z', 0);

        // Reset LED to green
        const statusLed = drone.children.find(child => child.name === 'status_led');
        if (statusLed) {
            statusLed.material.color.setHex(0x00ff00);
            statusLed.material.emissive.setHex(0x004400);
        }

        console.log(`Reset drone ${droneId} to origin position with smooth animation`);
    }

    resetDroneToOrigin(droneId) {
        const drone = this.drones.get(droneId);
        if (!drone) {
            console.warn(`Drone ${droneId} not found for reset`);
            return;
        }

        console.log(`🔄 RESET: ${droneId} - resetting to origin`);

        // Cancel any animations
        if (drone.userData && drone.userData.animationId) {
            cancelAnimationFrame(drone.userData.animationId);
            drone.userData.animationId = null;
        }

        // Reset position and rotation to zero immediately
        drone.position.set(0, 0, 0);
        drone.rotation.set(0, 0, 0);

        // Reset LED to green
        const statusLed = drone.children.find(child => child.name === 'status_led');
        if (statusLed) {
            statusLed.material.color.setHex(0x00ff00);
            statusLed.material.emissive.setHex(0x004400);
        }

        // Stop propellers
        this.animatePropellers(drone, false);

        // Clear all user data
        drone.userData = {};

        console.log(`✅ RESET COMPLETE: ${droneId} at origin (0,0,0)`);
    }

    startRenderLoop() {
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);

            this.controls.update();
            this.updateAllDroneLabels(); // Update label positions
            this.renderer.render(this.scene, this.camera);
        };

        animate();
    }

    stopRenderLoop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(width, height);
    }

    dispose() {
        this.stopRenderLoop();
        this.renderer.dispose();
        this.scene.clear();
    }
}

// Export for use in other scripts
window.ThreeScene = ThreeScene;
