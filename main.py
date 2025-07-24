from djitellopy import TelloSwarm, Tello
import signal
import sys
import threading
import time
import functools
import os

# Helper functions to eliminate duplicate code patterns


def execute_with_timeout_and_progress(operation_func, progress_message,
                                      timeout=10,
                                      success_message="Operation successful!",
                                      timeout_message="Operation timed out",
                                      error_prefix="Operation failed"):
    """Generic helper for executing operations with timeout and progress"""
    operation_result = {"success": False, "error": None, "completed": False}

    def operation_thread():
        try:
            operation_func()
            operation_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            operation_result["error"] = e
        finally:
            operation_result["completed"] = True

    def show_progress():
        for i in range(timeout):
            if operation_result["completed"]:
                break
            print(f"{progress_message} ({i+1}/{timeout}s)", end="\r")
            time.sleep(1)

    thread = threading.Thread(target=operation_thread)
    progress_thread = threading.Thread(target=show_progress)

    thread.daemon = True
    progress_thread.daemon = True

    print(f"Initiating {progress_message.lower()}...")
    thread.start()
    progress_thread.start()

    thread.join(timeout)

    # Stop progress thread
    operation_result["completed"] = True
    progress_thread.join(2)

    print("\n", end="")  # Clear progress line

    if thread.is_alive():
        print(f"⚠️ {timeout_message} after {timeout} seconds")
        operation_result["completed"] = True
        return False, f"{timeout_message.lower()}"

    if operation_result["success"]:
        print(f"✅ {success_message}")
        return True, None
    else:
        error_msg = operation_result["error"] or \
            f"Unknown {error_prefix.lower()} error"
        print(f"❌ {error_prefix}: {error_msg}")
        return False, operation_result["error"]


def check_battery_levels(swarm_instance):
    """Helper to check battery levels for all drones in swarm"""
    battery_info = []
    for i, tello in enumerate(swarm_instance.tellos):
        try:
            battery = tello.get_battery()
            battery_info.append({"drone": i+1, "battery": battery})
            print(f"Drone {i+1} battery: {battery}%")
            if battery < 50:
                print(f"Warning: Drone {i+1} battery is low ({battery}%).")
                print("Some operations may not work with low battery.")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Could not get battery level for drone {i+1}: {e}")
            battery_info.append({"drone": i+1, "battery": None,
                                 "error": str(e)})
    return battery_info


def execute_movement_pattern(swarm_instance, pattern_name, movements):
    """Helper to execute a series of movements with consistent error handling"""
    print(f"=== {pattern_name.upper()} ===")

    for movement in movements:
        command = movement["command"]
        args = movement.get("args", [])
        description = movement["description"]
        wait_time = movement.get("wait_time", 2)

        if safe_command(swarm_instance, command, *args, description=description):
            time.sleep(wait_time)
        else:
            print(f"⚠️ Skipping {description} due to error")
            time.sleep(1)

# Global variable to hold the swarm instance
swarm = None


def connect_with_timeout(swarm_instance, timeout=10):
    """Connect to swarm with timeout"""
    def connect_operation():
        swarm_instance.connect()

    return execute_with_timeout_and_progress(
        connect_operation,
        "Connecting",
        timeout,
        "Connection successful!",
        "Connection timed out",
        "Connection failed"
    )


def signal_handler(sig, frame):  # pylint: disable=unused-argument
    """Handle Ctrl+C gracefully by landing drones and ending connection"""
    print("\n🚨 EMERGENCY STOP - Received interrupt signal!")

    if swarm:
        emergency_land_with_force_exit(swarm, timeout=8)
    else:
        print("No active swarm connection to terminate")

    print("🚨 Emergency shutdown complete. Exiting...")
    os._exit(1)


# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


def safe_takeoff(swarm_instance, timeout=10):
    """Takeoff with timeout to prevent hanging"""
    def takeoff_operation():
        swarm_instance.takeoff()

    return execute_with_timeout_and_progress(
        takeoff_operation,
        "Taking off",
        timeout,
        "Takeoff successful!",
        "Takeoff timed out",
        "Takeoff failed"
    )


def safe_landing(swarm_instance, timeout=10):
    """Landing with timeout to prevent hanging"""
    def landing_operation():
        swarm_instance.land()

    return execute_with_timeout_and_progress(
        landing_operation,
        "Landing",
        timeout,
        "Landing successful!",
        "Landing timed out",
        "Landing failed"
    )


def safe_command(drone_or_swarm, command, *args, description="command",
                 timeout=5):
    """Execute a command safely with error handling and timeout"""
    command_result = {"success": False, "error": None, "completed": False}

    def command_thread():
        try:
            method = getattr(drone_or_swarm, command)
            method(*args)
            command_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            command_result["error"] = e
        finally:
            command_result["completed"] = True

    thread = threading.Thread(target=command_thread)
    thread.daemon = True
    thread.start()

    thread.join(timeout)

    if thread.is_alive():
        command_result["completed"] = True
        print(f"⚠️ Command timeout - {description} (>{timeout}s)")
        return False

    if command_result["success"]:
        print(f"✅ {description} - Success")
        return True
    else:
        error = command_result["error"]
        if error:
            error_msg = str(error).lower()
            if "out of range" in error_msg:
                print(f"⚠️ Range limit reached - {description}: {error}")
                print("   Drone reached boundary, skipping command")
                return False
            elif "unsuccessful" in error_msg:
                print(f"⚠️ Command failed - {description}: {error}")
                print("   Retrying not recommended, continuing")
                return False
            elif "timeout" in error_msg:
                print(f"⚠️ Command timeout - {description}: {error}")
                return False
            else:
                print(f"⚠️ Safe command failed - {description}: {error}")
        else:
            print(f"⚠️ Unknown error - {description}")
        return False


def force_exit():
    """Force exit the program if it hangs"""
    print("🚨 FORCE EXIT - Terminating immediately")
    os._exit(1)


def emergency_land_with_force_exit(swarm_instance, timeout=5):
    """Emergency landing with force exit if hanging"""
    if not swarm_instance:
        return

    print("🚨 Emergency landing with force exit protection...")

    # Set up force exit timer
    force_exit_timer = threading.Timer(timeout, force_exit)
    force_exit_timer.daemon = True
    force_exit_timer.start()

    try:
        # Try emergency command for each drone
        for i, tello in enumerate(swarm_instance.tellos):
            try:
                print(f"Emergency stop for drone {i+1}")
                tello.emergency()
            except Exception as e:
                print(f"Emergency command failed for drone {i+1}: {e}")
                try:
                    tello.land()
                    print(f"Land command sent for drone {i+1}")
                except Exception as land_e:
                    print(f"Land failed for drone {i+1}: {land_e}")

        # Brief wait for commands to process
        time.sleep(2)

        # End connection
        try:
            swarm_instance.end()
            print("Connection terminated")
        except Exception as e:
            print(f"End connection failed: {e}")

        # Cancel force exit timer since we completed successfully
        force_exit_timer.cancel()

    except Exception as e:
        print(f"Emergency landing error: {e}")
        # Don't cancel timer - let it force exit


def main():
    global swarm  # pylint: disable=global-statement

    try:
        # Create individual Tello instances for mock simulators
        # Drone-1 on localhost:8889, Drone-2 on localhost:8890
        # wsl_ip = "172.28.3.205"
        # drone1 = Tello(host=wsl_ip, control_udp=8889, state_udp=8890)
        # drone2 = Tello(host=wsl_ip, control_udp=8890, state_udp=8891)

        drone1 = Tello(host="192.168.137.21")
        drone2 = Tello(host="192.168.137.22")

        # Create swarm from individual drones
        swarm = TelloSwarm([drone1, drone2])

        print("Connecting to swarm...")

        # Connect with timeout to prevent hanging
        success, error = connect_with_timeout(swarm, timeout=15)

        if success:
            print("\nChecking battery levels...")
            check_battery_levels(swarm)

        if not success:
            print(f"Failed to connect to drone swarm: {error}")
            print("Please check:")
            print("1. Drone is powered on")
            print("2. WiFi connection to drone network")
            print("3. Drone IP address is correct")
            print("4. No firewall blocking the connection")
            return

        print("Successfully connected to swarm!")

        print("Taking off...")
        takeoff_success, takeoff_error = safe_takeoff(swarm, timeout=10)

        if not takeoff_success:
            print(f"❌ Takeoff failed: {takeoff_error}")
            print("Attempting to end connection safely...")
            try:
                swarm.end()
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error ending connection: {e}")
            return

        time.sleep(3)

        # Basic movement demonstration using helper
        basic_movements = [
            {"command": "move_up", "args": [50], "description": "Moving up"},
            # {"command": "move_down", "args": [15], "description": "Moving down"},
            {"command": "move_forward", "args": [150], "description": "Moving forward"},
            {"command": "move_back", "args": [150], "description": "Moving back"},
            {"command": "move_left", "args": [150], "description": "Moving left"},
            {"command": "move_right", "args": [150], "description": "Moving right"},
            {"command": "rotate_clockwise", "args": [90], "description": "Rotating clockwise"},
            {"command": "rotate_counter_clockwise", "args": [90], "description": "Rotating counter-clockwise"}
        ]

        execute_movement_pattern(swarm, "DRONE MOVEMENT DEMO", basic_movements)

        print("Performing flip forward...")
        try:
            # Check battery level first using helper
            check_battery_levels(swarm)

            # Ensure adequate height for flip (move up if needed)
            print("Ensuring adequate height for flip...")
            safe_command(swarm, "move_up", 30,
                        description="Extra height for flip")
            time.sleep(2)

            # Perform flips in all directions with safe commands
            flip_movements = [
                {"command": "flip_forward", "description": "Flip forward", "wait_time": 10},
                {"command": "flip_back", "description": "Flip back", "wait_time": 10},
                {"command": "flip_left", "description": "Flip left", "wait_time": 10},
                {"command": "flip_right", "description": "Flip right", "wait_time": 10}
            ]

            for movement in flip_movements:
                if safe_command(swarm, movement["command"],
                               description=movement["description"]):
                    time.sleep(movement["wait_time"])
                else:
                    print(f"⚠️ Skipping {movement['description']} due to error")
                    time.sleep(1)

            print("All flips completed!")

        #     # Additional flip for demonstration
        #     print("Ensuring adequate height for extra flip...")
        #     safe_command(swarm, "move_up", 30, description="Extra height")
        #     time.sleep(2)

        #     # Perform the flip with safe command
        #     safe_command(swarm, "flip_forward",
        #                 description="Extra flip forward")
        #     time.sleep(5)  # Increased wait time for flip completion

        except Exception as e:  # pylint: disable=broad-except
            print(f"Flip command failed: {e}")
            print("Possible reasons:")
            print("- Insufficient battery level (needs >50%)")
            print("- Not enough height (needs ~1.5m minimum)")
            print("- Drone model doesn't support flips")
            print("- Recent command interference")
            print("Continuing with remaining commands...")

        # # Square pattern using helper
        # print("Moving in a square pattern...")
        # square_movements = []
        # for i in range(4):
        #     square_movements.extend([
        #         {"command": "move_forward", "args": [60],
        #          "description": f"Square side {i+1}", "wait_time": 1.5},
        #         {"command": "rotate_clockwise", "args": [90],
        #          "description": f"Square turn {i+1}", "wait_time": 1.5}
        #     ])

        # execute_movement_pattern(swarm, "SQUARE PATTERN", square_movements)

        # print("Final hover...")
        # time.sleep(2)

        print("Landing...")
        landing_success, landing_error = safe_landing(swarm, timeout=15)

        if not landing_success:
            print(f"❌ Safe landing failed: {landing_error}")
            print("Attempting emergency landing...")
            emergency_land_with_force_exit(swarm, timeout=8)
        else:
            print("✅ Landing successful!")

        # End connection
        try:
            swarm.end()
            print("✅ Connection ended successfully")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error ending connection: {e}")

        print("🎉 Mission completed successfully!")

    except KeyboardInterrupt:
        # This shouldn't be reached due to signal handler, but just in case
        print("\n🚨 Keyboard interrupt detected!")
        signal_handler(signal.SIGINT, None)
    except Exception as e:  # pylint: disable=broad-except
        print(f"❌ An error occurred: {e}")
        print("Attempting emergency landing and cleanup...")
        if swarm:
            emergency_land_with_force_exit(swarm, timeout=10)
        sys.exit(1)


def main_with_timeout():
    """Main function wrapper with global timeout"""
    try:
        # Set a global timeout for the entire program
        global_timeout = 300  # 5 minutes for main.py
        timeout_result = {"completed": False}

        def timeout_monitor():
            time.sleep(global_timeout)
            if not timeout_result["completed"]:
                print("\n🚨 GLOBAL TIMEOUT - Program taking too long!")
                print("Force terminating...")
                if swarm:
                    try:
                        print("Emergency landing attempt...")
                        swarm.land()
                        swarm.end()
                    except Exception:  # pylint: disable=broad-except
                        pass
                os._exit(1)

        # Start timeout monitor thread
        timeout_thread = threading.Thread(target=timeout_monitor)
        timeout_thread.daemon = True
        timeout_thread.start()

        main()

        # Mark as completed to stop timeout monitor
        timeout_result["completed"] = True

    except Exception as e:  # pylint: disable=broad-except
        print(f"Wrapper error: {e}")
        timeout_result["completed"] = True
        main()  # Fall back to normal main


if __name__ == "__main__":
    try:
        main_with_timeout()
    except KeyboardInterrupt:
        print("\n🚨 Keyboard interrupt in main wrapper!")
        signal_handler(signal.SIGINT, None)
    except Exception as e:  # pylint: disable=broad-except
        print(f"Critical error in main wrapper: {e}")
        sys.exit(1)
