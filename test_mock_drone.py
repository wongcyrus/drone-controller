#!/usr/bin/env python3
"""
Test script for Mock Tello Drone

This script demonstrates how to use the mock drone and tests
basic functionality with the DJITelloPy library.
"""

import time
import subprocess
import sys
from threading import Thread

def start_mock_drone():
    """Start a mock drone in the background"""
    print("Starting mock drone...")
    # Start the mock drone as a subprocess
    proc = subprocess.Popen([
        sys.executable, "mock_tello_drone.py",
        "--ip", "127.0.0.1",
        "--name", "TestDrone"
    ])
    return proc

def test_single_drone():
    """Test basic drone commands with a single drone"""
    try:
        from djitellopy import Tello

        # Create Tello instance pointing to our mock drone
        tello = Tello("127.0.0.1")

        print("\n=== Testing Single Drone ===")

        # Connect to drone
        print("Connecting to drone...")
        tello.connect()
        print(f"Battery: {tello.get_battery()}%")

        # Test basic commands
        print("Taking off...")
        tello.takeoff()
        time.sleep(1)

        print("Moving up 50cm...")
        tello.move_up(50)
        time.sleep(1)

        print("Rotating 90 degrees...")
        tello.rotate_clockwise(90)
        time.sleep(1)

        print("Moving forward 30cm...")
        tello.move_forward(30)
        time.sleep(1)

        print("Landing...")
        tello.land()

        print("✓ Single drone test completed successfully!")

    except Exception as e:
        print(f"✗ Single drone test failed: {e}")

def test_swarm():
    """Test swarm functionality with multiple mock drones"""
    try:
        from djitellopy import TelloSwarm

        print("\n=== Testing Swarm (requires multiple mock drones) ===")
        print("Note: You need to start multiple mock drones manually for this test")

        # For swarm testing, you would need multiple drones
        # This is a placeholder showing how it would work
        swarm_ips = [
            "127.0.0.1",  # Would need different IPs for real swarm
            # "127.0.0.2",  # Start with: python mock_tello_drone.py --ip 127.0.0.2
        ]

        if len(swarm_ips) > 1:
            swarm = TelloSwarm.fromIps(swarm_ips)

            print("Connecting to swarm...")
            swarm.connect()

            print("Swarm takeoff...")
            swarm.takeoff()

            print("Swarm synchronized movement...")
            swarm.move_up(50)

            print("Swarm sequential movement...")
            swarm.sequential(lambda i, tello: tello.move_forward(20 + i * 10))

            print("Swarm landing...")
            swarm.land()
            swarm.end()

            print("✓ Swarm test completed successfully!")
        else:
            print("⚠ Swarm test skipped - need multiple IPs for proper swarm testing")

    except Exception as e:
        print(f"✗ Swarm test failed: {e}")

def main():
    """Main test function"""
    print("Mock Tello Drone Test Suite")
    print("=" * 40)

    # Start mock drone
    mock_proc = start_mock_drone()

    try:
        # Give the mock drone time to start
        time.sleep(2)

        # Run tests
        test_single_drone()
        test_swarm()

    finally:
        # Clean up
        print("\nStopping mock drone...")
        mock_proc.terminate()
        mock_proc.wait()
        print("Test suite completed!")

if __name__ == "__main__":
    main()
