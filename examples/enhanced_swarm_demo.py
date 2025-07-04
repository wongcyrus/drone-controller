"""
Enhanced swarm demonstration with motor stop error handling.

This example demonstrates how to handle motor stop errors gracefully
during swarm operations using the enhanced error handling capabilities.
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
from drone_controller.utils.error_handler import DroneErrorHandler, print_motor_stop_troubleshooting_guide


def enhanced_swarm_demo():
    """Demonstrate enhanced swarm operations with motor stop error handling."""

    # Setup logging
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting enhanced swarm demonstration with error handling")

    # Print troubleshooting guide for reference
    print_motor_stop_troubleshooting_guide()

    # Load configuration
    config = DroneConfig()
    swarm_config = config.get_swarm_config()
    error_handling_config = config.get_error_handling_config()

    logger.info(f"Error handling config: {error_handling_config}")

    # Create components
    swarm = SwarmController("enhanced_demo_swarm")
    formation_mgr = FormationManager("enhanced_demo_formation")
    error_handler = DroneErrorHandler(logger)

    try:
        # Add drones to swarm (adjust IPs as needed)
        drone_configs = [
            {"id": "drone_001", "ip": "192.168.137.21"},
            {"id": "drone_002", "ip": "192.168.137.22"},
            # Add more drones as needed
        ]

        logger.info("Adding drones to swarm...")
        successful_additions = 0
        for drone_config in drone_configs:
            success = swarm.add_drone(drone_config["id"], drone_config["ip"])
            if success:
                drone = swarm.drones[drone_config["id"]]
                formation_mgr.add_drone(drone)
                logger.info(f"Added {drone_config['id']} to swarm and formation")
                successful_additions += 1
            else:
                logger.error(f"Failed to add {drone_config['id']} to swarm")

        if successful_additions == 0:
            logger.error("No drones could be added to swarm")
            return

        # Set formation leader
        if drone_configs:
            formation_mgr.set_leader(drone_configs[0]["id"])

        # Initialize swarm with error monitoring
        logger.info("Initializing swarm...")
        if not swarm.initialize_swarm(timeout=30.0):
            logger.error("Swarm initialization failed")
            return

        # Initial health check
        health_status = swarm.get_swarm_health_status()
        logger.info(f"Initial swarm health: {health_status['operational_percentage']:.1f}% operational")

        if health_status['operational_percentage'] < 50:
            logger.error("Insufficient operational drones for safe demonstration")
            return

        # Take off all drones with error monitoring
        logger.info("Taking off swarm...")
        if not swarm.takeoff_all(stagger_delay=2.0):
            logger.error("Swarm takeoff failed")

            # Check what went wrong
            post_takeoff_health = swarm.get_swarm_health_status()
            logger.info("Post-takeoff health check:")
            print(error_handler.generate_error_report(swarm))
            return

        time.sleep(5)  # Wait for stable hover

        # Enhanced formation demonstration with error handling
        formations_demo = [
            ("line", lambda: formation_mgr.create_line_formation(spacing=150, orientation=0)),
            ("circle", lambda: formation_mgr.create_circle_formation(radius=200)),
            ("v_formation", lambda: formation_mgr.create_v_formation(spacing=150, angle=60)),
        ]

        for formation_name, formation_func in formations_demo:
            logger.info(f"\\n=== {formation_name.upper()} FORMATION ===")

            # Pre-formation health check
            pre_health = swarm.get_swarm_health_status()
            logger.info(f"Pre-formation health: {pre_health['operational_percentage']:.1f}% operational")

            if pre_health['operational_percentage'] < 50:
                logger.warning("Swarm health below threshold, attempting error recovery...")

                # Attempt error recovery
                recovery_results = error_handler.handle_swarm_motor_stop_errors(swarm)
                logger.info(f"Recovery results: {recovery_results}")

                # Check health after recovery
                post_recovery_health = swarm.get_swarm_health_status()
                if post_recovery_health['operational_percentage'] < 50:
                    logger.error("Cannot continue with low operational drone count")
                    break

            # Create formation
            logger.info(f"Creating {formation_name} formation...")
            if formation_func():
                logger.info(f"Moving to {formation_name} formation...")

                # Attempt formation movement with error monitoring
                start_time = time.time()
                formation_success = formation_mgr.move_to_formation(speed=25, timeout=45.0)
                formation_time = time.time() - start_time

                if formation_success:
                    logger.info(f"{formation_name.capitalize()} formation achieved in {formation_time:.1f}s!")

                    # Post-formation health check
                    post_health = swarm.get_swarm_health_status()
                    logger.info(f"Post-formation health: {post_health['operational_percentage']:.1f}% operational")

                    # Hold formation for extended time to prevent premature landing
                    hold_time = 12  # Extended hold time
                    logger.info(f"Holding {formation_name} formation for {hold_time} seconds...")
                    time.sleep(hold_time)

                    # Check for any new errors
                    if post_health['operational_drones'] < pre_health['operational_drones']:
                        lost_drones = pre_health['operational_drones'] - post_health['operational_drones']
                        logger.warning(f"Lost {lost_drones} operational drone(s) during formation")

                        # Generate detailed error report
                        error_report = error_handler.generate_error_report(swarm)
                        logger.warning("Error report:")
                        for line in error_report.split('\\n'):
                            logger.warning(line)

                    # Hold formation
                    logger.info(f"Holding {formation_name} formation for 8 seconds...")
                    time.sleep(8)

                    # Test formation movement
                    logger.info("Testing formation movement...")
                    move_success = formation_mgr.move_formation(50, 0, 0, speed=20)
                    if move_success:
                        logger.info("Formation movement successful")
                        time.sleep(3)

                        # Move back
                        formation_mgr.move_formation(-50, 0, 0, speed=20)
                        time.sleep(3)
                    else:
                        logger.warning("Formation movement failed")

                        # Check for errors during movement
                        movement_health = swarm.get_swarm_health_status()
                        if movement_health['operational_percentage'] < post_health['operational_percentage']:
                            logger.warning("Additional errors occurred during formation movement")
                            error_handler.handle_swarm_motor_stop_errors(swarm)

                else:
                    logger.error(f"{formation_name.capitalize()} formation failed")

                    # Analyze what went wrong
                    failed_health = swarm.get_swarm_health_status()
                    logger.error(f"Formation failure health: {failed_health['operational_percentage']:.1f}% operational")

                    # Attempt error recovery
                    logger.info("Attempting error recovery after formation failure...")
                    recovery_results = error_handler.handle_swarm_motor_stop_errors(swarm)
                    logger.info(f"Recovery results: {recovery_results}")

            else:
                logger.error(f"Failed to create {formation_name} formation")

            # Inter-formation pause
            time.sleep(2)

        # Final operations
        logger.info("\\n=== DEMONSTRATION COMPLETE ===")

        # Final health report
        final_health = swarm.get_swarm_health_status()
        logger.info(f"Final swarm health: {final_health['operational_percentage']:.1f}% operational")

        # Generate comprehensive final report
        final_report = error_handler.generate_error_report(swarm)
        logger.info("Final error report:")
        for line in final_report.split('\\n'):
            logger.info(line)

        # Land all drones
        logger.info("Landing all drones...")
        if swarm.land_all(stagger_delay=1.0):
            logger.info("All drones landed successfully")
        else:
            logger.warning("Some drones may not have landed properly")

            # Emergency stop if needed
            post_landing_health = swarm.get_swarm_health_status()
            if post_landing_health['operational_percentage'] < 80:
                logger.warning("Emergency stop due to landing issues")
                swarm.emergency_stop_all()

    except KeyboardInterrupt:
        logger.warning("Demonstration interrupted by user")
        logger.info("Executing emergency landing...")
        swarm.emergency_stop_all()

    except Exception as e:
        logger.error(f"Unexpected error during demonstration: {e}")
        logger.info("Executing emergency landing...")
        swarm.emergency_stop_all()

    finally:
        # Final cleanup and reporting
        try:
            final_health = swarm.get_swarm_health_status()
            logger.info("\\n=== FINAL STATUS ===")
            logger.info(f"Demonstration completed with {final_health['operational_percentage']:.1f}% drone health")

            if final_health['error_statistics']:
                logger.info("\\nErrors encountered during demonstration:")
                for drone_id, stats in final_health['error_statistics'].items():
                    if stats['total_errors'] > 0:
                        logger.info(f"  {drone_id}: {stats['total_errors']} total errors, {stats['motor_stop_errors']} motor stop")

            # Shutdown swarm
            swarm.shutdown_swarm()
            logger.info("Swarm shutdown complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    enhanced_swarm_demo()
