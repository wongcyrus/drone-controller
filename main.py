"""
Main entry point for the Drone Controller application.

This module provides a command-line interface for controlling single drones
or multi-robot swarms of Tello Talent drones.
"""

import argparse
import time
from typing import Optional

from drone_controller.core.tello_drone import TelloDrone
from drone_controller.multi_robot.swarm_controller import SwarmController
from drone_controller.multi_robot.formation_manager import FormationManager
from drone_controller.utils.logging_utils import setup_drone_logging
from drone_controller.utils.config_manager import DroneConfig


def single_drone_mode(drone_id: str, ip_address: Optional[str] = None):
    """Run in single drone mode."""
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info(f"Starting single drone mode for {drone_id}")

    drone = TelloDrone(drone_id, ip_address)

    try:
        if drone.connect():
            status = drone.get_state()
            logger.info(f"Drone connected - Battery: {status['battery']}%")

            print(f"\nDrone {drone_id} ready for commands!")
            print("Available commands:")
            print("  takeoff - Take off the drone")
            print("  land - Land the drone")
            print("  status - Show drone status")
            print("  move <x> <y> <z> - Move drone (cm)")
            print("  rotate <angle> - Rotate drone (degrees)")
            print("  quit - Exit program")

            while True:
                try:
                    command = input("\nEnter command: ").strip().lower()

                    if command == "quit":
                        break
                    elif command == "takeoff":
                        drone.takeoff()
                    elif command == "land":
                        drone.land()
                    elif command == "status":
                        status = drone.get_state()
                        print(f"Status: {status}")
                    elif command.startswith("move"):
                        try:
                            _, x, y, z = command.split()
                            drone.move(int(x), int(y), int(z))
                        except ValueError:
                            print("Usage: move <x> <y> <z>")
                    elif command.startswith("rotate"):
                        try:
                            _, angle = command.split()
                            drone.rotate(int(angle))
                        except ValueError:
                            print("Usage: rotate <angle>")
                    else:
                        print("Unknown command")

                except KeyboardInterrupt:
                    break

    except Exception as e:
        logger.error(f"Error in single drone mode: {e}")

    finally:
        drone.disconnect()


def swarm_mode(config_file: Optional[str] = None, auto_init: bool = False, verbose: bool = False):
    """
    Run in swarm mode.

    Args:
        config_file: Optional path to configuration file.
                    If None, loads from config/drone_config.yaml by default.
        auto_init: If True, automatically initialize swarm after loading drones.
        verbose: If True, show detailed logging on console. Otherwise only warnings/errors.
    """
    # Set console logging level based on verbose flag
    console_level = "INFO" if verbose else "WARNING"
    logger = setup_drone_logging(console_level, True, "logs")
    logger.info("Starting swarm mode")

    # Load configuration
    config = DroneConfig(config_file)
    swarm_config = config.get_swarm_config()

    swarm = SwarmController("main_swarm")
    formation_mgr = FormationManager("main_formation")

    # Apply swarm configuration
    if swarm_config:
        swarm.update_swarm_config(swarm_config)

    # Auto-load drones from configuration
    drones_config = config.config_data.get("drones", {})
    auto_added_drones = 0

    for drone_id, drone_config_data in drones_config.items():
        if drone_id == "default":
            continue

        # Skip commented out drones (those without ip_address)
        ip_address = drone_config_data.get("ip_address")
        if not ip_address:
            continue

        if verbose:
            logger.info(f"Auto-adding drone {drone_id} with IP {ip_address}")

        if swarm.add_drone(drone_id, ip_address):
            drone = swarm.drones[drone_id]
            formation_mgr.add_drone(drone)
            auto_added_drones += 1
            if verbose:
                print(f"✅ Auto-added {drone_id} ({ip_address}) to swarm")
        else:
            print(f"❌ Failed to auto-add {drone_id}")

    if auto_added_drones > 0:
        if verbose:
            print(f"\n🚁 Successfully auto-loaded {auto_added_drones} drones from configuration")
        else:
            print(f"\n🚁 Auto-loaded {auto_added_drones} drones from configuration")
            print("   Use --verbose flag to see detailed connection logs")

        # Auto-initialize if requested
        if auto_init:
            print("\n🔄 Auto-initializing swarm...")
            if swarm.initialize_swarm():
                print("✅ Swarm initialized successfully")
            else:
                print("❌ Swarm initialization failed")
    else:
        print("\n⚠️  No drones auto-loaded from configuration")
        print("Use 'add <drone_id> [ip]' to manually add drones to the swarm")

    try:
        print("\nSwarm Controller Interactive Mode")
        print("Available commands:")
        print("  add <drone_id> [ip] - Add drone to swarm")
        print("  init - Initialize swarm (connect all drones)")
        print("  takeoff - Take off all drones (synchronized)")
        print("  land - Land all drones")
        print("  status - Show swarm status")
        print("  formation <type> - Create formation (line, circle, diamond, v)")
        print("  move <x> <y> <z> - Move entire formation")
        print("  emergency - Emergency stop all drones")
        print("  timeout - Check command timeout status")
        print("  quit - Exit program")
        print("\nNote: After takeoff, you have 15 seconds to issue the next command!")
        if not verbose:
            print("💡 Use --verbose flag when starting for detailed logs")

        while True:
            try:
                # Check for command timeout before prompting (but don't spam warnings)
                timeout_triggered = swarm.enforce_command_timeout()

                # Create clean prompt
                prompt = "\nSwarm> "
                if timeout_triggered:
                    prompt = "\n⚠️  TIMEOUT! Emergency landed. " + prompt

                command = input(prompt).strip()

                if command == "quit":
                    break
                elif command.startswith("add"):
                    parts = command.split()
                    drone_id = parts[1] if len(parts) > 1 else "drone_001"
                    ip_addr = parts[2] if len(parts) > 2 else None

                    # Use configuration for drone settings if no IP provided
                    if not ip_addr:
                        drone_config_data = config.get_drone_config(drone_id)
                        ip_addr = drone_config_data.get("ip_address")

                    if swarm.add_drone(drone_id, ip_addr):
                        drone = swarm.drones[drone_id]
                        formation_mgr.add_drone(drone)
                        print(f"Added {drone_id} to swarm")
                    else:
                        print(f"Failed to add {drone_id}")

                elif command == "init":
                    if swarm.initialize_swarm():
                        print("Swarm initialized successfully")
                    else:
                        print("Swarm initialization failed")

                elif command == "takeoff":
                    if swarm.takeoff_all():
                        print("Swarm takeoff successful - synchronized takeoff enabled")
                        print("WARNING: You have 15 seconds to issue the next command!")
                    else:
                        print("Swarm takeoff failed")

                elif command == "land":
                    # Use synchronized landing from configuration
                    swarm_landing_config = config.get_swarm_config()
                    synchronized = swarm_landing_config.get('synchronized_landing', True) if swarm_landing_config else True

                    if swarm.land_all(synchronized=synchronized):
                        print("Swarm landing successful")
                    else:
                        print("Swarm landing failed")

                elif command == "timeout":
                    if swarm._last_takeoff_time is None:
                        print("No takeoff timeout active")
                    else:
                        elapsed = time.time() - swarm._last_takeoff_time
                        remaining = max(0, swarm.command_timeout - elapsed)
                        if remaining > 0:
                            print(f"Command timeout: {remaining:.1f} seconds remaining")
                        else:
                            print("Command timeout exceeded!")

                elif command == "status":
                    status = swarm.get_swarm_status()
                    print(f"Swarm Status:")
                    print(
                        f"  Active drones: {status['active_drones']}/{status['total_drones']}"
                    )
                    print(f"  Flying: {status['flying_drones']}")
                    print(f"  Average battery: {status['average_battery']:.1f}%")

                elif command.startswith("formation"):
                    parts = command.split()
                    formation_type = parts[1] if len(parts) > 1 else "line"

                    # Get formation configuration
                    formation_config_data = config.get_formation_config(formation_type)

                    if formation_type == "line":
                        spacing = formation_config_data.get("spacing", 150)
                        formation_mgr.create_line_formation(spacing)
                    elif formation_type == "circle":
                        radius = formation_config_data.get("radius", 200)
                        formation_mgr.create_circle_formation(radius)
                    elif formation_type == "diamond":
                        size = formation_config_data.get("size", 200)
                        formation_mgr.create_diamond_formation(size)
                    elif formation_type == "v":
                        spacing = formation_config_data.get("spacing", 150)
                        angle = formation_config_data.get("angle", 45)
                        formation_mgr.create_v_formation(spacing, angle)
                    else:
                        print("Unknown formation type")
                        continue

                    if formation_mgr.move_to_formation():
                        print(f"{formation_type.capitalize()} formation achieved")
                        # Reset timeout when formation command is executed
                        swarm.reset_command_timeout()
                    else:
                        print("Formation movement failed")

                elif command.startswith("move"):
                    try:
                        _, x, y, z = command.split()
                        formation_mgr.move_formation(int(x), int(y), int(z))
                        print("Formation moved")
                        # Reset timeout when movement command is executed
                        swarm.reset_command_timeout()
                    except ValueError:
                        print("Usage: move <x> <y> <z>")

                elif command == "emergency":
                    swarm.emergency_stop_all()
                    print("Emergency stop executed")
                    # Reset timeout after emergency stop
                    swarm.reset_command_timeout()

                else:
                    print("Unknown command")

            except KeyboardInterrupt:
                break

    except Exception as e:
        logger.error(f"Error in swarm mode: {e}")

    finally:
        swarm.shutdown_swarm()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Drone Controller for Tello Talent Multi-Robot System"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "swarm"],
        default="single",
        help="Operation mode: single drone or swarm",
    )
    parser.add_argument(
        "--drone-id", default="drone_001", help="Drone ID for single mode"
    )
    parser.add_argument("--ip", help="IP address for single drone mode")
    parser.add_argument(
        "--config",
        default="config/drone_config.yaml",
        help="Configuration file path (default: config/drone_config.yaml)"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run demonstration sequence"
    )
    # Note: To use simulator, start the standalone simulator first:
    # python simulator/udp_simulator.py
    parser.add_argument(
        "--auto-init", action="store_true",
        help="Automatically initialize swarm after loading drones from config"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose console output (show detailed INFO level logs)"
    )

    args = parser.parse_args()

    if args.demo:
        print("Running demonstration...")
        if args.mode == "single":
            print("Running real drone demo...")
            from examples.basic_flight import basic_flight_demo
            basic_flight_demo()
        else:  # swarm mode
            print("Running real drone swarm demo...")
            from examples.swarm_formation_demo import swarm_formation_demo
            swarm_formation_demo()
    else:
        if args.mode == "single":
            single_drone_mode(args.drone_id, args.ip)
        else:
            swarm_mode(args.config, args.auto_init, args.verbose)


if __name__ == "__main__":
    main()
