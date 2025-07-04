#!/usr/bin/env python3
"""
Simple test to debug djitellopy communication with mock drone
"""
import socket
import time

def test_manual_tello_communication():
    """Test direct UDP communication with mock Tello"""
    print("Testing manual Tello communication...")

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5.0)

    try:
        # Send command to mock drone
        command = "command"
        drone_address = ("192.168.221.1", 8889)  # Use VMware network IP

        print(f"Sending '{command}' to {drone_address}")
        sock.sendto(command.encode('utf-8'), drone_address)

        # Wait for response
        print("Waiting for response...")
        response, addr = sock.recvfrom(1024)
        response_str = response.decode('utf-8').strip()

        print(f"Received response from {addr}: '{response_str}'")

        # Test another command
        time.sleep(1)
        command = "battery?"
        print(f"Sending '{command}' to {drone_address}")
        sock.sendto(command.encode('utf-8'), drone_address)

        response, addr = sock.recvfrom(1024)
        response_str = response.decode('utf-8').strip()
        print(f"Received response from {addr}: '{response_str}'")

    except socket.timeout:
        print("Timeout - no response received")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

def test_djitellopy():
    """Test djitellopy library communication"""
    print("\nTesting djitellopy communication...")

    try:
        from djitellopy import Tello

        # Create Tello instance
        tello = Tello("192.168.221.1")  # Use VMware network IP

        print("Connecting to Tello...")
        tello.connect()

        print("Getting battery...")
        battery = tello.get_battery()
        print(f"Battery: {battery}%")

    except Exception as e:
        print(f"djitellopy error: {e}")

if __name__ == "__main__":
    test_manual_tello_communication()
    test_djitellopy()
