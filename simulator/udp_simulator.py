#!/usr/bin/env python3
"""
Tello Drone UDP Protocol Simulator

This simulator mocks the actual Tello drone UDP protocol, allowing the main
application to connect to simulated drones just like real ones.

Usage:
    python udp_simulator.py --drones 3  # Simulate 3 drones
    python udp_simulator.py --drone-ids alpha beta gamma  # Named drones

The simulator starts UDP servers on the standard Tello ports:
- Command Port: 8889 (receive commands)
- State Port: 8890 (send state data)

Example IP addresses for simulated drones:
- 192.168.10.1 (first drone)
- 192.168.10.2 (second drone)
- etc.
"""

import socket
import threading
import time
import argparse
import math
from typing import Dict, Optional
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

        # Mission pads (simplified)
        self.mission_pad_id = -1

        # Video simulation
        self.video_enabled = False

        # Timing
        self.last_command_time = time.time()
        self.takeoff_time = 0

        print(f"🚁 Simulated drone {drone_id} initialized at {ip_address}")

    def process_command(self, command: str) -> str:
        """Process a command and return appropriate response."""
        command = command.strip().lower()
        self.last_command_time = time.time()

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
            roll=self.position.roll, pitch=self.position.pitch, yaw=self.position.yaw
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

            self.position.x = self.start_position.x + (self.target_position.x - self.start_position.x) * progress
            self.position.y = self.start_position.y + (self.target_position.y - self.start_position.y) * progress
            self.position.z = self.start_position.z + (self.target_position.z - self.start_position.z) * progress
            self.position.roll = self.start_position.roll + (self.target_position.roll - self.start_position.roll) * progress
            self.position.pitch = self.start_position.pitch + (self.target_position.pitch - self.start_position.pitch) * progress
            self.position.yaw = self.start_position.yaw + (self.target_position.yaw - self.start_position.yaw) * progress

    def get_state_string(self) -> str:
        """Get state string in Tello format."""
        self.update_position()

        # Update status based on position
        self.status.height = int(self.position.z)
        self.status.tof = max(10, int(self.position.z * 10))  # Convert cm to mm

        # Simulate battery drain (very slowly)
        if self.state == DroneState.FLYING:
            time_flying = time.time() - self.takeoff_time if self.takeoff_time > 0 else 0
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
            f"time:0",
            f"agx:{self.status.agx:.2f}",
            f"agy:{self.status.agy:.2f}",
            f"agz:{self.status.agz:.2f}",
        ]

        return ";".join(state_parts) + ";"


class TelloSimulator:
    """Main simulator that handles multiple simulated drones."""

    def __init__(self, base_ip: str = "192.168.10", start_host: int = 1):
        self.base_ip = base_ip
        self.start_host = start_host
        self.drones: Dict[str, SimulatedDrone] = {}
        self.running = False

        # Sockets for communication
        self.command_socket = None
        self.state_socket = None

        # Threads
        self.command_thread = None
        self.state_thread = None

    def add_drone(self, drone_id: str, host_num: Optional[int] = None) -> str:
        """Add a simulated drone."""
        if host_num is None:
            host_num = self.start_host + len(self.drones)

        ip_address = f"{self.base_ip}.{host_num}"
        drone = SimulatedDrone(drone_id, ip_address)
        self.drones[ip_address] = drone

        print(f"✅ Added simulated drone '{drone_id}' at {ip_address}")
        return ip_address

    def start(self):
        """Start the simulator."""
        print("🚁 Starting Tello UDP Simulator...")
        print("=" * 50)

        self.running = True

        # Set up command socket (port 8889)
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.command_socket.bind(('', 8889))
        print("📡 Command server listening on port 8889")

        # Set up state socket (port 8890)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(('', 8890))
        print("📊 State server listening on port 8890")

        # Start threads
        self.command_thread = threading.Thread(target=self._command_handler, daemon=True)
        self.state_thread = threading.Thread(target=self._state_broadcaster, daemon=True)

        self.command_thread.start()
        self.state_thread.start()

        print(f"🎯 Simulating {len(self.drones)} drone(s)")
        for ip, drone in self.drones.items():
            print(f"   • {drone.drone_id} at {ip}")

        print("\n✅ Simulator ready! Drones can now connect.")
        print("💡 In your drone application, connect to the simulated drone IPs")
        print("🛑 Press Ctrl+C to stop the simulator")

    def stop(self):
        """Stop the simulator."""
        print("\n🛑 Stopping simulator...")
        self.running = False

        if self.command_socket:
            self.command_socket.close()
        if self.state_socket:
            self.state_socket.close()

    def _command_handler(self):
        """Handle incoming commands."""
        print("🎮 Command handler started")

        while self.running:
            try:
                # Receive command
                data, addr = self.command_socket.recvfrom(1024)
                command = data.decode('utf-8').strip()

                # Find drone by client IP (simple mapping)
                # In real scenario, you'd need more sophisticated drone mapping
                drone = None
                if self.drones:
                    # For simplicity, use the first drone or map by IP
                    drone = list(self.drones.values())[0]

                    # Try to find specific drone if multiple exist
                    client_ip = addr[0]
                    for drone_ip, d in self.drones.items():
                        # This is a simplified mapping - in reality you'd need
                        # more sophisticated drone-to-client mapping
                        if client_ip in drone_ip or len(self.drones) == 1:
                            drone = d
                            break

                if drone:
                    response = drone.process_command(command)
                    print(f"📨 {addr[0]}:{addr[1]} -> {command} -> {response}")

                    # Send response
                    self.command_socket.sendto(response.encode('utf-8'), addr)
                else:
                    print(f"❌ No drone found for command from {addr}")
                    self.command_socket.sendto(b"error", addr)

            except socket.error:
                if self.running:
                    print("❌ Socket error in command handler")
                break
            except Exception as e:
                print(f"❌ Error in command handler: {e}")

    def _state_broadcaster(self):
        """Broadcast state information."""
        print("📊 State broadcaster started")

        while self.running:
            try:
                # Send state for each drone
                for drone in self.drones.values():
                    state_data = drone.get_state_string()

                    # Broadcast to all potential clients
                    # In a real setup, you'd maintain a list of connected clients
                    try:
                        # This is a simplified broadcast - in reality you'd send
                        # to specific clients that have connected to each drone
                        self.state_socket.sendto(
                            state_data.encode('utf-8'),
                            ('127.0.0.1', 8890)
                        )
                    except:
                        pass  # Ignore broadcast errors

                time.sleep(0.1)  # 10Hz state updates

            except Exception as e:
                if self.running:
                    print(f"❌ Error in state broadcaster: {e}")
                break


def main():
    """Main entry point for the simulator."""
    parser = argparse.ArgumentParser(description="Tello Drone UDP Simulator")
    parser.add_argument(
        "--drones", type=int, default=1,
        help="Number of simulated drones (default: 1)"
    )
    parser.add_argument(
        "--base-ip", default="192.168.10",
        help="Base IP address (default: 192.168.10)"
    )
    parser.add_argument(
        "--start-host", type=int, default=1,
        help="Starting host number (default: 1)"
    )
    parser.add_argument(
        "--drone-ids", nargs="*",
        help="Specific drone IDs (default: drone_001, drone_002, etc.)"
    )

    args = parser.parse_args()

    # Create simulator
    simulator = TelloSimulator(args.base_ip, args.start_host)

    # Add drones
    drone_ids = args.drone_ids if args.drone_ids else [
        f"drone_{i:03d}" for i in range(1, args.drones + 1)
    ]

    for i, drone_id in enumerate(drone_ids[:args.drones]):
        simulator.add_drone(drone_id, args.start_host + i)

    try:
        simulator.start()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        simulator.stop()
        print("\n👋 Simulator stopped")


if __name__ == "__main__":
    main()
