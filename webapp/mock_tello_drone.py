#!/usr/bin/env python3
"""
Mock Tello Drone Simulator

This script simulates a Tello drone by listening on UDP ports and responding
to commands just like a real Tello drone would. It's useful for testing
TelloSwarm and Tello applications without actual hardware.
"""

import socket
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed output
    format='[%(levelname)s] %(name)s - %(message)s'
)


class MockTelloDrone:
    """
    Mock Tello drone that simulates real drone behavior over UDP
    """

    # Default Tello ports
    COMMAND_PORT = 8889  # Port for receiving commands
    STATE_PORT = 8890    # Port for sending state information
    VIDEO_PORT = 11111   # Port for video streaming (not implemented)

    def __init__(self, drone_ip: str = "127.0.0.1",
                 name: str = "MockTello",
                 command_port: int = None):
        self.drone_ip = drone_ip
        self.name = name
        self.command_port = command_port or self.COMMAND_PORT
        self.logger = logging.getLogger(f"MockTello-{drone_ip}")

        # Drone state
        self.state = {
            'mid': -1,     # Mission pad ID
            'x': 0,        # Mission pad X
            'y': 0,        # Mission pad Y
            'z': 0,        # Mission pad Z
            'pitch': 0,    # Pitch angle
            'roll': 0,     # Roll angle
            'yaw': 0,      # Yaw angle
            'vgx': 0,      # Velocity X
            'vgy': 0,      # Velocity Y
            'vgz': 0,      # Velocity Z
            'templ': 20,   # Temperature low
            'temph': 25,   # Temperature high
            'tof': 10,     # Time of flight distance
            'h': 0,        # Height
            'bat': 100,    # Battery percentage
            'baro': 1013.25,  # Barometer
            'time': 0,     # Flight time
            'agx': 0.0,    # Acceleration X
            'agy': 0.0,    # Acceleration Y
            'agz': -1000.0  # Acceleration Z (gravity)
        }

        # Drone status
        self.is_flying = False
        self.is_connected = False
        self.sdk_mode = False
        self.stream_on = False

        # Sockets
        self.command_socket = None
        self.state_socket = None

        # Threads
        self.command_thread = None
        self.state_thread = None
        self.running = False

        # Store client addresses for responses
        self.client_addresses = set()

        # Command responses
        self.command_responses = {
            # Control Commands
            'command': 'ok',
            'takeoff': 'ok',
            'land': 'ok',
            'streamon': 'ok',
            'streamoff': 'ok',
            'emergency': 'ok',
            'reset': 'ok',
            'up': 'ok',
            'down': 'ok',
            'left': 'ok',
            'right': 'ok',
            'forward': 'ok',
            'back': 'ok',
            'cw': 'ok',
            'ccw': 'ok',
            'flip': 'ok',
            'go': 'ok',
            'stop': 'ok',
            'curve': 'ok',
            'speed': 'ok',
            'rc': 'ok',

            # Set Commands
            'wifi': 'ok',
            'mon': 'ok',
            'moff': 'ok',
            'mdirection': 'ok',
            'ap': 'ok',

            # Read Commands - exact format per specifications
            'speed?': lambda: str(10),  # Current speed in cm/s (10-100)
            'battery?': lambda: str(self.state['bat']),  # Battery percentage (0-100)
            'time?': lambda: str(self.state['time']),  # Flight time in seconds
            'wifi?': lambda: str(90),  # WiFi SNR
            'sdk?': lambda: '"2.0"',  # SDK version (note: quoted string)
            'sn?': lambda: f'"TELLO{hash(self.name) % 10000000:07d}"',  # Serial number (quoted, deterministic)
            'height?': lambda: str(self.state['h']),  # Height in cm
            'temp?': lambda: f"{int(self.state['templ'])}~{int(self.state['temph'])}",  # Temperature range
            'attitude?': lambda: (
                f"pitch:{self.state['pitch']};"
                f"roll:{self.state['roll']};"
                f"yaw:{self.state['yaw']};"
            ),
            'baro?': lambda: f"{self.state['baro']:.2f}",  # Barometer reading
            'tof?': lambda: str(int(self.state['tof'])),  # Time of flight distance in cm
        }

    def start(self):
        """Start the mock drone servers"""
        self.running = True
        self.is_connected = True

        # Create and bind command socket
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set socket options to prevent address reuse issues
        self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.command_socket.bind((self.drone_ip, self.command_port))
            self.logger.info(
                "Command server listening on %s:%d",
                self.drone_ip, self.command_port
            )
        except OSError as e:
            self.logger.error(f"Failed to bind command socket: {e}")
            return False

        # Create state socket (for sending state data)
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Start command listener thread
        self.command_thread = threading.Thread(
            target=self._command_listener, daemon=True
        )
        self.command_thread.start()

        # Start state broadcaster thread
        self.state_thread = threading.Thread(
            target=self._state_broadcaster, daemon=True
        )
        self.state_thread.start()

        self.logger.info(
            f"Mock Tello drone '{self.name}' started successfully"
        )
        return True

    def stop(self):
        """Stop the mock drone servers"""
        self.running = False
        self.is_connected = False

        if self.command_socket:
            self.command_socket.close()
        if self.state_socket:
            self.state_socket.close()

        self.logger.info(f"Mock Tello drone '{self.name}' stopped")

    def _command_listener(self):
        """Listen for and respond to commands"""
        self.logger.info("Command listener started")
        self.logger.info("Listening on %s:%d", self.drone_ip, self.command_port)

        while self.running:
            try:
                # Receive command
                data, client_addr = self.command_socket.recvfrom(1024)
                command = data.decode('utf-8').strip().lower()

                self.logger.info(
                    "📥 RAW UDP: %s:%d -> %s:%d | '%s'",
                    client_addr[0], client_addr[1],
                    self.drone_ip, self.command_port, command
                )

                # Skip if receiving from our own IP and port (prevents loops)
                if (client_addr[1] == self.command_port and
                        client_addr[0] == self.drone_ip):
                    self.logger.debug(
                        "⛔ IGNORED: Same IP/port %s: '%s'",
                        client_addr, command
                    )
                    continue

                # Allow commands from port 8889 if they're from different IP
                # (djitellopy client is on different machine/network)

                # Filter out commands that look like error responses to prevent loops
                if (command.startswith('error ') or
                        command.startswith('ok') or
                        len(command.strip()) == 0):
                    self.logger.warning(
                        "⛔ IGNORED: Invalid/response command from %s: '%s'",
                        client_addr, command
                    )
                    continue

                # Store client address for state broadcasting
                self.client_addresses.add(client_addr)

                self.logger.info(
                    "✅ PROCESSING: Command from %s: '%s'", client_addr, command
                )

                # Process command and get response
                response = self._process_command(command)

                # Send response back to client
                if response:
                    self.command_socket.sendto(
                        response.encode('utf-8'), client_addr
                    )
                    self.logger.info(
                        "📤 RESPONSE: To %s: '%s'", client_addr, response
                    )

            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    self.logger.error("❌ ERROR in command listener: %s", e)

    def _process_command(self, command: str) -> str:
        """Process a command and return appropriate response"""

        # Handle SDK mode entry
        if command == 'command':
            self.sdk_mode = True
            return 'ok'

        # Require SDK mode for most commands
        if not self.sdk_mode and command not in ['command']:
            return 'error Not in SDK mode'

        # Split command and arguments
        parts = command.split()
        cmd = parts[0] if parts else ''
        args = parts[1:] if len(parts) > 1 else []

        # Handle movement commands
        if cmd in ['up', 'down', 'left', 'right', 'forward', 'back']:
            if args and args[0].isdigit():
                distance = int(args[0])
                if 20 <= distance <= 500:
                    self._simulate_movement(cmd, distance)
                    return 'ok'
                else:
                    return 'error Out of range'
            return 'error Invalid argument'

        # Handle rotation commands
        elif cmd in ['cw', 'ccw']:
            if args and args[0].isdigit():
                angle = int(args[0])
                if 1 <= angle <= 360:
                    self._simulate_rotation(cmd, angle)
                    return 'ok'
                else:
                    return 'error Out of range'
            return 'error Invalid argument'

        # Handle takeoff
        elif cmd == 'takeoff':
            if not self.is_flying:
                self.is_flying = True
                self.state['h'] = 50  # Default takeoff height
                # Predictable battery drain (3% for takeoff)
                self.state['bat'] = max(0, self.state['bat'] - 3)
                # Simulate takeoff delay
                time.sleep(0.5)
                return 'ok'
            else:
                return 'error Already flying'

        # Handle landing
        elif cmd == 'land':
            if self.is_flying:
                self.is_flying = False
                self.state['h'] = 0
                # Predictable battery drain (1% for landing)
                self.state['bat'] = max(0, self.state['bat'] - 1)
                return 'ok'
            else:
                return 'error Not flying'

        # Handle streaming
        elif cmd == 'streamon':
            self.stream_on = True
            return 'ok'

        elif cmd == 'streamoff':
            self.stream_on = False
            return 'ok'

        # Handle emergency stop
        elif cmd == 'emergency':
            self.is_flying = False
            self.state['h'] = 0
            return 'ok'

        # Handle reset command
        elif cmd == 'reset':
            # SIMPLE: Reset everything to initial state
            self.is_flying = False
            self.sdk_mode = False
            self.stream_on = False
            
            # Reset ALL state to initial values
            self.state = {
                'mid': -1,     # Mission pad ID
                'x': 0,        # Mission pad X
                'y': 0,        # Mission pad Y
                'z': 0,        # Mission pad Z
                'pitch': 0,    # Pitch angle
                'roll': 0,     # Roll angle
                'yaw': 0,      # Yaw angle
                'vgx': 0,      # Velocity X
                'vgy': 0,      # Velocity Y
                'vgz': 0,      # Velocity Z
                'templ': 20,   # Temperature low
                'temph': 25,   # Temperature high
                'tof': 10,     # Time of flight distance
                'h': 0,        # Height
                'bat': 100,    # Battery percentage
                'baro': 1013.25,  # Barometer
                'time': 0,     # Flight time
                'agx': 0.0,    # Acceleration X
                'agy': 0.0,    # Acceleration Y
                'agz': -1000.0  # Acceleration Z (gravity)
            }
            
            self.logger.info(f"🔄 RESET: {self.name} - everything reset to initial state")
            
            # Force state broadcast
            self._force_state_broadcast()
            
            return 'ok'

        # Handle speed setting
        elif cmd == 'speed':
            if args and args[0].isdigit():
                speed = int(args[0])
                if 10 <= speed <= 100:
                    return 'ok'
                else:
                    return 'error Out of range'
            return 'error Invalid argument'

        # Handle RC control
        elif cmd == 'rc':
            if (len(args) == 4 and
                    all(arg.lstrip('-').isdigit() for arg in args)):
                # RC control with 4 values: a b c d
                return 'ok'
            return 'error Invalid argument'

        # Handle flip
        elif cmd == 'flip':
            if args and args[0] in ['l', 'r', 'f', 'b']:
                if self.is_flying:
                    return 'ok'
                else:
                    return 'error Not flying'
            return 'error Invalid argument'

        # Handle stop command
        elif cmd == 'stop':
            # Stop and hover in place
            return 'ok'

        # Handle go command
        elif cmd == 'go':
            if len(args) >= 4:
                try:
                    x, y, z, speed = map(int, args[:4])
                    # Validate coordinates (-500 to 500) and speed (10-100)
                    if (-500 <= x <= 500 and -500 <= y <= 500 and
                            -500 <= z <= 500 and 10 <= speed <= 100):
                        if self.is_flying:
                            # Simulate movement to coordinates
                            self.state['x'] = x
                            self.state['y'] = y
                            self.state['h'] = max(0, z)
                            return 'ok'
                        else:
                            return 'error Not flying'
                    else:
                        return 'error Out of range'
                except ValueError:
                    return 'error Invalid argument'
            return 'error Invalid argument'

        # Handle go with mission pad
        elif cmd == 'go' and 'mid' in ' '.join(args):
            # This would be a more complex parsing for mission pad coordinates
            # For now, just return ok if flying
            if self.is_flying:
                return 'ok'
            else:
                return 'error Not flying'

        # Handle curve command
        elif cmd == 'curve':
            if len(args) >= 7:
                try:
                    x1, y1, z1, x2, y2, z2, speed = map(int, args[:7])
                    # Validate all coordinates and speed
                    if (all(-500 <= coord <= 500 for coord in [x1, y1, z1, x2, y2, z2])
                            and 10 <= speed <= 60):
                        if self.is_flying:
                            # Arc radius validation would be done here
                            return 'ok'
                        else:
                            return 'error Not flying'
                    else:
                        return 'error Out of range'
                except ValueError:
                    return 'error Invalid argument'
            return 'error Invalid argument'

        # Handle mission pad commands
        elif cmd == 'mon':
            # Enable mission pad detection
            return 'ok'

        elif cmd == 'moff':
            # Disable mission pad detection
            return 'ok'

        elif cmd == 'mdirection':
            if args and args[0] in ['0', '1', '2']:
                # 0=downward, 1=forward, 2=both
                return 'ok'
            return 'error Invalid argument'

        # Handle WiFi setup commands
        elif cmd == 'wifi':
            if len(args) >= 2:
                ssid, password = args[0], args[1]
                # In real implementation, would validate SSID/password
                return 'ok'
            return 'error Invalid argument'

        elif cmd == 'ap':
            if len(args) >= 2:
                ssid, password = args[0], args[1]
                # Set Tello to station mode and connect to AP
                return 'ok'
            return 'error Invalid argument'

        # Handle jump command (mission pad specific)
        elif cmd == 'jump':
            if len(args) >= 7:
                try:
                    x, y, z, speed, yaw, mid1, mid2 = map(int, args[:7])
                    if (all(-500 <= coord <= 500 for coord in [x, y, z]) and
                            10 <= speed <= 100 and 1 <= mid1 <= 8 and 1 <= mid2 <= 8):
                        if self.is_flying:
                            return 'ok'
                        else:
                            return 'error Not flying'
                    else:
                        return 'error Out of range'
                except ValueError:
                    return 'error Invalid argument'
            return 'error Invalid argument'

        # Handle query commands
        elif cmd.endswith('?'):
            if cmd in self.command_responses:
                response = self.command_responses[cmd]
                if callable(response):
                    return response()
                return str(response)
            return 'error Unknown command'

        # Handle other commands with known responses
        elif cmd in self.command_responses:
            response = self.command_responses[cmd]
            if callable(response):
                return response()
            return str(response)

        # Unknown command
        else:
            return 'error Unknown command'

    def _simulate_movement(self, direction: str, distance: int):
        """Simulate movement by updating drone state"""
        # Update position based on direction
        if direction == 'up':
            self.state['h'] = min(self.state['h'] + distance, 500)
        elif direction == 'down':
            self.state['h'] = max(self.state['h'] - distance, 0)
            if self.state['h'] == 0:
                self.is_flying = False
        elif direction == 'left':
            self.state['x'] = max(self.state['x'] - distance, -500)
        elif direction == 'right':
            self.state['x'] = min(self.state['x'] + distance, 500)
        elif direction == 'forward':
            self.state['y'] = min(self.state['y'] + distance, 500)
        elif direction == 'back':
            self.state['y'] = max(self.state['y'] - distance, -500)

        # Predictable battery drain (1% per movement command)
        self.state['bat'] = max(0, self.state['bat'] - 1)

    def _simulate_rotation(self, direction: str, angle: int):
        """Simulate rotation by updating yaw"""
        if direction == 'cw':
            self.state['yaw'] = (self.state['yaw'] + angle) % 360
        elif direction == 'ccw':
            self.state['yaw'] = (self.state['yaw'] - angle) % 360

        # Predictable battery drain (1% per rotation command)
        self.state['bat'] = max(0, self.state['bat'] - 1)

    def _state_broadcaster(self):
        """Broadcast state information periodically"""
        self.logger.info("State broadcaster started")

        while self.running:
            try:
                if self.sdk_mode and self.client_addresses:
                    # Build state string
                    state_str = self._build_state_string()

                    # Send to all known client addresses on the state port
                    for client_addr in list(self.client_addresses):
                        try:
                            # Send state to client's host on state port
                            state_addr = (client_addr[0], self.STATE_PORT)
                            self.state_socket.sendto(
                                state_str.encode('ascii'), state_addr
                            )
                        except Exception:
                            # Remove failed addresses
                            self.client_addresses.discard(client_addr)

                # Update dynamic state values
                self._update_dynamic_state()

                # Sleep for 0.1 seconds (10Hz update rate like real Tello)
                time.sleep(0.1)

            except Exception as e:
                if self.running:
                    self.logger.error("Error in state broadcaster: %s", e)

    def _build_state_string(self) -> str:
        """Build the state string in Tello format"""
        state_parts = []
        for key, value in self.state.items():
            if key in ['templ', 'temph']:
                # Temperature should be integers
                state_parts.append(f"{key}:{int(value)}")
            elif isinstance(value, float):
                state_parts.append(f"{key}:{value:.2f}")
            else:
                state_parts.append(f"{key}:{value}")

        return ';'.join(state_parts) + ';\r\n'

    def _update_dynamic_state(self):
        """Update state values that change over time"""
        # Increment flight time if flying
        if self.is_flying:
            self.state['time'] += 1

        # Keep temperature and barometer values stable
        # No random variations - maintain consistent sensor readings
        # Battery only drains on commands, not over time

    def _force_state_broadcast(self):
        """Force immediate state broadcast after reset"""
        if self.sdk_mode and self.client_addresses:
            state_str = self._build_state_string()
            for client_addr in list(self.client_addresses):
                try:
                    state_addr = (client_addr[0], self.STATE_PORT)
                    self.state_socket.sendto(state_str.encode('ascii'), state_addr)
                except Exception:
                    self.client_addresses.discard(client_addr)
            self.logger.info("🔄 Forced state broadcast after reset")


def main():
    """Main function to run mock drones"""
    import argparse

    parser = argparse.ArgumentParser(description='Mock Tello Drone Simulator')
    parser.add_argument('--ip', default='127.0.0.1',
                        help='IP address to bind to (default: 127.0.0.1)')
    parser.add_argument('--name', default='MockTello',
                        help='Name for this drone instance')
    parser.add_argument('--multiple', type=int,
                        help='Number of drones to create on sequential IPs')
    parser.add_argument('--port', type=int, default=8889,
                        help='Command port to bind to (default: 8889)')

    args = parser.parse_args()

    drones = []

    try:
        if args.multiple:
            # Create multiple drones on sequential IPs
            base_ip_parts = args.ip.split('.')
            base_ip_int = int(base_ip_parts[-1])

            for i in range(args.multiple):
                ip_parts = base_ip_parts[:-1] + [str(base_ip_int + i)]
                drone_ip = '.'.join(ip_parts)
                drone_name = f"{args.name}-{i+1}"
                # Use sequential ports for multiple drones
                port = args.port + i

                drone = MockTelloDrone(drone_ip, drone_name, port)
                if drone.start():
                    drones.append(drone)
                    print(f"Started drone {drone_name} on {drone_ip}:{port}")
                else:
                    msg = f"Failed to start drone {drone_name} on {drone_ip}:{port}"
                    print(msg)
        else:
            # Create single drone
            drone = MockTelloDrone(args.ip, args.name, args.port)
            if drone.start():
                drones.append(drone)
                print(f"Started drone {args.name} on {args.ip}:{args.port}")
            else:
                msg = f"Failed to start drone {args.name} on {args.ip}:{args.port}"
                print(msg)
                return

        if not drones:
            print("No drones started successfully")
            return

        print("\nMock Tello drone(s) running. Press Ctrl+C to stop.")
        print("Listening for commands on port 8889")
        print("Broadcasting state on port 8890")

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for drone in drones:
            drone.stop()


if __name__ == '__main__':
    main()
