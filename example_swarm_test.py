#!/usr/bin/env python3
"""
Simple example script to test the mock drone with your existing swarm code

This script shows how to adapt your existing main.py to work with mock drones.
"""

import time
import subprocess
import sys
from threading import Thread

def start_mock_drones():
    """Start multiple mock drones for swarm testing"""
    print("Starting mock drones...")

    # Start two mock drones on different IPs
    proc1 = subprocess.Popen([
        sys.executable, "mock_tello_drone.py",
        "--ip", "192.168.137.21",
        "--name", "MockDrone1"
    ])

    proc2 = subprocess.Popen([
        sys.executable, "mock_tello_drone.py",
        "--ip", "192.168.137.22",
        "--name", "MockDrone2"
    ])

    return [proc1, proc2]

def run_swarm_test():
    """Run the swarm test with mock drones"""
    print("Waiting for drones to start...")
    time.sleep(3)

    try:
        from djitellopy import TelloSwarm

        # Use the same IPs as your main.py, but now they're mock drones
        swarm = TelloSwarm.fromIps([
            "192.168.137.21",
            "192.168.137.22"  # Changed second IP since you had duplicate
        ])

        print("Connecting to swarm...")
        swarm.connect()

        print("Taking off...")
        swarm.takeoff()

        # run in parallel on all tellos
        print("Moving up 100cm...")
        swarm.move_up(100)

        # run by one tello after the other
        print("Sequential forward movement...")
        swarm.sequential(lambda i, tello: tello.move_forward(i * 20 + 20))

        # making each tello do something unique in parallel
        print("Parallel left movement...")
        swarm.parallel(lambda i, tello: tello.move_left(i * 100 + 20))

        print("Landing...")
        swarm.land()
        swarm.end()

        print("✅ Swarm test completed successfully!")

    except Exception as e:
        print(f"❌ Swarm test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🚁 Mock Drone Swarm Test")
    print("=" * 40)

    # Start mock drones
    mock_procs = start_mock_drones()

    try:
        # Run swarm test
        run_swarm_test()

    finally:
        # Clean up mock drones
        print("\nStopping mock drones...")
        for proc in mock_procs:
            proc.terminate()
            proc.wait()
        print("✨ Test completed!")

if __name__ == "__main__":
    main()
