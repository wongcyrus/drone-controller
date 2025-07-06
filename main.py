from djitellopy import TelloSwarm, Tello
import signal
import sys
import threading
import time
import functools
import os

# Global variable to hold the swarm instance
swarm = None


def connect_with_timeout(swarm_instance, timeout=10):
    """Connect to swarm with timeout"""
    connection_result = {"success": False, "error": None}

    def connect_thread():
        try:
            swarm_instance.connect()
            connection_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            connection_result["error"] = e

    # Show progress while connecting
    def show_progress():
        for i in range(timeout):
            if connection_result["success"] or connection_result["error"]:
                break
            print(f"Connecting... ({i+1}/{timeout}s)", end="\r")
            time.sleep(1)

    thread = threading.Thread(target=connect_thread)
    progress_thread = threading.Thread(target=show_progress)

    thread.daemon = True
    progress_thread.daemon = True

    thread.start()
    progress_thread.start()

    thread.join(timeout)

    if thread.is_alive():
        print(f"\nConnection timed out after {timeout} seconds")
        return False, "Connection timeout"

    progress_thread.join(1)  # Wait briefly for progress thread to finish
    print("\n", end="")  # Clear the progress line

    if connection_result["success"]:
        return True, None
    else:
        return False, connection_result["error"]


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
    takeoff_result = {"success": False, "error": None, "completed": False}

    def takeoff_thread():
        try:
            swarm_instance.takeoff()
            takeoff_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            takeoff_result["error"] = e
        finally:
            takeoff_result["completed"] = True

    def show_takeoff_progress():
        for i in range(timeout):
            if takeoff_result["completed"]:
                break
            print(f"Taking off... ({i+1}/{timeout}s)", end="\r")
            time.sleep(1)

    thread = threading.Thread(target=takeoff_thread)
    progress_thread = threading.Thread(target=show_takeoff_progress)

    thread.daemon = True
    progress_thread.daemon = True

    print("Initiating takeoff...")
    thread.start()
    progress_thread.start()

    thread.join(timeout)

    # Stop progress thread
    takeoff_result["completed"] = True
    progress_thread.join(2)

    print("\n", end="")  # Clear progress line

    if thread.is_alive():
        print(f"⚠️ Takeoff timed out after {timeout} seconds")
        takeoff_result["completed"] = True
        return False, "Takeoff timeout"

    if takeoff_result["success"]:
        print("✅ Takeoff successful!")
        return True, None
    else:
        error_msg = takeoff_result["error"] or "Unknown takeoff error"
        print(f"❌ Takeoff failed: {error_msg}")
        return False, takeoff_result["error"]


def safe_landing(swarm_instance, timeout=10):
    """Landing with timeout to prevent hanging"""
    landing_result = {"success": False, "error": None, "completed": False}

    def landing_thread():
        try:
            swarm_instance.land()
            landing_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            landing_result["error"] = e
        finally:
            landing_result["completed"] = True

    def show_landing_progress():
        for i in range(timeout):
            if landing_result["completed"]:
                break
            print(f"Landing... ({i+1}/{timeout}s)", end="\r")
            time.sleep(1)

    thread = threading.Thread(target=landing_thread)
    progress_thread = threading.Thread(target=show_landing_progress)

    thread.daemon = True
    progress_thread.daemon = True

    print("Initiating landing...")
    thread.start()
    progress_thread.start()

    thread.join(timeout)

    # Stop progress thread
    landing_result["completed"] = True
    progress_thread.join(2)

    print("\n", end="")  # Clear progress line

    if thread.is_alive():
        print(f"⚠️ Landing timed out after {timeout} seconds")
        landing_result["completed"] = True
        return False, "Landing timeout"

    if landing_result["success"]:
        print("✅ Landing successful!")
        return True, None
    else:
        error_msg = landing_result["error"] or "Unknown landing error"
        print(f"❌ Landing failed: {error_msg}")
        return False, landing_result["error"]


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
        wsl_ip = "172.28.3.205"
        drone1 = Tello(host=wsl_ip, control_udp=8889, state_udp=8890)
        drone2 = Tello(host=wsl_ip, control_udp=8890, state_udp=8891)

        # Create swarm from individual drones
        swarm = TelloSwarm([drone1, drone2])

        print("Connecting to swarm...")

        # Connect with timeout to prevent hanging
        success, error = connect_with_timeout(swarm, timeout=15)

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
        takeoff_success, takeoff_error = safe_takeoff(swarm, timeout=15)

        if not takeoff_success:
            print(f"❌ Takeoff failed: {takeoff_error}")
            print("Attempting to end connection safely...")
            try:
                swarm.end()
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error ending connection: {e}")
            return

        time.sleep(3)

        print("=== DRONE MOVEMENT DEMO ===")

        safe_command(swarm, "move_up", 50, description="Moving up")
        time.sleep(2)

        safe_command(swarm, "move_down", 30, description="Moving down")
        time.sleep(2)

        safe_command(swarm, "move_forward", 50, description="Moving forward")
        time.sleep(2)

        safe_command(swarm, "move_back", 50, description="Moving back")
        time.sleep(2)

        safe_command(swarm, "move_left", 50, description="Moving left")
        time.sleep(2)

        safe_command(swarm, "move_right", 50, description="Moving right")
        time.sleep(2)

        safe_command(swarm, "rotate_clockwise", 90,
                     description="Rotating clockwise")
        time.sleep(2)

        safe_command(swarm, "rotate_counter_clockwise", 90,
                     description="Rotating counter-clockwise")
        time.sleep(2)

        print("Performing flip forward...")
        try:
            # Check battery level first
            for i, tello in enumerate(swarm.tellos):
                try:
                    battery = tello.get_battery()
                    print(f"Drone {i+1} battery: {battery}%")
                    if battery < 50:
                        print(f"Warning: Drone {i+1} battery is low ({battery}%).")
                        print("Flips may not work with low battery.")
                except Exception as e:  # pylint: disable=broad-except
                    print(f"Could not get battery level for drone {i+1}: {e}")

            # Ensure adequate height for flip (move up if needed)
            print("Ensuring adequate height for flip...")
            safe_command(swarm, "move_up", 30, description="Extra height for flip")
            time.sleep(2)

            # Perform flips in all directions with safe commands
            safe_command(swarm, "flip_forward", description="Flip forward")
            time.sleep(3)
            safe_command(swarm, "flip_back", description="Flip back")
            time.sleep(3)
            safe_command(swarm, "flip_left", description="Flip left")
            time.sleep(3)
            safe_command(swarm, "flip_right", description="Flip right")
            time.sleep(3)
            print("All flips completed!")

            # Additional flip for demonstration
            print("Ensuring adequate height for extra flip...")
            safe_command(swarm, "move_up", 30, description="Extra height")
            time.sleep(2)

            # Perform the flip with safe command
            safe_command(swarm, "flip_forward", description="Extra flip forward")
            time.sleep(5)  # Increased wait time for flip completion

        except Exception as e:  # pylint: disable=broad-except
            print(f"Flip command failed: {e}")
            print("Possible reasons:")
            print("- Insufficient battery level (needs >50%)")
            print("- Not enough height (needs ~1.5m minimum)")
            print("- Drone model doesn't support flips")
            print("- Recent command interference")
            print("Continuing with remaining commands...")

        print("Moving in a square pattern...")
        for i in range(4):
            print(f"Square side {i+1}/4...")
            safe_command(swarm, "move_forward", 60,
                        description=f"Square side {i+1}")
            time.sleep(1.5)
            safe_command(swarm, "rotate_clockwise", 90,
                        description=f"Square turn {i+1}")
            time.sleep(1.5)

        print("Final hover...")
        time.sleep(2)

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
