#!/usr/bin/env python3
"""
Drone Simulator Launcher

This script launches the complete drone simulator system including:
- Multiple mock drones
- WebSocket server for real-time communication
- Flask web server for the HTML interface
- Three.js 3D visualization

Usage:
    python drone_simulator.py                    # Start with default settings
    python drone_simulator.py --drones 5        # Start with 5 virtual drones
    python drone_simulator.py --help            # Show all options
"""

import sys
import os
import time
import threading
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s - %(message)s'
)

# Import required modules
from mock_tello_drone import MockTelloDrone


class DroneSimulatorLauncher:
    """Main launcher for the drone simulator system"""

    def __init__(self, config=None):
        self.config = config or {}
        self.drones = []
        self.ws_server = None
        self.web_server_thread = None
        self.running = False

    def start_websocket_server(self):
        """Start the WebSocket server"""
        try:
            from webapp.websocket_server import start_websocket_server
            port = self.config.get('websocket_port', 8765)
            host = self.config.get('host', 'localhost')

            print(f"🔌 Starting WebSocket server on {host}:{port}...")
            self.ws_server = start_websocket_server(host, port)
            time.sleep(1)  # Give it time to start
            print(f"✅ WebSocket server started")
            return True
        except ImportError:
            print("❌ WebSocket server dependencies not available")
            print("   Install with: pip install websockets")
            return False
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")
            return False

    def start_web_server(self):
        """Start the Flask web server"""
        try:
            from webapp.web_server import run_web_server
            port = self.config.get('web_port', 8000)
            host = self.config.get('host', 'localhost')

            print(f"🌐 Starting web server on {host}:{port}...")

            self.web_server_thread = threading.Thread(
                target=run_web_server,
                args=(host, port, False),
                daemon=True
            )
            self.web_server_thread.start()
            time.sleep(1)  # Give it time to start
            print(f"✅ Web server started")
            return True
        except ImportError:
            print("❌ Web server dependencies not available")
            print("   Install with: pip install flask")
            return False
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            return False

    def create_drones(self):
        """Create mock drones"""
        num_drones = self.config.get('num_drones', 3)
        start_ip = self.config.get('start_ip', '127.0.0.1')
        start_port = self.config.get('start_port', 8889)

        print(f"🚁 Creating {num_drones} mock drones...")

        # Parse base IP
        ip_parts = start_ip.split('.')
        base_ip_int = int(ip_parts[-1])

        for i in range(num_drones):
            try:
                # Create sequential IP addresses and ports
                ip_parts[-1] = str(base_ip_int + i)
                drone_ip = '.'.join(ip_parts)
                port = start_port + i
                drone_name = f"Drone-{i+1}"

                # Try to import enhanced drone, fall back to basic if not available
                try:
                    from enhanced_mock_drone import EnhancedMockTelloDrone
                    drone = EnhancedMockTelloDrone(drone_ip, drone_name, port)
                except ImportError:
                    print(f"⚠️  Enhanced drone not available, using basic drone")
                    drone = MockTelloDrone(drone_ip, drone_name, port)

                if drone.start():
                    self.drones.append(drone)
                    print(f"✅ Started {drone_name} on {drone_ip}:{port}")
                else:
                    print(f"❌ Failed to start {drone_name} on {drone_ip}:{port}")

            except Exception as e:
                print(f"❌ Error creating drone {i+1}: {e}")

        return len(self.drones) > 0

    def start(self):
        """Start the complete drone simulator system"""
        print("🚁 Drone Simulator with WebApp")
        print("=" * 50)

        self.running = True
        success = True

        # Start WebSocket server
        if not self.start_websocket_server():
            success = False

        # Start web server
        if not self.start_web_server():
            success = False

        # Create and start drones
        if not self.create_drones():
            print("❌ No drones started successfully")
            success = False

        if not success:
            print("\n⚠️  Some components failed to start.")
            print("   The system may still be partially functional.")

        return success

    def stop(self):
        """Stop all components"""
        print("\n🛑 Shutting down drone simulator...")
        self.running = False

        # Stop all drones
        for drone in self.drones:
            try:
                drone.stop()
            except Exception as e:
                print(f"Error stopping drone: {e}")

        print("✅ All components stopped")

    def print_status(self):
        """Print system status and URLs"""
        if not self.running:
            return

        web_port = self.config.get('web_port', 8000)
        ws_port = self.config.get('websocket_port', 8765)
        host = self.config.get('host', 'localhost')

        print(f"\n✅ Drone Simulator System Running!")
        print(f"   Drones: {len(self.drones)} active")

        print(f"\n🌐 WebApp URLs:")
        print(f"   Main Interface: http://{host}:{web_port}")
        print(f"   WebSocket: ws://{host}:{ws_port}")

        print(f"\n📡 Drone UDP Endpoints:")
        for drone in self.drones:
            print(f"   {drone.name}: {drone.drone_ip}:{drone.command_port}")

        print(f"\n📋 Quick Start:")
        print(f"1. Open http://{host}:{web_port} in your browser")
        print(f"2. Click 'Connect' to connect to WebSocket")
        print(f"3. Select a drone and use the controls")
        print(f"4. Watch the 3D visualization!")

        print(f"\n🎮 Control Methods:")
        print(f"   - Web interface (recommended)")
        print(f"   - djitellopy library")
        print(f"   - Direct UDP commands")

        print(f"\n🚁 Press Ctrl+C to stop all drones")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Complete Drone Simulator with 3D WebApp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python drone_simulator.py
  python drone_simulator.py --drones 5 --web-port 8080
  python drone_simulator.py --host 0.0.0.0 --drones 1
        """
    )

    parser.add_argument('--drones', type=int, default=3,
                        help='Number of drones to create (default: 3)')
    parser.add_argument('--host', default='localhost',
                        help='Host to bind servers to (default: localhost)')
    parser.add_argument('--start-ip', default='127.0.0.1',
                        help='Starting IP for drones (default: 127.0.0.1)')
    parser.add_argument('--start-port', type=int, default=8889,
                        help='Starting port for drones (default: 8889)')
    parser.add_argument('--web-port', type=int, default=8000,
                        help='Web server port (default: 8000)')
    parser.add_argument('--websocket-port', type=int, default=8765,
                        help='WebSocket server port (default: 8765)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Create configuration
    config = {
        'num_drones': args.drones,
        'host': args.host,
        'start_ip': args.start_ip,
        'start_port': args.start_port,
        'web_port': args.web_port,
        'websocket_port': args.websocket_port,
    }

    # Create and start launcher
    launcher = DroneSimulatorLauncher(config)

    try:
        if launcher.start():
            launcher.print_status()

            # Keep running until interrupted
            while launcher.running:
                time.sleep(1)
        else:
            print("\n❌ Failed to start drone simulator")
            sys.exit(1)

    except KeyboardInterrupt:
        pass
    finally:
        launcher.stop()


if __name__ == '__main__':
    main()
