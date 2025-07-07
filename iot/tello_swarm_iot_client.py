"""
AWS IoT client for controlling Tello drone swarms
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List
import uuid

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import jsonschema

from .tello_action_executor import TelloSwarmActionExecutor

logger = logging.getLogger(__name__)


class TelloSwarmIoTClient:
    """AWS IoT client for controlling TelloSwarm via MQTT messages"""

    def __init__(
        self,
        client_id: str,
        endpoint: str,
        root_ca_path: str,
        private_key_path: str,
        certificate_path: str,
        swarm_id: str,
        drone_ips: List[str],
        schema_path: str = None
    ):
        """
        Initialize the TelloSwarmIoTClient

        Args:
            client_id: Unique client identifier
            endpoint: AWS IoT endpoint URL
            root_ca_path: Path to root CA certificate
            private_key_path: Path to private key file
            certificate_path: Path to device certificate
            swarm_id: Identifier for this drone swarm
            drone_ips: List of IP addresses for Tello drones
            schema_path: Optional path to JSON schema file
        """
        self.client_id = client_id
        self.swarm_id = swarm_id
        self.logger = logging.getLogger(__name__)

        # Initialize TelloSwarmActionExecutor
        self.action_executor = TelloSwarmActionExecutor(drone_ips, swarm_id)

        # MQTT topics
        self.command_topic = f"drone/swarm/{swarm_id}/command"
        self.response_topic = f"drone/swarm/{swarm_id}/response"
        self.status_topic = f"drone/swarm/{swarm_id}/status"
        self.emergency_topic = f"drone/swarm/{swarm_id}/emergency"
        self.telemetry_topic = f"drone/swarm/{swarm_id}/telemetry"

        # Initialize AWS IoT MQTT client
        self.mqtt_client = AWSIoTMQTTClient(client_id)
        self.mqtt_client.configureEndpoint(endpoint, 8883)
        self.mqtt_client.configureCredentials(root_ca_path, private_key_path, certificate_path)

        # Configure connection
        self.mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
        self.mqtt_client.configureOfflinePublishQueueing(-1)
        self.mqtt_client.configureDrainingFrequency(2)
        self.mqtt_client.configureConnectDisconnectTimeout(10)
        self.mqtt_client.configureMQTTOperationTimeout(5)

        # Load JSON schema for validation
        self.schema = None
        if schema_path:
            try:
                with open(schema_path, 'r') as f:
                    self.schema = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load schema: {e}")

        # Connection state
        self.is_connected = False

        # Start telemetry publishing
        self.telemetry_interval = 10  # seconds
        self._start_telemetry_publishing()

    def connect(self) -> bool:
        """Connect to AWS IoT and subscribe to command topics"""
        try:
            # Connect to AWS IoT
            self.mqtt_client.connect()
            self.is_connected = True
            self.logger.info(f"Connected to AWS IoT as {self.client_id}")

            # Subscribe to command topics
            self.mqtt_client.subscribe(self.command_topic, 1, self._on_command_received)
            self.mqtt_client.subscribe(self.emergency_topic, 1, self._on_emergency_received)

            self.logger.info(f"Subscribed to topics: {self.command_topic}, {self.emergency_topic}")

            # Connect to drone swarm
            if self.action_executor.connect():
                self.logger.info("Successfully connected to drone swarm")
                return True
            else:
                self.logger.error("Failed to connect to drone swarm")
                return False

        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from AWS IoT and shutdown"""
        try:
            self.mqtt_client.disconnect()
            self.action_executor.shutdown()
            self.is_connected = False
            self.logger.info("Disconnected from AWS IoT")
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")

    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """Validate incoming message against JSON schema"""
        if not self.schema:
            return True

        try:
            jsonschema.validate(message, self.schema)
            return True
        except jsonschema.ValidationError as e:
            self.logger.error(f"Message validation failed: {e}")
            return False

    def _on_command_received(self, client, userdata, message):
        """Handle incoming command messages"""
        try:
            payload = json.loads(message.payload.decode('utf-8'))
            self.logger.info(f"Received command: {payload}")

            # Validate message
            if not self._validate_message(payload):
                self._send_error_response(payload.get('message_id'), "Invalid message format")
                return

            # Process command based on type
            command_type = payload.get('command_type')

            if command_type == 'action':
                self._handle_action_command(payload)
            elif command_type == 'formation':
                self._handle_formation_command(payload)
            elif command_type == 'choreography':
                self._handle_choreography_command(payload)
            elif command_type == 'status_request':
                self._handle_status_request(payload)
            elif command_type == 'stream_control':
                self._handle_stream_control(payload)
            else:
                self._send_error_response(payload.get('message_id'), f"Unknown command type: {command_type}")

        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            self._send_error_response(None, str(e))

    def _on_emergency_received(self, client, userdata, message):
        """Handle emergency stop messages"""
        try:
            payload = json.loads(message.payload.decode('utf-8'))
            self.logger.warning(f"Emergency command received: {payload}")

            # Immediate emergency stop
            self.action_executor.emergency_stop()

            # Send emergency response
            response = {
                "message_id": payload.get('message_id'),
                "response_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "swarm_id": self.swarm_id,
                "status": "emergency_executed",
                "execution_time": 0.0,
                "message": "Emergency stop executed immediately"
            }

            self._publish_response(response)

        except Exception as e:
            self.logger.error(f"Error processing emergency command: {e}")

    def _handle_action_command(self, payload: Dict[str, Any]):
        """Handle basic action commands"""
        try:
            action = payload.get('action', {})
            action_name = action.get('name')
            target_drones = payload.get('target_drones', 'all')

            # Add action to queue
            action_id = self.action_executor.add_action_to_queue(action_name, target_drones)

            # Send acknowledgment
            response = {
                "message_id": payload.get('message_id'),
                "response_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "swarm_id": self.swarm_id,
                "status": "accepted",
                "action_id": action_id,
                "message": f"Action '{action_name}' queued for execution"
            }

            self._publish_response(response)

        except Exception as e:
            self.logger.error(f"Error handling action command: {e}")
            self._send_error_response(payload.get('message_id'), str(e))

    def _handle_formation_command(self, payload: Dict[str, Any]):
        """Handle formation commands"""
        try:
            formation = payload.get('formation', {})
            formation_type = formation.get('type')

            # Map formation types to action names
            formation_actions = {
                'line': 'formation_line',
                'circle': 'formation_circle',
                'diamond': 'formation_diamond'
            }

            action_name = formation_actions.get(formation_type)
            if not action_name:
                self._send_error_response(payload.get('message_id'), f"Unsupported formation type: {formation_type}")
                return

            target_drones = payload.get('target_drones', 'all')
            action_id = self.action_executor.add_action_to_queue(action_name, target_drones)

            response = {
                "message_id": payload.get('message_id'),
                "response_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "swarm_id": self.swarm_id,
                "status": "accepted",
                "action_id": action_id,
                "message": f"Formation '{formation_type}' queued for execution"
            }

            self._publish_response(response)

        except Exception as e:
            self.logger.error(f"Error handling formation command: {e}")
            self._send_error_response(payload.get('message_id'), str(e))

    def _handle_choreography_command(self, payload: Dict[str, Any]):
        """Handle choreography commands"""
        try:
            choreography = payload.get('choreography', {})
            sequence_name = choreography.get('sequence_name')

            # For now, map to predefined dance sequences
            dance_actions = {
                'spiral_dance': 'dance_sequence_1',
                'synchronized_dance': 'dance_sequence_2'
            }

            action_name = dance_actions.get(sequence_name, 'dance_sequence_1')
            target_drones = payload.get('target_drones', 'all')
            action_id = self.action_executor.add_action_to_queue(action_name, target_drones)

            response = {
                "message_id": payload.get('message_id'),
                "response_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "swarm_id": self.swarm_id,
                "status": "accepted",
                "action_id": action_id,
                "message": f"Choreography '{sequence_name}' queued for execution"
            }

            self._publish_response(response)

        except Exception as e:
            self.logger.error(f"Error handling choreography command: {e}")
            self._send_error_response(payload.get('message_id'), str(e))

    def _handle_status_request(self, payload: Dict[str, Any]):
        """Handle status request commands"""
        try:
            status = self.action_executor.get_swarm_status()

            response = {
                "message_id": payload.get('message_id'),
                "response_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "swarm_id": self.swarm_id,
                "status": "success",
                "swarm_status": status
            }

            # Publish to status topic
            self.mqtt_client.publish(self.status_topic, json.dumps(response), 1)

        except Exception as e:
            self.logger.error(f"Error handling status request: {e}")
            self._send_error_response(payload.get('message_id'), str(e))

    def _handle_stream_control(self, payload: Dict[str, Any]):
        """Handle video stream control commands"""
        try:
            action = payload.get('action', {})
            action_name = action.get('name')
            target_drones = payload.get('target_drones', 'all')

            if action_name in ['stream_on', 'stream_off']:
                action_id = self.action_executor.add_action_to_queue(action_name, target_drones)

                response = {
                    "message_id": payload.get('message_id'),
                    "response_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat() + 'Z',
                    "swarm_id": self.swarm_id,
                    "status": "accepted",
                    "action_id": action_id,
                    "message": f"Stream control '{action_name}' queued for execution"
                }

                self._publish_response(response)
            else:
                self._send_error_response(payload.get('message_id'), f"Invalid stream action: {action_name}")

        except Exception as e:
            self.logger.error(f"Error handling stream control: {e}")
            self._send_error_response(payload.get('message_id'), str(e))

    def _send_error_response(self, message_id: str, error_message: str):
        """Send error response"""
        response = {
            "message_id": message_id,
            "response_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "swarm_id": self.swarm_id,
            "status": "error",
            "error": error_message
        }

        self._publish_response(response)

    def _publish_response(self, response: Dict[str, Any]):
        """Publish response to response topic"""
        try:
            self.mqtt_client.publish(self.response_topic, json.dumps(response), 1)
        except Exception as e:
            self.logger.error(f"Failed to publish response: {e}")

    def _start_telemetry_publishing(self):
        """Start background thread for publishing telemetry data"""
        def telemetry_worker():
            while self.is_connected:
                try:
                    if self.action_executor.is_connected:
                        status = self.action_executor.get_swarm_status()

                        telemetry = {
                            "timestamp": datetime.utcnow().isoformat() + 'Z',
                            "swarm_id": self.swarm_id,
                            "telemetry": status
                        }

                        self.mqtt_client.publish(self.telemetry_topic, json.dumps(telemetry), 1)

                    time.sleep(self.telemetry_interval)

                except Exception as e:
                    self.logger.error(f"Error publishing telemetry: {e}")
                    time.sleep(self.telemetry_interval)

        import threading
        self.telemetry_thread = threading.Thread(target=telemetry_worker, daemon=True)
        self.telemetry_thread.start()

    def run(self):
        """Main run loop"""
        try:
            while self.is_connected:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down IoT client")
            self.disconnect()


def main():
    """Main function for running the IoT client"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Tello Swarm IoT Client')
    parser.add_argument('--config', required=True, help='Configuration file path')
    args = parser.parse_args()

    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)

    # Initialize and run client
    client = TelloSwarmIoTClient(
        client_id=config['client_id'],
        endpoint=config['endpoint'],
        root_ca_path=config['root_ca_path'],
        private_key_path=config['private_key_path'],
        certificate_path=config['certificate_path'],
        swarm_id=config['swarm_id'],
        drone_ips=config['drone_ips'],
        schema_path=config.get('schema_path')
    )

    if client.connect():
        client.run()
    else:
        print("Failed to connect to AWS IoT")


if __name__ == '__main__':
    main()
