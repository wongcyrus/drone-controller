"""
Enhanced Tello Drone Controller with advanced features for multi-robot coordination.

This module provides an enhanced wrapper around djitellopy for better multi-robot
control, state management, and coordinated operations.
"""

import time
import threading
import logging
import socket
import random
from typing import Optional, Tuple, Dict, Any, Callable
from djitellopy import Tello
import cv2
import numpy as np


class TelloDrone:
    """
    Enhanced Tello drone controller with multi-robot capabilities.

    This class wraps the djitellopy Tello class and adds features specifically
    designed for multi-robot coordination and swarm control.
    """

    def __init__(self, drone_id: str, ip_address: Optional[str] = None):
        """
        Initialize a TelloDrone instance.

        Args:
            drone_id: Unique identifier for this drone
            ip_address: IP address of the drone (optional, will auto-discover if None)
        """
        self.drone_id = drone_id
        self.ip_address = ip_address
        self.tello = Tello(host=ip_address) if ip_address else Tello()

        # Apply UTF-8 error handling patch
        self._patch_tello_for_utf8_errors()

        # State tracking
        self._is_connected = False
        self._is_flying = False
        self._battery_level = 0
        self._current_position = {"x": 0, "y": 0, "z": 0}
        self._target_position = {"x": 0, "y": 0, "z": 0}

        # Threading and async support
        self._command_lock = threading.Lock()
        self._state_update_thread = None
        self._stop_state_updates = False
        self._frame_capture_thread = None
        self._stop_frame_capture = False
        self._event_callbacks = {}

        # Enhanced error handling attributes
        self._motor_stop_count = 0
        self._consecutive_failures = 0
        self._last_error_time = 0
        self._is_in_degraded_mode = False
        self._error_cooldown_until = 0
        self._movement_delays = {"base": 0.1, "current": 0.1}

        # Video streaming
        self._video_enabled = False
        self._frame = None
        self._frame_lock = threading.Lock()

        # Event callbacks
        self._event_callbacks: Dict[str, list] = {
            "takeoff": [],
            "land": [],
            "battery_low": [],
            "connection_lost": [],
            "emergency": []
        }

        # Setup logging
        self.logger = logging.getLogger(f"TelloDrone_{drone_id}")
        self.logger.setLevel(logging.INFO)

    def connect(self) -> bool:
        """
        Connect to the drone and start state monitoring.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to drone {self.drone_id}...")

            # Connect to the drone with UTF-8 error handling
            self._safe_connect()

            # Verify connection by getting battery
            self._battery_level = self._safe_get_battery()
            self._is_connected = True

            # Start state monitoring thread
            self._start_state_monitoring()

            self.logger.info(f"Successfully connected to drone {self.drone_id} (Battery: {self._battery_level}%)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to drone {self.drone_id}: {e}")
            self._is_connected = False
            return False

    def disconnect(self):
        """Disconnect from the drone and cleanup resources."""
        self.logger.info(f"Disconnecting drone {self.drone_id}...")

        # Stop state monitoring
        self._stop_state_updates = True
        if self._state_update_thread and self._state_update_thread.is_alive():
            self._state_update_thread.join(timeout=2.0)

        # Stop video streaming
        if self._video_enabled:
            self.stop_video_stream()

        # Land if flying
        if self._is_flying:
            self.emergency_land()

        # End connection
        try:
            self._safe_execute_command(self.tello.end)
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {e}")

        self._is_connected = False
        self.logger.info(f"Drone {self.drone_id} disconnected")

    def takeoff(self, timeout: float = 10.0) -> bool:
        """
        Take off the drone.

        Args:
            timeout: Maximum time to wait for takeoff completion

        Returns:
            bool: True if takeoff successful, False otherwise
        """
        if not self._is_connected:
            self.logger.error("Cannot takeoff: drone not connected")
            return False

        if self._is_flying:
            self.logger.warning("Drone is already flying")
            return True

        try:
            with self._command_lock:
                self.logger.info(f"Taking off drone {self.drone_id}...")
                self._safe_takeoff()
                self._is_flying = True

                # Trigger takeoff callbacks
                self._trigger_event_callbacks("takeoff")

                self.logger.info(f"Drone {self.drone_id} takeoff successful")
                return True

        except Exception as e:
            self.logger.error(f"Takeoff failed for drone {self.drone_id}: {e}")
            return False

    def _safe_takeoff(self):
        """Safely execute takeoff with UTF-8 error handling."""
        try:
            self.tello.takeoff()
        except UnicodeDecodeError as e:
            self.logger.warning(f"UTF-8 decode error during takeoff, attempting retry: {e}")
            time.sleep(0.5)
            self.tello.takeoff()
        except Exception as e:
            raise e

    def land(self, timeout: float = 10.0) -> bool:
        """
        Land the drone.

        Args:
            timeout: Maximum time to wait for landing completion

        Returns:
            bool: True if landing successful, False otherwise
        """
        if not self._is_connected:
            self.logger.error("Cannot land: drone not connected")
            return False

        if not self._is_flying:
            self.logger.warning("Drone is already on ground")
            return True

        try:
            with self._command_lock:
                self.logger.info(f"Landing drone {self.drone_id}...")
                self._safe_land()
                self._is_flying = False

                # Trigger land callbacks
                self._trigger_event_callbacks("land")

                self.logger.info(f"Drone {self.drone_id} landing successful")
                return True

        except Exception as e:
            self.logger.error(f"Landing failed for drone {self.drone_id}: {e}")
            return False

    def _safe_land(self):
        """Safely execute landing with UTF-8 error handling."""
        try:
            self.tello.land()
        except UnicodeDecodeError as e:
            self.logger.warning(f"UTF-8 decode error during landing, attempting retry: {e}")
            time.sleep(0.5)
            self.tello.land()
        except Exception as e:
            raise e

    def emergency_land(self):
        """Emergency landing - immediate stop of all motors."""
        try:
            with self._command_lock:
                self.logger.warning(f"Emergency landing drone {self.drone_id}")
                self._safe_execute_command(self.tello.emergency)
                self._is_flying = False
                self._trigger_event_callbacks("emergency")
        except Exception as e:
            self.logger.error(f"Emergency landing failed for drone {self.drone_id}: {e}")

    def move(self, x: int, y: int, z: int, speed: int = 50) -> bool:
        """
        Move drone to relative position.

        Args:
            x: Forward/backward movement (cm)
            y: Left/right movement (cm)
            z: Up/down movement (cm)
            speed: Movement speed (10-100)

        Returns:
            bool: True if movement successful, False otherwise
        """
        if not self._is_flying:
            self.logger.error("Cannot move: drone not flying")
            return False

        try:
            with self._command_lock:
                self.logger.debug(f"Moving drone {self.drone_id}: x={x}, y={y}, z={z}, speed={speed}")

                # Set speed
                self._safe_execute_command(self.tello.set_speed, speed)

                # Execute movement
                if abs(x) >= 20 or abs(y) >= 20 or abs(z) >= 20:
                    self._safe_execute_command(self.tello.go_xyz_speed, x, y, z, speed)
                else:
                    # Use smaller movements for fine control
                    if abs(x) >= 20:
                        if x > 0:
                            self._safe_execute_command(self.tello.move_forward, x)
                        else:
                            self._safe_execute_command(self.tello.move_back, abs(x))
                    if abs(y) >= 20:
                        if y > 0:
                            self._safe_execute_command(self.tello.move_right, y)
                        else:
                            self._safe_execute_command(self.tello.move_left, abs(y))
                    if abs(z) >= 20:
                        if z > 0:
                            self._safe_execute_command(self.tello.move_up, z)
                        else:
                            self._safe_execute_command(self.tello.move_down, abs(z))

                # Update position tracking (approximate)
                self._current_position["x"] += x
                self._current_position["y"] += y
                self._current_position["z"] += z

                return True

        except Exception as e:
            self.logger.error(f"Movement failed for drone {self.drone_id}: {e}")
            return False

    def rotate(self, angle: int) -> bool:
        """
        Rotate drone clockwise by specified angle.

        Args:
            angle: Rotation angle in degrees (positive = clockwise)

        Returns:
            bool: True if rotation successful, False otherwise
        """
        if not self._is_flying:
            self.logger.error("Cannot rotate: drone not flying")
            return False

        try:
            with self._command_lock:
                if angle > 0:
                    self._safe_execute_command(self.tello.rotate_clockwise, angle)
                else:
                    self._safe_execute_command(self.tello.rotate_counter_clockwise, abs(angle))
                return True
        except Exception as e:
            self.logger.error(f"Rotation failed for drone {self.drone_id}: {e}")
            return False

    def start_video_stream(self) -> bool:
        """
        Start video streaming from drone camera.

        Returns:
            bool: True if stream started successfully, False otherwise
        """
        try:
            self._safe_execute_command(self.tello.streamon)
            self._video_enabled = True

            # Start frame capture thread
            self._start_frame_capture()

            self.logger.info(f"Video stream started for drone {self.drone_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start video stream for drone {self.drone_id}: {e}")
            return False

    def stop_video_stream(self):
        """Stop video streaming."""
        try:
            self._safe_execute_command(self.tello.streamoff)
            self._video_enabled = False
            self.logger.info(f"Video stream stopped for drone {self.drone_id}")
        except Exception as e:
            self.logger.error(f"Failed to stop video stream for drone {self.drone_id}: {e}")

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest video frame.

        Returns:
            numpy.ndarray: Latest frame, or None if no frame available
        """
        with self._frame_lock:
            return self._frame.copy() if self._frame is not None else None

    def get_state(self) -> Dict[str, Any]:
        """
        Get current drone state.

        Returns:
            dict: Dictionary containing drone state information
        """
        return {
            "drone_id": self.drone_id,
            "connected": self._is_connected,
            "flying": self._is_flying,
            "battery": self._battery_level,
            "position": self._current_position.copy(),
            "target_position": self._target_position.copy(),
            "video_enabled": self._video_enabled,
            "ip_address": self.ip_address
        }

    def add_event_callback(self, event: str, callback: Callable):
        """
        Add event callback function.

        Args:
            event: Event name (takeoff, land, battery_low, connection_lost, emergency)
            callback: Function to call when event occurs
        """
        if event in self._event_callbacks:
            self._event_callbacks[event].append(callback)

    def _start_state_monitoring(self):
        """Start the state monitoring thread."""
        self._stop_state_updates = False
        self._state_update_thread = threading.Thread(target=self._state_update_loop, daemon=True)
        self._state_update_thread.start()

    def _state_update_loop(self):
        """Main loop for state monitoring."""
        while not self._stop_state_updates and self._is_connected:
            try:
                # Update battery level
                battery_result = self._safe_execute_command(self.tello.get_battery)
                if isinstance(battery_result, (int, float)) and battery_result > 0:
                    self._battery_level = int(battery_result)
                elif isinstance(battery_result, str) and battery_result.isdigit():
                    self._battery_level = int(battery_result)

                # Check for low battery (only if we have a valid battery reading)
                if isinstance(self._battery_level, (int, float)) and self._battery_level < 20:
                    self._trigger_event_callbacks("battery_low")

                time.sleep(1.0)  # Update every second

            except Exception as e:
                self.logger.warning(f"State update error for drone {self.drone_id}: {e}")
                time.sleep(2.0)

    def _start_frame_capture(self):
        """Start frame capture thread for video streaming."""
        def capture_frames():
            while self._video_enabled and self._is_connected:
                try:
                    frame = self.tello.get_frame_read().frame
                    if frame is not None:
                        with self._frame_lock:
                            self._frame = frame
                    time.sleep(1/30)  # 30 FPS
                except Exception as e:
                    self.logger.warning(f"Frame capture error for drone {self.drone_id}: {e}")
                    time.sleep(0.1)

        frame_thread = threading.Thread(target=capture_frames, daemon=True)
        frame_thread.start()

    def _trigger_event_callbacks(self, event: str):
        """Trigger all callbacks for a specific event."""
        if event in self._event_callbacks:
            for callback in self._event_callbacks[event]:
                try:
                    callback(self)
                except Exception as e:
                    self.logger.error(f"Error in event callback for {event}: {e}")

    def _patch_tello_for_utf8_errors(self):
        """
        Patch the djitellopy Tello class to handle UTF-8 decoding errors gracefully.

        This fixes the common issue where Tello drones sometimes send malformed
        UDP packets that cause UTF-8 decoding errors.
        """
        # Store original method
        original_recv = self.tello.udp_state_socket.recv if hasattr(self.tello, 'udp_state_socket') else None

        def safe_recv(self, bufsize):
            """Safe version of socket recv that handles UTF-8 errors."""
            try:
                data = socket.socket.recv(self, bufsize)
                # Try to decode to catch potential UTF-8 issues early
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    # Log the error but don't crash
                    logging.getLogger('TelloDrone').debug(
                        f"Received malformed UTF-8 data from drone, ignoring packet"
                    )
                    # Return empty bytes to indicate no valid data
                    return b''
                return data
            except Exception as e:
                logging.getLogger('TelloDrone').debug(f"Socket recv error: {e}")
                return b''

        # Patch the recv method if socket exists
        try:
            if hasattr(self.tello, 'udp_state_socket') and self.tello.udp_state_socket:
                # Monkey patch the recv method
                import types
                self.tello.udp_state_socket.recv = types.MethodType(safe_recv, self.tello.udp_state_socket)
        except Exception as e:
            self.logger.debug(f"Could not patch UDP socket: {e}")

        # Also patch the response parsing if available
        if hasattr(self.tello, '_parse_response'):
            original_parse = self.tello._parse_response

            def safe_parse_response(response):
                """Safe version of response parsing that handles UTF-8 errors."""
                try:
                    if isinstance(response, bytes):
                        response = response.decode('utf-8', errors='ignore')
                    return original_parse(response)
                except UnicodeDecodeError:
                    self.logger.debug("Ignoring malformed response from drone")
                    return "ok"  # Return default success response
                except Exception as e:
                    self.logger.debug(f"Response parsing error: {e}")
                    return "ok"

            self.tello._parse_response = safe_parse_response

    def _safe_connect(self):
        """Safely connect to the drone with UTF-8 error handling and better diagnostics."""
        return self._safe_execute_command(self.tello.connect)

    def _safe_get_battery(self) -> int:
        """Safely get battery level with UTF-8 error handling."""
        try:
            return self.tello.get_battery()
        except UnicodeDecodeError as e:
            self.logger.warning(f"UTF-8 decode error getting battery, using default: {e}")
            return 50  # Return reasonable default
        except Exception as e:
            self.logger.warning(f"Error getting battery level: {e}")
            return 50

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self._is_connected:
            self.disconnect()

    def _safe_execute_command(self, command_func, *args, **kwargs):
        """
        Safely execute any drone command with enhanced error handling.

        Args:
            command_func: The djitellopy method to execute
            *args: Arguments to pass to the command
            **kwargs: Keyword arguments to pass to the command

        Returns:
            The result of the command execution

        Raises:
            Exception: Re-raises non-recoverable exceptions
        """
        # Check if we're in cooldown period
        if time.time() < self._error_cooldown_until:
            self.logger.warning(f"Drone {self.drone_id} in error cooldown, skipping command")
            return "error_cooldown"

        max_retries = 2
        retry_delay = 0.5

        for attempt in range(max_retries + 1):
            try:
                result = command_func(*args, **kwargs)

                # Check for motor stop error in response
                if isinstance(result, str) and "Motor stop" in result:
                    return self._handle_motor_stop_error(command_func, args, kwargs, attempt, max_retries)

                # Reset failure counters on success
                self._consecutive_failures = 0
                self._movement_delays["current"] = self._movement_delays["base"]

                return result

            except UnicodeDecodeError as e:
                if attempt < max_retries:
                    self.logger.warning(
                        f"UTF-8 decode error (attempt {attempt + 1}/{max_retries + 1}), retrying: {e}"
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"UTF-8 decode error after {max_retries + 1} attempts: {e}")
                    return "ok"  # Return success to prevent cascading failures
            except Exception as e:
                self.logger.error(f"Command execution error: {e}")
                self._consecutive_failures += 1
                raise e

    def _handle_motor_stop_error(self, command_func, args, kwargs, current_attempt, max_retries):
        """
        Enhanced motor stop error handling with exponential backoff and degraded mode.

        Args:
            command_func: The command function that failed
            args: Command arguments
            kwargs: Command keyword arguments
            current_attempt: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            Result of retry or error status
        """
        self._motor_stop_count += 1
        self._consecutive_failures += 1
        self._last_error_time = time.time()

        # Configure retry settings (these could come from config)
        motor_stop_max_retries = 5
        base_delay = 2.0
        backoff_multiplier = 1.5
        max_delay = 10.0

        self.logger.warning(
            f"Motor stop error #{self._motor_stop_count} for drone {self.drone_id} "
            f"(attempt {current_attempt + 1})"
        )

        if current_attempt >= motor_stop_max_retries:
            self.logger.error(
                f"Motor stop error persists after {motor_stop_max_retries} attempts, "
                f"entering degraded mode for drone {self.drone_id}"
            )
            self._enter_degraded_mode()
            return "error_motor_stop_persistent"

        # Calculate exponential backoff delay with jitter
        delay = min(base_delay * (backoff_multiplier ** current_attempt), max_delay)
        jitter = random.uniform(-0.5, 0.5)  # Add jitter to prevent synchronization
        delay += jitter

        self.logger.info(f"Retrying motor stop command after {delay:.1f}s delay...")
        time.sleep(delay)

        # Try the command again with potentially reduced parameters
        try:
            if self._is_in_degraded_mode and hasattr(command_func, '__name__'):
                # Modify command parameters for degraded mode
                modified_args, modified_kwargs = self._modify_command_for_degraded_mode(
                    command_func.__name__, args, kwargs
                )
                result = command_func(*modified_args, **modified_kwargs)
            else:
                result = command_func(*args, **kwargs)

            if isinstance(result, str) and "Motor stop" in result:
                # Still failing, try next iteration
                return self._handle_motor_stop_error(
                    command_func, args, kwargs, current_attempt + 1, max_retries
                )
            else:
                self.logger.info(f"Motor stop error resolved for drone {self.drone_id}")
                return result

        except Exception as e:
            self.logger.error(f"Motor stop retry failed: {e}")
            return self._handle_motor_stop_error(
                command_func, args, kwargs, current_attempt + 1, max_retries
            )

    def _enter_degraded_mode(self):
        """Enter degraded performance mode to handle problematic drone."""
        self._is_in_degraded_mode = True
        self._error_cooldown_until = time.time() + 30.0  # 30 second cooldown
        self._movement_delays["current"] = self._movement_delays["base"] * 3

        self.logger.warning(f"Drone {self.drone_id} entered degraded mode due to persistent errors")
        self._trigger_event_callbacks("degraded_mode_entered")

    def _exit_degraded_mode(self):
        """Exit degraded performance mode."""
        self._is_in_degraded_mode = False
        self._motor_stop_count = 0
        self._consecutive_failures = 0
        self._movement_delays["current"] = self._movement_delays["base"]

        self.logger.info(f"Drone {self.drone_id} exited degraded mode")
        self._trigger_event_callbacks("degraded_mode_exited")

    def _modify_command_for_degraded_mode(self, command_name, args, kwargs):
        """
        Modify command parameters for degraded performance mode.

        Args:
            command_name: Name of the command function
            args: Original arguments
            kwargs: Original keyword arguments

        Returns:
            Tuple of (modified_args, modified_kwargs)
        """
        modified_args = list(args)
        modified_kwargs = kwargs.copy()

        # Reduce movement distances and speeds for degraded mode
        if "go_xyz_speed" in command_name:
            # Reduce movement distances by 50%
            if len(modified_args) >= 3:
                modified_args[0] = int(modified_args[0] * 0.5)  # x
                modified_args[1] = int(modified_args[1] * 0.5)  # y
                modified_args[2] = int(modified_args[2] * 0.5)  # z
            # Reduce speed
            if len(modified_args) >= 4:
                modified_args[3] = min(int(modified_args[3] * 0.7), 30)  # speed

        elif "set_speed" in command_name:
            # Reduce speed in degraded mode
            if len(modified_args) >= 1:
                modified_args[0] = min(int(modified_args[0] * 0.7), 30)

        elif any(move_cmd in command_name for move_cmd in ["move_forward", "move_back", "move_left", "move_right", "move_up", "move_down"]):
            # Reduce single-axis movement distances
            if len(modified_args) >= 1:
                modified_args[0] = max(20, int(modified_args[0] * 0.6))  # Don't go below minimum

        return tuple(modified_args), modified_kwargs

    def is_in_degraded_mode(self) -> bool:
        """Check if drone is in degraded performance mode."""
        return self._is_in_degraded_mode

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for this drone."""
        return {
            "motor_stop_count": self._motor_stop_count,
            "consecutive_failures": self._consecutive_failures,
            "last_error_time": self._last_error_time,
            "degraded_mode": self._is_in_degraded_mode,
            "cooldown_until": self._error_cooldown_until
        }

    def reset_error_stats(self):
        """Reset error statistics and exit degraded mode."""
        self._motor_stop_count = 0
        self._consecutive_failures = 0
        self._last_error_time = 0
        self._exit_degraded_mode()
