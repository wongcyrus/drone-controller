"""
Action Executor for Tello Drone Swarm IoT Control

Handles connection to TelloSwarm and executes commands from IoT messages.
Designed for integration with MCP (Model Context Protocol) server format.

Key Features:
- WSL-compatible drone swarm setup with configurable IP/ports
- Direct message format support for MCP server integration
- Comprehensive action mapping (move, rotate, flip, takeoff, land)
- Battery monitoring and emergency stop functionality
- Thread-safe connection management

Usage:
    executor = ActionExecutor()
    result = executor.execute_action({
        "droneID": "drone_1",
        "action": "takeoff",
        "parameters": {}
    })
"""

import json
import logging
import threading
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path to import djitellopy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from djitellopy import TelloSwarm, Tello


class ActionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_COMMAND = "invalid_command"
    DRONE_NOT_FOUND = "drone_not_found"
    SWARM_NOT_CONNECTED = "swarm_not_connected"


@dataclass
class ActionResult:
    status: ActionStatus
    message: str
    drone_id: Optional[str] = None
    error_details: Optional[str] = None


class ActionExecutor:
    """Handles Tello drone swarm actions from IoT messages"""

    def __init__(self,
                 drone_hosts: List[str] = None):
        """
        Initialize ActionExecutor with drone hosts

        Args:
            drone_hosts: List of drone IP addresses. Defaults to WSL-compatible configuration.
                        Note: Currently configured for WSL environment with specific IP and ports.
        """
        self.logger = logging.getLogger(__name__)

        self.swarm: Optional[TelloSwarm] = None
        self.drone_map: Dict[str, Tello] = {}
        self.connected = False
        self.connection_lock = threading.Lock()

        # Note: drone_hosts parameter is kept for future compatibility
        # Currently using WSL-specific configuration regardless of this parameter
        if drone_hosts is None:
            drone_hosts = ["192.168.137.21", "192.168.137.22"]  # Legacy default

        self.drone_hosts = drone_hosts

        # Setup swarm
        self.setup_swarm()

    def setup_swarm(self):
        """Initialize the TelloSwarm with WSL-compatible configuration

        Sets up two drones using a specific WSL IP with different UDP ports
        for control and state communication to avoid port conflicts.
        """
        # For WSL compatibility, use a specific IP and ports
        wsl_ip = "172.28.3.205"
        drone1 = Tello(host=wsl_ip, control_udp=8889, state_udp=8890)
        drone2 = Tello(host=wsl_ip, control_udp=8890, state_udp=8891)
        drones = [drone1, drone2]
        self.swarm = TelloSwarm(drones)

        # Update drone map for WSL setup
        self.drone_map["drone_1"] = drone1
        self.drone_map["drone_2"] = drone2

        self.logger.info(f"TelloSwarm created with {len(drones)} drones")

    def connect_swarm(self) -> ActionResult:
        """
        Connect to the drone swarm

        Returns:
            ActionResult with connection status
        """
        with self.connection_lock:
            if self.connected:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Swarm already connected"
                )

            try:
                self.logger.info("Connecting to drone swarm...")
                self.swarm.connect()
                self.connected = True

                # Log battery levels
                self._log_battery_levels()

                self.logger.info("Successfully connected to swarm")
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Successfully connected to swarm"
                )

            except Exception as e:
                self.logger.error(f"Failed to connect to swarm: {e}")
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message="Failed to connect to swarm",
                    error_details=str(e)
                )

    def disconnect_swarm(self) -> ActionResult:
        """
        Disconnect from the drone swarm

        Returns:
            ActionResult with disconnection status
        """
        with self.connection_lock:
            if not self.connected:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Swarm already disconnected"
                )

            try:
                self.logger.info("Disconnecting from drone swarm...")

                if self.swarm:
                    self.swarm.end()

                self.connected = False
                self.logger.info("Successfully disconnected from swarm")

                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Successfully disconnected from swarm"
                )

            except Exception as e:
                self.logger.error(f"Failed to disconnect from swarm: {e}")
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message="Failed to disconnect from swarm",
                    error_details=str(e)
                )

    def execute_action(self, message: Dict[str, Any]) -> ActionResult:
        """
        Execute a drone action from IoT message

        Args:
            message: IoT message containing action details

        Returns:
            ActionResult with execution status
        """
        try:
            # Parse the message
            action_data = self._parse_message(message)
            if not action_data:
                return ActionResult(
                    status=ActionStatus.INVALID_COMMAND,
                    message="Invalid message format"
                )

            drone_id = action_data.get("droneID")
            action = action_data.get("action")
            parameters = action_data.get("parameters", {})

            self.logger.info(
                f"Executing action: {action} for drone: {drone_id} "
                f"with parameters: {parameters}"
            )

            # Check if swarm is connected
            if not self.connected:
                connect_result = self.connect_swarm()
                if connect_result.status != ActionStatus.SUCCESS:
                    return connect_result

            # Execute the action
            return self._execute_drone_action(drone_id, action, parameters)

        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Failed to execute action",
                error_details=str(e)
            )

    def _parse_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse IoT message to extract action data

        Supports the direct message format:
        {"droneID": "drone_1", "action": "takeoff", "parameters": {...}}

        Args:
            message: Raw IoT message dictionary

        Returns:
            Parsed action data dictionary or None if parsing fails
        """
        try:
            # Direct action format from MCP server
            if "droneID" in message and "action" in message:
                return message

            self.logger.warning(f"Unrecognized message format: {message}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to parse message: {e}")
            return None

    def _execute_drone_action(self, drone_id: str, action: str,
                              parameters: Dict[str, Any]) -> ActionResult:
        """Execute action on specific drone or swarm"""
        try:
            # Determine target (individual drone or swarm)
            if drone_id == "all" or drone_id is None:
                target = self.swarm
                target_name = "swarm"
            else:
                target = self.drone_map.get(drone_id)
                target_name = drone_id

                if not target:
                    return ActionResult(
                        status=ActionStatus.DRONE_NOT_FOUND,
                        message=f"Drone {drone_id} not found in swarm",
                        drone_id=drone_id
                    )

            # Execute the action
            result = self._safe_execute_command(target, action, parameters)
            result.drone_id = drone_id

            self.logger.info(
                f"Action {action} on {target_name} completed: "
                f"{result.status.value}"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"Error executing action {action} on {drone_id}: {e}"
            )
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Failed to execute {action}",
                drone_id=drone_id,
                error_details=str(e)
            )

    def _safe_execute_command(self, target, action: str,
                              parameters: Dict[str, Any]) -> ActionResult:
        """Safely execute command with error handling and action mapping

        Handles action translation and parameter mapping for drone commands.
        Supports both legacy action names and MCP server compatible actions.

        Args:
            target: Drone or swarm object to execute command on
            action: Action name (e.g., "takeoff", "flip", "up", "cw")
            parameters: Action parameters dictionary

        Returns:
            ActionResult indicating success/failure and details
        """

        # Handle generic "flip" action by mapping direction to specific flip
        if action == "flip" and "direction" in parameters:
            direction = parameters["direction"].lower()
            direction_mapping = {
                "f": "flip_forward",
                "forward": "flip_forward",
                "b": "flip_back",
                "back": "flip_back",
                "l": "flip_left",
                "left": "flip_left",
                "r": "flip_right",
                "right": "flip_right"
            }

            if direction in direction_mapping:
                action = direction_mapping[direction]
                self.logger.info(
                    "Mapped flip direction '%s' to action '%s'",
                    direction, action
                )
            else:
                return ActionResult(
                    status=ActionStatus.INVALID_COMMAND,
                    message=f"Invalid flip direction: {direction}. "
                            f"Valid directions: f, b, l, r, forward, back, "
                            f"left, right"
                )

        # Map action names to method names and parameter handling
        action_mapping = {
            "takeoff": ("takeoff", []),
            "land": ("land", []),
            # Original move_ actions
            "move_up": ("move_up", ["distance"]),
            "move_down": ("move_down", ["distance"]),
            "move_forward": ("move_forward", ["distance"]),
            "move_back": ("move_back", ["distance"]),
            "move_left": ("move_left", ["distance"]),
            "move_right": ("move_right", ["distance"]),
            # MCP handler compatible actions
            "up": ("move_up", ["distance"]),
            "down": ("move_down", ["distance"]),
            "forward": ("move_forward", ["distance"]),
            "back": ("move_back", ["distance"]),
            "left": ("move_left", ["distance"]),
            "right": ("move_right", ["distance"]),
            # Rotation actions
            "rotate_clockwise": ("rotate_clockwise", ["degrees"]),
            "rotate_counter_clockwise": ("rotate_counter_clockwise", ["degrees"]),
            "rotate_counterclockwise": ("rotate_counter_clockwise", ["degrees"]),
            "cw": ("rotate_clockwise", ["degrees"]),
            "ccw": ("rotate_counter_clockwise", ["degrees"]),
            # Flip actions
            "flip_forward": ("flip_forward", []),
            "flip_back": ("flip_back", []),
            "flip_left": ("flip_left", []),
            "flip_right": ("flip_right", []),
            "emergency": ("emergency", []),
            "move": ("move", ["x", "y", "z"])
        }

        if action not in action_mapping:
            return ActionResult(
                status=ActionStatus.INVALID_COMMAND,
                message=f"Unknown action: {action}"
            )

        method_name, param_names = action_mapping[action]

        # Check if target has the method
        if not hasattr(target, method_name):
            return ActionResult(
                status=ActionStatus.INVALID_COMMAND,
                message=f"Target does not support action: {action}"
            )

        # Prepare parameters
        args = []
        for param_name in param_names:
            if param_name in parameters:
                args.append(parameters[param_name])
            else:
                # Use default values for missing parameters
                if param_name == "distance":
                    # Try different parameter names for distance
                    value = parameters.get("distance", parameters.get("x", 30))
                    args.append(value)
                elif param_name == "degrees":
                    # Try different parameter names for degrees/angle
                    value = parameters.get("degrees", parameters.get("angle", parameters.get("x", 90)))
                    args.append(value)
                elif param_name in ["x", "y", "z"]:
                    args.append(parameters.get(param_name, 0))

        # Execute command
        try:
            method = getattr(target, method_name)
            method(*args)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Successfully executed {action}"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Failed to execute {action}",
                error_details=str(e)
            )

    def _log_battery_levels(self):
        """Log battery levels for all drones"""
        if not self.swarm:
            return

        for i, tello in enumerate(self.swarm.tellos):
            try:
                battery = tello.get_battery()
                drone_id = f"drone_{i + 1}"
                self.logger.info(f"{drone_id} battery: {battery}%")

                if battery < 20:
                    self.logger.warning(f"{drone_id} battery critically low: {battery}%")
                elif battery < 50:
                    self.logger.warning(f"{drone_id} battery low: {battery}%")
            except Exception as e:
                self.logger.error(f"Could not get battery for drone_{i + 1}: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the executor and swarm"""
        status = {
            "connected": self.connected,
            "swarm_initialized": self.swarm is not None,
            "drone_count": len(self.drone_hosts),
            "drone_hosts": self.drone_hosts
        }

        if self.connected and self.swarm:
            batteries = {}
            for i, tello in enumerate(self.swarm.tellos):
                try:
                    drone_id = f"drone_{i + 1}"
                    batteries[drone_id] = tello.get_battery()
                except Exception as e:
                    batteries[drone_id] = f"Error: {e}"

            status["batteries"] = batteries

        return status

    def emergency_stop(self) -> ActionResult:
        """Emergency stop for all drones"""
        self.logger.warning("EMERGENCY STOP initiated")

        if not self.connected:
            return ActionResult(
                status=ActionStatus.SWARM_NOT_CONNECTED,
                message="Swarm not connected for emergency stop"
            )

        if not self.swarm:
            return ActionResult(
                status=ActionStatus.SWARM_NOT_CONNECTED,
                message="Swarm not initialized for emergency stop"
            )

        # Try emergency command for each drone
        for i, tello in enumerate(self.swarm.tellos):
            try:
                drone_id = f"drone_{i + 1}"
                self.logger.info(f"Emergency stop for {drone_id}")
                tello.emergency()
            except Exception as e:
                self.logger.error(f"Emergency command failed for drone_{i + 1}: {e}")

        # End connection
        try:
            self.swarm.end()
            self.connected = False
        except Exception as e:
            self.logger.error(f"Failed to end connection during emergency stop: {e}")

        return ActionResult(
            status=ActionStatus.SUCCESS,
            message="Emergency stop completed"
        )

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'connected') and self.connected:
            self.disconnect_swarm()


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Create executor with WSL configuration
    executor = ActionExecutor()

    # Test connection
    print("Testing connection...")
    result = executor.connect_swarm()
    print(f"Connection result: {result.status.value} - {result.message}")

    if result.status == ActionStatus.SUCCESS:
        # Test status
        print("\nGetting status...")
        status = executor.get_status()
        print(f"Status: {json.dumps(status, indent=2)}")

        # Test MCP-compatible action execution
        print("\nTesting MCP format action execution...")
        test_message = {
            "droneID": "drone_1",
            "action": "cw",
            "parameters": {"x": 90}
        }

        action_result = executor.execute_action(test_message)
        print(f"Action result: {action_result.status.value} - "
              f"{action_result.message}")

        # Test another MCP action format
        print("\nTesting movement action...")
        move_message = {
            "droneID": "drone_1",
            "action": "up",
            "parameters": {"x": 50}
        }

        move_result = executor.execute_action(move_message)
        print(f"Move result: {move_result.status.value} - "
              f"{move_result.message}")

        # Disconnect
        print("\nDisconnecting...")
        disconnect_result = executor.disconnect_swarm()
        print(f"Disconnect result: {disconnect_result.status.value} - "
              f"{disconnect_result.message}")

    print("Test completed.")
