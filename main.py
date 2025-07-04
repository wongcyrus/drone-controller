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
    """Run in swarm mode."""
    logger = setup_drone_logging("INFO", True, "logs")
    logger.info("Starting swarm mode")

    # Load configuration
    config = DroneConfig(config_file)

    swarm = SwarmController("main_swarm")
    formation_mgr = FormationManager("main_formation")

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

                    if formation_type == "line":
                        formation_mgr.create_line_formation()
                    elif formation_type == "circle":
                        formation_mgr.create_circle_formation()
                    elif formation_type == "diamond":
                        formation_mgr.create_diamond_formation()
                    elif formation_type == "v":
                        formation_mgr.create_v_formation()
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

    args = parser.parse_args()

    if args.demo:
        print("Running demonstration...")
        if args.mode == "single":
            from examples.basic_flight import basic_flight_demo

            basic_flight_demo()
        else:
            from examples.swarm_formation_demo import swarm_formation_demo

            swarm_formation_demo()
    else:
        if args.mode == "single":
            single_drone_mode(args.drone_id, args.ip)
        else:
            swarm_mode(args.config)


if __name__ == "__main__":
    main()
