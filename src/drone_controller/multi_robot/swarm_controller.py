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
        
        # Logging
        self.logger = logging.getLogger(f"SwarmController_{swarm_id}")
        self.logger.setLevel(logging.INFO)
        
        # Safety limits
        self.max_drones = 10
        self.safety_distance = 100  # cm
        self.max_altitude = 300  # cm
        
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
    
    def takeoff_all(self, stagger_delay: float = 1.0) -> bool:
        """
        Take off all active drones in the swarm.
        
        Args:
            stagger_delay: Delay between each drone takeoff (seconds)
            
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
        
        # Sequential takeoff with stagger delay for safety
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
        
        self.logger.info(f"Takeoff complete: {len(successful_takeoffs)}/{len(self.active_drones)} drones airborne ({success_rate:.1%})")
        
        return success_rate >= 0.8  # Consider successful if 80% of drones are airborne
    
    def land_all(self, stagger_delay: float = 0.5) -> bool:
        """
        Land all flying drones in the swarm.
        
        Args:
            stagger_delay: Delay between each drone landing (seconds)
            
        Returns:
            bool: True if all drones landed successfully, False otherwise
        """
        if not self.is_flying:
            self.logger.warning("Swarm is not flying")
            return True
        
        self.logger.info(f"Landing {len(self.active_drones)} drones...")
        
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
        Execute a command on all active drones simultaneously.
        
        Args:
            command_func: Function to execute on each drone
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            dict: Results from each drone
        """
        if not self.active_drones:
            self.logger.error("No active drones to execute command on")
            return {}
        
        self.logger.info(f"Executing coordinated command on {len(self.active_drones)} drones")
        
        # Execute command on all drones in parallel
        futures = {}
        for drone_id in self.active_drones:
            drone = self.drones[drone_id]
            future = self._executor.submit(command_func, drone, *args, **kwargs)
            futures[future] = drone_id
        
        # Collect results
        results = {}
        for future in as_completed(futures, timeout=30.0):
            drone_id = futures[future]
            try:
                result = future.result()
                results[drone_id] = {"success": True, "result": result}
            except Exception as e:
                results[drone_id] = {"success": False, "error": str(e)}
                self.logger.error(f"Command failed for drone {drone_id}: {e}")
        
        return results
    
    def set_formation_config(self, formation_config: Dict):
        """Set the formation configuration for the swarm."""
        self._formation_config = formation_config
        self.logger.info(f"Formation configuration set: {formation_config}")
    
    def add_mission_callback(self, callback: Callable):
        """Add a callback function for mission events."""
        self._mission_callbacks.append(callback)
    
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
