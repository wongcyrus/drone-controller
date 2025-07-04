#!/usr/bin/env python3
"""
Simple Mock Tello Drone - Fixed Version

This version correctly simulates how a real Tello drone communicates over UDP.
"""

import socket
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class SimpleMockTello:
    """Simplified mock Tello that works correctly with djitellopy"""

    def __init__(self, bind_ip='0.0.0.0', bind_port=8889):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.running = False
        self.socket = None
        self.thread = None

        # Drone state
        self.battery = 100
        self.height = 0
        self.is_flying = False
        self.sdk_mode = False

        self.logger = logging.getLogger("SimpleMockTello")

    def start(self):
        """Start the mock drone server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allow port reuse
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.bind_ip, self.bind_port))

            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

            self.logger.info(f"Mock Tello started on {self.bind_ip}:{self.bind_port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start: {e}")
            return False

    def stop(self):
        """Stop the mock drone server"""
        self.running = False
        if self.socket:
            self.socket.close()
        self.logger.info("Mock Tello stopped")

    def _run(self):
        """Main server loop"""
        while self.running:
            try:
                data, client_addr = self.socket.recvfrom(1024)
                command = data.decode('utf-8').strip().lower()

                self.logger.info(f"Received '{command}' from {client_addr}")

                # Process command
                response = self._process_command(command)

                # Send response
                if response:
                    self.socket.sendto(response.encode('utf-8'), client_addr)
                    self.logger.info(f"Sent '{response}' to {client_addr}")

            except Exception as e:
                if self.running:
                    self.logger.error(f"Error: {e}")

    def _process_command(self, command):
        """Process a command and return response"""
        if command == 'command':
            self.sdk_mode = True
            return 'ok'
        elif command == 'takeoff':
            if self.sdk_mode:
                self.is_flying = True
                self.height = 50
                return 'ok'
            return 'error'
        elif command == 'land':
            if self.sdk_mode:
                self.is_flying = False
                self.height = 0
                return 'ok'
            return 'error'
        elif command.startswith('up '):
            if self.sdk_mode and self.is_flying:
                try:
                    distance = int(command.split()[1])
                    if 20 <= distance <= 500:
                        self.height += distance
                        return 'ok'
                except:
                    pass
            return 'error'
        elif command.startswith('cw '):
            if self.sdk_mode and self.is_flying:
                try:
                    angle = int(command.split()[1])
                    if 1 <= angle <= 360:
                        return 'ok'
                except:
                    pass
            return 'error'
        elif command == 'battery?':
            return str(self.battery)
        elif command == 'height?':
            return str(self.height)
        else:
            return 'error'


def main():
    """Test the simple mock drone"""
    # For testing on same machine, use a different port
    # In real usage, this would run on port 8889 on the drone's IP
    mock = SimpleMockTello('127.0.0.1', 8889)

    if mock.start():
        print("Mock Tello started! Try running your djitellopy code now.")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            mock.stop()
    else:
        print("Failed to start mock Tello")


if __name__ == "__main__":
    main()
