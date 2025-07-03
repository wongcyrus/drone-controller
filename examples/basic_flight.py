"""
Basic example: Single drone takeoff, movement, and landing.

This example demonstrates the basic functionality of the TelloDrone class
for controlling a single Tello Talent drone.
"""

import time
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drone_controller.core.tello_drone import TelloDrone
from drone_controller.utils.logging_utils import setup_drone_logging


def basic_flight_demo():
    """Demonstrate basic flight operations with a single drone."""
    
    # Setup logging
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting basic flight demonstration")
    
    # Create drone instance
    drone = TelloDrone("demo_drone")
    
    try:
        # Connect to drone
        logger.info("Connecting to drone...")
        if not drone.connect():
            logger.error("Failed to connect to drone")
            return
        
        # Get initial status
        status = drone.get_state()
        logger.info(f"Initial battery level: {status['battery']}%")
        
        # Check battery level
        if status['battery'] < 30:
            logger.warning("Low battery level - consider charging before flight")
            return
        
        # Take off
        logger.info("Taking off...")
        if not drone.takeoff():
            logger.error("Takeoff failed")
            return
        
        time.sleep(3)  # Wait for stable hover
        
        # Perform basic movements
        logger.info("Performing basic movements...")
        
        # Move forward
        logger.info("Moving forward 100cm")
        drone.move(100, 0, 0, 30)
        time.sleep(2)
        
        # Move right
        logger.info("Moving right 50cm")
        drone.move(0, 50, 0, 30)
        time.sleep(2)
        
        # Move up
        logger.info("Moving up 50cm")
        drone.move(0, 0, 50, 30)
        time.sleep(2)
        
        # Rotate clockwise
        logger.info("Rotating clockwise 90 degrees")
        drone.rotate(90)
        time.sleep(2)
        
        # Return to start position
        logger.info("Returning to start position")
        drone.move(-100, -50, -50, 30)
        time.sleep(3)
        
        # Rotate back
        logger.info("Rotating back to original orientation")
        drone.rotate(-90)
        time.sleep(2)
        
        # Land
        logger.info("Landing...")
        if not drone.land():
            logger.error("Landing failed")
            return
        
        logger.info("Basic flight demonstration completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("Flight interrupted by user")
        if drone._is_flying:
            logger.info("Emergency landing...")
            drone.emergency_land()
    
    except Exception as e:
        logger.error(f"Unexpected error during flight: {e}")
        if drone._is_flying:
            logger.info("Emergency landing...")
            drone.emergency_land()
    
    finally:
        # Disconnect
        logger.info("Disconnecting from drone...")
        drone.disconnect()
        logger.info("Demonstration complete")


if __name__ == "__main__":
    basic_flight_demo()
