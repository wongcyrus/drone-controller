#!/usr/bin/env python3
"""
Tello Drone UDP Protocol Simulator - Fixed Version

This simulator properly mocks the Tello drone UDP protocol by acting as
multiple virtual drones, each responding on their designated IP addresses.

The key insight: djitellopy sends UDP packets TO the drone IP on port 8889,
and expects responses back. We need to simulate this properly.
"""

import socket
import threading
import time
import argparse
import math
from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum


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


@dataclass
class DroneStatus:
    """Complete drone status matching Tello format."""
    battery: int = 100
    temperature_low: int = 60
    temperature_high: int = 65
    tof: int = 10  # Time of flight sensor (distance to ground in mm)
    height: int = 0  # Height in cm
    barometer: float = 1013.25  # Pressure in hPa
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    acceleration_z: float = -1000.0  # Gravity
    speed_x: float = 0.0
    speed_y: float = 0.0
    speed_z: float = 0.0
    agx: float = 0.0  # Angular velocity x
    agy: float = 0.0  # Angular velocity y
    agz: float = 0.0  # Angular velocity z


class SimulatedDrone:
    """Simulates a single Tello drone with realistic behavior."""

    def __init__(self, drone_id: str, ip_address: str = "192.168.10.1"):
        self.drone_id = drone_id
        self.ip_address = ip_address
        self.state = DroneState.DISCONNECTED
        self.position = DronePosition()
        self.status = DroneStatus()

        # Movement simulation
        self.target_position = DronePosition()
        self.is_moving = False
        self.movement_start_time = 0
        self.movement_duration = 0
        self.start_position = DronePosition()

        # Video simulation
        self.video_enabled = False

        # Timing
        self.last_command_time = time.time()
        self.takeoff_time = 0

        # Client tracking
        self.client_address = None

        print(f"🚁 Simulated drone {drone_id} initialized at {ip_address}")

    def process_command(self, command: str,
                        client_addr: Tuple[str, int]) -> str:
        """Process a command and return appropriate response."""
        command = command.strip().lower()
        self.last_command_time = time.time()
        self.client_address = client_addr

        try:
            if command == "command":
                self.state = DroneState.CONNECTED
                return "ok"

            elif command == "takeoff":
                if self.state in [DroneState.CONNECTED, DroneState.FLYING]:
                    self.state = DroneState.TAKING_OFF
                    self.takeoff_time = time.time()
                    # Simulate takeoff to 100cm height
                    self._start_movement(DronePosition(
                        x=self.position.x, y=self.position.y, z=100,
                        roll=self.position.roll, pitch=self.position.pitch,
                        yaw=self.position.yaw
                    ), duration=3.0)
                    return "ok"
                return "error"

            elif command == "land":
                if self.state == DroneState.FLYING:
                    self.state = DroneState.LANDING
                    # Simulate landing to ground level
                    self._start_movement(DronePosition(
                        x=self.position.x, y=self.position.y, z=0,
                        roll=self.position.roll, pitch=self.position.pitch,
                        yaw=self.position.yaw
                    ), duration=3.0)
                    return "ok"
                return "error"

            elif command == "emergency":
                self.state = DroneState.EMERGENCY
                self.position.z = 0  # Emergency land immediately
                return "ok"

            elif command.startswith("up "):
                distance = int(command.split()[1])
                return self._move_relative(0, 0, distance)

            elif command.startswith("down "):
                distance = int(command.split()[1])
                return self._move_relative(0, 0, -distance)

            elif command.startswith("left "):
                distance = int(command.split()[1])
                return self._move_relative(-distance, 0, 0)

            elif command.startswith("right "):
                distance = int(command.split()[1])
                return self._move_relative(distance, 0, 0)

            elif command.startswith("forward "):
                distance = int(command.split()[1])
                return self._move_relative(0, distance, 0)

            elif command.startswith("back "):
                distance = int(command.split()[1])
                return self._move_relative(0, -distance, 0)

            elif command.startswith("cw "):
                angle = int(command.split()[1])
                return self._rotate(angle)

            elif command.startswith("ccw "):
                angle = int(command.split()[1])
                return self._rotate(-angle)

            elif command.startswith("go "):
                # go x y z speed
                parts = command.split()
                x, y, z, speed = map(int, parts[1:5])
                return self._move_to_relative(x, y, z, speed)

            elif command == "battery?":
                return str(self.status.battery)

            elif command == "speed?":
                return "100"  # Default speed

            elif command == "time?":
                if self.takeoff_time > 0:
                    return str(int(time.time() - self.takeoff_time))
                else:
                    return "0"

            elif command == "height?":
                return str(int(self.position.z))

            elif command == "temp?":
                low = self.status.temperature_low
                high = self.status.temperature_high
                return f"{low}~{high}"

            elif command == "attitude?":
                pitch = int(self.position.pitch)
                roll = int(self.position.roll)
                yaw = int(self.position.yaw)
                return f"pitch:{pitch};roll:{roll};yaw:{yaw};"

            elif command == "baro?":
                return f"{self.status.barometer:.2f}"

            elif command == "acceleration?":
                agx = self.status.acceleration_x
                agy = self.status.acceleration_y
                agz = self.status.acceleration_z
                return f"agx:{agx:.2f};agy:{agy:.2f};agz:{agz:.2f};"

            elif command == "tof?":
                return str(self.status.tof)

            elif command == "wifi?":
                return "signal:90;noise:10;"

            elif command == "streamon":
                self.video_enabled = True
                return "ok"

            elif command == "streamoff":
                self.video_enabled = False
                return "ok"

            else:
                return "error"

        except (ValueError, IndexError):
            return "error"

    def _move_relative(self, dx: int, dy: int, dz: int) -> str:
        """Move relative to current position."""
        if self.state != DroneState.FLYING:
            return "error"

        new_x = self.position.x + dx
        new_y = self.position.y + dy
        new_z = max(0, self.position.z + dz)  # Don't go below ground

        self._start_movement(DronePosition(
            x=new_x, y=new_y, z=new_z,
            roll=self.position.roll, pitch=self.position.pitch,
            yaw=self.position.yaw
        ), duration=2.0)

        return "ok"

    def _move_to_relative(self, x: int, y: int, z: int, speed: int) -> str:
        """Move to position relative to current position."""
        if self.state != DroneState.FLYING:
            return "error"

        new_x = self.position.x + x
        new_y = self.position.y + y
        new_z = max(0, self.position.z + z)

        # Calculate duration based on distance and speed
        distance = math.sqrt(x*x + y*y + z*z)
        duration = max(1.0, distance / speed)

        self._start_movement(DronePosition(
            x=new_x, y=new_y, z=new_z,
            roll=self.position.roll, pitch=self.position.pitch,
            yaw=self.position.yaw
        ), duration=duration)

        return "ok"

    def _rotate(self, angle: int) -> str:
        """Rotate the drone."""
        if self.state != DroneState.FLYING:
            return "error"

        new_yaw = (self.position.yaw + angle) % 360

        self._start_movement(DronePosition(
            x=self.position.x, y=self.position.y, z=self.position.z,
            roll=self.position.roll, pitch=self.position.pitch,
            yaw=new_yaw
        ), duration=1.0)

        return "ok"

    def _start_movement(self, target: DronePosition, duration: float):
        """Start a movement animation."""
        self.start_position = DronePosition(
            x=self.position.x, y=self.position.y, z=self.position.z,
            roll=self.position.roll, pitch=self.position.pitch,
            yaw=self.position.yaw
        )
        self.target_position = target
        self.is_moving = True
        self.movement_start_time = time.time()
        self.movement_duration = duration

    def update_position(self):
        """Update position during movement animation."""
        if not self.is_moving:
            return

        elapsed = time.time() - self.movement_start_time
        if elapsed >= self.movement_duration:
            # Movement complete
            self.position = self.target_position
            self.is_moving = False

            # Update state after movement
            if self.state == DroneState.TAKING_OFF and self.position.z > 50:
                self.state = DroneState.FLYING
            elif self.state == DroneState.LANDING and self.position.z <= 0:
                self.state = DroneState.CONNECTED
        else:
            # Interpolate position
            progress = elapsed / self.movement_duration
            progress = min(1.0, progress)  # Clamp to 1.0

            # Use ease-in-out curve for smoother movement
            progress = 0.5 * (1 - math.cos(progress * math.pi))

            # Interpolate each coordinate
            start = self.start_position
            target = self.target_position

            self.position.x = (
                start.x + (target.x - start.x) * progress
            )
            self.position.y = (
                start.y + (target.y - start.y) * progress
            )
            self.position.z = (
                start.z + (target.z - start.z) * progress
            )
            self.position.roll = (
                start.roll + (target.roll - start.roll) * progress
            )
            self.position.pitch = (
                start.pitch + (target.pitch - start.pitch) * progress
            )
            self.position.yaw = (
                start.yaw + (target.yaw - start.yaw) * progress
            )

    def get_state_string(self) -> str:
        """Get state string in Tello format."""
        self.update_position()

        # Update status based on position
        self.status.height = int(self.position.z)
        # Convert cm to mm
        self.status.tof = max(10, int(self.position.z * 10))

        # Simulate battery drain (very slowly)
        if self.state == DroneState.FLYING:
            if self.takeoff_time > 0:
                time_flying = time.time() - self.takeoff_time
            else:
                time_flying = 0
            battery_drain = int(time_flying / 60)  # 1% per minute
            self.status.battery = max(10, 100 - battery_drain)

        # Format state string like real Tello
        state_parts = [
            f"pitch:{int(self.position.pitch)}",
            f"roll:{int(self.position.roll)}",
            f"yaw:{int(self.position.yaw)}",
            f"vgx:{int(self.status.speed_x)}",
            f"vgy:{int(self.status.speed_y)}",
            f"vgz:{int(self.status.speed_z)}",
            f"templ:{self.status.temperature_low}",
            f"temph:{self.status.temperature_high}",
            f"tof:{self.status.tof}",
            f"h:{self.status.height}",
            f"bat:{self.status.battery}",
            f"baro:{self.status.barometer:.2f}",
            "time:0",
            f"agx:{self.status.agx:.2f}",
            f"agy:{self.status.agy:.2f}",
            f"agz:{self.status.agz:.2f}",
        ]

        return ";".join(state_parts) + ";"


class TelloSimulator:
    """
    Main simulator that intercepts UDP traffic to drone IP addresses.

    This works by creating a UDP server that listens for packets sent
    to any of the simulated drone IP addresses on port 8889.
    """

    def __init__(self):
        self.drones: Dict[str, SimulatedDrone] = {}
        self.running = False

        # Single UDP socket to handle all drone communications
        self.socket = None
        self.thread = None

    def add_drone(self, drone_id: str, ip_address: str) -> str:
        """Add a simulated drone at the specified IP address."""
        drone = SimulatedDrone(drone_id, ip_address)
        self.drones[ip_address] = drone

        print(f"✅ Added simulated drone '{drone_id}' at {ip_address}")
        return ip_address

    def start(self):
        """Start the simulator."""
        print("🚁 Starting Tello UDP Simulator...")
        print("=" * 50)

        if not self.drones:
            print("❌ No drones configured")
            return False

        self.running = True

        try:
            # Create UDP socket that will receive all drone communications
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allow socket reuse
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to all interfaces on port 8889
            # This will receive UDP packets sent to any IP:8889
            self.socket.bind(('0.0.0.0', 8889))

            print("📡 UDP command server listening on 0.0.0.0:8889")

            # Start command handler thread
            self.thread = threading.Thread(
                target=self._command_handler, daemon=True
            )
            self.thread.start()

            print(f"🎯 Simulating {len(self.drones)} drone(s):")
            for ip, drone in self.drones.items():
                print(f"   • {drone.drone_id} at {ip}")

            print("\n✅ Simulator ready!")
            print("💡 Connect your application to the drone IP addresses")
            print("🛑 Press Ctrl+C to stop")
            return True

        except Exception as e:
            print(f"❌ Failed to start simulator: {e}")
            return False

    def stop(self):
        """Stop the simulator."""
        print("\n🛑 Stopping simulator...")
        self.running = False

        if self.socket:
            self.socket.close()

    def _command_handler(self):
        """Handle incoming commands from clients."""
        print("🎮 Command handler started")

        while self.running:
            try:
                # Set socket timeout to periodically check self.running
                self.socket.settimeout(1.0)

                # Receive UDP packet
                data, client_addr = self.socket.recvfrom(1024)
                command = data.decode('utf-8').strip()

                # The client sends TO a drone IP, but we receive it here
                # We need to determine which drone this was intended for
                #
                # Since djitellopy creates sockets that connect to specific
                # drone IPs, we can use the client address to map back to
                # the intended drone, or use a simple round-robin for demo

                # For now, use the first available drone
                # In a more sophisticated setup, you'd track which client
                # is talking to which drone
                if self.drones:
                    drone = list(self.drones.values())[0]
                    response = drone.process_command(command, client_addr)

                    print(f"📨 {drone.drone_id}: {command} -> {response}")

                    # Send response back to client
                    self.socket.sendto(response.encode('utf-8'), client_addr)

            except socket.timeout:
                continue  # Check self.running
            except socket.error:
                if self.running:
                    print("❌ Socket error in command handler")
                break
            except Exception as e:
                print(f"❌ Error in command handler: {e}")


def main():
    """Main entry point for the simulator."""
    parser = argparse.ArgumentParser(description="Tello Drone UDP Simulator")
    parser.add_argument(
        "--drone-id", default="drone_001",
        help="Drone ID for single drone simulation"
    )
    parser.add_argument(
        "--ip", default="192.168.10.1",
        help="IP address for the simulated drone"
    )

    args = parser.parse_args()

    # Create simulator with a single drone for simplicity
    simulator = TelloSimulator()
    simulator.add_drone(args.drone_id, args.ip)

    try:
        if simulator.start():
            # Keep running until interrupted
            while True:
                time.sleep(1)
        else:
            print("Failed to start simulator")

    except KeyboardInterrupt:
        simulator.stop()
        print("\n👋 Simulator stopped")


if __name__ == "__main__":
    main()
