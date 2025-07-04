/**
 * main.js - Application entry point and initialization
 */

class DroneSimulatorApp {
    constructor() {
        this.simulator = null;
        this.ui = null;
        this.isLoaded = false;

        this.init();
    }

    async init() {
        try {
            // Show loading screen
            this.showLoadingScreen();

            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.startApp());
            } else {
                this.startApp();
            }

        } catch (error) {
            console.error('Failed to initialize Drone Simulator:', error);
            this.showError('Failed to initialize application');
        }
    }

    startApp() {
        try {
            // Get canvas element
            const canvas = document.getElementById('canvas3d');
            if (!canvas) {
                throw new Error('Canvas element not found');
            }

            // Initialize simulator
            this.simulator = new DroneSimulator(canvas);

            // Initialize UI
            this.ui = new UI(this.simulator);

            // Hide loading screen
            this.hideLoadingScreen();

            // Show welcome message
            this.showWelcomeMessage();

            this.isLoaded = true;

            console.log('Drone Simulator initialized successfully');

        } catch (error) {
            console.error('Failed to start application:', error);
            this.showError('Failed to start application: ' + error.message);
        }
    }

    showLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
    }

    showError(message) {
        this.hideLoadingScreen();

        // Create error overlay
        const errorOverlay = document.createElement('div');
        errorOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;

        errorOverlay.innerHTML = `
            <h2 style="color: #ff4444; margin-bottom: 20px;">⚠️ Error</h2>
            <p style="text-align: center; margin-bottom: 20px;">${message}</p>
            <button onclick="location.reload()" style="
                padding: 10px 20px;
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            ">Reload Application</button>
        `;

        document.body.appendChild(errorOverlay);
    }

    showWelcomeMessage() {
        if (this.ui) {
            this.ui.log('🚁 Welcome to Drone Simulator 3D!', 'success');
            this.ui.log('Use the controls on the right to operate drones', 'info');
            this.ui.log('Press Space for takeoff/land, WASD for movement', 'info');
            this.ui.log('Click on a drone to select it for keyboard control', 'info');
        }
    }

    // Demo functions that can be called from Python
    runSingleDroneDemo() {
        if (!this.isLoaded) {
            console.warn('Simulator not loaded yet');
            return false;
        }

        try {
            // Switch to single mode
            this.ui.switchMode('single');

            // Connect and demo sequence
            setTimeout(() => {
                this.ui.connectSingleDrone();
                this.ui.log('Demo: Connecting to drone...', 'info');
            }, 1000);

            setTimeout(() => {
                this.ui.takeoffSingleDrone();
                this.ui.log('Demo: Taking off...', 'info');
            }, 2000);

            setTimeout(() => {
                this.ui.moveSingleDrone(100, 0, 0);
                this.ui.log('Demo: Moving forward...', 'info');
            }, 4000);

            setTimeout(() => {
                this.ui.rotateSingleDrone();
                this.ui.log('Demo: Rotating...', 'info');
            }, 6000);

            setTimeout(() => {
                this.ui.moveSingleDrone(0, 100, 0);
                this.ui.log('Demo: Moving right...', 'info');
            }, 8000);

            setTimeout(() => {
                this.ui.landSingleDrone();
                this.ui.log('Demo: Landing...', 'info');
            }, 10000);

            setTimeout(() => {
                this.ui.log('Demo completed!', 'success');
            }, 12000);

            return true;

        } catch (error) {
            console.error('Demo failed:', error);
            return false;
        }
    }

    runSwarmDemo() {
        if (!this.isLoaded) {
            console.warn('Simulator not loaded yet');
            return false;
        }

        try {
            // Switch to swarm mode
            this.ui.switchMode('swarm');

            // Add multiple drones
            const droneIds = ['alpha', 'beta', 'gamma', 'delta'];

            droneIds.forEach((id, index) => {
                setTimeout(() => {
                    document.getElementById('newDroneId').value = id;
                    this.ui.addDroneToSwarm();
                    this.ui.log(`Demo: Added drone ${id}`, 'info');
                }, index * 500);
            });

            // Initialize swarm
            setTimeout(() => {
                this.ui.initializeSwarm();
                this.ui.log('Demo: Initializing swarm...', 'info');
            }, 3000);

            // Takeoff
            setTimeout(() => {
                this.ui.takeoffSwarm();
                this.ui.log('Demo: Swarm takeoff...', 'info');
            }, 4000);

            // Create formations
            setTimeout(() => {
                document.getElementById('formationType').value = 'line';
                this.ui.createFormation();
                this.ui.log('Demo: Creating line formation...', 'info');
            }, 6000);

            setTimeout(() => {
                document.getElementById('formationType').value = 'circle';
                this.ui.createFormation();
                this.ui.log('Demo: Creating circle formation...', 'info');
            }, 9000);

            setTimeout(() => {
                document.getElementById('formationType').value = 'v';
                this.ui.createFormation();
                this.ui.log('Demo: Creating V formation...', 'info');
            }, 12000);

            // Move formation
            setTimeout(() => {
                document.getElementById('formationX').value = '50';
                document.getElementById('formationY').value = '50';
                this.ui.moveFormation();
                this.ui.log('Demo: Moving formation...', 'info');
            }, 15000);

            // Land
            setTimeout(() => {
                this.ui.landSwarm();
                this.ui.log('Demo: Landing swarm...', 'info');
            }, 18000);

            setTimeout(() => {
                this.ui.log('Swarm demo completed!', 'success');
            }, 20000);

            return true;

        } catch (error) {
            console.error('Swarm demo failed:', error);
            return false;
        }
    }

    // API for external control (Python integration)
    getSimulatorAPI() {
        if (!this.isLoaded) {
            console.warn('Simulator not loaded yet');
            return null;
        }

        return {
            // Single drone operations
            addDrone: (id, ip) => this.simulator.addDrone(id, ip),
            connectDrone: (id) => this.simulator.connectDrone(id),
            takeoffDrone: (id) => this.simulator.takeoffDrone(id),
            landDrone: (id) => this.simulator.landDrone(id),
            moveDrone: (id, x, y, z) => this.simulator.moveDrone(id, x, y, z),
            rotateDrone: (id, angle) => this.simulator.rotateDrone(id, angle),
            getDroneState: (id) => {
                const drone = this.simulator.getDrone(id);
                return drone ? drone.getState() : null;
            },

            // Swarm operations
            createSwarm: (id) => this.ui.swarmManager.createSwarm(id),
            addDroneToSwarm: (swarmId, droneId) => this.ui.swarmManager.addDroneToSwarm(swarmId, droneId),
            initializeSwarm: (id) => this.ui.swarmManager.initializeSwarm(id),
            takeoffSwarm: (id) => this.ui.swarmManager.takeoffSwarm(id),
            landSwarm: (id) => this.ui.swarmManager.landSwarm(id),

            // Formation operations
            createFormation: (id, droneIds, pattern, params) =>
                this.ui.formationManager.createFormation(id, droneIds, pattern, params),
            moveToFormation: (id, x, y, z) =>
                this.ui.formationManager.moveToFormation(id, x, y, z),
            moveFormation: (id, dx, dy, dz) =>
                this.ui.formationManager.moveFormation(id, dx, dy, dz),

            // Environment
            setWind: (x, y, z, strength) => this.simulator.setWind(x, y, z, strength),
            setWeather: (type) => this.simulator.setWeather(type),

            // Camera
            focusOnDrone: (id) => this.simulator.focusOnDrone(id),
            resetCamera: () => this.simulator.resetCamera(),

            // Utilities
            getStats: () => this.simulator.getStats(),
            log: (message, type) => this.ui.log(message, type)
        };
    }
}

// Global app instance
let droneSimulatorApp;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    droneSimulatorApp = new DroneSimulatorApp();

    // Make API available globally for Python integration
    window.droneSimulator = {
        getAPI: () => droneSimulatorApp.getSimulatorAPI(),
        runSingleDemo: () => droneSimulatorApp.runSingleDroneDemo(),
        runSwarmDemo: () => droneSimulatorApp.runSwarmDemo(),
        isLoaded: () => droneSimulatorApp.isLoaded
    };
});

// Handle window unload
window.addEventListener('beforeunload', () => {
    if (droneSimulatorApp && droneSimulatorApp.simulator) {
        droneSimulatorApp.simulator.stop();
    }
});

// Error handling
window.addEventListener('error', (event) => {
    console.error('Application error:', event.error);
    if (droneSimulatorApp) {
        droneSimulatorApp.showError('An unexpected error occurred: ' + event.error.message);
    }
});

// Handle uncaught promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    if (droneSimulatorApp) {
        droneSimulatorApp.showError('An unexpected error occurred: ' + event.reason);
    }
});

console.log('🚁 Drone Simulator 3D - Loading...');
