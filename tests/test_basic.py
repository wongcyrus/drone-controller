"""
Basic tests for the drone controller package.

These tests verify the core functionality without requiring actual drones.
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_controller.core.tello_drone import TelloDrone
from drone_controller.multi_robot.swarm_controller import SwarmController
from drone_controller.multi_robot.formation_manager import FormationManager, FormationType
from drone_controller.utils.config_manager import DroneConfig


class TestTelloDrone(unittest.TestCase):
    """Test cases for TelloDrone class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.drone = TelloDrone("test_drone")
    
    def test_drone_initialization(self):
        """Test drone initialization."""
        self.assertEqual(self.drone.drone_id, "test_drone")
        self.assertFalse(self.drone._is_connected)
        self.assertFalse(self.drone._is_flying)
        self.assertEqual(self.drone._battery_level, 0)
    
    def test_get_state(self):
        """Test get_state method."""
        state = self.drone.get_state()
        
        expected_keys = [
            "drone_id", "connected", "flying", "battery", 
            "position", "target_position", "video_enabled", "ip_address"
        ]
        
        for key in expected_keys:
            self.assertIn(key, state)
        
        self.assertEqual(state["drone_id"], "test_drone")
        self.assertFalse(state["connected"])
        self.assertFalse(state["flying"])


class TestSwarmController(unittest.TestCase):
    """Test cases for SwarmController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.swarm = SwarmController("test_swarm")
    
    def test_swarm_initialization(self):
        """Test swarm initialization."""
        self.assertEqual(self.swarm.swarm_id, "test_swarm")
        self.assertEqual(len(self.swarm.drones), 0)
        self.assertFalse(self.swarm.is_initialized)
        self.assertFalse(self.swarm.is_flying)
    
    def test_add_remove_drone(self):
        """Test adding and removing drones."""
        # Add drone
        success = self.swarm.add_drone("drone_001", "192.168.1.1")
        self.assertTrue(success)
        self.assertEqual(len(self.swarm.drones), 1)
        self.assertIn("drone_001", self.swarm.drones)
        
        # Try to add same drone again
        success = self.swarm.add_drone("drone_001", "192.168.1.1")
        self.assertFalse(success)
        self.assertEqual(len(self.swarm.drones), 1)
        
        # Remove drone
        success = self.swarm.remove_drone("drone_001")
        self.assertTrue(success)
        self.assertEqual(len(self.swarm.drones), 0)
    
    def test_max_drones_limit(self):
        """Test maximum drone limit."""
        original_max = self.swarm.max_drones
        self.swarm.max_drones = 2
        
        # Add drones up to limit
        self.assertTrue(self.swarm.add_drone("drone_001"))
        self.assertTrue(self.swarm.add_drone("drone_002"))
        
        # Try to exceed limit
        self.assertFalse(self.swarm.add_drone("drone_003"))
        
        self.swarm.max_drones = original_max
    
    def test_get_swarm_status(self):
        """Test get_swarm_status method."""
        status = self.swarm.get_swarm_status()
        
        expected_keys = [
            "swarm_id", "total_drones", "active_drones", "flying_drones",
            "is_initialized", "is_flying", "mission_active", "average_battery",
            "drone_states", "formation_config"
        ]
        
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status["swarm_id"], "test_swarm")
        self.assertEqual(status["total_drones"], 0)


class TestFormationManager(unittest.TestCase):
    """Test cases for FormationManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formation_mgr = FormationManager("test_formation")
        
        # Create mock drones (need 4 for diamond formation test)
        self.mock_drones = []
        for i in range(4):  # Changed from 3 to 4
            mock_drone = Mock()
            mock_drone.drone_id = f"drone_{i:03d}"
            mock_drone._is_flying = False
            mock_drone._current_position = {"x": 0, "y": 0, "z": 100}
            self.mock_drones.append(mock_drone)
            self.formation_mgr.add_drone(mock_drone)
    
    def test_formation_initialization(self):
        """Test formation manager initialization."""
        self.assertEqual(self.formation_mgr.formation_id, "test_formation")
        self.assertEqual(len(self.formation_mgr.drones), 4)  # Changed from 3 to 4
        self.assertIsNone(self.formation_mgr.current_formation)
        self.assertFalse(self.formation_mgr.is_active)
    
    def test_line_formation(self):
        """Test line formation creation."""
        success = self.formation_mgr.create_line_formation(spacing=150, orientation=0)
        self.assertTrue(success)
        self.assertEqual(self.formation_mgr.current_formation, FormationType.LINE)
        
        # Check formation positions
        self.assertEqual(len(self.formation_mgr.formation_positions), 3)
        
        # Verify spacing
        positions = list(self.formation_mgr.formation_positions.values())
        if len(positions) >= 2:
            dx = positions[1]["x"] - positions[0]["x"]
            self.assertAlmostEqual(abs(dx), 150, delta=1)
    
    def test_circle_formation(self):
        """Test circle formation creation."""
        success = self.formation_mgr.create_circle_formation(radius=200)
        self.assertTrue(success)
        self.assertEqual(self.formation_mgr.current_formation, FormationType.CIRCLE)
        
        # Check formation positions
        self.assertEqual(len(self.formation_mgr.formation_positions), 3)
        
        # Verify positions are roughly on circle
        for pos in self.formation_mgr.formation_positions.values():
            distance = (pos["x"]**2 + pos["y"]**2)**0.5
            self.assertAlmostEqual(distance, 200, delta=1)
    
    def test_diamond_formation(self):
        """Test diamond formation creation."""
        success = self.formation_mgr.create_diamond_formation(size=200)
        self.assertTrue(success)
        self.assertEqual(self.formation_mgr.current_formation, FormationType.DIAMOND)
        
        # Check formation positions
        self.assertEqual(len(self.formation_mgr.formation_positions), 4)  # Changed from 3 to 4
    
    def test_v_formation(self):
        """Test V formation creation."""
        success = self.formation_mgr.create_v_formation(spacing=150, angle=60)
        self.assertTrue(success)
        self.assertEqual(self.formation_mgr.current_formation, FormationType.V_FORMATION)
        
        # Check formation positions
        self.assertEqual(len(self.formation_mgr.formation_positions), 4)  # Updated for 4 drones
    
    def test_formation_status(self):
        """Test formation status reporting."""
        status = self.formation_mgr.get_formation_status()
        
        expected_keys = [
            "formation_id", "current_formation", "formation_parameters",
            "is_active", "num_drones", "leader_drone", "center_position",
            "formation_positions", "drone_distances", "safety_settings"
        ]
        
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status["formation_id"], "test_formation")
        self.assertEqual(status["num_drones"], 4)  # Updated for 4 drones
    
    def test_collision_risk_detection(self):
        """Test collision risk detection."""
        # Initially high collision risk since all mock drones start at same position
        risks = self.formation_mgr.check_collision_risk()
        self.assertEqual(len(risks), 6)  # 4 drones = C(4,2) = 6 pairs all at same position
        
        # Move drones apart to test no collision risk
        for i, drone in enumerate(self.mock_drones):
            drone._current_position = {"x": i * 200, "y": 0, "z": 100}
        
        risks = self.formation_mgr.check_collision_risk()
        self.assertEqual(len(risks), 0)  # No collision risk when spread apart
    
    def test_add_remove_drone(self):
        """Test adding and removing drones from formation."""
        initial_count = len(self.formation_mgr.drones)
        
        # Add new drone
        new_drone = Mock()
        new_drone.drone_id = "new_drone"
        new_drone._current_position = {"x": 0, "y": 0, "z": 100}
        
        self.formation_mgr.add_drone(new_drone)
        self.assertEqual(len(self.formation_mgr.drones), initial_count + 1)
        
        # Remove drone
        self.formation_mgr.remove_drone("new_drone")
        self.assertEqual(len(self.formation_mgr.drones), initial_count)


class TestConfigManager(unittest.TestCase):
    """Test cases for DroneConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = DroneConfig()
    
    def test_default_config_loaded(self):
        """Test that default configuration is loaded."""
        self.assertIsInstance(self.config.config_data, dict)
        self.assertIn("drones", self.config.config_data)
        self.assertIn("safety", self.config.config_data)
        self.assertIn("formations", self.config.config_data)
    
    def test_get_drone_config(self):
        """Test getting drone configuration."""
        # Get default drone config
        default_config = self.config.get_drone_config("unknown_drone")
        self.assertIsInstance(default_config, dict)
        
        # Add specific drone config
        self.config.add_drone_config("test_drone", {"ip_address": "192.168.1.100"})
        specific_config = self.config.get_drone_config("test_drone")
        self.assertEqual(specific_config["ip_address"], "192.168.1.100")
    
    def test_get_safety_config(self):
        """Test getting safety configuration."""
        safety_config = self.config.get_safety_config()
        self.assertIsInstance(safety_config, dict)
        self.assertIn("min_distance", safety_config)
        self.assertIn("collision_threshold", safety_config)
    
    def test_config_validation(self):
        """Test configuration validation."""
        errors = self.config.validate_config()
        self.assertIsInstance(errors, list)
        
        # Add invalid config and test validation
        self.config.config_data["safety"]["min_distance"] = 10  # Too small
        errors = self.config.validate_config()
        self.assertTrue(any("min_distance" in error for error in errors))
    
    def test_add_formation_config(self):
        """Test adding formation configuration."""
        formation_config = {
            "type": "custom",
            "positions": [{"x": 0, "y": 0, "z": 100}, {"x": 100, "y": 0, "z": 100}]
        }
        
        self.config.add_formation_config("test_formation", formation_config)
        retrieved_config = self.config.get_formation_config("test_formation")
        self.assertEqual(retrieved_config, formation_config)


if __name__ == "__main__":
    unittest.main()
