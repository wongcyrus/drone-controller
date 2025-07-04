#!/usr/bin/env python3
"""
Start the Tello UDP Simulator with pre-configured drones.

This script starts the simulator with drone configurations that match
the main application's configuration file.
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.udp_simulator import TelloSimulator


def start_simulator_with_config():
    """Start simulator with drones from config."""

    # Pre-configured drones that match the main app's config
    drone_configs = [
        ("drone_001", 1),
        ("drone_002", 2),
        ("drone_003", 3),
        ("alpha", 4),
        ("beta", 5),
        ("gamma", 6),
        ("delta", 7),
    ]

    print("🚁 Starting Tello UDP Simulator with Pre-configured Drones")
    print("=" * 60)

    simulator = TelloSimulator("192.168.10", 1)

    # Add configured drones
    for drone_id, host_num in drone_configs:
        simulator.add_drone(drone_id, host_num)

    print("\n📋 Available Simulated Drones:")
    print("   • drone_001 at 192.168.10.1")
    print("   • drone_002 at 192.168.10.2")
    print("   • drone_003 at 192.168.10.3")
    print("   • alpha at 192.168.10.4")
    print("   • beta at 192.168.10.5")
    print("   • gamma at 192.168.10.6")
    print("   • delta at 192.168.10.7")

    print("\n💡 Usage in your drone application:")
    single_cmd = "python main.py --mode single --drone-id drone_001"
    print(f"   {single_cmd} --ip 192.168.10.1")
    print("   python main.py --mode swarm")  # Will auto-load from config

    try:
        simulator.start()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        simulator.stop()
        print("\n👋 Simulator stopped")


if __name__ == "__main__":
    start_simulator_with_config()
