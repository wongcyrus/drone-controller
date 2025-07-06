#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced port configuration features in djitellopy.
"""

import sys
import os

# Add the parent directory to the path so we can import djitellopy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from djitellopy import Tello

def test_port_configuration():
    """Test the new port configuration features."""

    print("Testing enhanced port configuration features...")

    # Test 1: Default initialization
    print("\n1. Testing default initialization:")
    tello1 = Tello()
    config = tello1.get_port_configuration()
    print(f"Default ports: {config}")

    # Test 2: Custom port initialization
    print("\n2. Testing custom port initialization:")
    try:
        tello2 = Tello(
            host='192.168.10.1',
            control_udp=8890,  # Custom control port
            state_udp=8891,    # Custom state port
            vs_udp=11112       # Custom video port
        )
        config2 = tello2.get_port_configuration()
        print(f"Custom ports: {config2}")
        print("✓ Custom port initialization successful")
    except Exception as e:
        print(f"✗ Custom port initialization failed: {e}")

    # Test 3: Dynamic port configuration
    print("\n3. Testing dynamic port configuration:")
    try:
        # Set individual ports
        tello1.set_control_port(8892)
        tello1.set_state_port(8893)
        tello1.set_video_port(11113)

        config3 = tello1.get_port_configuration()
        print(f"Updated ports: {config3}")
        print("✓ Dynamic port configuration successful")
    except Exception as e:
        print(f"✗ Dynamic port configuration failed: {e}")

    # Test 4: Backward compatibility with change_vs_udp
    print("\n4. Testing backward compatibility:")
    try:
        tello1.change_vs_udp(11114)
        config4 = tello1.get_port_configuration()
        print(f"After change_vs_udp: video_port = {config4['video_port']}")
        print("✓ Backward compatibility maintained")
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")

    print("\n" + "="*50)
    print("Port configuration enhancement tests completed!")
    print("="*50)

if __name__ == "__main__":
    test_port_configuration()
