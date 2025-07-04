"""
Demo script for synchronized takeoff with command timeout in swarm mode.

This example demonstrates the new synchronized takeoff feature where all drones
take off together, and the 15-second timeout for the next command.
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_controller.multi_robot.swarm_controller import SwarmController
from drone_controller.multi_robot.formation_manager import FormationManager
from drone_controller.utils.logging_utils import setup_drone_logging
from drone_controller.utils.config_manager import DroneConfig


def synchronized_takeoff_demo():
    """Demonstrate synchronized takeoff with command timeout."""

    # Setup logging
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting synchronized takeoff demo")

    # Load configuration
    config = DroneConfig()

    # Create swarm controller
    swarm = SwarmController("sync_demo_swarm")

    # Create formation manager
    formation_mgr = FormationManager("sync_demo_formation")

    try:
        # Add drones to swarm (adjust IPs as needed)
        drone_configs = [
            {"id": "drone_001", "ip": "192.168.137.21"},
            {"id": "drone_002", "ip": "192.168.137.22"},
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

        # Demonstrate synchronized takeoff
        logger.info("=== SYNCHRONIZED TAKEOFF DEMO ===")
        logger.info("Taking off all drones simultaneously...")

        if not swarm.takeoff_all(synchronized=True):
            logger.error("Synchronized takeoff failed")
            return

        logger.info("✅ Synchronized takeoff successful!")
        logger.info("All drones are now airborne simultaneously")

        # Show command timeout warning
        logger.warning("⚠️  COMMAND TIMEOUT ACTIVE: 15 seconds to issue next command!")

        # Wait and show countdown
        for i in range(5, 0, -1):
            time.sleep(1)
            if swarm._last_takeoff_time:
                remaining = swarm.command_timeout - (time.time() - swarm._last_takeoff_time)
                logger.info(f"Time remaining for next command: {remaining:.1f} seconds")

        # Create a formation quickly to reset timeout
        logger.info("Creating line formation to reset timeout...")
        formation_mgr.create_line_formation(spacing=150)
        if formation_mgr.move_to_formation(speed=25, timeout=30.0):
            logger.info("✅ Line formation achieved - timeout reset!")
            swarm.reset_command_timeout()
        else:
            logger.error("Formation creation failed")

        # Hold formation briefly
        time.sleep(3)

        # Test timeout enforcement by waiting longer than 15 seconds
        logger.info("=== TIMEOUT ENFORCEMENT DEMO ===")
        logger.info("Taking off again and then waiting to demonstrate timeout...")

        # Land first
        swarm.land_all(synchronized=True)
        time.sleep(3)

        # Take off again
        if swarm.takeoff_all(synchronized=True):
            logger.info("✅ Second synchronized takeoff successful!")
            logger.warning("⚠️  Now waiting 16 seconds to demonstrate timeout enforcement...")

            # Start a timer thread to check timeout status
            def timeout_monitor():
                for i in range(16):
                    time.sleep(1)
                    if swarm._last_takeoff_time:
                        elapsed = time.time() - swarm._last_takeoff_time
                        remaining = max(0, swarm.command_timeout - elapsed)
                        if remaining <= 0:
                            logger.error(f"⚠️  TIMEOUT EXCEEDED at {elapsed:.1f} seconds!")
                            break
                        else:
                            logger.info(f"Timeout countdown: {remaining:.1f} seconds remaining")

            timeout_thread = threading.Thread(target=timeout_monitor)
            timeout_thread.start()
            timeout_thread.join()

            # Check if timeout was enforced
            if swarm.check_command_timeout():
                logger.error("❌ Command timeout exceeded - emergency landing should be triggered")
                swarm.enforce_command_timeout()
            else:
                logger.info("✅ Timeout enforcement working correctly")

        # Final landing
        logger.info("=== FINAL LANDING ===")
        if swarm.is_flying:
            if swarm.land_all(synchronized=True):
                logger.info("✅ Final synchronized landing successful")
            else:
                logger.warning("Landing partially failed")

        logger.info("=== DEMO COMPLETE ===")
        logger.info("Key features demonstrated:")
        logger.info("  ✅ Synchronized takeoff - all drones lift off together")
        logger.info("  ✅ 15-second command timeout after takeoff")
        logger.info("  ✅ Automatic emergency landing on timeout")
        logger.info("  ✅ Timeout reset on new commands")

    except KeyboardInterrupt:
        logger.warning("Demo interrupted by user")
        logger.info("Emergency landing all drones...")
        swarm.emergency_stop_all()

    except Exception as e:
        logger.error(f"Unexpected error during demo: {e}")
        logger.info("Emergency landing all drones...")
        swarm.emergency_stop_all()

    finally:
        # Shutdown swarm
        logger.info("Shutting down swarm...")
        swarm.shutdown_swarm()
        logger.info("Demo complete")


if __name__ == "__main__":
    synchronized_takeoff_demo()
