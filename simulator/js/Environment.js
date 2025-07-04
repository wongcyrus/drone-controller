/**
 * Environment.js - 3D Environment and Scene Setup
 */

class Environment {
    constructor(scene) {
        this.scene = scene;
        this.setupLighting();
        this.createGround();
        this.createSkybox();
        this.createLandmarks();
    }

    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);

        // Main directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -200;
        directionalLight.shadow.camera.right = 200;
        directionalLight.shadow.camera.top = 200;
        directionalLight.shadow.camera.bottom = -200;
        this.scene.add(directionalLight);

        // Secondary fill light
        const fillLight = new THREE.DirectionalLight(0x4169e1, 0.3);
        fillLight.position.set(-50, 50, -50);
        this.scene.add(fillLight);
    }

    createGround() {
        // Main ground plane
        const groundGeometry = new THREE.PlaneGeometry(500, 500);
        const groundMaterial = new THREE.MeshLambertMaterial({
            color: 0x3a8a3a,
            transparent: true,
            opacity: 0.8
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Grid helper
        const gridHelper = new THREE.GridHelper(500, 50, 0x888888, 0x444444);
        gridHelper.material.transparent = true;
        gridHelper.material.opacity = 0.3;
        this.scene.add(gridHelper);

        // Landing pad
        const padGeometry = new THREE.CircleGeometry(10, 32);
        const padMaterial = new THREE.MeshPhongMaterial({
            color: 0xffff00,
            transparent: true,
            opacity: 0.8
        });
        const landingPad = new THREE.Mesh(padGeometry, padMaterial);
        landingPad.rotation.x = -Math.PI / 2;
        landingPad.position.y = 0.1;
        this.scene.add(landingPad);

        // Landing pad markings
        const markingGeometry = new THREE.RingGeometry(8, 9, 8);
        const markingMaterial = new THREE.MeshBasicMaterial({
            color: 0x000000,
            side: THREE.DoubleSide
        });
        const marking = new THREE.Mesh(markingGeometry, markingMaterial);
        marking.rotation.x = -Math.PI / 2;
        marking.position.y = 0.2;
        this.scene.add(marking);
    }

    createSkybox() {
        // Simple gradient skybox
        const skyGeometry = new THREE.SphereGeometry(400, 32, 32);
        const skyMaterial = new THREE.ShaderMaterial({
            uniforms: {
                topColor: { value: new THREE.Color(0x87CEEB) },
                bottomColor: { value: new THREE.Color(0x98D8E8) },
                offset: { value: 33 },
                exponent: { value: 0.6 }
            },
            vertexShader: `
                varying vec3 vWorldPosition;
                void main() {
                    vec4 worldPosition = modelMatrix * vec4(position, 1.0);
                    vWorldPosition = worldPosition.xyz;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 topColor;
                uniform vec3 bottomColor;
                uniform float offset;
                uniform float exponent;
                varying vec3 vWorldPosition;
                void main() {
                    float h = normalize(vWorldPosition + offset).y;
                    gl_FragColor = vec4(mix(bottomColor, topColor, max(pow(max(h, 0.0), exponent), 0.0)), 1.0);
                }
            `,
            side: THREE.BackSide
        });

        const sky = new THREE.Mesh(skyGeometry, skyMaterial);
        this.scene.add(sky);

        // Add some clouds
        this.createClouds();
    }

    createClouds() {
        const cloudGeometry = new THREE.SphereGeometry(5, 8, 8);
        const cloudMaterial = new THREE.MeshLambertMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.6
        });

        for (let i = 0; i < 20; i++) {
            const cloud = new THREE.Mesh(cloudGeometry, cloudMaterial);
            cloud.position.set(
                (Math.random() - 0.5) * 400,
                50 + Math.random() * 50,
                (Math.random() - 0.5) * 400
            );
            cloud.scale.set(
                1 + Math.random() * 2,
                0.5 + Math.random() * 0.5,
                1 + Math.random() * 2
            );
            this.scene.add(cloud);
        }
    }

    createLandmarks() {
        // Buildings for navigation reference
        const buildingGeometry = new THREE.BoxGeometry(10, 20, 10);
        const buildingMaterial = new THREE.MeshPhongMaterial({ color: 0x8B4513 });

        const buildingPositions = [
            { x: 50, z: 50 },
            { x: -60, z: 40 },
            { x: 30, z: -70 },
            { x: -40, z: -50 }
        ];

        buildingPositions.forEach(pos => {
            const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
            building.position.set(pos.x, 10, pos.z);
            building.castShadow = true;
            building.receiveShadow = true;
            this.scene.add(building);
        });

        // Trees
        const treeGeometry = new THREE.ConeGeometry(3, 12, 8);
        const treeMaterial = new THREE.MeshPhongMaterial({ color: 0x0F5132 });

        for (let i = 0; i < 30; i++) {
            const tree = new THREE.Mesh(treeGeometry, treeMaterial);
            tree.position.set(
                (Math.random() - 0.5) * 300,
                6,
                (Math.random() - 0.5) * 300
            );
            // Avoid placing trees too close to the center
            if (Math.abs(tree.position.x) < 30 && Math.abs(tree.position.z) < 30) {
                continue;
            }
            tree.castShadow = true;
            this.scene.add(tree);
        }

        // Flight boundaries (invisible collision boxes)
        this.createFlightBoundaries();
    }

    createFlightBoundaries() {
        // Create invisible boundary walls to prevent drones from flying too far
        const boundaryMaterial = new THREE.MeshBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 0,
            visible: false
        });

        const boundaryGeometry = new THREE.PlaneGeometry(500, 200);

        // North boundary
        const northBoundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
        northBoundary.position.set(0, 100, -250);
        northBoundary.userData = { type: 'boundary', direction: 'north' };
        this.scene.add(northBoundary);

        // South boundary
        const southBoundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
        southBoundary.position.set(0, 100, 250);
        southBoundary.rotation.y = Math.PI;
        southBoundary.userData = { type: 'boundary', direction: 'south' };
        this.scene.add(southBoundary);

        // East boundary
        const eastBoundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
        eastBoundary.position.set(250, 100, 0);
        eastBoundary.rotation.y = Math.PI / 2;
        eastBoundary.userData = { type: 'boundary', direction: 'east' };
        this.scene.add(eastBoundary);

        // West boundary
        const westBoundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
        westBoundary.position.set(-250, 100, 0);
        westBoundary.rotation.y = -Math.PI / 2;
        westBoundary.userData = { type: 'boundary', direction: 'west' };
        this.scene.add(westBoundary);

        // Ceiling
        const ceilingBoundary = new THREE.Mesh(
            new THREE.PlaneGeometry(500, 500),
            boundaryMaterial
        );
        ceilingBoundary.position.set(0, 150, 0);
        ceilingBoundary.rotation.x = Math.PI / 2;
        ceilingBoundary.userData = { type: 'boundary', direction: 'up' };
        this.scene.add(ceilingBoundary);
    }

    addWeatherEffect(type = 'clear') {
        // Remove existing weather effects
        this.clearWeatherEffects();

        switch (type) {
            case 'rain':
                this.addRain();
                break;
            case 'snow':
                this.addSnow();
                break;
            case 'fog':
                this.addFog();
                break;
            default:
                break;
        }
    }

    addRain() {
        const rainGeometry = new THREE.BufferGeometry();
        const rainCount = 15000;
        const positions = new Float32Array(rainCount * 3);

        for (let i = 0; i < rainCount * 3; i += 3) {
            positions[i] = (Math.random() - 0.5) * 1000;
            positions[i + 1] = Math.random() * 300;
            positions[i + 2] = (Math.random() - 0.5) * 1000;
        }

        rainGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const rainMaterial = new THREE.PointsMaterial({
            color: 0x87CEEB,
            size: 0.5,
            transparent: true,
            opacity: 0.6
        });

        this.rain = new THREE.Points(rainGeometry, rainMaterial);
        this.scene.add(this.rain);

        // Animate rain
        this.animateRain();
    }

    animateRain() {
        if (this.rain) {
            const positions = this.rain.geometry.attributes.position.array;

            for (let i = 1; i < positions.length; i += 3) {
                positions[i] -= 2; // Fall speed

                if (positions[i] < 0) {
                    positions[i] = 300; // Reset to top
                }
            }

            this.rain.geometry.attributes.position.needsUpdate = true;
        }
    }

    addFog() {
        this.scene.fog = new THREE.Fog(0xcccccc, 50, 300);
    }

    clearWeatherEffects() {
        if (this.rain) {
            this.scene.remove(this.rain);
            this.rain = null;
        }
        if (this.snow) {
            this.scene.remove(this.snow);
            this.snow = null;
        }
        this.scene.fog = null;
    }

    animate() {
        // Animate weather effects
        if (this.rain) {
            this.animateRain();
        }
    }
}
