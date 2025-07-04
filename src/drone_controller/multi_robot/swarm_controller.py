"""
Swarm Controller for managing multiple Tello Talent drones simultaneously.

This module provides high-level coordination and synchronization capabilities
for controlling multiple drones as a unified swarm.
"""

import time
import threading
import logging
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

from ..core.tello_drone import TelloDrone


class SwarmController:
    """
    Main controller for managing a swarm of Tello drones.

    This class provides high-level coordination capabilities for multiple drones,
    including synchronized takeoff/landing, coordinated movements, and mission execution.
    """

    def __init__(self, swarm_id: str = "swarm_001"):
        """
        Initialize the SwarmController.

        Args:
            swarm_id: Unique identifier for this swarm
        """
        self.swarm_id = swarm_id
        self.drones: Dict[str, TelloDrone] = {}
        self.active_drones: List[str] = []

        # Swarm state
        self.is_initialized = False
        self.is_flying = False
        self.mission_active = False

        # Threading
        self._command_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=10)

        # Mission and coordination
        self._mission_callbacks: List[Callable] = []
        self._formation_config: Optional[Dict] = None

        # Configuration settings with defaults
        self._swarm_config = {
            'max_drones': 10,
            'takeoff_stagger_delay': 1.0,
            'landing_stagger_delay': 0.0,
            'synchronized_landing': True
        }

        # Logging
        self.logger = logging.getLogger(f"drone_controller.swarm.{swarm_id}")

        # Enhanced error handling
        self._problematic_drones = set()  # Drones with persistent errors
        self._degraded_drones = set()     # Drones in degraded mode
        self._excluded_drones = set()     # Temporarily excluded drones
        self._error_statistics = {}       # Per-drone error statistics

        # Safety limits
        self.max_drones = 10
        self.safety_distance = 100  # cm
        self.max_altitude = 300  # cm

        # Command timeout for next action after takeoff
        self.command_timeout = self._swarm_config.get('command_timeout', 15.0)  # seconds
        self._last_takeoff_time = None

    def add_drone(self, drone_id: str, ip_address: Optional[str] = None) -> bool:
        """
        Add a drone to the swarm.

        Args:
            drone_id: Unique identifier for the drone
            ip_address: IP address of the drone (optional)

        Returns:
            bool: True if drone added successfully, False otherwise
        """
        if len(self.drones) >= self.max_drones:
            self.logger.error(f"Cannot add drone {drone_id}: maximum drone limit ({self.max_drones}) reached")
            return False

        if drone_id in self.drones:
            self.logger.warning(f"Drone {drone_id} already exists in swarm")
            return False

        try:
            drone = TelloDrone(drone_id, ip_address)
            self.drones[drone_id] = drone

            # Add swarm-level event callbacks
            drone.add_event_callback("battery_low", self._on_drone_battery_low)
            drone.add_event_callback("emergency", self._on_drone_emergency)
            drone.add_event_callback("connection_lost", self._on_drone_connection_lost)

            self.logger.info(f"Added drone {drone_id} to swarm {self.swarm_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add drone {drone_id}: {e}")
            return False

    def remove_drone(self, drone_id: str) -> bool:
        """
        Remove a drone from the swarm.

        Args:
            drone_id: ID of the drone to remove

        Returns:
            bool: True if drone removed successfully, False otherwise
        """
        if drone_id not in self.drones:
            self.logger.warning(f"Drone {drone_id} not found in swarm")
            return False

        try:
            # Disconnect drone if connected
            drone = self.drones[drone_id]
            if drone._is_connected:
                drone.disconnect()

            # Remove from active list
            if drone_id in self.active_drones:
                self.active_drones.remove(drone_id)

            # Remove from drones dict
            del self.drones[drone_id]

            self.logger.info(f"Removed drone {drone_id} from swarm {self.swarm_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove drone {drone_id}: {e}")
            return False

    def initialize_swarm(self, timeout: float = 30.0) -> bool:
        """
        Initialize all drones in the swarm (connect and prepare for flight).

        Args:
            timeout: Maximum time to wait for all drones to connect

        Returns:
            bool: True if all drones initialized successfully, False otherwise
        """
        if not self.drones:
            self.logger.error("No drones in swarm to initialize")
            return False

        self.logger.info(f"Initializing swarm {self.swarm_id} with {len(self.drones)} drones...")

        # Connect all drones in parallel
        futures = {}
        for drone_id, drone in self.drones.items():
            future = self._executor.submit(drone.connect)
            futures[future] = drone_id

        # Wait for all connections
        connected_drones = []
        start_time = time.time()

        for future in as_completed(futures, timeout=timeout):
            drone_id = futures[future]
            try:
                success = future.result()
                if success:
                    connected_drones.append(drone_id)
                    self.logger.info(f"Drone {drone_id} connected successfully")
                else:
                    self.logger.error(f"Failed to connect drone {drone_id}")
            except Exception as e:
                self.logger.error(f"Exception connecting drone {drone_id}: {e}")

        self.active_drones = connected_drones
        self.is_initialized = len(connected_drones) > 0

        if self.is_initialized:
            self.logger.info(f"Swarm initialization complete: {len(connected_drones)}/{len(self.drones)} drones active")
        else:
            self.logger.error("Swarm initialization failed: no drones connected")

        return self.is_initialized

    def shutdown_swarm(self):
        """Shutdown the entire swarm and disconnect all drones."""
        self.logger.info(f"Shutting down swarm {self.swarm_id}...")

        # Land all flying drones first
        if self.is_flying:
            self.land_all()

        # Disconnect all drones in parallel
        futures = []
        for drone_id in list(self.active_drones):
            drone = self.drones[drone_id]
            future = self._executor.submit(drone.disconnect)
            futures.append(future)

        # Wait for all disconnections
        for future in as_completed(futures, timeout=10.0):
            try:
                future.result()
            except Exception as e:
                self.logger.warning(f"Error during drone disconnect: {e}")

        self.active_drones.clear()
        self.is_initialized = False
        self.is_flying = False
        self.mission_active = False

        self.logger.info(f"Swarm {self.swarm_id} shutdown complete")

    def takeoff_all(self, stagger_delay: float = 1.0, synchronized: Optional[bool] = None) -> bool:
        """
        Take off all active drones in the swarm.

        Args:
            stagger_delay: Delay between each drone takeoff (seconds) - ignored if synchronized=True
            synchronized: If True, all drones take off simultaneously; if False, use stagger delay

        Returns:
            bool: True if all drones took off successfully, False otherwise
        """
        if not self.active_drones:
            self.logger.error("No active drones to take off")
            return False

        if self.is_flying:
            self.logger.warning("Swarm is already flying")
            return True

        self.logger.info(f"Taking off {len(self.active_drones)} drones...")

        # Get configured settings
        stagger_delay = self._swarm_config.get('takeoff_stagger_delay', stagger_delay)
        if synchronized is None:
            synchronized = self._swarm_config.get('synchronized_takeoff', True)

        if synchronized:
            # Synchronized takeoff - all drones take off together
            return self._takeoff_all_synchronized()
        else:
            # Sequential takeoff with stagger delay for safety
            return self._takeoff_all_sequential(stagger_delay)

    def _takeoff_all_synchronized(self) -> bool:
        """Take off all drones simultaneously using parallel execution."""
        self.logger.info("Executing synchronized takeoff for all drones...")

        # Start takeoff commands for all drones simultaneously
        futures = {}
        for drone_id in self.active_drones:
            drone = self.drones[drone_id]
            future = self._executor.submit(drone.takeoff)
            futures[future] = drone_id

        # Wait for all takeoffs to complete with timeout
        successful_takeoffs = []
        for future in as_completed(futures, timeout=30.0):
            drone_id = futures[future]
            try:
                success = future.result()
                if success:
                    successful_takeoffs.append(drone_id)
                    self.logger.info(f"Drone {drone_id} synchronized takeoff successful")
                else:
                    self.logger.error(f"Drone {drone_id} synchronized takeoff failed")
            except Exception as e:
                self.logger.error(f"Exception during synchronized takeoff for drone {drone_id}: {e}")

        self.is_flying = len(successful_takeoffs) > 0
        success_rate = len(successful_takeoffs) / len(futures) if futures else 1.0

        if success_rate >= 0.8:
            # Record takeoff time for command timeout enforcement
            self._last_takeoff_time = time.time()

        self.logger.info(f"Synchronized takeoff complete: {len(successful_takeoffs)}/{len(futures)} drones airborne ({success_rate:.1%})")
        return success_rate >= 0.8

    def _takeoff_all_sequential(self, stagger_delay: float) -> bool:
        """Take off all drones sequentially with stagger delay."""
        self.logger.info(f"Executing sequential takeoff with {stagger_delay}s delay...")

        successful_takeoffs = []
        for i, drone_id in enumerate(self.active_drones):
            drone = self.drones[drone_id]

            # Add delay between takeoffs
            if i > 0 and stagger_delay > 0:
                time.sleep(stagger_delay)

            success = drone.takeoff()
            if success:
                successful_takeoffs.append(drone_id)
                self.logger.info(f"Drone {drone_id} takeoff successful")
            else:
                self.logger.error(f"Drone {drone_id} takeoff failed")

        self.is_flying = len(successful_takeoffs) > 0
        success_rate = len(successful_takeoffs) / len(self.active_drones)

        if success_rate >= 0.8:
            # Record takeoff time for command timeout enforcement
            self._last_takeoff_time = time.time()

        self.logger.info(f"Sequential takeoff complete: {len(successful_takeoffs)}/{len(self.active_drones)} drones airborne ({success_rate:.1%})")

        return success_rate >= 0.8  # Consider successful if 80% of drones are airborne

    def land_all(self, stagger_delay: float = 0.0, synchronized: bool = True) -> bool:
        """
        Land all flying drones in the swarm.

        Args:
            stagger_delay: Delay between each drone landing (seconds) - use 0 for simultaneous
            synchronized: If True, all drones land simultaneously; if False, use stagger delay

        Returns:
            bool: True if all drones landed successfully, False otherwise
        """
        # Reset command timeout when landing command is received
        self.reset_command_timeout()

        if not self.is_flying:
            self.logger.warning("Swarm is not flying")
            return True

        self.logger.info(f"Landing {len(self.active_drones)} drones...")

        # Get configured stagger delay
        stagger_delay = self._swarm_config.get('landing_stagger_delay', stagger_delay)

        if synchronized or stagger_delay == 0.0:
            # Simultaneous landing using parallel execution
            return self._land_all_synchronized()
        else:
            # Sequential landing with stagger delay
            return self._land_all_sequential(stagger_delay)

    def _land_all_synchronized(self) -> bool:
        """Land all drones simultaneously using parallel execution."""
        self.logger.info("Executing synchronized landing for all drones...")

        # Start landing commands for all drones simultaneously
        futures = {}
        for drone_id in self.active_drones:
            drone = self.drones[drone_id]
            if drone._is_flying:
                future = self._executor.submit(drone.land)
                futures[future] = drone_id

        # Wait for all landings to complete
        successful_landings = []
        for future in as_completed(futures, timeout=30.0):
            drone_id = futures[future]
            try:
                success = future.result()
                if success:
                    successful_landings.append(drone_id)
                    self.logger.info(f"Drone {drone_id} synchronized landing successful")
                else:
                    self.logger.error(f"Drone {drone_id} synchronized landing failed")
            except Exception as e:
                self.logger.error(f"Exception during synchronized landing for drone {drone_id}: {e}")

        self.is_flying = False
        success_rate = len(successful_landings) / len(futures) if futures else 1.0

        self.logger.info(f"Synchronized landing complete: {len(successful_landings)}/{len(futures)} drones landed ({success_rate:.1%})")
        return success_rate >= 0.8

    def _land_all_sequential(self, stagger_delay: float) -> bool:
        """Land all drones sequentially with stagger delay."""
        self.logger.info(f"Executing sequential landing with {stagger_delay}s delay...")

        # Sequential landing with stagger delay
        successful_landings = []
        for i, drone_id in enumerate(self.active_drones):
            drone = self.drones[drone_id]

            if drone._is_flying:
                # Add delay between landings
                if i > 0 and stagger_delay > 0:
                    time.sleep(stagger_delay)

                success = drone.land()
                if success:
                    successful_landings.append(drone_id)
                    self.logger.info(f"Drone {drone_id} landing successful")
                else:
                    self.logger.error(f"Drone {drone_id} landing failed")

        self.is_flying = False
        success_rate = len(successful_landings) / len(self.active_drones)

        self.logger.info(f"Landing complete: {len(successful_landings)}/{len(self.active_drones)} drones landed ({success_rate:.1%})")

        return success_rate >= 0.8

    def emergency_stop_all(self):
        """Emergency stop all drones - immediate landing."""
        self.logger.warning("EMERGENCY STOP - All drones landing immediately!")

        # Emergency land all drones in parallel
        futures = []
        for drone_id in self.active_drones:
            drone = self.drones[drone_id]
            if drone._is_flying:
                future = self._executor.submit(drone.emergency_land)
                futures.append(future)

        # Wait for all emergency landings
        for future in as_completed(futures, timeout=5.0):
            try:
                future.result()
            except Exception as e:
                self.logger.error(f"Error during emergency landing: {e}")

        self.is_flying = False
        self.mission_active = False
        self.logger.warning("Emergency stop complete")

    def move_swarm_formation(self, formation_offsets: Dict[str, Dict[str, int]], speed: int = 50) -> bool:
        """
        Move drones to maintain formation with specified offsets.

        Args:
            formation_offsets: Dict mapping drone_id to position offset {x, y, z}
            speed: Movement speed for all drones

        Returns:
            bool: True if formation movement successful, False otherwise
        """
        # Reset command timeout when movement command is received
        self.reset_command_timeout()

        if not self.is_flying:
            self.logger.error("Cannot move formation: swarm not flying")
            return False

        self.logger.info("Moving swarm in formation...")

        # Execute formation movement in parallel
        futures = {}
        for drone_id in self.active_drones:
            if drone_id in formation_offsets:
                drone = self.drones[drone_id]
                offsets = formation_offsets[drone_id]
                future = self._executor.submit(
                    drone.move,
                    offsets.get("x", 0),
                    offsets.get("y", 0),
                    offsets.get("z", 0),
                    speed
                )
                futures[future] = drone_id

        # Wait for all movements to complete
        successful_moves = []
        for future in as_completed(futures, timeout=30.0):
            drone_id = futures[future]
            try:
                success = future.result()
                if success:
                    successful_moves.append(drone_id)
            except Exception as e:
                self.logger.error(f"Formation movement failed for drone {drone_id}: {e}")

        success_rate = len(successful_moves) / len(futures)
        self.logger.info(f"Formation movement complete: {len(successful_moves)}/{len(futures)} drones moved successfully ({success_rate:.1%})")

        return success_rate >= 0.8

    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the entire swarm.

        Returns:
            dict: Swarm status information
        """
        drone_states = {}
        for drone_id, drone in self.drones.items():
            drone_states[drone_id] = drone.get_state()

        # Calculate swarm statistics
        active_count = len(self.active_drones)
        flying_count = sum(1 for drone_id in self.active_drones if self.drones[drone_id]._is_flying)
        avg_battery = sum(self.drones[drone_id]._battery_level for drone_id in self.active_drones) / active_count if active_count > 0 else 0

        return {
            "swarm_id": self.swarm_id,
            "total_drones": len(self.drones),
            "active_drones": active_count,
            "flying_drones": flying_count,
            "is_initialized": self.is_initialized,
            "is_flying": self.is_flying,
            "mission_active": self.mission_active,
            "average_battery": avg_battery,
            "drone_states": drone_states,
            "formation_config": self._formation_config
        }

    def execute_coordinated_command(self, command_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a command on all active drones with enhanced error handling.

        Args:
            command_func: Function to execute on each drone
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Dict containing results for each drone
        """
        # Filter out excluded and problematic drones
        operational_drones = [
            drone_id for drone_id in self.active_drones
            if drone_id not in self._excluded_drones
        ]

        if not operational_drones:
            self.logger.error("No operational drones available for command execution")
            return {}

        self.logger.info(f"Executing coordinated command on {len(operational_drones)} drones")

        futures = {}
        for drone_id in operational_drones:
            future = self._executor.submit(self._execute_drone_command_with_error_handling,
                                         drone_id, command_func, *args, **kwargs)
            futures[future] = drone_id

        results = {}
        for future in as_completed(futures, timeout=30.0):
            drone_id = futures[future]
            try:
                result = future.result()
                results[drone_id] = result

                # Check for motor stop errors in result
                if isinstance(result, dict) and not result.get("success", True):
                    self._handle_drone_error(drone_id, result.get("error", "Unknown error"))

            except Exception as e:
                error_msg = str(e)
                results[drone_id] = {"success": False, "error": error_msg}
                self._handle_drone_error(drone_id, error_msg)
                self.logger.error(f"Command failed for drone {drone_id}: {e}")

        return results

    def _execute_drone_command_with_error_handling(self, drone_id: str, command_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute a command on a single drone with enhanced error handling.

        Args:
            drone_id: ID of the drone
            command_func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Dict containing success status and result/error
        """
        try:
            drone = self.drones[drone_id]
            result = command_func(drone, *args, **kwargs)

            # Check for motor stop or other error indicators
            if isinstance(result, str) and "Motor stop" in result:
                return {
                    "success": False,
                    "error": "Motor stop error",
                    "result": result,
                    "requires_degraded_mode": True
                }
            elif isinstance(result, str) and "error" in result.lower():
                return {
                    "success": False,
                    "error": f"Command error: {result}",
                    "result": result
                }
            else:
                return {"success": True, "result": result}

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "exception": e
            }

    def _handle_drone_error(self, drone_id: str, error_msg: str):
        """
        Handle errors from individual drones.

        Args:
            drone_id: ID of the drone with error
            error_msg: Error message
        """
        # Track error statistics
        if drone_id not in self._error_statistics:
            self._error_statistics[drone_id] = {
                "total_errors": 0,
                "motor_stop_errors": 0,
                "last_error_time": 0,
                "consecutive_errors": 0
            }

        stats = self._error_statistics[drone_id]
        stats["total_errors"] += 1
        stats["last_error_time"] = time.time()
        stats["consecutive_errors"] += 1

        if "Motor stop" in error_msg:
            stats["motor_stop_errors"] += 1
            self.logger.warning(f"Motor stop error #{stats['motor_stop_errors']} for drone {drone_id}")

            # Check if we should mark this drone as problematic
            if stats["motor_stop_errors"] >= 3:
                self._mark_drone_problematic(drone_id)

        # Auto-exclude drone if too many consecutive errors
        if stats["consecutive_errors"] >= 5:
            self._temporarily_exclude_drone(drone_id)

    def _mark_drone_problematic(self, drone_id: str):
        """Mark a drone as problematic due to persistent errors."""
        self._problematic_drones.add(drone_id)
        self.logger.warning(f"Drone {drone_id} marked as problematic due to persistent motor stop errors")

        # Check if drone supports degraded mode
        drone = self.drones.get(drone_id)
        if drone and hasattr(drone, 'is_in_degraded_mode'):
            if not drone.is_in_degraded_mode():
                self.logger.info(f"Attempting to put drone {drone_id} in degraded mode")
                drone._enter_degraded_mode()
                self._degraded_drones.add(drone_id)

    def _temporarily_exclude_drone(self, drone_id: str, duration: float = 60.0):
        """
        Temporarily exclude a drone from operations.

        Args:
            drone_id: ID of the drone to exclude
            duration: Exclusion duration in seconds
        """
        self._excluded_drones.add(drone_id)
        self.logger.warning(f"Temporarily excluding drone {drone_id} for {duration} seconds")

        # Schedule re-inclusion
        def re_include_drone():
            time.sleep(duration)
            if drone_id in self._excluded_drones:
                self._excluded_drones.remove(drone_id)
                # Reset consecutive error counter
                if drone_id in self._error_statistics:
                    self._error_statistics[drone_id]["consecutive_errors"] = 0
                self.logger.info(f"Re-including drone {drone_id} after exclusion period")

        threading.Thread(target=re_include_drone, daemon=True).start()

    def get_swarm_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the swarm.

        Returns:
            Dict containing swarm health information
        """
        total_drones = len(self.drones)
        operational_drones = len([d for d in self.active_drones if d not in self._excluded_drones])
        degraded_drones = len(self._degraded_drones)
        problematic_drones = len(self._problematic_drones)

        return {
            "total_drones": total_drones,
            "active_drones": len(self.active_drones),
            "operational_drones": operational_drones,
            "degraded_drones": degraded_drones,
            "problematic_drones": problematic_drones,
            "excluded_drones": len(self._excluded_drones),
            "operational_percentage": operational_drones / total_drones * 100 if total_drones > 0 else 0,
            "error_statistics": self._error_statistics.copy()
        }

    def force_exclude_drone(self, drone_id: str, reason: str = "Manual exclusion"):
        """
        Manually exclude a drone from operations.

        Args:
            drone_id: ID of the drone to exclude
            reason: Reason for exclusion
        """
        self._excluded_drones.add(drone_id)
        self.logger.warning(f"Manually excluding drone {drone_id}: {reason}")

    def force_include_drone(self, drone_id: str):
        """
        Manually re-include a previously excluded drone.

        Args:
            drone_id: ID of the drone to re-include
        """
        if drone_id in self._excluded_drones:
            self._excluded_drones.remove(drone_id)
            # Reset error counters
            if drone_id in self._error_statistics:
                self._error_statistics[drone_id]["consecutive_errors"] = 0
            self.logger.info(f"Manually re-including drone {drone_id}")

    def reset_drone_error_stats(self, drone_id: str):
        """
        Reset error statistics for a specific drone.

        Args:
            drone_id: ID of the drone
        """
        if drone_id in self._error_statistics:
            self._error_statistics[drone_id] = {
                "total_errors": 0,
                "motor_stop_errors": 0,
                "last_error_time": 0,
                "consecutive_errors": 0
            }

        # Remove from problematic sets
        self._problematic_drones.discard(drone_id)
        self._degraded_drones.discard(drone_id)
        self._excluded_drones.discard(drone_id)

        # Exit degraded mode if applicable
        drone = self.drones.get(drone_id)
        if drone and hasattr(drone, 'reset_error_stats'):
            drone.reset_error_stats()

        self.logger.info(f"Reset error statistics for drone {drone_id}")

    def update_swarm_config(self, config: Dict[str, Any]):
        """
        Update swarm configuration settings.

        Args:
            config: Dictionary containing swarm configuration
        """
        if config:
            self._swarm_config.update(config)
            self.max_drones = self._swarm_config.get('max_drones', 10)
            self.logger.info(f"Updated swarm configuration: {self._swarm_config}")

    def get_swarm_config(self) -> Dict[str, Any]:
        """Get current swarm configuration."""
        return self._swarm_config.copy()

    def _on_drone_battery_low(self, drone: TelloDrone):
        """Handle low battery event from a drone."""
        self.logger.warning(f"Low battery warning from drone {drone.drone_id}: {drone._battery_level}%")

        # Consider emergency landing if battery is critically low
        if drone._battery_level < 10:
            self.logger.error(f"Critical battery level for drone {drone.drone_id} - initiating emergency landing")
            drone.emergency_land()

    def _on_drone_emergency(self, drone: TelloDrone):
        """Handle emergency event from a drone."""
        self.logger.error(f"Emergency event from drone {drone.drone_id}")

        # Remove from active drones list
        if drone.drone_id in self.active_drones:
            self.active_drones.remove(drone.drone_id)

        # Check if we should stop the entire mission
        if len(self.active_drones) < len(self.drones) * 0.5:  # If less than 50% drones active
            self.logger.error("Too many drone failures - initiating swarm emergency stop")
            self.emergency_stop_all()

    def _on_drone_connection_lost(self, drone: TelloDrone):
        """Handle connection lost event from a drone."""
        self.logger.error(f"Connection lost to drone {drone.drone_id}")

        # Remove from active drones list
        if drone.drone_id in self.active_drones:
            self.active_drones.remove(drone.drone_id)

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.is_initialized:
            self.shutdown_swarm()
        self._executor.shutdown(wait=True)

    def check_command_timeout(self) -> bool:
        """
        Check if command timeout has been exceeded after takeoff.

        Returns:
            bool: True if timeout exceeded, False otherwise
        """
        if self._last_takeoff_time is None or not self.is_flying:
            return False

        elapsed_time = time.time() - self._last_takeoff_time
        if elapsed_time > self.command_timeout:
            self.logger.warning(f"Command timeout exceeded ({elapsed_time:.1f}s > {self.command_timeout}s) - initiating emergency landing")
            return True
        return False

    def reset_command_timeout(self):
        """Reset the command timeout timer (call when a new command is received)."""
        self._last_takeoff_time = None

    def enforce_command_timeout(self) -> bool:
        """
        Automatically enforce command timeout by landing drones if timeout exceeded.

        Returns:
            bool: True if timeout was enforced (drones landed), False otherwise
        """
        if self.check_command_timeout():
            self.logger.warning("Enforcing command timeout - emergency landing all drones")
            self.emergency_stop_all()
            return True
        return False
