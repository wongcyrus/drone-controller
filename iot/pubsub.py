# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

import json
import logging
import os
import threading
from concurrent.futures import Future
from typing import Any, Dict, Optional

import yaml
from action_executor import ActionExecutor
from awscrt import auth, mqtt5
from awsiot import mqtt5_client_builder
import configparser

TIMEOUT = 5

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def load_settings(settings_path: str) -> dict:
    try:
        with open(settings_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error("Failed to load settings: %s", e)
        raise


def format_settings(
    settings: Dict[str, Any], robot_name: str, base_path: str
) -> Dict[str, Any]:
    # Format all relevant fields with robot_name and base_path
    for key in ["input_topic", "input_cert", "input_key", "input_ca", "input_clientId"]:
        if key in settings:
            settings[key] = settings[key].format(
                robot_name=robot_name, base_path=base_path
            )
    return settings


class PubSubClient:
    def __init__(self, settings: Dict[str, Any], executor: ActionExecutor):
        self.settings = settings
        self.executor = executor
        self.client: Optional[mqtt5.Client] = None
        self.future_stopped = Future()
        self.future_connection_success = Future()
        self.received_all_event = threading.Event()
        self.message_topic = settings["input_topic"]

    def on_publish_received(self, publish_packet_data):
        try:
            publish_packet = publish_packet_data.publish_packet
            assert isinstance(publish_packet, mqtt5.PublishPacket)
            logging.info(
                "Received message from topic '%s': %s",
                publish_packet.topic,
                publish_packet.payload,
            )
            try:
                # Decode bytes to string before parsing JSON
                payload_str = publish_packet.payload.decode('utf-8')
                print(f"Raw payload string: {payload_str}")

                # First try to parse the outer JSON
                try:
                    payload = json.loads(payload_str)
                    print(f"Received payload: {payload}")

                    # Execute action with robust error handling to prevent stopping message processing
                    try:
                        result = self.executor.execute_action(payload)
                        # Log the result but continue processing regardless of outcome
                        if result.status.value == "success":
                            if result.error_details:
                                logging.info(f"Action executed with warnings: {result.message}")
                            else:
                                logging.info(f"Action executed successfully: {result.message}")
                        else:
                            logging.warning(f"Action execution had issues: {result.status.value} - {result.message}")
                            if result.error_details:
                                logging.warning(f"Error details: {result.error_details}")
                    except Exception as exec_error:
                        # Even if action execution completely fails, continue processing
                        logging.warning(f"Exception during action execution: {exec_error}")
                        logging.info(f"Continuing to process future AWS IoT messages...")

                    # Always continue processing - this is key for robustness

                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse outer JSON: {e}")
                    logging.error(f"Raw payload: {payload_str}")
                    return

            except json.JSONDecodeError:
                logging.error("Invalid JSON payload received")
        except Exception as e:
            logging.error("Exception in on_publish_received: %s", e)
            logging.error("Continuing to process future messages...")

    def on_lifecycle_stopped(self, lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
        logging.info("Lifecycle Stopped")
        if not self.future_stopped.done():
            self.future_stopped.set_result(lifecycle_stopped_data)

    def on_lifecycle_connection_success(
        self, lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData
    ):
        logging.info("Lifecycle Connection Success")
        if not self.future_connection_success.done():
            self.future_connection_success.set_result(lifecycle_connect_success_data)

    def on_lifecycle_connection_failure(
        self, lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData
    ):
        logging.error(
            "Lifecycle Connection Failure: %s", lifecycle_connection_failure.exception
        )

    def build_mqtt_client(self, use_websocket: bool = False) -> mqtt5.Client:
        client_args = dict(
            endpoint=self.settings["input_endpoint"],
            client_id=self.settings["input_clientId"],
            keep_alive_interval_sec=5,
            on_publish_received=self.on_publish_received,
            on_lifecycle_stopped=self.on_lifecycle_stopped,
            on_lifecycle_connection_success=self.on_lifecycle_connection_success,
            on_lifecycle_connection_failure=self.on_lifecycle_connection_failure,
        )
        if not use_websocket:
            return mqtt5_client_builder.mtls_from_path(
                port=8883,
                cert_filepath=self.settings["input_cert"],
                pri_key_filepath=self.settings["input_key"],
                ca_filepath=self.settings["input_ca"],
                **client_args
            )
        else:
            region = self.settings.get("region", "us-east-1")
            credentials_provider = auth.AwsCredentialsProvider.new_static(
                access_key_id=self.settings["aws_access_key_id"],
                secret_access_key=self.settings["aws_secret_access_key"],
            )
            return mqtt5_client_builder.websockets_with_default_aws_signing(
                region=region,
                credentials_provider=credentials_provider,
                ca_filepath=self.settings["input_ca"],
                port=443,
                **client_args
            )

    def connect(self) -> None:
        try:
            logging.info("Trying MQTT mTLS connection...")
            self.client = self.build_mqtt_client(use_websocket=False)
            self.client.start()
            lifecycle_connect_success_data = self.future_connection_success.result(
                TIMEOUT
            )
            connack_packet = lifecycle_connect_success_data.connack_packet
            logging.info(
                "Connected to endpoint: '%s' with Client ID: '%s' reason_code: %s",
                self.settings["input_endpoint"],
                self.settings["input_clientId"],
                repr(connack_packet.reason_code),
            )
        except Exception as e:
            logging.warning("MQTT mTLS failed: %s. Trying WebSocket...", e)
            # Reset the future for websocket attempt
            self.future_connection_success = Future()
            self.client = self.build_mqtt_client(use_websocket=True)
            self.client.start()
            lifecycle_connect_success_data = self.future_connection_success.result(
                TIMEOUT
            )
            connack_packet = lifecycle_connect_success_data.connack_packet
            logging.info(
                "Connected to endpoint: '%s' with Client ID: '%s' (WebSocket) reason_code: %s",
                self.settings["input_endpoint"],
                self.settings["input_clientId"],
                repr(connack_packet.reason_code),
            )

    def subscribe(self) -> None:
        logging.info("Subscribing to topic '%s'...", self.message_topic)
        subscribe_future = self.client.subscribe(
            subscribe_packet=mqtt5.SubscribePacket(
                subscriptions=[
                    mqtt5.Subscription(
                        topic_filter=self.message_topic, qos=mqtt5.QoS.AT_LEAST_ONCE
                    )
                ]
            )
        )
        suback = subscribe_future.result(TIMEOUT)
        logging.info("Subscribed with %s", suback.reason_codes)

    def unsubscribe(self) -> None:
        try:
            logging.info("Unsubscribing from topic '%s'", self.message_topic)
            unsubscribe_future = self.client.unsubscribe(
                unsubscribe_packet=mqtt5.UnsubscribePacket(
                    topic_filters=[self.message_topic]
                )
            )
            unsuback = unsubscribe_future.result(TIMEOUT)
            logging.info("Unsubscribed with %s", unsuback.reason_codes)
        except Exception as e:
            logging.warning("Exception during unsubscribe: %s", e)

    def stop(self) -> None:
        logging.info("Stopping Client")
        if self.client:
            self.client.stop()
        # Disconnect the executor instead of calling stop()
        if hasattr(self.executor, 'disconnect_swarm'):
            self.executor.disconnect_swarm()
        try:
            self.future_stopped.result(TIMEOUT)
        except Exception as e:
            logging.warning("Exception waiting for client stop: %s", e)
        logging.info("Client Stopped!")

    def run(self) -> None:
        self.connect()
        self.subscribe()
        logging.info("Sending messages until user inputs 's' to stop")
        try:
            while True:
                user_input = input("Type 's' and press Enter to stop the program: ")
                if user_input.strip().lower() == "s":
                    logging.info("'s' received, shutting down gracefully...")
                    self.received_all_event.set()
                    break
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received, shutting down...")
        finally:
            self.unsubscribe()
            self.stop()


def main():
    try:
        settings = load_settings("settings.yaml")
        robot_name = settings["robot_name"]
        base_path = settings["base_path"]
        settings = format_settings(settings, robot_name, base_path)
        if not settings.get("aws_access_key_id"):
            settings["aws_access_key_id"] = os.environ.get("IoTRobotAccessKeyId", "")
        if not settings["aws_access_key_id"]:
            settings["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
        if not settings["aws_access_key_id"]:
            # Try to read from AWS CLI config (~/.aws/credentials)
            aws_creds_path = os.path.expanduser("~/.aws/credentials")
            if os.path.exists(aws_creds_path):
                config = configparser.ConfigParser()
                config.read(aws_creds_path)
                profile = os.environ.get("AWS_PROFILE", "default")
                if config.has_section(profile):
                    settings["aws_access_key_id"] = config.get(profile, "aws_access_key_id", fallback="")
                    settings["aws_secret_access_key"] = config.get(profile, "aws_secret_access_key", fallback="")
        if not settings.get("aws_secret_access_key"):
            settings["aws_secret_access_key"] = os.environ.get("IoTRobotSecretAccessKey", "")
        if not settings["aws_secret_access_key"]:
            settings["aws_secret_access_key"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        print("Settings loaded successfully:", json.dumps(settings, indent=2))

        # Try Tello executor first, fallback to simulator if not available

        executor = ActionExecutor()
        logging.info("Using Tello executor")

        client = PubSubClient(settings, executor)
        client.run()
    except Exception as e:
        logging.error("Exception occurred in main loop: %s", e)


if __name__ == "__main__":
    main()
