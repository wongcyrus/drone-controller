#!/usr/bin/env python3
"""
Working example - demonstrates the mock drone with your swarm code

This version shows how to adapt your main.py to work with mock drones
running on localhost with different ports.
"""

import time
import subprocess
import threading
import sys
import os


def start_mock_drone(port, name):
    """Start a mock drone on a specific port"""
    # Import here to avoid import issues
    import socket
    import logging

    logger = logging.getLogger(f"MockDrone-{name}")

    class MockDrone:
        def __init__(self, port, name):
            self.port = port
            self.name = name
            self.socket = None
            self.running = False
            self.battery = 100
            self.height = 0
            self.is_flying = False
            self.sdk_mode = False

        def start(self):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind(('127.0.0.1', self.port))
                self.running = True

                logger.info(f"Mock drone {self.name} started on port {self.port}")

                while self.running:
                    try:
                        data, addr = self.socket.recvfrom(1024)
                        command = data.decode('utf-8').strip().lower()

                        logger.info(f"{self.name} received: '{command}' from {addr}")

                        response = self._process_command(command)

                        if response:
                            self.socket.sendto(response.encode('utf-8'), addr)
                            logger.info(f"{self.name} sent: '{response}' to {addr}")

                    except Exception as e:
                        if self.running:
                            logger.error(f"{self.name} error: {e}")

            except Exception as e:
                logger.error(f"Failed to start {self.name}: {e}")

        def _process_command(self, command):
            if command == 'command':
                self.sdk_mode = True
                return 'ok'
            elif command == 'takeoff' and self.sdk_mode:
                self.is_flying = True
                self.height = 50
                return 'ok'
            elif command == 'land' and self.sdk_mode:
                self.is_flying = False
                self.height = 0
                return 'ok'
            elif command.startswith('up ') and self.sdk_mode and self.is_flying:
                try:
                    distance = int(command.split()[1])
                    if 20 <= distance <= 500:
                        self.height += distance
                        return 'ok'
                except:
                    pass
                return 'error'
            elif command.startswith(('left ', 'right ', 'forward ', 'back ')):
                if self.sdk_mode and self.is_flying:
                    return 'ok'
                return 'error'
            elif command.startswith('cw ') and self.sdk_mode and self.is_flying:
                return 'ok'
            elif command == 'battery?':
                return str(self.battery)
            elif command == 'height?':
                return str(self.height)
            else:
                return 'error'

        def stop(self):
            self.running = False
            if self.socket:
                self.socket.close()

    # Create and run mock drone
    drone = MockDrone(port, name)
    drone.start()


def run_modified_swarm_test():
    """Run a modified version of your swarm test"""

    print("🚁 Starting Mock Drone Swarm Test")
    print("=" * 50)

    # Start mock drones in background threads
    drone1_thread = threading.Thread(
        target=start_mock_drone,
        args=(8889, "Drone1"),
        daemon=True
    )
    drone2_thread = threading.Thread(
        target=start_mock_drone,
        args=(8890, "Drone2"),
        daemon=True
    )

    drone1_thread.start()
    drone2_thread.start()

    # Give drones time to start
    time.sleep(2)

    # Now create a custom Tello class that uses different ports
    try:
        from djitellopy.tello import Tello

        class CustomTello(Tello):
            def __init__(self, host, port=8889):
                # Store original port
                self.custom_port = port
                # Initialize with host
                super().__init__(host)
                # Override the address to use custom port
                self.address = (host, port)

        # Create Tello instances with custom ports
        print("📡 Creating Tello instances...")
        tello1 = CustomTello("127.0.0.1", 8889)
        tello2 = CustomTello("127.0.0.1", 8890)

        drones = [tello1, tello2]

        # Connect to drones individually
        print("🔗 Connecting to drones...")
        for i, drone in enumerate(drones):
            print(f"   Connecting to drone {i+1}...")
            drone.connect()
            print(f"   ✅ Drone {i+1} connected! Battery: {drone.get_battery()}%")

        # Takeoff
        print("\n🚁 Taking off...")
        for i, drone in enumerate(drones):
            print(f"   Drone {i+1} taking off...")
            drone.takeoff()
            print(f"   ✅ Drone {i+1} airborne!")

        # Move up in parallel (simulated)
        print("\n⬆️ Moving up 100cm...")
        for i, drone in enumerate(drones):
            print(f"   Drone {i+1} moving up...")
            drone.move_up(100)
            print(f"   ✅ Drone {i+1} moved up!")

        # Sequential forward movement
        print("\n➡️ Sequential forward movement...")
        for i, drone in enumerate(drones):
            distance = i * 20 + 20
            print(f"   Drone {i+1} moving forward {distance}cm...")
            drone.move_forward(distance)
            print(f"   ✅ Drone {i+1} moved forward!")

        # Parallel left movement (simulated)
        print("\n⬅️ Parallel left movement...")
        for i, drone in enumerate(drones):
            distance = i * 100 + 20
            print(f"   Drone {i+1} moving left {distance}cm...")
            drone.move_left(distance)
            print(f"   ✅ Drone {i+1} moved left!")

        # Land
        print("\n🛬 Landing...")
        for i, drone in enumerate(drones):
            print(f"   Drone {i+1} landing...")
            drone.land()
            print(f"   ✅ Drone {i+1} landed!")

        print("\n🎉 Swarm test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_modified_swarm_test()

    # Keep running for a bit to see logs
    print("\nKeeping drones running for 5 more seconds...")
    time.sleep(5)
    print("✨ Test complete!")
