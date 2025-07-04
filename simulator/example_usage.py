#!/usr/bin/env python3
"""
Example usage of the UDP simulator with the drone controller.

This example demonstrates how to:
1. Start the UDP simulator programmatically
2. Connect to simulated drones
3. Perform basic operations

Run this from the main drone-controller directory.
"""

import time
import threading
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from simulator.udp_simulator import TelloSimulator
from drone_controller.core.tello_drone import TelloDrone


def simulator_thread():
    """Run the simulator in a separate thread."""
    simulator = TelloSimulator("192.168.10", 1)
    simulator.add_drone("test_drone", 1)

    try:
        simulator.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        simulator.stop()


def main():
    """Demonstrate simulator usage."""
    print("🚁 UDP Simulator Integration Example")
    print("=" * 40)

    # Start simulator in background thread
    print("1. Starting UDP simulator...")
    sim_thread = threading.Thread(target=simulator_thread, daemon=True)
    sim_thread.start()

    # Give simulator time to start
    time.sleep(2)

    # Connect to simulated drone
    print("2. Connecting to simulated drone...")
    drone = TelloDrone("test_drone", "192.168.10.1")

    try:
        if drone.connect():
            print("✅ Connected to simulated drone!")

            # Get initial status
            status = drone.get_state()
            print(f"📊 Battery: {status['battery']}%")

            # Perform basic flight operations
            print("3. Performing basic flight operations...")

            print("   Taking off...")
            drone.takeoff()
            time.sleep(3)

            print("   Moving forward...")
            drone.move(0, 50, 0)  # Forward 50cm
            time.sleep(2)

            print("   Rotating...")
            drone.rotate(90)  # Turn 90 degrees
            time.sleep(2)

            print("   Landing...")
            drone.land()
            time.sleep(3)

            print("✅ Flight operations completed!")

        else:
            print("❌ Failed to connect to simulated drone")

    except (ConnectionError, TimeoutError) as e:
        print(f"❌ Connection error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Flight interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    finally:
        drone.disconnect()
        print("👋 Disconnected from drone")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Example stopped by user")
