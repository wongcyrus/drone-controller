#!/usr/bin/env python3
"""
Enhanced Mock Tello Drone with WebSocket Integration

This enhanced version of the mock drone integrates with the WebSocket server
to provide real-time visualization and control through the webapp.
"""

import sys
import os
import asyncio
import threading
import time

# Import from the same directory - handle both relative and absolute imports
try:
    from mock_tello_drone import MockTelloDrone
except ImportError:
    from .mock_tello_drone import MockTelloDrone
try:
    from websocket_server import start_websocket_server, ws_server
except ImportError:
    from .websocket_server import start_websocket_server, ws_server


class EnhancedMockTelloDrone(MockTelloDrone):
    """Enhanced Mock Tello drone with WebSocket integration"""

    def __init__(self, drone_ip: str = "127.0.0.1",
                 name: str = "MockTello",
                 command_port: int = None):
        super().__init__(drone_ip, name, command_port)
        self.ws_server = None
        self.webapp_enabled = True

    def start(self):
        """Start the mock drone with WebSocket integration"""
        # Start the base mock drone
        if not super().start():
            return False

        # Register with WebSocket server if enabled
        if self.webapp_enabled:
            self.register_with_webapp()

        return True

    def stop(self):
        """Stop the mock drone and unregister from WebSocket"""
        if self.webapp_enabled:
            self.unregister_from_webapp()

        super().stop()

    def register_with_webapp(self):
        """Register this drone with the WebSocket server"""
        try:
            if ws_server and ws_server.loop and ws_server.loop.is_running():
                drone_info = {
                    'name': self.name,
                    'ip': self.drone_ip,
                    'port': self.command_port,
                    'connected': True,
                    'state': self.state.copy()
                }
                ws_server.register_drone(self.name, drone_info)
                self.logger.info(f"Registered {self.name} with webapp")
            else:
                self.logger.warning(f"WebSocket server not ready, skipping registration for {self.name}")
        except Exception as e:
            self.logger.error(f"Failed to register with webapp: {e}")

    def unregister_from_webapp(self):
        """Unregister this drone from the WebSocket server"""
        try:
            if ws_server and ws_server.loop and ws_server.loop.is_running():
                ws_server.unregister_drone(self.name)
                self.logger.info(f"Unregistered {self.name} from webapp")
        except Exception as e:
            self.logger.error(f"Failed to unregister from webapp: {e}")

    def _process_command(self, command: str) -> str:
        """Enhanced command processing with webapp notifications"""
        # Process command with base implementation
        response = super()._process_command(command)

        # Notify webapp of command execution
        if self.webapp_enabled:
            try:
                if ws_server and ws_server.loop and ws_server.loop.is_running():
                    ws_server.notify_command_executed(self.name, command, response)
            except Exception as e:
                self.logger.error(f"Failed to notify webapp of command: {e}")

        return response

    def _simulate_movement(self, direction: str, distance: int):
        """Enhanced movement simulation with webapp updates"""
        super()._simulate_movement(direction, distance)
        self.update_webapp_state()

    def _simulate_rotation(self, direction: str, angle: int):
        """Enhanced rotation simulation with webapp updates"""
        super()._simulate_rotation(direction, angle)
        self.update_webapp_state()

    def update_webapp_state(self):
        """Update the webapp with current drone state"""
        if self.webapp_enabled:
            try:
                if ws_server and ws_server.loop and ws_server.loop.is_running():
                    ws_server.update_drone_state(self.name, self.state.copy())
            except Exception as e:
                self.logger.error(f"Failed to update webapp state: {e}")

    def _state_broadcaster(self):
        """Enhanced state broadcaster that also updates webapp"""
        self.logger.info("Enhanced state broadcaster started")

        while self.running:
            try:
                # Run base state broadcasting
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

                # Update webapp with new state
                self.update_webapp_state()

                # Sleep for 0.1 seconds (10Hz update rate like real Tello)
                time.sleep(0.1)

            except Exception as e:
                if self.running:
                    self.logger.error("Error in enhanced state broadcaster: %s", e)


def create_multi_drone_system(num_drones=3, start_ip="127.0.0.1", webapp_port=8765, web_port=8000, host='0.0.0.0'):
    """Create a system with multiple drones and webapp"""

    print(f"Starting WebSocket server on {host}:{webapp_port}...")
    ws_result = start_websocket_server(host, webapp_port)
    
    if not ws_result:
        print(f"⚠️  WebSocket server failed to start on port {webapp_port}")
        print("   Continuing without webapp integration...")
        webapp_enabled = False
    else:
        print("✅ WebSocket server started successfully")
        webapp_enabled = True

    if webapp_enabled:
        print(f"Starting web server on port {web_port}...")
        from web_server import run_web_server

        # Start web server in a separate thread
        web_thread = threading.Thread(
            target=run_web_server,
            args=(host, web_port, False),
            daemon=True
        )
        web_thread.start()
        print("✅ Web server started successfully")

    print(f"Creating {num_drones} virtual drones...")
    drones = []

    # Parse base IP
    ip_parts = start_ip.split('.')
    base_ip_int = int(ip_parts[-1])

    for i in range(num_drones):
        # Create sequential IP addresses
        ip_parts[-1] = str(base_ip_int + i)
        drone_ip = '.'.join(ip_parts)

        # Create sequential ports
        port = 8889 + i

        drone_name = f"Drone-{i+1}"

        try:
            drone = EnhancedMockTelloDrone(drone_ip, drone_name, port)
            drone.webapp_enabled = webapp_enabled  # Set webapp status
            if drone.start():
                drones.append(drone)
                print(f"✅ Started {drone_name} on {drone_ip}:{port}")
            else:
                print(f"❌ Failed to start {drone_name} on {drone_ip}:{port}")
        except Exception as e:
            print(f"❌ Error creating {drone_name}: {e}")

    return drones


def main():
    """Main function with enhanced options"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced Mock Tello Drone Simulator with WebApp'
    )
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host to bind servers to (default: 0.0.0.0 for external access)')
    parser.add_argument('--ip', default='127.0.0.1',
                        help='IP address to bind drones to (default: 127.0.0.1)')
    parser.add_argument('--name', default='MockTello',
                        help='Name for this drone instance')
    parser.add_argument('--multiple', type=int,
                        help='Number of drones to create on sequential IPs')
    parser.add_argument('--port', type=int, default=8889,
                        help='Command port to bind to (default: 8889)')
    parser.add_argument('--webapp-port', type=int, default=8766,
                        help='WebSocket server port (default: 8766)')
    parser.add_argument('--web-port', type=int, default=8000,
                        help='Web server port (default: 8000)')
    parser.add_argument('--no-webapp', action='store_true',
                        help='Disable webapp integration')

    args = parser.parse_args()

    if args.no_webapp:
        # Use original MockTelloDrone
        print("Running without webapp integration...")
        from mock_tello_drone import main as original_main
        original_main()
        return

    print("🚁 Enhanced Drone Simulator with WebApp")
    print("=" * 50)

    if args.multiple:
        # Multi-drone system
        drones = create_multi_drone_system(
            args.multiple,
            args.ip,
            args.webapp_port,
            args.web_port,
            args.host
        )

        if not drones:
            print("❌ No drones started successfully")
            return

        print(f"\n✅ Started {len(drones)} drones successfully!")

    else:
        # Single drone
        print(f"Starting WebSocket server on {args.host}:{args.webapp_port}...")
        ws_result = start_websocket_server(args.host, args.webapp_port)
        
        if not ws_result:
            print(f"⚠️  WebSocket server failed to start on port {args.webapp_port}")
            print("   Continuing without webapp integration...")
            webapp_enabled = False
        else:
            print("✅ WebSocket server started successfully")
            webapp_enabled = True

        if webapp_enabled:
            print(f"Starting web server on port {args.web_port}...")
            from web_server import run_web_server
            web_thread = threading.Thread(
                target=run_web_server,
                args=(args.host, args.web_port, False),
                daemon=True
            )
            web_thread.start()
            print("✅ Web server started successfully")

        drone = EnhancedMockTelloDrone(args.ip, args.name, args.port)
        drone.webapp_enabled = webapp_enabled  # Set webapp status
        if drone.start():
            drones = [drone]
            print(f"✅ Started {args.name} on {args.ip}:{args.port}")
        else:
            print(f"❌ Failed to start {args.name}")
            return

    print("\n🌐 WebApp URLs:")
    if args.host == '0.0.0.0':
        print(f"   Main Interface: http://localhost:{args.web_port} (from WSL)")
        print(f"   Main Interface: http://<WSL-IP>:{args.web_port} (from Windows)")
        print(f"   WebSocket: ws://localhost:{args.webapp_port} (from WSL)")
        print(f"   WebSocket: ws://<WSL-IP>:{args.webapp_port} (from Windows)")
    else:
        print(f"   Main Interface: http://{args.host}:{args.web_port}")
        print(f"   WebSocket: ws://{args.host}:{args.webapp_port}")

    print("\n📡 UDP Endpoints:")
    for i, drone in enumerate(drones):
        print(f"   {drone.name}: {drone.drone_ip}:{drone.command_port}")

    print("\n📋 Instructions:")
    print("1. Open the web interface in your browser")
    print("2. Click 'Connect' to connect to the WebSocket server")
    print("3. Select a drone from the list or add virtual drones")
    print("4. Use the manual controls or send custom commands")
    print("5. Watch the 3D visualization respond to commands")

    print("\n🎮 You can also control drones via:")
    print("   - djitellopy library")
    print("   - Any UDP client sending to the drone ports")
    print("   - The webapp interface")

    print(f"\n🚁 {len(drones)} drone(s) running. Press Ctrl+C to stop.")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        for drone in drones:
            drone.stop()
        print("✅ All drones stopped")


if __name__ == '__main__':
    main()
