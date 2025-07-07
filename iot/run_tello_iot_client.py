#!/usr/bin/env python3
"""
Startup script for Tello Drone Swarm IoT Client
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from iot.tello_swarm_iot_client import TelloSwarmIoTClient


def setup_logging(config: dict):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    level = getattr(logging, log_config.get('level', 'INFO'))
    format_str = log_config.get('format', '[%(levelname)s] %(asctime)s - %(name)s - %(message)s')

    # Create logs directory if it doesn't exist
    log_file = log_config.get('file')
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(level=level, format=format_str)


def validate_config(config: dict) -> bool:
    """Validate configuration file"""
    required_fields = [
        'client_id', 'endpoint', 'root_ca_path',
        'private_key_path', 'certificate_path',
        'swarm_id', 'drone_ips'
    ]

    for field in required_fields:
        if field not in config:
            print(f"Error: Missing required field '{field}' in configuration")
            return False

    # Check certificate files exist
    cert_files = [
        config['root_ca_path'],
        config['private_key_path'],
        config['certificate_path']
    ]

    for cert_file in cert_files:
        if not Path(cert_file).exists():
            print(f"Error: Certificate file not found: {cert_file}")
            return False

    # Validate drone IPs
    if not config['drone_ips'] or len(config['drone_ips']) == 0:
        print("Error: No drone IPs specified")
        return False

    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Tello Swarm IoT Client')
    parser.add_argument(
        '--config',
        required=True,
        help='Configuration file path (JSON format)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration and exit'
    )
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test drone connections and exit'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        return 1

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    # Validate configuration
    if not validate_config(config):
        return 1

    logger.info(f"Configuration loaded from {args.config}")
    logger.info(f"Swarm ID: {config['swarm_id']}")
    logger.info(f"Drone count: {len(config['drone_ips'])}")

    if args.validate_only:
        print("Configuration validation passed")
        return 0

    # Initialize IoT client
    try:
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

        logger.info("IoT client initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize IoT client: {e}")
        return 1

    # Test drone connections if requested
    if args.test_connection:
        logger.info("Testing drone connections...")
        if client.action_executor.connect():
            logger.info("All drone connections successful")
            status = client.action_executor.get_swarm_status()
            print(f"Connected drones: {status['drone_count']}")
            for drone in status['drone_status']:
                if 'error' in drone:
                    print(f"Drone {drone['drone_id']} ({drone['ip']}): ERROR - {drone['error']}")
                else:
                    print(f"Drone {drone['drone_id']} ({drone['ip']}): Battery {drone['battery']}%")
            client.action_executor.shutdown()
            return 0
        else:
            logger.error("Failed to connect to drones")
            return 1

    # Connect and run
    try:
        logger.info("Connecting to AWS IoT and drone swarm...")
        if client.connect():
            logger.info("Successfully connected. Starting main loop...")
            print("Tello Swarm IoT Client is running. Press Ctrl+C to stop.")
            client.run()
        else:
            logger.error("Failed to connect")
            return 1

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        logger.info("Shutting down...")
        client.disconnect()

    return 0


if __name__ == '__main__':
    sys.exit(main())
