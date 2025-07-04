#!/usr/bin/env python3
"""
Direct UDP test to understand Tello communication
"""

import socket
import time
import threading

def test_udp_communication():
    """Test direct UDP communication"""

    # Create client socket (like djitellopy does)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('', 8889))  # Bind to receive responses

    # Create mock drone socket
    drone_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    drone_socket.bind(('127.0.0.1', 8890))  # Use different port for mock

    def drone_listener():
        """Mock drone response handler"""
        while True:
            try:
                data, addr = drone_socket.recvfrom(1024)
                print(f"Mock drone received: {data.decode()} from {addr}")

                # Send response back
                response = b"ok"
                client_socket.sendto(response, addr)
                print(f"Mock drone sent response: {response.decode()} to {addr}")

            except Exception as e:
                print(f"Drone error: {e}")
                break

    # Start drone listener
    drone_thread = threading.Thread(target=drone_listener, daemon=True)
    drone_thread.start()

    time.sleep(1)

    # Send command to mock drone
    try:
        command = b"command"
        print(f"Client sending: {command.decode()} to 127.0.0.1:8890")
        client_socket.sendto(command, ('127.0.0.1', 8890))

        # Wait for response
        client_socket.settimeout(5)
        data, addr = client_socket.recvfrom(1024)
        print(f"Client received response: {data.decode()} from {addr}")

    except Exception as e:
        print(f"Client error: {e}")

    finally:
        client_socket.close()
        drone_socket.close()

if __name__ == "__main__":
    test_udp_communication()
