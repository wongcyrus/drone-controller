#!/usr/bin/env python3
"""
WebSocket Server for Drone Simulator

This server provides a WebSocket interface for the drone simulator webapp.
It integrates with the MockTelloDrone to provide real-time visual feedback
of drone commands and state.
"""

import asyncio
import websockets
import json
import logging
import threading
import time
from typing import Dict, Set, Any

# Configure logging to reduce websockets debug noise
logging.getLogger('websockets.server').setLevel(logging.INFO)
logging.getLogger('websockets.protocol').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class DroneWebSocketServer:
    """WebSocket server for drone simulator webapp"""

    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.drones: Dict[str, Any] = {}  # drone_id -> drone_info
        self.running = False
        self.loop = None  # Store the asyncio event loop
        self._message_queue = None  # Queue for cross-thread messages

    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        # Send current drone states to new client
        await self.send_initial_state(websocket)

    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def send_initial_state(self, websocket):
        """Send initial state to a newly connected client"""
        for drone_id, drone_info in self.drones.items():
            message = {
                'type': 'drone_state',
                'drone_id': drone_id,
                'data': drone_info['state']
            }
            await websocket.send(json.dumps(message))

    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.clients:
            message_str = json.dumps(message)
            disconnected = set()

            for client in self.clients:
                try:
                    await client.send(message_str)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    disconnected.add(client)

            # Remove disconnected clients
            for client in disconnected:
                self.clients.discard(client)

    async def handle_client_message(self, websocket, message_str):
        """Handle incoming message from client"""
        try:
            message = json.loads(message_str)
            message_type = message.get('type')

            if message_type == 'drone_command':
                await self.handle_drone_command(message)
            elif message_type == 'get_drones':
                await self.send_drone_list(websocket)
            elif message_type == 'ping':
                await websocket.send(json.dumps({'type': 'pong'}))

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message_str}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def handle_drone_command(self, message):
        """Handle drone command from webapp"""
        drone_id = message.get('drone_id')
        command = message.get('command')

        if drone_id in self.drones:
            # Forward command to actual drone (if needed)
            logger.info(f"Command for {drone_id}: {command}")

            # Broadcast command execution to all clients for visualization
            await self.broadcast_message({
                'type': 'command_executed',
                'drone_id': drone_id,
                'command': command,
                'timestamp': time.time()
            })

    async def send_drone_list(self, websocket):
        """Send list of available drones to client"""
        # Convert drone dictionary to array format expected by frontend
        drone_array = []
        for drone_id, drone_info in self.drones.items():
            drone_array.append({
                'id': drone_id,
                'name': drone_info.get('name', drone_id),
                'ip': drone_info.get('ip', ''),
                'port': drone_info.get('port', 0),
                'connected': drone_info.get('connected', False),
                'state': drone_info.get('state', {})
            })
        
        drone_list = {
            'type': 'drone_list',
            'drones': drone_array
        }
        logger.info(f"Sending drone list to client: {[d['id'] for d in drone_array]}")
        await websocket.send(json.dumps(drone_list))

    async def handle_client(self, websocket):
        """Handle a WebSocket client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    def _schedule_message(self, message: dict):
        """Schedule a message to be broadcast from a non-async context"""
        if self.loop and self.loop.is_running():
            # We're in a different thread, schedule the coroutine safely
            asyncio.run_coroutine_threadsafe(
                self.broadcast_message(message), self.loop
            )
        else:
            # No event loop running, queue the message
            logger.warning("No event loop running, message queued")

    def register_drone(self, drone_id: str, drone_info: dict):
        """Register a drone with the WebSocket server"""
        self.drones[drone_id] = drone_info
        logger.info("Drone registered: %s", drone_id)
        logger.debug("Drone info: %s", drone_info)
        logger.info("Total drones registered: %d", len(self.drones))

        # Schedule broadcast message
        self._schedule_message({
            'type': 'drone_added',
            'drone_id': drone_id,
            'data': drone_info
        })

    def unregister_drone(self, drone_id: str):
        """Unregister a drone from the WebSocket server"""
        if drone_id in self.drones:
            del self.drones[drone_id]
            logger.info("Drone unregistered: %s", drone_id)

            # Schedule broadcast message
            self._schedule_message({
                'type': 'drone_removed',
                'drone_id': drone_id
            })

    def update_drone_state(self, drone_id: str, state: dict):
        """Update drone state and broadcast to clients"""
        if drone_id in self.drones:
            self.drones[drone_id]['state'] = state

            # Schedule broadcast message
            self._schedule_message({
                'type': 'drone_state',
                'drone_id': drone_id,
                'data': state
            })

    def notify_command_executed(self, drone_id: str, command: str,
                                response: str):
        """Notify clients that a command was executed"""
        logger.info("UDP Command executed - Drone: %s, Command: %s, Response: %s", 
                   drone_id, command, response)
        self._schedule_message({
            'type': 'command_result',
            'drone_id': drone_id,
            'command': command,
            'response': response,
            'timestamp': time.time()
        })

    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        self.loop = asyncio.get_event_loop()  # Store the event loop
        logger.info("Starting WebSocket server on %s:%d",
                    self.host, self.port)

        # Start the server with newer websockets API
        async with websockets.serve(self.handle_client, self.host, self.port) as server:
            logger.info("WebSocket server listening on ws://%s:%d",
                        self.host, self.port)
            
            # Signal that server is ready (if we have a ready event)
            if hasattr(self, '_server_ready_event'):
                self._server_ready_event.set()
            
            # Keep server running indefinitely
            await asyncio.Future()  # Run forever

    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        logger.info("WebSocket server stopped")


# Global WebSocket server instance
ws_server = DroneWebSocketServer()


def start_websocket_server(host='localhost', port=8765):
    """Start WebSocket server in a separate thread with better error handling"""
    # Update global server instance with provided host/port
    ws_server.host = host
    ws_server.port = port
    
    # Event to signal when server is ready
    server_ready = threading.Event()
    server_error = [None]  # Use list to allow modification in nested function
    
    # Add the ready event to the server instance
    ws_server._server_ready_event = server_ready

    def run_server():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Start the server
            loop.run_until_complete(ws_server.start_server())
        except OSError as e:
            server_error[0] = f"Port binding error: {e}"
            logger.error(f"WebSocket server failed to start: {e}")
            server_ready.set()  # Signal completion even on error
        except Exception as e:
            server_error[0] = f"Server error: {e}"
            logger.error(f"WebSocket server error: {e}")
            server_ready.set()  # Signal completion even on error

    # Start server thread
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for server to start (with timeout)
    if server_ready.wait(timeout=5):
        if server_error[0]:
            logger.error(f"WebSocket server startup failed: {server_error[0]}")
            return None
        else:
            logger.info(f"WebSocket server started on {host}:{port}")
            return ws_server
    else:
        logger.error("WebSocket server startup timed out")
        return None


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Drone WebSocket Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(ws_server.start_server())
    except KeyboardInterrupt:
        print("\nServer stopped")
