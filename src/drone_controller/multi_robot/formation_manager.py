"""
Formation Manager for coordinated multi-drone formations and patterns.

This module provides sophisticated formation control capabilities including
predefined formations, dynamic formation changes, and collision avoidance.
"""

import math
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from enum import Enum
import numpy as np

from ..core.tello_drone import TelloDrone


class FormationType(Enum):
    """Predefined formation types."""
    LINE = "line"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    SQUARE = "square"
    TRIANGLE = "triangle"
    V_FORMATION = "v_formation"
    GRID = "grid"
    CUSTOM = "custom"


class FormationManager:
    """
    Advanced formation manager for coordinating drone positions and movements.
    
    This class provides sophisticated formation control including predefined
    formations, dynamic formation changes, path planning, and collision avoidance.
    """
    
    def __init__(self, formation_id: str = "formation_001"):
        """
        Initialize the FormationManager.
        
        Args:
            formation_id: Unique identifier for this formation
        """
        self.formation_id = formation_id
        self.drones: Dict[str, TelloDrone] = {}
        self.formation_positions: Dict[str, Dict[str, float]] = {}
        self.current_formation: Optional[FormationType] = None
        self.formation_parameters: Dict[str, Any] = {}
        
        # Formation state
        self.is_active = False
        self.leader_drone_id: Optional[str] = None
        self.center_position = {"x": 0, "y": 0, "z": 100}  # Default center position
        
        # Safety parameters
        self.min_distance = 100  # Minimum distance between drones (cm)
        self.collision_threshold = 80  # Distance threshold for collision avoidance (cm)
        self.max_speed = 30  # Maximum movement speed for formation changes
        
        # Logging
        self.logger = logging.getLogger(f"FormationManager_{formation_id}")
        self.logger.setLevel(logging.INFO)
    
    def add_drone(self, drone: TelloDrone, position_id: Optional[str] = None):
        """
        Add a drone to the formation.
        
        Args:
            drone: TelloDrone instance to add
            position_id: Optional specific position ID in formation
        """
        if position_id is None:
            position_id = f"pos_{len(self.drones)}"
        
        self.drones[drone.drone_id] = drone
        
        # Set initial position
        self.formation_positions[drone.drone_id] = {
            "x": 0, "y": 0, "z": 100,
            "position_id": position_id
        }
        
        self.logger.info(f"Added drone {drone.drone_id} to formation at position {position_id}")
    
    def remove_drone(self, drone_id: str):
        """Remove a drone from the formation."""
        if drone_id in self.drones:
            del self.drones[drone_id]
            del self.formation_positions[drone_id]
            
            # Update leader if necessary
            if self.leader_drone_id == drone_id:
                self.set_leader(list(self.drones.keys())[0] if self.drones else None)
            
            self.logger.info(f"Removed drone {drone_id} from formation")
    
    def set_leader(self, drone_id: Optional[str]):
        """
        Set the leader drone for the formation.
        
        Args:
            drone_id: ID of the drone to set as leader, or None for no leader
        """
        if drone_id is None or drone_id in self.drones:
            self.leader_drone_id = drone_id
            self.logger.info(f"Set formation leader to: {drone_id}")
        else:
            self.logger.error(f"Cannot set leader: drone {drone_id} not in formation")
    
    def create_line_formation(self, spacing: float = 150, orientation: float = 0) -> bool:
        """
        Create a line formation.
        
        Args:
            spacing: Distance between drones in line (cm)
            orientation: Line orientation in degrees (0 = horizontal)
            
        Returns:
            bool: True if formation created successfully
        """
        if not self.drones:
            self.logger.error("No drones available for formation")
            return False
        
        self.current_formation = FormationType.LINE
        self.formation_parameters = {"spacing": spacing, "orientation": orientation}
        
        drone_ids = list(self.drones.keys())
        num_drones = len(drone_ids)
        
        # Calculate positions along line
        start_offset = -(num_drones - 1) * spacing / 2
        
        for i, drone_id in enumerate(drone_ids):
            offset = start_offset + i * spacing
            
            # Apply rotation based on orientation
            x = offset * math.cos(math.radians(orientation))
            y = offset * math.sin(math.radians(orientation))
            
            self.formation_positions[drone_id] = {
                "x": x,
                "y": y, 
                "z": self.center_position["z"],
                "position_id": f"line_{i}"
            }
        
        self.logger.info(f"Created line formation with {num_drones} drones (spacing: {spacing}cm, orientation: {orientation}°)")
        return True
    
    def create_circle_formation(self, radius: float = 200) -> bool:
        """
        Create a circular formation.
        
        Args:
            radius: Radius of the circle (cm)
            
        Returns:
            bool: True if formation created successfully
        """
        if not self.drones:
            self.logger.error("No drones available for formation")
            return False
        
        self.current_formation = FormationType.CIRCLE
        self.formation_parameters = {"radius": radius}
        
        drone_ids = list(self.drones.keys())
        num_drones = len(drone_ids)
        
        if num_drones == 1:
            # Single drone at center
            self.formation_positions[drone_ids[0]] = {
                "x": 0, "y": 0, "z": self.center_position["z"],
                "position_id": "center"
            }
        else:
            # Multiple drones around circle
            angle_step = 360 / num_drones
            
            for i, drone_id in enumerate(drone_ids):
                angle = math.radians(i * angle_step)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                self.formation_positions[drone_id] = {
                    "x": x,
                    "y": y,
                    "z": self.center_position["z"],
                    "position_id": f"circle_{i}"
                }
        
        self.logger.info(f"Created circle formation with {num_drones} drones (radius: {radius}cm)")
        return True
    
    def create_diamond_formation(self, size: float = 200) -> bool:
        """
        Create a diamond formation.
        
        Args:
            size: Size of the diamond (cm)
            
        Returns:
            bool: True if formation created successfully
        """
        if not self.drones:
            self.logger.error("No drones available for formation")
            return False
        
        if len(self.drones) < 4:
            self.logger.error("Diamond formation requires at least 4 drones")
            return False
        
        self.current_formation = FormationType.DIAMOND
        self.formation_parameters = {"size": size}
        
        drone_ids = list(self.drones.keys())
        
        # Diamond positions (front, left, right, back, center if 5+ drones)
        positions = [
            {"x": 0, "y": size/2, "z": self.center_position["z"], "position_id": "front"},  # Front
            {"x": -size/2, "y": 0, "z": self.center_position["z"], "position_id": "left"},  # Left
            {"x": size/2, "y": 0, "z": self.center_position["z"], "position_id": "right"},  # Right
            {"x": 0, "y": -size/2, "z": self.center_position["z"], "position_id": "back"},  # Back
        ]
        
        # Add center positions for additional drones
        if len(drone_ids) > 4:
            positions.append({"x": 0, "y": 0, "z": self.center_position["z"], "position_id": "center"})
        
        for i, drone_id in enumerate(drone_ids[:len(positions)]):
            self.formation_positions[drone_id] = positions[i]
        
        self.logger.info(f"Created diamond formation with {min(len(drone_ids), len(positions))} drones (size: {size}cm)")
        return True
    
    def create_v_formation(self, spacing: float = 150, angle: float = 45) -> bool:
        """
        Create a V formation.
        
        Args:
            spacing: Distance between drones (cm)
            angle: Angle of the V in degrees
            
        Returns:
            bool: True if formation created successfully
        """
        if not self.drones:
            self.logger.error("No drones available for formation")
            return False
        
        self.current_formation = FormationType.V_FORMATION
        self.formation_parameters = {"spacing": spacing, "angle": angle}
        
        drone_ids = list(self.drones.keys())
        num_drones = len(drone_ids)
        
        # Leader at the front
        if self.leader_drone_id and self.leader_drone_id in drone_ids:
            leader_index = drone_ids.index(self.leader_drone_id)
            drone_ids[0], drone_ids[leader_index] = drone_ids[leader_index], drone_ids[0]
        
        # Calculate V formation positions
        half_angle = math.radians(angle / 2)
        
        for i, drone_id in enumerate(drone_ids):
            if i == 0:
                # Leader at front point
                self.formation_positions[drone_id] = {
                    "x": 0, "y": 0, "z": self.center_position["z"],
                    "position_id": "leader"
                }
            else:
                # Alternate left and right sides
                side = 1 if i % 2 == 1 else -1  # Right side for odd indices, left for even
                row = (i + 1) // 2  # Row number (how far back)
                
                x = -row * spacing * math.cos(half_angle)  # Negative = behind leader
                y = side * row * spacing * math.sin(half_angle)
                
                self.formation_positions[drone_id] = {
                    "x": x,
                    "y": y,
                    "z": self.center_position["z"],
                    "position_id": f"v_{side}_{row}"
                }
        
        self.logger.info(f"Created V formation with {num_drones} drones (spacing: {spacing}cm, angle: {angle}°)")
        return True
    
    def create_grid_formation(self, rows: int, cols: int, spacing: float = 150) -> bool:
        """
        Create a grid formation.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            spacing: Distance between drones (cm)
            
        Returns:
            bool: True if formation created successfully
        """
        if not self.drones:
            self.logger.error("No drones available for formation")
            return False
        
        if len(self.drones) > rows * cols:
            self.logger.warning(f"More drones ({len(self.drones)}) than grid positions ({rows * cols})")
        
        self.current_formation = FormationType.GRID
        self.formation_parameters = {"rows": rows, "cols": cols, "spacing": spacing}
        
        drone_ids = list(self.drones.keys())
        
        # Calculate grid positions
        start_x = -(cols - 1) * spacing / 2
        start_y = -(rows - 1) * spacing / 2
        
        for i, drone_id in enumerate(drone_ids[:rows * cols]):
            row = i // cols
            col = i % cols
            
            x = start_x + col * spacing
            y = start_y + row * spacing
            
            self.formation_positions[drone_id] = {
                "x": x,
                "y": y,
                "z": self.center_position["z"],
                "position_id": f"grid_{row}_{col}"
            }
        
        self.logger.info(f"Created {rows}x{cols} grid formation with {min(len(drone_ids), rows * cols)} drones")
        return True
    
    def move_to_formation(self, speed: int = 30, timeout: float = 60.0) -> bool:
        """
        Move all drones to their assigned formation positions.
        
        Args:
            speed: Movement speed for all drones
            timeout: Maximum time to wait for formation completion
            
        Returns:
            bool: True if formation movement successful
        """
        if not self.formation_positions:
            self.logger.error("No formation positions defined")
            return False
        
        if not all(drone._is_flying for drone in self.drones.values()):
            self.logger.error("All drones must be flying before moving to formation")
            return False
        
        self.logger.info(f"Moving {len(self.drones)} drones to formation positions...")
        
        start_time = time.time()
        max_iterations = int(timeout / 2.0)  # Check every 2 seconds
        
        for iteration in range(max_iterations):
            all_in_position = True
            
            for drone_id, target_pos in self.formation_positions.items():
                if drone_id not in self.drones:
                    continue
                
                drone = self.drones[drone_id]
                current_pos = drone._current_position
                
                # Calculate movement needed
                dx = target_pos["x"] - current_pos["x"]
                dy = target_pos["y"] - current_pos["y"]
                dz = target_pos["z"] - current_pos["z"]
                
                # Check if drone is close enough to target
                distance = math.sqrt(dx**2 + dy**2 + dz**2)
                if distance > 30:  # 30cm tolerance
                    all_in_position = False
                    
                    # Move towards target position
                    max_move = 100  # Maximum single movement distance
                    if distance > max_move:
                        # Scale movement to max_move distance
                        scale = max_move / distance
                        dx *= scale
                        dy *= scale
                        dz *= scale
                    
                    # Execute movement
                    drone.move(int(dx), int(dy), int(dz), speed)
            
            if all_in_position:
                self.is_active = True
                elapsed_time = time.time() - start_time
                self.logger.info(f"Formation achieved in {elapsed_time:.1f} seconds")
                return True
            
            time.sleep(2.0)  # Wait before next iteration
        
        self.logger.warning(f"Formation timeout after {timeout} seconds")
        return False
    
    def move_formation(self, dx: int, dy: int, dz: int, speed: int = 30) -> bool:
        """
        Move the entire formation by the specified offset.
        
        Args:
            dx: Forward/backward movement (cm)
            dy: Left/right movement (cm)
            dz: Up/down movement (cm)
            speed: Movement speed
            
        Returns:
            bool: True if formation movement successful
        """
        if not self.is_active:
            self.logger.error("Formation not active - cannot move")
            return False
        
        self.logger.info(f"Moving formation by offset: dx={dx}, dy={dy}, dz={dz}")
        
        # Update center position
        self.center_position["x"] += dx
        self.center_position["y"] += dy
        self.center_position["z"] += dz
        
        # Update all formation positions
        for drone_id in self.formation_positions:
            self.formation_positions[drone_id]["x"] += dx
            self.formation_positions[drone_id]["y"] += dy
            self.formation_positions[drone_id]["z"] += dz
        
        # Move all drones simultaneously
        successful_moves = 0
        for drone_id, drone in self.drones.items():
            if drone._is_flying:
                success = drone.move(dx, dy, dz, speed)
                if success:
                    successful_moves += 1
        
        success_rate = successful_moves / len(self.drones)
        self.logger.info(f"Formation movement: {successful_moves}/{len(self.drones)} drones moved successfully ({success_rate:.1%})")
        
        return success_rate >= 0.8
    
    def rotate_formation(self, angle: float, speed: int = 30) -> bool:
        """
        Rotate the entire formation around its center.
        
        Args:
            angle: Rotation angle in degrees (positive = clockwise)
            speed: Movement speed
            
        Returns:
            bool: True if rotation successful
        """
        if not self.is_active:
            self.logger.error("Formation not active - cannot rotate")
            return False
        
        self.logger.info(f"Rotating formation by {angle} degrees")
        
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Rotate all positions around center
        for drone_id in self.formation_positions:
            pos = self.formation_positions[drone_id]
            rel_x = pos["x"] - self.center_position["x"]
            rel_y = pos["y"] - self.center_position["y"]
            
            # Apply rotation matrix
            new_rel_x = rel_x * cos_a - rel_y * sin_a
            new_rel_y = rel_x * sin_a + rel_y * cos_a
            
            pos["x"] = self.center_position["x"] + new_rel_x
            pos["y"] = self.center_position["y"] + new_rel_y
        
        # Move drones to new positions
        return self.move_to_formation(speed)
    
    def scale_formation(self, scale_factor: float, speed: int = 30) -> bool:
        """
        Scale the formation size by the specified factor.
        
        Args:
            scale_factor: Scale factor (1.0 = no change, 2.0 = double size, 0.5 = half size)
            speed: Movement speed
            
        Returns:
            bool: True if scaling successful
        """
        if not self.is_active:
            self.logger.error("Formation not active - cannot scale")
            return False
        
        if scale_factor <= 0:
            self.logger.error("Scale factor must be positive")
            return False
        
        self.logger.info(f"Scaling formation by factor {scale_factor}")
        
        # Check collision constraints
        min_scaled_distance = self.min_distance / scale_factor
        if scale_factor > 1.0 and min_scaled_distance < self.collision_threshold:
            self.logger.warning(f"Scaling may cause collisions (min distance: {min_scaled_distance:.1f}cm)")
        
        # Scale all positions relative to center
        for drone_id in self.formation_positions:
            pos = self.formation_positions[drone_id]
            rel_x = pos["x"] - self.center_position["x"]
            rel_y = pos["y"] - self.center_position["y"]
            
            pos["x"] = self.center_position["x"] + rel_x * scale_factor
            pos["y"] = self.center_position["y"] + rel_y * scale_factor
        
        # Update formation parameters if applicable
        if "spacing" in self.formation_parameters:
            self.formation_parameters["spacing"] *= scale_factor
        if "radius" in self.formation_parameters:
            self.formation_parameters["radius"] *= scale_factor
        if "size" in self.formation_parameters:
            self.formation_parameters["size"] *= scale_factor
        
        # Move drones to new positions
        return self.move_to_formation(speed)
    
    def get_formation_status(self) -> Dict[str, Any]:
        """
        Get current formation status and information.
        
        Returns:
            dict: Formation status information
        """
        drone_distances = {}
        if len(self.drones) > 1:
            drone_ids = list(self.drones.keys())
            for i, drone_id_1 in enumerate(drone_ids):
                for drone_id_2 in drone_ids[i+1:]:
                    pos1 = self.drones[drone_id_1]._current_position
                    pos2 = self.drones[drone_id_2]._current_position
                    
                    distance = math.sqrt(
                        (pos1["x"] - pos2["x"])**2 + 
                        (pos1["y"] - pos2["y"])**2 + 
                        (pos1["z"] - pos2["z"])**2
                    )
                    drone_distances[f"{drone_id_1}-{drone_id_2}"] = distance
        
        return {
            "formation_id": self.formation_id,
            "current_formation": self.current_formation.value if self.current_formation else None,
            "formation_parameters": self.formation_parameters,
            "is_active": self.is_active,
            "num_drones": len(self.drones),
            "leader_drone": self.leader_drone_id,
            "center_position": self.center_position,
            "formation_positions": self.formation_positions,
            "drone_distances": drone_distances,
            "safety_settings": {
                "min_distance": self.min_distance,
                "collision_threshold": self.collision_threshold,
                "max_speed": self.max_speed
            }
        }
    
    def check_collision_risk(self) -> List[Tuple[str, str, float]]:
        """
        Check for potential collisions between drones.
        
        Returns:
            list: List of tuples (drone_id_1, drone_id_2, distance) for close pairs
        """
        collision_risks = []
        
        if len(self.drones) < 2:
            return collision_risks
        
        drone_ids = list(self.drones.keys())
        for i, drone_id_1 in enumerate(drone_ids):
            for drone_id_2 in drone_ids[i+1:]:
                pos1 = self.drones[drone_id_1]._current_position
                pos2 = self.drones[drone_id_2]._current_position
                
                distance = math.sqrt(
                    (pos1["x"] - pos2["x"])**2 + 
                    (pos1["y"] - pos2["y"])**2 + 
                    (pos1["z"] - pos2["z"])**2
                )
                
                if distance < self.collision_threshold:
                    collision_risks.append((drone_id_1, drone_id_2, distance))
        
        return collision_risks
    
    def emergency_spread(self, spread_distance: float = 200) -> bool:
        """
        Emergency procedure to spread drones apart to avoid collisions.
        
        Args:
            spread_distance: Target distance between drones (cm)
            
        Returns:
            bool: True if emergency spread successful
        """
        self.logger.warning("Executing emergency spread formation")
        
        if not self.drones:
            return False
        
        drone_ids = list(self.drones.keys())
        num_drones = len(drone_ids)
        
        # Create simple spread pattern
        if num_drones == 1:
            return True  # Single drone, no collision risk
        
        # Create circle formation with large radius for emergency spread
        radius = max(spread_distance, self.collision_threshold * 2)
        angle_step = 360 / num_drones
        
        for i, drone_id in enumerate(drone_ids):
            angle = math.radians(i * angle_step)
            target_x = self.center_position["x"] + radius * math.cos(angle)
            target_y = self.center_position["y"] + radius * math.sin(angle)
            
            # Move to spread position
            drone = self.drones[drone_id]
            current_pos = drone._current_position
            
            dx = int(target_x - current_pos["x"])
            dy = int(target_y - current_pos["y"])
            
            drone.move(dx, dy, 0, self.max_speed)
        
        self.logger.info(f"Emergency spread executed for {num_drones} drones")
        return True
