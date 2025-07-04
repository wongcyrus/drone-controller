"""
Enhanced error handling and recovery utilities for drone operations.

This module provides utilities for diagnosing and recovering from common
drone errors, particularly motor stop errors.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from ..core.tello_drone import TelloDrone
from ..multi_robot.swarm_controller import SwarmController


class DroneErrorHandler:
    """Utility class for handling and recovering from drone errors."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler.

        Args:
            logger: Logger instance to use
        """
        self.logger = logger or logging.getLogger("drone_controller.error_handler")

    def diagnose_motor_stop_error(self, drone: TelloDrone) -> Dict[str, Any]:
        """
        Diagnose potential causes of motor stop errors.

        Args:
            drone: The drone experiencing motor stop errors

        Returns:
            Dict containing diagnosis information
        """
        diagnosis = {
            "drone_id": drone.drone_id,
            "battery_level": drone._battery_level,
            "connection_status": drone._is_connected,
            "flying_status": drone._is_flying,
            "error_stats": drone.get_error_stats() if hasattr(drone, 'get_error_stats') else {},
            "potential_causes": [],
            "recommended_actions": []
        }

        # Check battery level
        battery = diagnosis["battery_level"]
        if isinstance(battery, (int, float)) and battery < 20:
            diagnosis["potential_causes"].append("Low battery level")
            diagnosis["recommended_actions"].append("Land drone and replace/charge battery")
        elif isinstance(battery, (int, float)) and battery < 30:
            diagnosis["potential_causes"].append("Marginal battery level")
            diagnosis["recommended_actions"].append("Consider landing soon")

        # Check error frequency
        error_stats = diagnosis["error_stats"]
        if error_stats.get("motor_stop_count", 0) > 3:
            diagnosis["potential_causes"].append("Hardware motor issue")
            diagnosis["recommended_actions"].append("Physical inspection of motors required")

        if error_stats.get("consecutive_failures", 0) > 2:
            diagnosis["potential_causes"].append("Communication/timing issues")
            diagnosis["recommended_actions"].append("Reduce command frequency, use degraded mode")

        # Check if drone is overheated (inferred from error pattern)
        if error_stats.get("motor_stop_count", 0) > 1 and time.time() - error_stats.get("last_error_time", 0) < 60:
            diagnosis["potential_causes"].append("Possible motor overheating")
            diagnosis["recommended_actions"].append("Allow cooling period before retry")

        return diagnosis

    def attempt_motor_stop_recovery(self, drone: TelloDrone, max_attempts: int = 3) -> bool:
        """
        Attempt to recover from motor stop errors.

        Args:
            drone: The drone to recover
            max_attempts: Maximum recovery attempts

        Returns:
            bool: True if recovery successful, False otherwise
        """
        self.logger.info(f"Attempting motor stop recovery for drone {drone.drone_id}")

        for attempt in range(max_attempts):
            self.logger.info(f"Recovery attempt {attempt + 1}/{max_attempts}")

            try:
                # Step 1: Wait for any ongoing operations to complete
                time.sleep(3.0)

                # Step 2: Try a simple status check
                battery = drone._battery_level
                self.logger.info(f"Battery level: {battery}%")

                # Step 3: If flying, try a small movement
                if drone._is_flying:
                    self.logger.info("Attempting small test movement...")
                    success = drone.move(0, 0, 10, 20)  # Small upward movement at low speed

                    if success:
                        self.logger.info("Test movement successful - recovery appears successful")
                        return True
                    else:
                        self.logger.warning(f"Test movement failed on attempt {attempt + 1}")

                # Step 4: If not flying, try takeoff (if safe)
                elif drone._is_connected:
                    self.logger.info("Drone not flying, testing connection with battery check...")
                    # Just test connection without takeoff for safety
                    if isinstance(battery, (int, float)) and battery > 20:
                        self.logger.info("Connection test successful")
                        return True

                # Step 5: Progressive wait between attempts
                if attempt < max_attempts - 1:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    self.logger.info(f"Waiting {wait_time} seconds before next attempt...")
                    time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"Recovery attempt {attempt + 1} failed: {e}")

        self.logger.error(f"Motor stop recovery failed after {max_attempts} attempts")
        return False

    def handle_swarm_motor_stop_errors(self, swarm: SwarmController) -> Dict[str, Any]:
        """
        Handle motor stop errors across a swarm.

        Args:
            swarm: The swarm controller

        Returns:
            Dict containing recovery results
        """
        health_status = swarm.get_swarm_health_status()
        error_stats = health_status.get("error_statistics", {})

        recovery_results = {
            "total_problematic_drones": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "permanently_excluded": 0,
            "drone_details": {}
        }

        for drone_id, stats in error_stats.items():
            if stats.get("motor_stop_errors", 0) > 0:
                recovery_results["total_problematic_drones"] += 1

                drone = swarm.drones.get(drone_id)
                if drone:
                    self.logger.info(f"Handling motor stop errors for drone {drone_id}")

                    # Diagnose the issue
                    diagnosis = self.diagnose_motor_stop_error(drone)
                    recovery_results["drone_details"][drone_id] = diagnosis

                    # Attempt recovery if appropriate
                    if stats["motor_stop_errors"] < 5:  # Don't attempt if too many errors
                        recovery_results["recovery_attempts"] += 1

                        if self.attempt_motor_stop_recovery(drone):
                            recovery_results["successful_recoveries"] += 1
                            swarm.reset_drone_error_stats(drone_id)
                            self.logger.info(f"Successfully recovered drone {drone_id}")
                        else:
                            # Mark for exclusion if recovery failed
                            swarm.force_exclude_drone(drone_id, "Failed motor stop recovery")
                            recovery_results["permanently_excluded"] += 1
                            self.logger.warning(f"Permanently excluding drone {drone_id}")
                    else:
                        # Too many errors, exclude immediately
                        swarm.force_exclude_drone(drone_id, "Excessive motor stop errors")
                        recovery_results["permanently_excluded"] += 1
                        self.logger.warning(f"Excluding drone {drone_id} due to excessive errors")

        return recovery_results

    def generate_error_report(self, swarm: SwarmController) -> str:
        """
        Generate a comprehensive error report for the swarm.

        Args:
            swarm: The swarm controller

        Returns:
            String containing the error report
        """
        health_status = swarm.get_swarm_health_status()

        report = []
        report.append("=== SWARM ERROR REPORT ===")
        report.append(f"Total Drones: {health_status['total_drones']}")
        report.append(f"Operational: {health_status['operational_drones']} ({health_status['operational_percentage']:.1f}%)")
        report.append(f"Degraded: {health_status['degraded_drones']}")
        report.append(f"Excluded: {health_status['excluded_drones']}")
        report.append("")

        error_stats = health_status.get("error_statistics", {})
        if error_stats:
            report.append("=== PER-DRONE ERROR DETAILS ===")
            for drone_id, stats in error_stats.items():
                if stats["total_errors"] > 0:
                    report.append(f"Drone {drone_id}:")
                    report.append(f"  Total Errors: {stats['total_errors']}")
                    report.append(f"  Motor Stop Errors: {stats['motor_stop_errors']}")
                    report.append(f"  Consecutive Failures: {stats['consecutive_failures']}")
                    if stats["last_error_time"] > 0:
                        time_since = time.time() - stats["last_error_time"]
                        report.append(f"  Last Error: {time_since:.0f} seconds ago")
                    report.append("")
        else:
            report.append("No error statistics available")

        return "\n".join(report)


def print_motor_stop_troubleshooting_guide():
    """Print a troubleshooting guide for motor stop errors."""
    guide = """
=== MOTOR STOP ERROR TROUBLESHOOTING GUIDE ===

Motor stop errors can occur due to several factors:

1. LOW BATTERY
   - Symptoms: Errors increase as battery drops below 30%
   - Solution: Land drone and replace/charge battery
   - Prevention: Monitor battery levels regularly

2. MOTOR OVERHEATING
   - Symptoms: Errors after extended flight time
   - Solution: Allow 5-10 minute cooling period
   - Prevention: Limit continuous flight time

3. COMMUNICATION TIMING
   - Symptoms: Intermittent errors, especially in swarms
   - Solution: Reduce command frequency, add delays
   - Prevention: Use staggered commands, avoid rapid movements

4. HARDWARE ISSUES
   - Symptoms: Persistent errors on same drone
   - Solution: Physical motor inspection, possible replacement
   - Prevention: Regular maintenance checks

5. ENVIRONMENTAL FACTORS
   - Symptoms: Errors in specific locations/conditions
   - Solution: Change flight area, check for interference
   - Prevention: Test in controlled environment first

RECOVERY STRATEGIES:
- Implement exponential backoff (2s, 4s, 8s delays)
- Use degraded mode (reduced speed/distance)
- Temporarily exclude problematic drones
- Monitor swarm health percentage
- Always maintain minimum operational threshold

EMERGENCY PROCEDURES:
- If >50% of swarm affected: Emergency land all
- If single drone persistent: Exclude from formation
- If battery critical: Immediate landing priority
- If hardware suspected: Ground inspection required
"""
    print(guide)
