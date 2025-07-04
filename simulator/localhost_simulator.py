#!/usr/bin/env python3
"""
Localhost Tello Drone Simulator

This simulator is specifically designed to work with djitellopy on the same
machine. It uses a different port strategy to avoid conflicts.

The key insight:
- djitellopy binds to port 8889 for receiving responses
- The real Tello drone listens on port 8889 for commands
- So we need to simulate the drone behavior, not the client behavior

This simulator acts as a "fake drone" that responds to commands sent to
127.0.0.1:8889
"""

import socket
import threading
import time
import argparse
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DroneState(Enum):
    """Possible drone states."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    FLYING = "flying"
    LANDING = "landing"
    TAKING_OFF = "taking_off"
    EMERGENCY = "emergency"


@dataclass
class DronePosition:
    """3D position and orientation of the drone."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class LocalhostTelloDrone:
    """Simulated Tello drone for localhost testing."""

    def __init__(self, drone_id: str):
        self.drone_id = drone_id
        self.state = DroneState.DISCONNECTED
        self.position = DronePosition()
        self.battery = 100
        self.temperature = 60
        self.last_command_time = time.time()
        self.takeoff_time = 0
        self.is_moving = False
        self.movement_end_time = 0

    def process_command(self, command: str) -> str:
        """Process a command and return appropriate response."""
        command = command.strip().lower()
        self.last_command_time = time.time()

        print(f"📨 Drone {self.drone_id} received: {command}")

        try:
            if command == "command":
                self.state = DroneState.CONNECTED
                return "ok"

            elif command == "takeoff":
                if self.state in [DroneState.CONNECTED, DroneState.FLYING]:
                    self.state = DroneState.TAKING_OFF
                    self.takeoff_time = time.time()
                    self.position.z = 100  # Simulate takeoff to 100cm
                    threading.Timer(3.0, self._finish_takeoff).start()
                    return "ok"
                return "error"

            elif command == "land":
                if self.state == DroneState.FLYING:
                    self.state = DroneState.LANDING
                    self.position.z = 0  # Land to ground
                    threading.Timer(3.0, self._finish_landing).start()
                    return "ok"
                return "error"

            elif command == "emergency":
                self.state = DroneState.EMERGENCY
                self.position.z = 0
                return "ok"

            elif command.startswith("battery?"):
                return str(self.battery)

            elif command.startswith("up "):
                distance = int(command.split()[1])
                self._move_relative(0, 0, distance)
                return "ok"

            elif command.startswith("down "):
                distance = int(command.split()[1])
                self._move_relative(0, 0, -distance)
                return "ok"

            elif command.startswith("left "):
                distance = int(command.split()[1])
                self._move_relative(0, -distance, 0)
                return "ok"

            elif command.startswith("right "):
                distance = int(command.split()[1])
                self._move_relative(0, distance, 0)
                return "ok"

            elif command.startswith("forward "):
                distance = int(command.split()[1])
                self._move_relative(distance, 0, 0)
                return "ok"

            elif command.startswith("back "):
                distance = int(command.split()[1])
                self._move_relative(-distance, 0, 0)
                return "ok"

            elif command.startswith("cw "):
                angle = int(command.split()[1])
                self.position.yaw += angle
                self.position.yaw %= 360
                return "ok"

            elif command.startswith("ccw "):
                angle = int(command.split()[1])
                self.position.yaw -= angle
                self.position.yaw %= 360
                return "ok"

            elif command.startswith("go "):
                # Parse go x y z speed command
                parts = command.split()
                if len(parts) >= 4:
                    x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
                    self._move_relative(x, y, z)
                    return "ok"
                return "error"

            elif command.startswith("speed "):
                # Set speed command - just acknowledge it
                return "ok"

            else:
                # Don't respond to "error" commands to avoid feedback loops
                if command == "error":
                    print("⚠️  Ignoring error feedback loop")
                    return ""  # Return empty response to break the loop

                # Don't respond to "ok" responses to avoid feedback loops
                if command == "ok":
                    print("⚠️  Ignoring ok response loop")
                    return ""  # Return empty response to break the loop

                print(f"⚠️  Unknown command: {command}")
                return "error"

        except (ValueError, IndexError) as e:
            print(f"❌ Command parsing error: {e}")
            return "error"
        except (AttributeError, TypeError) as e:
            print(f"❌ Command execution error: {e}")
            return "error"

    def _move_relative(self, x: int, y: int, z: int):
        """Simulate relative movement."""
        if (self.state == DroneState.FLYING or
                self.state == DroneState.CONNECTED):
            self.position.x += x
            self.position.y += y
            self.position.z += z

            # Simulate movement time (2 seconds)
            self.is_moving = True
            self.movement_end_time = time.time() + 2.0
            threading.Timer(2.0, self._finish_movement).start()

    def _finish_takeoff(self):
        """Finish takeoff sequence."""
        self.state = DroneState.FLYING
        print(f"✈️  Drone {self.drone_id} takeoff complete")

    def _finish_landing(self):
        """Finish landing sequence."""
        self.state = DroneState.CONNECTED
        print(f"🛬 Drone {self.drone_id} landing complete")

    def _finish_movement(self):
        """Finish movement sequence."""
        self.is_moving = False
        print(f"📍 Drone {self.drone_id} movement complete")

    def get_status(self) -> dict:
        """Get current drone status."""
        return {
            "drone_id": self.drone_id,
            "state": self.state.value,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "z": self.position.z,
                "yaw": self.position.yaw
            },
            "battery": self.battery,
            "is_moving": self.is_moving
        }


class LocalhostSimulator:
    """
    Localhost Tello simulator that works with djitellopy.

    This simulator receives UDP packets on a different approach:
    - Creates a UDP server that binds to a specific port
    - Responds to commands sent to that port
    - Works with djitellopy's client approach
    """

    def __init__(self):
        self.drone = LocalhostTelloDrone("localhost_drone")
        self.running = False
        self.socket: Optional[socket.socket] = None
        self.thread = None

    def start(self):
        """Start the localhost simulator."""
        print("🚁 Starting Localhost Tello Simulator...")
        print("=" * 50)

        self.running = True

        # Create UDP socket that listens for commands
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # The key: bind to 127.0.0.1:8889 to receive commands sent to localhost
        try:
            self.socket.bind(('127.0.0.1', 8889))
            print("📡 Simulator listening on 127.0.0.1:8889")
        except OSError as e:
            print(f"❌ Failed to bind to 127.0.0.1:8889: {e}")
            print("💡 Trying alternative port...")
            self.socket.bind(('127.0.0.1', 8890))
            print("📡 Simulator listening on 127.0.0.1:8890")

        # Start command handling thread
        self.thread = threading.Thread(
            target=self._command_handler, daemon=True
        )
        self.thread.start()

        print(f"🎯 Simulated drone '{self.drone.drone_id}' ready")
        print("💡 Connect your application to 127.0.0.1")
        print("🛑 Press Ctrl+C to stop")

    def stop(self):
        """Stop the simulator."""
        print("\\n🛑 Stopping simulator...")
        self.running = False
        if self.socket:
            self.socket.close()

    def _command_handler(self):
        """Handle incoming UDP commands."""
        print("🎮 Command handler started")

        while self.running and self.socket:
            try:
                # Receive command
                data, addr = self.socket.recvfrom(1024)
                command = data.decode('utf-8').strip()

                # Process command
                response = self.drone.process_command(command)

                print(f"📨 {addr[0]}:{addr[1]} -> {command} -> {response}")

                # Only send response back if it's not empty
                # (empty responses are used to break feedback loops)
                if response and self.socket:
                    self.socket.sendto(response.encode('utf-8'), addr)

            except socket.error as e:
                if self.running:
                    print(f"❌ Socket error: {e}")
                break
            except (UnicodeDecodeError, AttributeError) as e:
                print(f"❌ Error in command handler: {e}")

    def get_drone_status(self):
        """Get current drone status."""
        return self.drone.get_status()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Localhost Tello Drone Simulator"
    )
    parser.parse_args()  # Parse but don't store unused args

    simulator = LocalhostSimulator()

    try:
        simulator.start()

        # Keep running and show status updates
        while True:
            time.sleep(5)
            status = simulator.get_drone_status()
            print(
                f"📊 Status: {status['state']} | "
                f"Battery: {status['battery']}% | "
                f"Pos: ({status['position']['x']}, "
                f"{status['position']['y']}, {status['position']['z']})"
            )

    except KeyboardInterrupt:
        simulator.stop()
        print("\\n👋 Simulator stopped")


if __name__ == "__main__":
    main()
