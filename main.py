"""
Main entry point for the Drone Controller application.

This module provides a command-line interface for controlling single drones
or multi-robot swarms of Tello Talent drones.
"""

import argparse
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


def swarm_mode(config_file: Optional[str] = None):
    """
    Run in swarm mode.

    Args:
        config_file: Optional path to configuration file.
                    If None, loads from config/drone_config.yaml by default.
    """
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting swarm mode")

    # Load configuration
    config = DroneConfig(config_file)
    swarm_config = config.get_swarm_config()

    swarm = SwarmController("main_swarm")
    formation_mgr = FormationManager("main_formation")

    # Apply swarm configuration
    if swarm_config:
        swarm.set_formation_config(swarm_config)

    try:
        print("\nSwarm Controller Interactive Mode")
        print("Available commands:")
        print("  add <drone_id> [ip] - Add drone to swarm")
        print("  init - Initialize swarm (connect all drones)")
        print("  takeoff - Take off all drones")
        print("  land - Land all drones")
        print("  status - Show swarm status")
        print("  formation <type> - Create formation (line, circle, diamond, v)")
        print("  move <x> <y> <z> - Move entire formation")
        print("  emergency - Emergency stop all drones")
        print("  quit - Exit program")

        while True:
            try:
                command = input("\nSwarm> ").strip()

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
                        print("Swarm takeoff successful")
                    else:
                        print("Swarm takeoff failed")

                elif command == "land":
                    if swarm.land_all():
                        print("Swarm landing successful")
                    else:
                        print("Swarm landing failed")

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
                    else:
                        print("Formation movement failed")

                elif command.startswith("move"):
                    try:
                        _, x, y, z = command.split()
                        formation_mgr.move_formation(int(x), int(y), int(z))
                        print("Formation moved")
                    except ValueError:
                        print("Usage: move <x> <y> <z>")

                elif command == "emergency":
                    swarm.emergency_stop_all()
                    print("Emergency stop executed")

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
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument(
        "--demo", action="store_true", help="Run demonstration sequence"
    )
    parser.add_argument(
        "--simulator", action="store_true", help="Start 3D web simulator"
    )
    parser.add_argument(
        "--use-simulator", action="store_true",
        help="Force use of simulator instead of real drones"
    )
    parser.add_argument(
        "--use-real", action="store_true",
        help="Force use of real drones instead of simulator"
    )

    args = parser.parse_args()

    # Validate conflicting arguments
    if args.use_simulator and args.use_real:
        print("Error: Cannot specify both --use-simulator and --use-real")
        return

    if args.simulator:
        print("Starting 3D Drone Simulator...")
        try:
            from simulator.simulator_bridge import start_simulator
            start_simulator()
        except ImportError as e:
            print(f"Failed to start simulator: {e}")
            print("Please ensure all simulator dependencies are installed.")
        return

    # Determine whether to use simulator or real drones
    use_simulator = args.use_simulator
    use_real = args.use_real

    # If neither explicitly specified, choose based on mode and availability
    if not use_simulator and not use_real:
        if args.demo:
            # For demos, prefer simulator if available
            try:
                import simulator.simulator_bridge  # noqa: F401
                use_simulator = True
                print("Simulator available - using simulator for demo")
            except ImportError:
                use_real = True
                print("Simulator not available - using real drones for demo")
        else:
            # For interactive mode, default to real drones
            use_real = True
            print("Interactive mode - using real drones")
            print("(use --use-simulator to force simulator)")

    if args.demo:
        print("Running demonstration...")
        if args.mode == "single":
            if use_simulator:
                try:
                    from simulator.simulator_bridge import (
                        run_basic_flight_demo
                    )
                    print("Starting 3D simulator demo...")
                    run_basic_flight_demo()
                except (ImportError, AttributeError):
                    print("Simulator not available, using real drone...")
                    from examples.basic_flight import basic_flight_demo
                    basic_flight_demo()
            else:
                print("Running real drone demo...")
                from examples.basic_flight import basic_flight_demo
                basic_flight_demo()
        else:  # swarm mode
            if use_simulator:
                try:
                    from simulator.simulator_bridge import (
                        run_swarm_formation_demo
                    )
                    print("Starting 3D swarm simulator demo...")
                    run_swarm_formation_demo()
                except ImportError:
                    print("Simulator not available, using real drone...")
                    from examples.swarm_formation_demo import (
                        swarm_formation_demo
                    )
                    swarm_formation_demo()
            else:
                print("Running real drone swarm demo...")
                from examples.swarm_formation_demo import swarm_formation_demo
                swarm_formation_demo()
    else:
        if args.mode == "single":
            if use_simulator:
                print("Starting single drone simulator mode...")
                print("Interactive simulator mode not yet implemented.")
                print("Use --demo flag for simulator demonstrations.")
            else:
                single_drone_mode(args.drone_id, args.ip)
        else:
            if use_simulator:
                print("Starting swarm simulator mode...")
                print("Interactive simulator swarm mode not yet implemented.")
                print("Use --demo flag for simulator demonstrations.")
            else:
                swarm_mode(args.config)


if __name__ == "__main__":
    main()
