"""
Example: Drone Controller Integration with 3D Simulator

This example shows how to integrate the 3D simulator with your existing
drone controller code for visualization and testing without physical drones.
"""

import asyncio
import logging
from pathlib import Path

# Import your existing drone controller modules
try:
    from drone_controller.core.tello_drone import TelloDrone
    from drone_controller.multi_robot.swarm_controller import SwarmController
    from drone_controller.multi_robot.formation_manager import FormationManager
    from drone_controller.utils.logging_utils import setup_drone_logging
except ImportError:
    print("Drone controller modules not found. This is just an example.")
    TelloDrone = SwarmController = FormationManager = None

# Import simulator bridge
try:
    from simulator.simulator_bridge import DroneSimulatorBridge
except ImportError:
    print("Simulator bridge not found. Please ensure simulator files are present.")
    DroneSimulatorBridge = None


class SimulatedDroneController:
    """
    Example integration of drone controller with 3D simulator.

    This class demonstrates how to use the simulator as a visualization
    and testing tool alongside your real drone operations.
    """

    def __init__(self, use_simulator=True):
        self.use_simulator = use_simulator
        self.simulator_bridge = None
        self.real_drones = {}
        self.logger = setup_drone_logging("INFO", True, "logs") if setup_drone_logging else None

    async def start_simulator(self):
        """Start the 3D simulator bridge."""
        if not self.use_simulator or not DroneSimulatorBridge:
            return False

        try:
            self.simulator_bridge = DroneSimulatorBridge()
            await self.simulator_bridge.start()
            self.log("3D Simulator started successfully")
            return True
        except Exception as e:
            self.log(f"Failed to start simulator: {e}", "error")
            return False

    def log(self, message, level="info"):
        """Log message to both console and simulator."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")

        # Send to simulator
        if self.simulator_bridge:
            self.simulator_bridge.log_to_simulator(message, level)

    async def add_drone(self, drone_id, ip_address=None):
        """Add a drone to both real controller and simulator."""

        # Add to simulator first for visualization
        if self.simulator_bridge:
            self.simulator_bridge.add_drone(drone_id, ip_address)
            self.log(f"Added {drone_id} to simulator")

        # Try to create real drone connection
        if TelloDrone:
            try:
                real_drone = TelloDrone(drone_id, ip_address)
                self.real_drones[drone_id] = real_drone
                self.log(f"Real drone {drone_id} initialized")
                return True
            except Exception as e:
                self.log(f"Failed to initialize real drone {drone_id}: {e}", "warning")
                self.log("Continuing with simulator-only mode")

        return True

    async def connect_drone(self, drone_id):
        """Connect to drone (real or simulated)."""

        # Try real drone first
        real_drone = self.real_drones.get(drone_id)
        if real_drone:
            try:
                if real_drone.connect():
                    self.log(f"Connected to real drone {drone_id}")
                    # Mirror state to simulator
                    if self.simulator_bridge:
                        self.simulator_bridge.connect_drone(drone_id)
                    return True
            except Exception as e:
                self.log(f"Real drone connection failed: {e}", "warning")

        # Fallback to simulator
        if self.simulator_bridge:
            if self.simulator_bridge.connect_drone(drone_id):
                self.log(f"Connected to simulated drone {drone_id}")
                return True

        return False

    async def takeoff_drone(self, drone_id):
        """Takeoff drone (real or simulated)."""

        # Try real drone first
        real_drone = self.real_drones.get(drone_id)
        if real_drone and real_drone.connected:
            try:
                real_drone.takeoff()
                self.log(f"Real drone {drone_id} taking off")
                # Mirror to simulator
                if self.simulator_bridge:
                    self.simulator_bridge.takeoff_drone(drone_id)
                return True
            except Exception as e:
                self.log(f"Real drone takeoff failed: {e}", "error")
                return False

        # Fallback to simulator
        if self.simulator_bridge:
            if self.simulator_bridge.takeoff_drone(drone_id):
                self.log(f"Simulated drone {drone_id} taking off")
                return True

        return False

    async def move_drone(self, drone_id, x, y, z):
        """Move drone (real or simulated)."""

        # Try real drone first
        real_drone = self.real_drones.get(drone_id)
        if real_drone and hasattr(real_drone, 'move'):
            try:
                real_drone.move(x, y, z)
                self.log(f"Real drone {drone_id} moving by ({x}, {y}, {z})")
                # Mirror to simulator
                if self.simulator_bridge:
                    self.simulator_bridge.move_drone(drone_id, x, y, z)
                return True
            except Exception as e:
                self.log(f"Real drone movement failed: {e}", "error")
                return False

        # Fallback to simulator
        if self.simulator_bridge:
            if self.simulator_bridge.move_drone(drone_id, x, y, z):
                self.log(f"Simulated drone {drone_id} moving by ({x}, {y}, {z})")
                return True

        return False

    async def land_drone(self, drone_id):
        """Land drone (real or simulated)."""

        # Try real drone first
        real_drone = self.real_drones.get(drone_id)
        if real_drone and hasattr(real_drone, 'land'):
            try:
                real_drone.land()
                self.log(f"Real drone {drone_id} landing")
                # Mirror to simulator
                if self.simulator_bridge:
                    self.simulator_bridge.land_drone(drone_id)
                return True
            except Exception as e:
                self.log(f"Real drone landing failed: {e}", "error")
                return False

        # Fallback to simulator
        if self.simulator_bridge:
            if self.simulator_bridge.land_drone(drone_id):
                self.log(f"Simulated drone {drone_id} landing")
                return True

        return False

    async def create_swarm_formation(self, drone_ids, formation_type="line"):
        """Create a swarm formation."""

        if self.simulator_bridge:
            # Create formation in simulator
            formation_params = {
                "line": {"spacing": 150},
                "circle": {"radius": 200},
                "diamond": {"size": 200},
                "v": {"spacing": 150, "angle": 45}
            }

            params = formation_params.get(formation_type, {})

            if self.simulator_bridge.create_formation(
                f"formation_{formation_type}",
                drone_ids,
                formation_type,
                params
            ):
                self.log(f"Created {formation_type} formation with {len(drone_ids)} drones")
                return True

        return False

    async def run_basic_demo(self):
        """Run a basic flight demonstration."""
        self.log("Starting basic flight demo...")

        # Add and connect drone
        await self.add_drone("demo_drone", "192.168.10.1")
        await self.connect_drone("demo_drone")
        await asyncio.sleep(1)

        # Takeoff
        await self.takeoff_drone("demo_drone")
        await asyncio.sleep(3)

        # Move around
        movements = [
            (100, 0, 0),    # Forward
            (0, 100, 0),    # Right
            (0, 0, 50),     # Up
            (-100, 0, 0),   # Back
            (0, -100, 0),   # Left
            (0, 0, -50),    # Down
        ]

        for x, y, z in movements:
            await self.move_drone("demo_drone", x, y, z)
            await asyncio.sleep(2)

        # Land
        await self.land_drone("demo_drone")
        await asyncio.sleep(2)

        self.log("Basic demo completed!")

    async def run_swarm_demo(self):
        """Run a swarm formation demonstration."""
        self.log("Starting swarm formation demo...")

        # Add multiple drones
        drone_ids = ["alpha", "beta", "gamma", "delta", "echo"]
        for drone_id in drone_ids:
            await self.add_drone(drone_id)
            await self.connect_drone(drone_id)
            await asyncio.sleep(0.5)

        # Takeoff all
        for drone_id in drone_ids:
            await self.takeoff_drone(drone_id)
        await asyncio.sleep(3)

        # Try different formations
        formations = ["line", "circle", "diamond", "v"]
        for formation in formations:
            self.log(f"Creating {formation} formation...")
            await self.create_swarm_formation(drone_ids, formation)
            await asyncio.sleep(4)

        # Land all
        for drone_id in drone_ids:
            await self.land_drone(drone_id)
        await asyncio.sleep(2)

        self.log("Swarm demo completed!")

    async def stop(self):
        """Stop the controller and simulator."""
        # Disconnect real drones
        for drone_id, drone in self.real_drones.items():
            try:
                if hasattr(drone, 'disconnect'):
                    drone.disconnect()
                self.log(f"Disconnected real drone {drone_id}")
            except Exception as e:
                self.log(f"Error disconnecting {drone_id}: {e}", "warning")

        # Stop simulator
        if self.simulator_bridge:
            await self.simulator_bridge.stop()
            self.log("Simulator stopped")


async def main():
    """Main example function."""
    print("🚁 Drone Controller + 3D Simulator Integration Example")
    print("=" * 60)

    # Create controller with simulator
    controller = SimulatedDroneController(use_simulator=True)

    try:
        # Start simulator
        if await controller.start_simulator():
            print("✅ Simulator started successfully")
            print("🌐 Check your browser for the 3D visualization")
        else:
            print("⚠️  Simulator not available, continuing with basic mode")

        print("\nChoose a demo:")
        print("1. Basic flight demo (single drone)")
        print("2. Swarm formation demo (multiple drones)")
        print("3. Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            await controller.run_basic_demo()
        elif choice == "2":
            await controller.run_swarm_demo()
        elif choice == "3":
            print("Exiting...")
        else:
            print("Invalid choice")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
    finally:
        await controller.stop()
        print("Demo finished")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
