"""
Multi-robot swarm demonstration with formation flying.

This example demonstrates controlling multiple Tello Talent drones in
coordinated formations using the SwarmController and FormationManager.
"""

import time
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_controller.multi_robot.swarm_controller import SwarmController
from drone_controller.multi_robot.formation_manager import FormationManager, FormationType
from drone_controller.utils.logging_utils import setup_drone_logging
from drone_controller.utils.config_manager import DroneConfig


def swarm_formation_demo():
    """Demonstrate multi-robot swarm operations with formation flying."""
    
    # Setup logging
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting swarm formation demonstration")
    
    # Load configuration
    config = DroneConfig()
    swarm_config = config.get_swarm_config()
    
    # Create swarm controller
    swarm = SwarmController("demo_swarm")
    
    # Create formation manager
    formation_mgr = FormationManager("demo_formation")
    
    try:
        # Add drones to swarm (adjust IPs as needed)
        drone_configs = [
            {"id": "drone_001", "ip": "192.168.10.1"},
            {"id": "drone_002", "ip": "192.168.10.2"},
            {"id": "drone_003", "ip": "192.168.10.3"},
        ]
        
        logger.info("Adding drones to swarm...")
        for drone_config in drone_configs:
            success = swarm.add_drone(drone_config["id"], drone_config["ip"])
            if success:
                # Also add to formation manager
                drone = swarm.drones[drone_config["id"]]
                formation_mgr.add_drone(drone)
                logger.info(f"Added {drone_config['id']} to swarm and formation")
            else:
                logger.error(f"Failed to add {drone_config['id']} to swarm")
        
        # Set formation leader
        if drone_configs:
            formation_mgr.set_leader(drone_configs[0]["id"])
        
        # Initialize swarm
        logger.info("Initializing swarm...")
        if not swarm.initialize_swarm(timeout=30.0):
            logger.error("Swarm initialization failed")
            return
        
        # Check swarm status
        status = swarm.get_swarm_status()
        logger.info(f"Swarm ready: {status['active_drones']}/{status['total_drones']} drones active")
        
        # Take off all drones
        logger.info("Taking off swarm...")
        if not swarm.takeoff_all(stagger_delay=2.0):
            logger.error("Swarm takeoff failed")
            return
        
        time.sleep(5)  # Wait for stable hover
        
        # Demonstration sequence
        formations_demo = [
            ("line", lambda: formation_mgr.create_line_formation(spacing=150, orientation=0)),
            ("circle", lambda: formation_mgr.create_circle_formation(radius=200)),
            ("v_formation", lambda: formation_mgr.create_v_formation(spacing=150, angle=60)),
            ("diamond", lambda: formation_mgr.create_diamond_formation(size=180)),
        ]
        
        for formation_name, formation_func in formations_demo:
            logger.info(f"Creating {formation_name} formation...")
            
            # Create formation
            if formation_func():
                logger.info(f"Moving to {formation_name} formation...")
                if formation_mgr.move_to_formation(speed=25, timeout=30.0):
                    logger.info(f"{formation_name.capitalize()} formation achieved!")
                    
                    # Hold formation for a moment
                    time.sleep(5)
                    
                    # Demonstrate formation movements
                    if formation_name == "line":
                        logger.info("Moving line formation forward...")
                        formation_mgr.move_formation(50, 0, 0, 25)
                        time.sleep(3)
                        
                        logger.info("Rotating line formation...")
                        formation_mgr.rotate_formation(45, 25)
                        time.sleep(3)
                    
                    elif formation_name == "circle":
                        logger.info("Scaling circle formation...")
                        formation_mgr.scale_formation(1.5, 25)
                        time.sleep(3)
                        
                        logger.info("Rotating circle formation...")
                        formation_mgr.rotate_formation(90, 25)
                        time.sleep(3)
                    
                    elif formation_name == "v_formation":
                        logger.info("Moving V formation...")
                        formation_mgr.move_formation(0, 50, 0, 25)
                        time.sleep(3)
                    
                    # Check formation status
                    form_status = formation_mgr.get_formation_status()
                    logger.info(f"Formation status: {form_status['is_active']}, drones: {form_status['num_drones']}")
                    
                    # Check for collision risks
                    collision_risks = formation_mgr.check_collision_risk()
                    if collision_risks:
                        logger.warning(f"Collision risks detected: {len(collision_risks)} pairs")
                        for drone1, drone2, distance in collision_risks:
                            logger.warning(f"  {drone1} - {drone2}: {distance:.1f}cm")
                    
                else:
                    logger.error(f"Failed to achieve {formation_name} formation")
            else:
                logger.error(f"Failed to create {formation_name} formation")
            
            time.sleep(2)  # Brief pause between formations
        
        # Demonstrate coordinated movement
        logger.info("Demonstrating coordinated swarm movement...")
        
        # Move entire swarm
        movement_sequence = [
            (50, 0, 0, "forward"),
            (0, 50, 0, "right"),
            (0, 0, 30, "up"),
            (-50, -50, -30, "back to start")
        ]
        
        for dx, dy, dz, description in movement_sequence:
            logger.info(f"Moving swarm {description}...")
            formation_offsets = {}
            for drone_id in swarm.active_drones:
                formation_offsets[drone_id] = {"x": dx, "y": dy, "z": dz}
            
            success = swarm.move_swarm_formation(formation_offsets, speed=30)
            if success:
                logger.info(f"Swarm movement {description} successful")
            else:
                logger.warning(f"Swarm movement {description} partially failed")
            
            time.sleep(3)
        
        # Final status check
        final_status = swarm.get_swarm_status()
        logger.info(f"Final swarm status: {final_status['flying_drones']} drones flying, "
                   f"average battery: {final_status['average_battery']:.1f}%")
        
        # Land all drones
        logger.info("Landing swarm...")
        if swarm.land_all(stagger_delay=1.0):
            logger.info("Swarm landing successful")
        else:
            logger.warning("Swarm landing partially failed")
        
        logger.info("Swarm formation demonstration completed!")
        
    except KeyboardInterrupt:
        logger.warning("Demonstration interrupted by user")
        logger.info("Emergency landing all drones...")
        swarm.emergency_stop_all()
    
    except Exception as e:
        logger.error(f"Unexpected error during demonstration: {e}")
        logger.info("Emergency landing all drones...")
        swarm.emergency_stop_all()
    
    finally:
        # Shutdown swarm
        logger.info("Shutting down swarm...")
        swarm.shutdown_swarm()
        logger.info("Demonstration complete")


def simple_two_drone_demo():
    """Simplified demonstration with just two drones."""
    
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting simple two-drone demonstration")
    
    swarm = SwarmController("simple_swarm")
    formation_mgr = FormationManager("simple_formation")
    
    try:
        # Add two drones
        drone_configs = [
            {"id": "drone_A", "ip": None},  # Use None for auto-discovery
            {"id": "drone_B", "ip": None},
        ]
        
        for drone_config in drone_configs:
            if swarm.add_drone(drone_config["id"], drone_config["ip"]):
                drone = swarm.drones[drone_config["id"]]
                formation_mgr.add_drone(drone)
        
        # Initialize and takeoff
        if swarm.initialize_swarm(timeout=20.0):
            if swarm.takeoff_all(stagger_delay=2.0):
                time.sleep(3)
                
                # Simple line formation
                formation_mgr.create_line_formation(spacing=200)
                formation_mgr.move_to_formation(speed=25)
                time.sleep(5)
                
                # Move formation around
                formation_mgr.move_formation(100, 0, 0, 25)
                time.sleep(3)
                formation_mgr.rotate_formation(180, 25)
                time.sleep(3)
                
                # Land
                swarm.land_all()
            
        swarm.shutdown_swarm()
        
    except Exception as e:
        logger.error(f"Error in simple demo: {e}")
        swarm.emergency_stop_all()
        swarm.shutdown_swarm()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Swarm formation demonstration")
    parser.add_argument("--simple", action="store_true", 
                       help="Run simple two-drone demo instead of full demo")
    args = parser.parse_args()
    
    if args.simple:
        simple_two_drone_demo()
    else:
        swarm_formation_demo()
