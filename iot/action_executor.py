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
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path to import djitellopy
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from djitellopy import TelloSwarm, Tello

WSL = False

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
    execution_time: Optional[float] = None


class ActionExecutor:
    """Handles Tello drone swarm actions from IoT messages"""

    # Command timeout settings (no retries)
    COMMAND_TIMEOUT = 5  # seconds

    def __init__(self):
        """
        Initialize ActionExecutor

        Uses WSL-compatible configuration with specific IP and ports.
        """
        self.logger = logging.getLogger(__name__)

        self.swarm: Optional[TelloSwarm] = None
        self.drone_map: Dict[str, Tello] = {}
        self.connected = False
        self.connection_lock = threading.Lock()

        # Initialize keepalive-related attributes
        self.keepalive_thread = None
        self.stop_keepalive = threading.Event()
        self.keepalive_interval = 14  # seconds
        self.action_lock = threading.Lock()
        self.last_action_time = time.time()

        # Note: drone_hosts parameter is kept for future compatibility
        # Currently using WSL-specific configuration regardless of this parameter

        # Setup swarm
        self.setup_swarm()

    def _is_connection_error(self, error: Exception) -> bool:
        """
        Check if an error is related to connection issues

        Args:
            error: Exception to check

        Returns:
            True if the error is connection-related
        """
        error_str = str(error).lower()
        error_type = str(type(error))

        connection_indicators = [
            "telloexception",
            "timeout",
            "did not receive a response",
            "aborting command",
            "unsuccessful",
            "connection",
            "network",
            "socket"
        ]

        return any(indicator in error_str or indicator in error_type.lower()
                  for indicator in connection_indicators)

    def _reset_drone_state(self, drone):
        """
        Reset drone connection state after failed connection

        Args:
            drone: Tello drone object to reset
        """
        try:
            # Reset internal connection state
            if hasattr(drone, 'is_connected'):
                drone.is_connected = False
            if hasattr(drone, 'stream_on'):
                drone.stream_on = False
            if hasattr(drone, 'response_thread'):
                if drone.response_thread and drone.response_thread.is_alive():
                    drone.response_thread = None
        except Exception as e:
            self.logger.warning(f"Error resetting drone state: {e}")

    def setup_swarm(self):
        """Initialize the TelloSwarm with WSL-compatible configuration

        Sets up two drones using a specific WSL IP with different UDP ports
        for control and state communication to avoid port conflicts.
        """
        # For WSL compatibility, use a specific IP and ports

        if WSL:
            wsl_ip = "172.28.3.205"
            # Match the simulator configuration: starts at port 8889 with sequential ports
            drone1 = Tello(host=wsl_ip, control_udp=8890, state_udp=8891)
            drone2 = Tello(host=wsl_ip, control_udp=8891, state_udp=8892)
            drones = [drone1, drone2]
        else:
            # Real drone
            drone_hosts = ["192.168.137.22"]
            drone1 = Tello(host=drone_hosts[0])
            # drone2 = Tello(host=drone_hosts[1])
            drones = [drone1]

        self.swarm = TelloSwarm(drones)

        self.drone_map["drone_1"] = drone1
        # self.drone_map["drone_2"] = drone2

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
                start_time = time.time()
                self.logger.info("Connecting to drone swarm...")
                if self.swarm:
                    # Instead of using swarm.connect() which can throw unhandled thread exceptions,
                    # connect to individual drones to have better error control
                    connection_errors = []
                    successful_connections = 0

                    for drone_id, drone in self.drone_map.items():
                        try:
                            self.logger.info(f"Connecting to {drone_id}...")
                            drone.connect()
                            successful_connections += 1
                            self.logger.info(f"Successfully connected to {drone_id}")

                        except Exception as drone_error:
                            error_msg = f"{drone_id}: {str(drone_error)}"
                            connection_errors.append(error_msg)
                            self.logger.error(f"Failed to connect to {drone_id}: {drone_error}")
                            # Ensure drone state is reset after failed connection
                            self._reset_drone_state(drone)

                    # If at least one drone connected successfully, consider it a partial success
                    if successful_connections > 0:
                        self.connected = True
                        execution_time = time.time() - start_time

                        if connection_errors:
                            message = f"Partially connected ({successful_connections}/{len(self.drone_map)} drones). Errors: {'; '.join(connection_errors)}"
                            self.logger.warning(message)
                        else:
                            message = f"Successfully connected to all {successful_connections} drones"
                            self.logger.info(f"Successfully connected to swarm in {execution_time:.2f}s")

                        return ActionResult(
                            status=ActionStatus.SUCCESS,
                            message=message
                        )
                    else:
                        # No drones connected successfully
                        self.connected = False
                        error_details = '; '.join(connection_errors) if connection_errors else "Unknown connection error"
                        return ActionResult(
                            status=ActionStatus.FAILED,
                            message="Failed to connect to any drones",
                            error_details=error_details
                        )
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Successfully connected to swarm"
                )

            except Exception as e:
                self.logger.error(f"Failed to connect to swarm: {e}")
                # Make sure connected flag is false on failure
                self.connected = False
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

                # Stop keepalive thread
                self._stop_keepalive()

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

            # Check if swarm is connected, try to connect once
            if not self.connected:
                self.logger.info("Drone not connected, attempting to connect...")
                connect_result = self.connect_swarm()
                if connect_result.status != ActionStatus.SUCCESS:
                    self.logger.error(f"Connection failed: {connect_result.message}")
                    return connect_result

            # Execute the action
            try:
                result = self._execute_drone_action(drone_id, action, parameters)
                return result
            except Exception as action_error:
                self.logger.error(f"Action execution failed: {action_error}")
                # If it's a connection-related error, reset connection status
                if self._is_connection_error(action_error):
                    self.logger.warning("Connection issue detected, marking as disconnected")
                    self.connected = False
                # Return the error but continue processing future messages
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Action execution failed: {action_error}",
                    error_details=str(action_error)
                )

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

    def _execute_drone_action(self, drone_id: Optional[str], action: Optional[str],
                              parameters: Dict[str, Any]) -> ActionResult:
        """Execute action on specific drone or swarm"""
        if not action:
            return ActionResult(
                status=ActionStatus.INVALID_COMMAND,
                message="No action specified"
            )
        try:
            # Determine target (individual drone or individual execution on all drones)
            if drone_id == "all" or drone_id is None:
                # Execute on all drones individually to avoid swarm.parallel() thread issues
                target_name = "all drones"
                start_time = time.time()

                results = []
                for individual_drone_id, drone in self.drone_map.items():
                    try:
                        result = self._safe_execute_command(drone, action, parameters)
                        results.append((individual_drone_id, result))
                        self.logger.info(f"Action {action} on {individual_drone_id}: {result.status.value}")
                    except Exception as drone_error:
                        self.logger.error(f"Error executing {action} on {individual_drone_id}: {drone_error}")
                        results.append((individual_drone_id, ActionResult(
                            status=ActionStatus.FAILED,
                            message=f"Failed to execute {action}",
                            error_details=str(drone_error)
                        )))

                # Aggregate results
                successful_count = sum(1 for _, result in results if result.status == ActionStatus.SUCCESS)
                total_count = len(results)

                if successful_count == total_count:
                    final_result = ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Successfully executed {action} on all {total_count} drones"
                    )
                elif successful_count > 0:
                    failures = [f"{drone_id}: {result.message}" for drone_id, result in results if result.status != ActionStatus.SUCCESS]
                    final_result = ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Executed {action} on {successful_count}/{total_count} drones. Failures: {'; '.join(failures)}"
                    )
                else:
                    failures = [f"{drone_id}: {result.message}" for drone_id, result in results]
                    final_result = ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Failed to execute {action} on all drones: {'; '.join(failures)}"
                    )

            else:
                target = self.drone_map.get(drone_id)
                target_name = drone_id

                if not target:
                    return ActionResult(
                        status=ActionStatus.DRONE_NOT_FOUND,
                        message=f"Drone {drone_id} not found in swarm",
                        drone_id=drone_id
                    )

                start_time = time.time()
                # Execute the action on individual drone
                final_result = self._safe_execute_command(target, action, parameters)

            final_result.drone_id = drone_id
            execution_time = time.time() - start_time
            final_result.execution_time = execution_time

            # Update last action timestamp
            with self.action_lock:
                self.last_action_time = start_time

            self.logger.info(
                f"Action {action} on {target_name} completed: "
                f"{final_result.status.value}"
            )
            return final_result

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

    def _execute_with_timeout(self, tello, method_name, args):
        """Execute a command on a single drone with timeout (no retries)"""
        start_time = time.time()

        try:
            if time.time() - start_time > self.COMMAND_TIMEOUT:
                return False, f"Command timed out after {self.COMMAND_TIMEOUT}s"

            method = getattr(tello, method_name)
            method(*args)
            return True, None

        except Exception as e:
            return False, str(e)

    def _execute_swarm_command(self, swarm, method_name, args):
        """Execute command on swarm with individual drone failure handling"""
        results = []
        successful = False

        def worker(i, tello):
            try:
                success, error = self._execute_with_timeout(tello, method_name, args)
                results.append((i, success, error))
                if success:
                    nonlocal successful
                    successful = True
            except Exception as e:
                results.append((i, False, str(e)))

        # Execute commands in parallel
        swarm.parallel(worker)

        # Process results
        failures = []
        connection_errors = []
        for i, success, error in results:
            if not success:
                failures.append(f"drone_{i+1}: {error}")
                # Check if this is a connection error
                if self._is_connection_error(Exception(error)):
                    connection_errors.append(f"drone_{i+1}")

        # If all failures are connection errors, mark connection as failed
        if failures and len(connection_errors) == len(failures):
            self.logger.warning("All drone command failures appear to be connection-related")
            self.connected = False

        if not failures:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Successfully executed on all drones"
            )
        elif successful:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Executed successfully on some drones. Failures: {'; '.join(failures)}"
            )
        else:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Failed on all drones: {'; '.join(failures)}"
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
            if isinstance(target, TelloSwarm):
                print(f"Executing {action} on swarm with args: {args}")
                return self._execute_swarm_command(target, method_name, args)
            else:
                print(f"Executing {action} on drone {target.get_id()} with args: {args}")
                success, error = self._execute_with_timeout(target, method_name, args)
                if success:
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Successfully executed {action}"
                    )
                else:
                    # Check if this is a connection error and mark connection as failed
                    if self._is_connection_error(Exception(error)):
                        self.logger.warning("Connection error detected in command execution")
                        self.connected = False
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Failed to execute {action}",
                        error_details=error
                    )
        except Exception as e:
            # Check if this is a connection error and mark connection as failed
            if self._is_connection_error(e):
                self.logger.warning("Connection error detected in command execution")
                self.connected = False
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Failed to execute {action}",
                error_details=str(e)
            )

    def _log_battery_levels(self):
        """Log battery levels for all drones"""
        if WSL or not self.swarm:
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

    def _send_keepalive(self):
        """Send keepalive signals to all drones periodically"""
        while not self.stop_keepalive.is_set():
            current_time = time.time()

            # Skip keepalive if there was a recent action
            with self.action_lock:
                time_since_last_action = current_time - self.last_action_time
                if time_since_last_action < self.keepalive_interval:
                    self.logger.debug(
                        f"Skipping keepalive, last action was {time_since_last_action:.1f}s ago"
                    )
                    # Wait for the remaining time until next interval
                    wait_time = self.keepalive_interval - time_since_last_action
                    self.stop_keepalive.wait(wait_time)
                    continue

            if not WSL and self.connected and self.swarm:
                try:
                    self.swarm.parallel(lambda i,t: t.send_keepalive())
                    # print("Sending skippedkeepalive to all drones")
                except Exception as e:
                    self.logger.error(f"Error in keepalive thread: {e}")

            # Wait for the specified interval
            self.stop_keepalive.wait(self.keepalive_interval)

    def _start_keepalive(self):
        """Start the keepalive thread"""
        if self.keepalive_thread is None or not self.keepalive_thread.is_alive():
            self.stop_keepalive.clear()
            self.keepalive_thread = threading.Thread(
                target=self._send_keepalive,
                daemon=True
            )
            self.keepalive_thread.start()
            self.logger.info("Started keepalive thread")

    def _stop_keepalive(self):
        """Stop the keepalive thread"""
        if self.keepalive_thread and self.keepalive_thread.is_alive():
            self.stop_keepalive.set()
            self.keepalive_thread.join(timeout=5)
            self.keepalive_thread = None
            self.logger.info("Stopped keepalive thread")



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
        try:
            self._stop_keepalive()
            if hasattr(self, 'connected') and self.connected:
                self.disconnect_swarm()
        except Exception:
            pass


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
