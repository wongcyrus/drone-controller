"""
Configuration management utilities for drone operations.

Provides configuration loading, validation, and management for drones and swarms.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


class DroneConfig:
    """Configuration manager for drone operations."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.config_data: Dict[str, Any] = {}
        self.config_file = config_file
        self.logger = logging.getLogger("drone_controller.config")

        if config_file:
            self.load_config(config_file)
        else:
            self._load_default_config()

    def load_config(self, config_file: str) -> bool:
        """
        Load configuration from file.

        Args:
            config_file: Path to configuration file

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            config_path = Path(config_file)

            if not config_path.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                return False

            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    self.config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    self.config_data = json.load(f)
                else:
                    self.logger.error(f"Unsupported configuration file format: {config_path.suffix}")
                    return False

            self.config_file = config_file
            self.logger.info(f"Configuration loaded from {config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False

    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        Save current configuration to file.

        Args:
            config_file: Path to save configuration (uses loaded file if None)

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if config_file is None:
            config_file = self.config_file

        if not config_file:
            self.logger.error("No configuration file specified")
            return False

        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(self.config_data, f, default_flow_style=False, indent=2)
                elif config_path.suffix.lower() == '.json':
                    json.dump(self.config_data, f, indent=2)
                else:
                    self.logger.error(f"Unsupported configuration file format: {config_path.suffix}")
                    return False

            self.logger.info(f"Configuration saved to {config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def get_drone_config(self, drone_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific drone.

        Args:
            drone_id: Drone identifier

        Returns:
            dict: Drone configuration
        """
        drones_config = self.config_data.get("drones", {})

        # Check for specific drone config
        if drone_id in drones_config:
            specific_config = drones_config[drone_id].copy()
            # Merge with default drone config
            default_config = drones_config.get("default", {})
            default_config.update(specific_config)
            return default_config

        # Return default drone config
        return drones_config.get("default", {})

    def get_swarm_config(self, swarm_id: str = "default") -> Dict[str, Any]:
        """
        Get configuration for a swarm.

        Args:
            swarm_id: Swarm identifier

        Returns:
            dict: Swarm configuration
        """
        swarms_config = self.config_data.get("swarms", {})
        return swarms_config.get(swarm_id, swarms_config.get("default", {}))

    def get_formation_config(self, formation_name: str) -> Dict[str, Any]:
        """
        Get configuration for a formation.

        Args:
            formation_name: Formation name

        Returns:
            dict: Formation configuration
        """
        formations_config = self.config_data.get("formations", {})
        return formations_config.get(formation_name, {})

    def get_safety_config(self) -> Dict[str, Any]:
        """
        Get safety configuration parameters.

        Returns:
            dict: Safety configuration
        """
        return self.config_data.get("safety", {})

    def get_error_handling_config(self) -> Dict[str, Any]:
        """
        Get error handling configuration parameters.

        Returns:
            dict: Error handling configuration
        """
        return self.config_data.get("error_handling", {})

    def get_retry_config(self) -> Dict[str, Any]:
        """
        Get retry configuration parameters.

        Returns:
            dict: Retry configuration
        """
        return self.config_data.get("retry_config", {})

    def get_motor_stop_handling_config(self) -> Dict[str, Any]:
        """
        Get motor stop error handling configuration.

        Returns:
            dict: Motor stop handling configuration
        """
        error_handling = self.get_error_handling_config()
        return error_handling.get("motor_stop", {})

    def get_degraded_performance_config(self) -> Dict[str, Any]:
        """
        Get degraded performance mode configuration.

        Returns:
            dict: Degraded performance configuration
        """
        return self.config_data.get("degraded_performance", {})

    def add_drone_config(self, drone_id: str, config: Dict[str, Any]):
        """
        Add or update configuration for a drone.

        Args:
            drone_id: Drone identifier
            config: Configuration dictionary
        """
        if "drones" not in self.config_data:
            self.config_data["drones"] = {}

        self.config_data["drones"][drone_id] = config
        self.logger.info(f"Added configuration for drone {drone_id}")

    def add_formation_config(self, formation_name: str, config: Dict[str, Any]):
        """
        Add or update configuration for a formation.

        Args:
            formation_name: Formation name
            config: Configuration dictionary
        """
        if "formations" not in self.config_data:
            self.config_data["formations"] = {}

        self.config_data["formations"][formation_name] = config
        self.logger.info(f"Added configuration for formation {formation_name}")

    def validate_config(self) -> List[str]:
        """
        Validate the current configuration.

        Returns:
            list: List of validation errors (empty if valid)
        """
        errors = []

        # Validate drone configurations
        drones_config = self.config_data.get("drones", {})
        for drone_id, drone_config in drones_config.items():
            if drone_id == "default":
                continue

            # Check required fields
            if "ip_address" not in drone_config and "ip_address" not in drones_config.get("default", {}):
                errors.append(f"Drone {drone_id}: missing ip_address")

        # Validate safety parameters
        safety_config = self.config_data.get("safety", {})
        min_distance = safety_config.get("min_distance", 100)
        if min_distance < 50:
            errors.append("Safety: min_distance should be at least 50cm")

        max_altitude = safety_config.get("max_altitude", 300)
        if max_altitude > 500:
            errors.append("Safety: max_altitude should not exceed 500cm for indoor use")

        return errors

    def _load_default_config(self):
        """Load default configuration from drone_config.yaml."""
        # Try to load from default config file first
        default_config_path = Path("config/drone_config.yaml")

        if default_config_path.exists():
            if self.load_config(str(default_config_path)):
                self.logger.info("Loaded default configuration from config/drone_config.yaml")
                return
            else:
                self.logger.warning("Failed to load config/drone_config.yaml, using hardcoded defaults")
        else:
            self.logger.warning("config/drone_config.yaml not found, using hardcoded defaults")

        # Fallback to hardcoded defaults
        self.config_data = {
            "drones": {
                "default": {
                    "connection_timeout": 10.0,
                    "command_timeout": 5.0,
                    "max_speed": 50,
                    "video_enabled": False
                }
            },
            "swarms": {
                "default": {
                    "max_drones": 10,
                    "takeoff_stagger_delay": 1.0,
                    "landing_stagger_delay": 0.5
                }
            },
            "formations": {
                "line": {
                    "spacing": 150,
                    "orientation": 0
                },
                "circle": {
                    "radius": 200
                },
                "diamond": {
                    "size": 200
                },
                "v_formation": {
                    "spacing": 150,
                    "angle": 45
                }
            },
            "safety": {
                "min_distance": 100,
                "collision_threshold": 80,
                "max_altitude": 300,
                "battery_warning_threshold": 20,
                "battery_critical_threshold": 10
            },
            "error_handling": {
                "motor_stop": {
                    "max_retries": 5,
                    "base_delay": 2.0,
                    "backoff_multiplier": 1.5,
                    "max_delay": 10.0,
                    "enable_degraded_mode": True,
                    "auto_exclude_problematic_drones": True,
                    "cooldown_period": 30.0
                },
                "connection_timeout": {
                    "max_retries": 3,
                    "base_delay": 1.0,
                    "backoff_multiplier": 2.0
                },
                "movement_timeout": {
                    "max_retries": 3,
                    "base_delay": 0.5,
                    "backoff_multiplier": 1.5
                }
            },
            "retry_config": {
                "default_max_retries": 3,
                "default_base_delay": 1.0,
                "default_backoff_multiplier": 1.5,
                "enable_exponential_backoff": True,
                "enable_jitter": True,
                "jitter_max_ms": 1000
            },
            "degraded_performance": {
                "enable_auto_mode": True,
                "reduced_speed_factor": 0.7,
                "reduced_movement_distance": 0.8,
                "extended_delays": True,
                "skip_non_critical_operations": True,
                "battery_threshold_for_degraded_mode": 30
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
                "log_directory": "logs"
            }
        }

        self.logger.info("Default configuration loaded")


def create_sample_config(output_file: str = "config/drone_config.yaml") -> bool:
    """
    Create a sample configuration file.

    Args:
        output_file: Path to save the sample configuration

    Returns:
        bool: True if created successfully, False otherwise
    """
    config = DroneConfig()

    # Add some sample drone configurations
    config.add_drone_config("drone_001", {
        "ip_address": "192.168.10.1",
        "video_enabled": True,
        "max_speed": 40
    })

    config.add_drone_config("drone_002", {
        "ip_address": "192.168.10.2",
        "video_enabled": True,
        "max_speed": 40
    })

    config.add_drone_config("drone_003", {
        "ip_address": "192.168.10.3",
        "video_enabled": False,
        "max_speed": 45
    })

    # Add custom formation
    config.add_formation_config("triangle", {
        "type": "custom",
        "positions": [
            {"x": 0, "y": 100, "z": 150},
            {"x": -87, "y": -50, "z": 150},
            {"x": 87, "y": -50, "z": 150}
        ]
    })

    return config.save_config(output_file)
