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
        this.scene.fog = new THREE.Fog(0x0a0a0a, 100, 1000);
    }

    createCamera() {
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 2000);
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
        this.controls.maxDistance = 500;
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
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);
        this.lights.push(directionalLight);

        // Fill light
        const fillLight = new THREE.DirectionalLight(0x4080ff, 0.3);
        fillLight.position.set(-50, 50, -50);
        this.scene.add(fillLight);
        this.lights.push(fillLight);
    }

    createEnvironment() {
        // Grid
        this.grid = new THREE.GridHelper(200, 20, 0x444444, 0x222222);
        this.scene.add(this.grid);

        // Axes helper
        this.axes = new THREE.AxesHelper(20);
        this.scene.add(this.axes);

        // Ground plane (invisible, for shadows)
        const groundGeometry = new THREE.PlaneGeometry(500, 500);
        const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.3 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }

    createDroneModel(droneId) {
        const group = new THREE.Group();
        group.name = `drone_${droneId}`;

        // Main body (sphere)
        const bodyGeometry = new THREE.SphereGeometry(2, 16, 12);
        const bodyMaterial = new THREE.MeshLambertMaterial({
            color: 0x2196f3,
            transparent: true,
            opacity: 0.9
        });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);

        // Propellers
        const propellerPositions = [
            { x: 3, z: 3 },   // Front right
            { x: -3, z: 3 },  // Front left
            { x: 3, z: -3 },  // Back right
            { x: -3, z: -3 }  // Back left
        ];

        propellerPositions.forEach((pos, index) => {
            // Motor
            const motorGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1);
            const motorMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
            const motor = new THREE.Mesh(motorGeometry, motorMaterial);
            motor.position.set(pos.x, 0.5, pos.z);
            motor.castShadow = true;
            group.add(motor);

            // Propeller blades
            const bladeGeometry = new THREE.BoxGeometry(4, 0.1, 0.3);
            const bladeMaterial = new THREE.MeshLambertMaterial({
                color: 0x666666,
                transparent: true,
                opacity: 0.7
            });
            const blade = new THREE.Mesh(bladeGeometry, bladeMaterial);
            blade.position.set(pos.x, 1, pos.z);
            blade.name = `propeller_${index}`;
            group.add(blade);
        });

        // LED indicators
        const ledGeometry = new THREE.SphereGeometry(0.2, 8, 6);
        const frontLedMaterial = new THREE.MeshLambertMaterial({
            color: 0x00ff00,
            emissive: 0x004400
        });
        const backLedMaterial = new THREE.MeshLambertMaterial({
            color: 0xff0000,
            emissive: 0x440000
        });

        const frontLed = new THREE.Mesh(ledGeometry, frontLedMaterial);
        frontLed.position.set(0, 0, 2.5);
        group.add(frontLed);

        const backLed = new THREE.Mesh(ledGeometry, backLedMaterial);
        backLed.position.set(0, 0, -2.5);
        group.add(backLed);

        // Trail (for movement visualization)
        const trailGeometry = new THREE.BufferGeometry();
        const trailMaterial = new THREE.LineBasicMaterial({
            color: 0x4fc3f7,
            transparent: true,
            opacity: 0.6
        });
        const trail = new THREE.Line(trailGeometry, trailMaterial);
        trail.name = 'trail';
        trail.userData = { positions: [] };
        group.add(trail);

        return group;
    }

    addDrone(droneId, initialPosition = { x: 0, y: 0, z: 0 }) {
        if (this.drones.has(droneId)) {
            console.warn(`Drone ${droneId} already exists`);
            return;
        }

        const droneModel = this.createDroneModel(droneId);
        droneModel.position.set(initialPosition.x, initialPosition.y, initialPosition.z);

        this.scene.add(droneModel);
        this.drones.set(droneId, droneModel);

        console.log(`Added drone ${droneId} to scene`);
    }

    removeDrone(droneId) {
        const drone = this.drones.get(droneId);
        if (drone) {
            this.scene.remove(drone);
            this.drones.delete(droneId);
            console.log(`Removed drone ${droneId} from scene`);
        }
    }

    updateDroneState(droneId, state) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        // Update position (convert from cm to meters for better scale)
        const scale = 0.1; // 1cm = 0.1 units in 3D space
        drone.position.y = (state.h || 0) * scale;

        // Update rotation
        if (state.yaw !== undefined) {
            drone.rotation.y = THREE.MathUtils.degToRad(state.yaw);
        }
        if (state.pitch !== undefined) {
            drone.rotation.x = THREE.MathUtils.degToRad(state.pitch);
        }
        if (state.roll !== undefined) {
            drone.rotation.z = THREE.MathUtils.degToRad(state.roll);
        }

        // Update LED colors based on battery
        const battery = state.bat || 100;
        const frontLed = drone.children.find(child =>
            child.position.z > 0 && child.geometry instanceof THREE.SphereGeometry
        );
        const backLed = drone.children.find(child =>
            child.position.z < 0 && child.geometry instanceof THREE.SphereGeometry
        );

        if (frontLed) {
            if (battery > 50) {
                frontLed.material.color.setHex(0x00ff00);
                frontLed.material.emissive.setHex(0x004400);
            } else if (battery > 20) {
                frontLed.material.color.setHex(0xffff00);
                frontLed.material.emissive.setHex(0x444400);
            } else {
                frontLed.material.color.setHex(0xff0000);
                frontLed.material.emissive.setHex(0x440000);
            }
        }

        // Animate propellers if flying
        this.animatePropellers(drone, state.h > 0);

        // Update trail
        this.updateTrail(drone);
    }

    animatePropellers(drone, isFlying) {
        drone.children.forEach(child => {
            if (child.name && child.name.startsWith('propeller_')) {
                if (isFlying) {
                    child.rotation.y += 0.5; // Fast rotation when flying
                    child.material.opacity = 0.3; // More transparent when spinning fast
                } else {
                    child.rotation.y += 0.01; // Slow rotation when idle
                    child.material.opacity = 0.7; // More visible when not spinning
                }
            }
        });
    }

    updateTrail(drone) {
        const trail = drone.children.find(child => child.name === 'trail');
        if (!trail) return;

        const positions = trail.userData.positions;
        const currentPos = drone.position.clone();

        // Add current position to trail
        positions.push(currentPos.x, currentPos.y, currentPos.z);

        // Limit trail length
        const maxTrailPoints = 50;
        if (positions.length > maxTrailPoints * 3) {
            positions.splice(0, 3); // Remove oldest point
        }

        // Update trail geometry
        if (positions.length >= 6) { // At least 2 points
            trail.geometry.setAttribute('position',
                new THREE.Float32BufferAttribute(positions, 3));
            trail.visible = true;
        } else {
            trail.visible = false;
        }
    }

    animateCommand(droneId, command) {
        const drone = this.drones.get(droneId);
        if (!drone) return;

        // Visual feedback for commands
        if (command === 'takeoff') {
            this.animateTakeoff(drone);
        } else if (command === 'land') {
            this.animateLanding(drone);
        } else if (command.includes('flip')) {
            this.animateFlip(drone);
        }
    }

    animateTakeoff(drone) {
        // Quick upward animation
        const startY = drone.position.y;
        const targetY = startY + 5;

        const animate = () => {
            drone.position.y = THREE.MathUtils.lerp(drone.position.y, targetY, 0.1);
            if (Math.abs(drone.position.y - targetY) > 0.1) {
                requestAnimationFrame(animate);
            }
        };
        animate();
    }

    animateLanding(drone) {
        // Smooth downward animation
        const animate = () => {
            drone.position.y = THREE.MathUtils.lerp(drone.position.y, 0, 0.05);
            if (drone.position.y > 0.1) {
                requestAnimationFrame(animate);
            } else {
                drone.position.y = 0;
            }
        };
        animate();
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

    startRenderLoop() {
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);

            this.controls.update();
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
