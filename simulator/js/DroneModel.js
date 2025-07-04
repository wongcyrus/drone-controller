/**
 * DroneModel.js - 3D Drone Model and Animation
 */

class DroneModel {
    constructor(id, scene, position = { x: 0, y: 0, z: 0 }) {
        this.id = id;
        this.scene = scene;
        this.group = new THREE.Group();
        this.position = position;
        this.rotation = { x: 0, y: 0, z: 0 };
        this.targetPosition = { ...position };
        this.targetRotation = { ...this.rotation };

        // Drone state
        this.isConnected = false;
        this.isFlying = false;
        this.battery = 100;
        this.speed = 0;
        this.altitude = 0;

        // Animation properties
        this.propellerRotation = 0;
        this.propellers = [];
        this.body = null;
        this.lights = [];

        this.createDroneModel();
        this.updatePosition();
        scene.add(this.group);
    }

    createDroneModel() {
        try {
            // Main body
            const bodyGeometry = new THREE.BoxGeometry(8, 2, 8);
            const bodyMaterial = new THREE.MeshPhongMaterial({
                color: this.isConnected ? 0x2196F3 : 0x666666,
                shininess: 100
            });
            this.body = new THREE.Mesh(bodyGeometry, bodyMaterial);
            this.group.add(this.body);

            // Arms
            const armGeometry = new THREE.CylinderGeometry(0.3, 0.3, 12);
            const armMaterial = new THREE.MeshPhongMaterial({ color: 0x333333 });

            // Create 4 arms
            const armPositions = [
                { x: 6, z: 6, rotation: Math.PI / 4 },
                { x: -6, z: 6, rotation: -Math.PI / 4 },
                { x: -6, z: -6, rotation: Math.PI / 4 },
                { x: 6, z: -6, rotation: -Math.PI / 4 }
            ];

            armPositions.forEach((pos, index) => {
                const arm = new THREE.Mesh(armGeometry, armMaterial);
                arm.position.set(pos.x, 0, pos.z);
                arm.rotation.y = pos.rotation;
                this.group.add(arm);

                // Propeller motor
                const motorGeometry = new THREE.CylinderGeometry(1, 1, 1);
                const motorMaterial = new THREE.MeshPhongMaterial({ color: 0x222222 });
                const motor = new THREE.Mesh(motorGeometry, motorMaterial);
                motor.position.set(pos.x * 1.4, 1, pos.z * 1.4);
                this.group.add(motor);

                // Propeller
                const propellerGroup = new THREE.Group();
                const bladeGeometry = new THREE.BoxGeometry(6, 0.1, 0.5);
                const bladeMaterial = new THREE.MeshPhongMaterial({
                    color: 0x444444,
                    transparent: true,
                    opacity: 0.8
                });

                // Two blades per propeller
                for (let i = 0; i < 2; i++) {
                    const blade = new THREE.Mesh(bladeGeometry, bladeMaterial);
                    blade.rotation.y = i * Math.PI;
                    propellerGroup.add(blade);
                }

                propellerGroup.position.set(pos.x * 1.4, 1.5, pos.z * 1.4);
                this.propellers.push(propellerGroup);
                this.group.add(propellerGroup);

                // LED lights
                const lightGeometry = new THREE.SphereGeometry(0.2);
                const lightMaterial = new THREE.MeshBasicMaterial({
                    color: this.isFlying ? 0x00ff00 : 0xff0000,
                    emissive: this.isFlying ? 0x003300 : 0x330000
                });
                const light = new THREE.Mesh(lightGeometry, lightMaterial);
                light.position.set(pos.x * 1.2, -0.5, pos.z * 1.2);
                this.lights.push(light);
                this.group.add(light);
            });

            // Camera gimbal (optional detail)
            const gimbalGeometry = new THREE.SphereGeometry(1);
            const gimbalMaterial = new THREE.MeshPhongMaterial({ color: 0x111111 });
            const gimbal = new THREE.Mesh(gimbalGeometry, gimbalMaterial);
            gimbal.position.set(0, -2, 0);
            this.group.add(gimbal);

            // Drone label
            this.createLabel();

        } catch (error) {
            console.error('Error creating drone model:', error);
            // Create a simple fallback model
            const fallbackGeometry = new THREE.BoxGeometry(8, 2, 8);
            const fallbackMaterial = new THREE.MeshBasicMaterial({ color: 0x666666 });
            this.body = new THREE.Mesh(fallbackGeometry, fallbackMaterial);
            this.group.add(this.body);
        }
    }

    createLabel() {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;

        context.fillStyle = 'rgba(0, 0, 0, 0.8)';
        context.fillRect(0, 0, canvas.width, canvas.height);

        context.fillStyle = '#ffffff';
        context.font = '24px Arial';
        context.textAlign = 'center';
        context.fillText(this.id, canvas.width / 2, 40);

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(material);
        sprite.position.set(0, 8, 0);
        sprite.scale.set(8, 2, 1);

        this.group.add(sprite);
    }

    updatePosition() {
        this.group.position.set(this.position.x, this.position.y, this.position.z);
        this.group.rotation.set(this.rotation.x, this.rotation.y, this.rotation.z);
        this.altitude = this.position.y;
    }

    animate() {
        // Smooth movement interpolation
        const lerpFactor = 0.05;

        this.position.x += (this.targetPosition.x - this.position.x) * lerpFactor;
        this.position.y += (this.targetPosition.y - this.position.y) * lerpFactor;
        this.position.z += (this.targetPosition.z - this.position.z) * lerpFactor;

        this.rotation.y += (this.targetRotation.y - this.rotation.y) * lerpFactor;

        this.updatePosition();

        // Propeller animation
        if (this.isFlying) {
            this.propellerRotation += 0.5;
            this.propellers.forEach(propeller => {
                propeller.rotation.y = this.propellerRotation;
            });

            // Add slight hovering motion
            const hoverOffset = Math.sin(Date.now() * 0.003) * 0.2;
            this.group.position.y += hoverOffset;
        }

        // Update LED colors based on state
        this.lights.forEach(light => {
            if (light && light.material && light.material.color) {
                if (this.isFlying) {
                    light.material.color.setHex(0x00ff00);
                    if (light.material.emissive) light.material.emissive.setHex(0x003300);
                } else if (this.isConnected) {
                    light.material.color.setHex(0x0000ff);
                    if (light.material.emissive) light.material.emissive.setHex(0x000033);
                } else {
                    light.material.color.setHex(0xff0000);
                    if (light.material.emissive) light.material.emissive.setHex(0x330000);
                }
            }
        });

        // Update body color
        if (this.body && this.body.material && this.body.material.color) {
            if (this.isFlying) {
                this.body.material.color.setHex(0x4CAF50);
            } else if (this.isConnected) {
                this.body.material.color.setHex(0x2196F3);
            } else {
                this.body.material.color.setHex(0x666666);
            }
        }
    }

    // Control methods
    connect() {
        this.isConnected = true;
        this.battery = 85 + Math.random() * 15; // Random battery level
        return true;
    }

    disconnect() {
        this.isConnected = false;
        this.isFlying = false;
        return true;
    }

    takeoff() {
        if (!this.isConnected) return false;
        this.isFlying = true;
        this.targetPosition.y = Math.max(this.targetPosition.y, 20);
        return true;
    }

    land() {
        if (!this.isConnected) return false;
        this.isFlying = false;
        this.targetPosition.y = 0;
        return true;
    }

    moveTo(x, y, z) {
        if (!this.isFlying) return false;
        this.targetPosition.x += x;
        this.targetPosition.y += z; // Z is up in our coordinate system
        this.targetPosition.z += y; // Y is forward

        // Clamp altitude
        this.targetPosition.y = Math.max(0, Math.min(100, this.targetPosition.y));

        return true;
    }

    rotateTo(angle) {
        if (!this.isConnected) return false;
        this.targetRotation.y += (angle * Math.PI) / 180;
        return true;
    }

    emergencyStop() {
        this.isFlying = false;
        this.targetPosition.y = 0;
        this.propellerRotation = 0;
    }

    getState() {
        return {
            id: this.id,
            connected: this.isConnected,
            flying: this.isFlying,
            battery: Math.floor(this.battery),
            position: { ...this.position },
            altitude: this.altitude.toFixed(1),
            speed: this.speed.toFixed(1)
        };
    }

    updateBattery() {
        if (this.isFlying && this.battery > 0) {
            this.battery -= 0.01; // Drain battery slowly
        }
    }

    remove() {
        this.scene.remove(this.group);
    }
}
