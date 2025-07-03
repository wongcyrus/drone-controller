"""
Enhanced Tello Drone Controller with advanced features for multi-robot coordination.

This module provides an enhanced wrapper around djitellopy for better multi-robot
control, state management, and coordinated operations.
"""

import time
import threading
import logging
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
            
            # Connect to the drone
            self.tello.connect()
            
            # Verify connection by getting battery
            self._battery_level = self.tello.get_battery()
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
            self.tello.end()
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
                self.tello.takeoff()
                self._is_flying = True
                
                # Trigger takeoff callbacks
                self._trigger_event_callbacks("takeoff")
                
                self.logger.info(f"Drone {self.drone_id} takeoff successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Takeoff failed for drone {self.drone_id}: {e}")
            return False
    
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
                self.tello.land()
                self._is_flying = False
                
                # Trigger land callbacks
                self._trigger_event_callbacks("land")
                
                self.logger.info(f"Drone {self.drone_id} landing successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Landing failed for drone {self.drone_id}: {e}")
            return False
    
    def emergency_land(self):
        """Emergency landing - immediate stop of all motors."""
        try:
            with self._command_lock:
                self.logger.warning(f"Emergency landing drone {self.drone_id}")
                self.tello.emergency()
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
                self.tello.set_speed(speed)
                
                # Execute movement
                if abs(x) >= 20 or abs(y) >= 20 or abs(z) >= 20:
                    self.tello.go_xyz_speed(x, y, z, speed)
                else:
                    # Use smaller movements for fine control
                    if abs(x) >= 20:
                        self.tello.move_forward(x) if x > 0 else self.tello.move_back(abs(x))
                    if abs(y) >= 20:
                        self.tello.move_right(y) if y > 0 else self.tello.move_left(abs(y))
                    if abs(z) >= 20:
                        self.tello.move_up(z) if z > 0 else self.tello.move_down(abs(z))
                
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
                    self.tello.rotate_clockwise(angle)
                else:
                    self.tello.rotate_counter_clockwise(abs(angle))
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
            self.tello.streamon()
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
            self.tello.streamoff()
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
                self._battery_level = self.tello.get_battery()
                
                # Check for low battery
                if self._battery_level < 20:
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
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self._is_connected:
            self.disconnect()
