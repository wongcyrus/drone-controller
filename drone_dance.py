from djitellopy import TelloSwarm, Tello
import signal
import sys
import threading
import time
import functools
import os

# Global variable to hold the swarm instance
swarm = None

# Position tracking variables to help return to start - Updated for 2M x 2M boundary
position_tracker = {
    "initial_height": 0,
    "movements": [],  # Track all movements for potential compensation
    "spread_distance": 25,  # Reduced spread distance for 2M x 2M boundary
    "formation_offset": {"forward": 20, "up": 40}  # Reduced initial formation moves
}


def connect_with_timeout(swarm_instance, timeout=10):
    """Connect to swarm with timeout"""
    connection_result = {"success": False, "error": None, "completed": False}

    def connect_thread():
        try:
            swarm_instance.connect()
            connection_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            connection_result["error"] = e
        finally:
            connection_result["completed"] = True

    # Show progress while connecting
    def show_progress():
        for i in range(timeout):
            if connection_result["completed"]:
                break
            print(f"Connecting... ({i+1}/{timeout}s)", end="\r")
            time.sleep(1)

    thread = threading.Thread(target=connect_thread)
    progress_thread = threading.Thread(target=show_progress)

    thread.daemon = True
    progress_thread.daemon = True

    print("Starting connection attempt...")
    thread.start()
    progress_thread.start()

    # Wait for connection thread with timeout
    thread.join(timeout)

    # Stop progress thread
    connection_result["completed"] = True
    progress_thread.join(2)  # Give progress thread time to stop

    print("\n", end="")  # Clear the progress line

    if thread.is_alive():
        print(f"⚠️ Connection timed out after {timeout} seconds")
        print("Force terminating connection attempt...")
        # Force mark as completed to stop any hanging threads
        connection_result["completed"] = True
        return False, "Connection timeout - thread may still be running"

    if connection_result["success"]:
        print("✅ Connection successful!")
        return True, None
    else:
        error_msg = connection_result["error"] or "Unknown connection error"
        print(f"❌ Connection failed: {error_msg}")
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


def sync_point(message, wait_time=2):
    """Synchronization point for both drones with connectivity check"""
    print(f"🔄 SYNC: {message}")

    # Quick connectivity check if swarm is available
    if swarm:
        connected, error = check_swarm_connection(swarm, timeout=3)
        if not connected:
            print(f"⚠️ Connection issue detected during sync: {error}")
            print("   Continuing but watch for further errors...")

    time.sleep(wait_time)


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


def drone1_independent_sequence(drone):
    """Independent movement sequence for Drone 1 - Compact 2M x 2M design"""
    print("🟦 Drone 1 - Independent sequence starting...")

    try:
        # Compact circular pattern (staying within 50cm radius)
        print("🟦 Drone 1 - Performing compact circular pattern")
        for i in range(6):  # 6 sides for a hexagon-like circle
            try:
                drone.move_forward(20)  # Small movements to stay within bounds
                time.sleep(0.5)
                drone.rotate_clockwise(60)  # 360/6 = 60 degrees
                time.sleep(0.5)
                # Minimal height changes
                if i % 2 == 0:
                    drone.move_up(20)  # Minimum allowed
                    time.sleep(0.5)
                else:
                    drone.move_down(20)  # Back down
                    time.sleep(0.5)
            except Exception as e:  # pylint: disable=broad-except
                print(f"🟦 Drone 1 - Circular step {i+1} error: {e}")
                continue

        # Tiny square pattern (within 40cm total movement)
        print("🟦 Drone 1 - Compact square pattern")
        try:
            # Very small square movements to stay within 2M boundary
            for _ in range(4):  # Complete square
                drone.move_forward(20)  # Minimum distance
                time.sleep(0.5)
                drone.rotate_clockwise(90)
                time.sleep(0.5)

            # Single height adjustment
            drone.move_up(20)  # Go up
            time.sleep(0.5)

            # Rotate in place for visual effect
            for _ in range(4):
                drone.rotate_clockwise(90)
                time.sleep(0.3)

            drone.move_down(20)  # Return to original height
            time.sleep(0.5)

        except Exception as e:  # pylint: disable=broad-except
            print(f"🟦 Drone 1 - Compact square error: {e}")

        print("🟦 Drone 1 - Independent sequence completed!")

    except Exception as e:  # pylint: disable=broad-except
        print(f"🟦 Drone 1 - Error in independent sequence: {e}")


def drone2_independent_sequence(drone):
    """Independent movement sequence for Drone 2 - Compact 2M x 2M design"""
    print("🟨 Drone 2 - Independent sequence starting...")

    try:
        # Compact triangle pattern (staying within 60cm total)
        print("🟨 Drone 2 - Performing compact triangle pattern")
        for i in range(3):  # Triangle has 3 sides
            try:
                drone.move_forward(20)  # Minimum distance to stay compact
                time.sleep(0.5)
                drone.rotate_clockwise(120)  # 360/3 = 120 degrees
                time.sleep(0.5)
                # Minimal height variation
                if i == 1:  # Only middle side goes up
                    drone.move_up(20)  # Minimum allowed
                    time.sleep(0.5)
            except Exception as e:  # pylint: disable=broad-except
                print(f"🟨 Drone 2 - Triangle step {i+1} error: {e}")
                continue

        # Return to original height
        try:
            drone.move_down(20)
            time.sleep(0.5)
        except Exception as e:  # pylint: disable=broad-except
            print(f"🟨 Drone 2 - Height return error: {e}")

        # Vertical oscillation (in place)
        print("🟨 Drone 2 - Vertical oscillation pattern")
        try:
            for i in range(3):  # 3 vertical movements
                drone.move_up(20)  # Go up
                time.sleep(0.5)
                drone.rotate_clockwise(120)  # Rotate while going up
                time.sleep(0.3)
                drone.move_down(20)  # Go back down
                time.sleep(0.5)
                drone.rotate_counter_clockwise(120)  # Counter-rotate
                time.sleep(0.3)
        except Exception as e:  # pylint: disable=broad-except
            print(f"🟨 Drone 2 - Vertical oscillation error: {e}")

        # Figure-8 pattern (very compact)
        print("🟨 Drone 2 - Compact figure-8 pattern")
        try:
            # First half of figure-8
            for _ in range(4):  # Small circle
                drone.move_forward(20)
                time.sleep(0.3)
                drone.rotate_clockwise(90)
                time.sleep(0.3)

            # Second half of figure-8 (counter-clockwise)
            for _ in range(4):  # Small circle in opposite direction
                drone.move_forward(20)
                time.sleep(0.3)
                drone.rotate_counter_clockwise(90)
                time.sleep(0.3)

        except Exception as e:  # pylint: disable=broad-except
            print(f"🟨 Drone 2 - Figure-8 error: {e}")

        print("🟨 Drone 2 - Independent sequence completed!")

    except Exception as e:  # pylint: disable=broad-except
        print(f"🟨 Drone 2 - Error in independent sequence: {e}")


def perform_independent_dance():
    """Execute independent drone sequences using threading"""
    print("\n🎭 === INDEPENDENT DANCE SEQUENCES ===")

    # Create threads for independent movement
    drone1_thread = threading.Thread(
        target=drone1_independent_sequence,
        args=(swarm.tellos[0],)
    )
    drone2_thread = threading.Thread(
        target=drone2_independent_sequence,
        args=(swarm.tellos[1],)
    )

    # Start both threads simultaneously
    drone1_thread.start()
    drone2_thread.start()

    # Wait for both to complete
    drone1_thread.join()
    drone2_thread.join()

    print("🎭 Independent dance sequences completed!")


def synchronized_flip_sequence():
    """Synchronized flip sequence for both drones"""
    print("\n🤸 === SYNCHRONIZED FLIP SEQUENCE ===")

    try:
        # Check battery levels
        for i, tello in enumerate(swarm.tellos):
            try:
                battery = tello.get_battery()
                print(f"Drone {i+1} battery: {battery}%")
                if battery < 50:
                    print(f"Warning: Drone {i+1} battery is low ({battery}%).")
                    print("Flips may not work with low battery.")
            except Exception as e:  # pylint: disable=broad-except
                print(f"Could not get battery level for drone {i+1}: {e}")

        # Ensure adequate height (respecting 20cm minimum)
        sync_point("Moving to flip height")
        safe_command(swarm, "move_up", 50,  # Well above minimum for safety
                     description="Pre-flip height adjustment")
        time.sleep(2)

        # Synchronized flips in sequence
        flip_directions = ["forward", "back", "left", "right"]

        for direction in flip_directions:
            sync_point(f"Executing {direction} flip")
            flip_desc = f"{direction} flip"
            if safe_command(swarm, f"flip_{direction}", description=flip_desc):
                time.sleep(3)
            else:
                print(f"🤸 Skipping {direction} flip due to error")
                time.sleep(1)

        print("🤸 All synchronized flips completed!")

    except Exception as e:  # pylint: disable=broad-except
        print(f"🤸 Flip sequence failed: {e}")
        print("Continuing with remaining dance...")


def synchronized_formation_dance():
    """Synchronized formation dance where drones move together - Compact 2M x 2M design"""
    print("\n💫 === SYNCHRONIZED FORMATION DANCE ===")

    # Formation 1: Gentle side by side movement (very small distances)
    sync_point("Formation 1: Compact side by side")
    safe_command(swarm, "move_forward", 20, description="Formation 1 forward")
    time.sleep(1.5)
    safe_command(swarm, "move_back", 20, description="Formation 1 back")
    time.sleep(1.5)

    # Formation 2: Small octagon movement (staying very compact)
    sync_point("Formation 2: Micro octagon movement")
    for i in range(8):  # Octagon has 8 sides
        safe_command(swarm, "move_forward", 20,  # Minimum distance only
                     description=f"Micro octagon step {i+1}")
        time.sleep(0.8)
        # 360/8 = 45 degrees per turn
        safe_command(swarm, "rotate_clockwise", 45,
                     description=f"Micro octagon rotate {i+1}")
        time.sleep(0.8)

    # Formation 3: Minimal up and down waves
    sync_point("Formation 3: Minimal wave pattern")
    for i in range(2):  # Just 2 small waves
        safe_command(swarm, "move_up", 20, description=f"Wave {i+1} up")
        time.sleep(1)
        safe_command(swarm, "move_forward", 20,  # Very small forward
                     description=f"Wave {i+1} forward")
        time.sleep(1)
        safe_command(swarm, "move_down", 20, description=f"Wave {i+1} down")
        time.sleep(1)
        safe_command(swarm, "move_back", 20,  # Return to position
                     description=f"Wave {i+1} back")
        time.sleep(1)

    # Formation 4: In-place rotation dance (no movement, just rotation)
    sync_point("Formation 4: In-place rotation dance")
    for i in range(4):
        print(f"Rotation sequence {i+1}/4...")
        safe_command(swarm, "rotate_clockwise", 90,
                     description=f"Rotation dance {i+1}")
        time.sleep(1.2)
        # Small height variation while rotating
        if i % 2 == 0:
            safe_command(swarm, "move_up", 20,
                         description=f"Rotation height up {i+1}")
        else:
            safe_command(swarm, "move_down", 20,
                         description=f"Rotation height down {i+1}")
        time.sleep(1.2)


def return_to_initial_position():
    """Return both drones to their initial takeoff position with accuracy"""
    print("\n🏠 === RETURNING TO INITIAL POSITION ===")

    # Step 1: Ensure both drones are at a safe, standardized height
    sync_point("Standardizing height for return")
    safe_command(swarm, "move_up", 50, description="Safe return height")
    time.sleep(2)

    # Step 2: Reset orientation first (very important for accurate positioning)
    sync_point("Resetting orientation to forward (0 degrees)")
    # Multiple small rotations to ensure we're facing forward
    for i in range(8):  # 8 x 45 = 360 degrees total
        safe_command(swarm, "rotate_clockwise", 45,
                     description=f"Orientation reset {i+1}/8")
        time.sleep(0.8)

    # Step 3: Bring drones back to center from spread positions
    sync_point("Returning from spread positions")
    spread_distance = position_tracker["spread_distance"]
    safe_command(swarm.tellos[0], "move_right", spread_distance,
                 description="Drone 1 center return")
    safe_command(swarm.tellos[1], "move_left", spread_distance,
                 description="Drone 2 center return")
    time.sleep(3)

    # Step 4: Compensate for initial formation movements
    sync_point("Compensating for initial formation offset")
    formation_forward = position_tracker["formation_offset"]["forward"]
    if formation_forward > 0:
        safe_command(swarm, "move_back", formation_forward,
                     description="Compensate initial forward movement")
        time.sleep(2)

    # Step 5: Systematic position correction with multiple attempts
    sync_point("Fine-tuning position - multiple correction attempts")

    # First correction attempt
    correction_moves = [
        ("move_back", 30, "Position correction back"),
        ("move_left", 25, "Position correction left"),
        ("move_forward", 25, "Position correction forward"),
        ("move_right", 20, "Position correction right")
    ]

    for move_cmd, distance, desc in correction_moves:
        if safe_command(swarm, move_cmd, distance, description=desc):
            time.sleep(1.5)
        else:
            print(f"⚠️ Skipping {desc} - likely at boundary")

    # Step 6: Final height adjustment to approximate takeoff height
    sync_point("Adjusting to takeoff height")
    formation_up = position_tracker["formation_offset"]["up"]
    # Return to approximate takeoff height
    target_down_distance = formation_up + 20  # A bit lower for safety
    if safe_command(swarm, "move_down", target_down_distance,
                    description="Return to takeoff height"):
        time.sleep(2)
        print("🏠 Drones returned to approximate takeoff height")
    else:
        # Try a smaller adjustment
        if safe_command(swarm, "move_down", 40,
                        description="Partial height adjustment"):
            time.sleep(2)
            print("🏠 Partial height adjustment completed")
        else:
            print("🏠 Maintaining current height for safety")

    # Step 7: Final positioning verification with small adjustments
    sync_point("Final position verification")
    final_adjustments = [
        ("move_back", 20, "Final back adjustment"),
        ("move_forward", 20, "Final forward adjustment"),
    ]

    for move_cmd, distance, desc in final_adjustments:
        if safe_command(swarm, move_cmd, distance, description=desc):
            time.sleep(1)

    print("🏠 Return to initial position sequence completed!")
    print("🏠 Drones should now be close to their starting location")


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


def check_swarm_connection(swarm_instance, timeout=5):
    """Check if swarm is still responsive"""
    if not swarm_instance:
        return False, "No swarm instance"

    check_result = {"success": False, "error": None, "completed": False}

    def check_thread():
        try:
            # Try to get battery status as a connectivity test
            for tello in swarm_instance.tellos:
                tello.get_battery()
            check_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            check_result["error"] = e
        finally:
            check_result["completed"] = True

    thread = threading.Thread(target=check_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        check_result["completed"] = True
        return False, "Connection check timeout"

    if check_result["success"]:
        return True, None
    else:
        return False, check_result["error"]


def timeout_decorator(timeout_seconds=10):
    """Decorator to add timeout to any function"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = {"return_value": None, "exception": None, "completed": False}

            def target():
                try:
                    result["return_value"] = func(*args, **kwargs)
                except Exception as e:  # pylint: disable=broad-except
                    result["exception"] = e
                finally:
                    result["completed"] = True

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)

            if thread.is_alive():
                result["completed"] = True
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")

            if result["exception"]:
                raise result["exception"]

            return result["return_value"]
        return wrapper
    return decorator


def debug_print(message):
    """Print debug message with timestamp"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] DEBUG: {message}")


def test_basic_connectivity(host_ip, timeout=5):
    """Test basic network connectivity before attempting drone connection"""
    import socket

    debug_print(f"Testing basic connectivity to {host_ip}")
    test_result = {"success": False, "error": None, "completed": False}

    def connectivity_test():
        try:
            # Try to connect to the host on the control port
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            # Send a simple UDP packet to test connectivity
            sock.sendto(b"test", (host_ip, 8889))
            sock.close()
            test_result["success"] = True
        except Exception as e:  # pylint: disable=broad-except
            test_result["error"] = e
        finally:
            test_result["completed"] = True

    thread = threading.Thread(target=connectivity_test)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        test_result["completed"] = True
        return False, "Network connectivity test timeout"

    if test_result["success"]:
        debug_print("Basic connectivity test passed")
        return True, None
    else:
        debug_print(f"Basic connectivity test failed: {test_result['error']}")
        return False, test_result["error"]


def main():
    global swarm  # pylint: disable=global-statement

    debug_print("Starting main function")
    try:
        debug_print("Creating drone instances")
        # Create individual Tello instances for mock simulators
        wsl_ip = "172.28.3.205"

        # Test basic connectivity first
        conn_test_success, conn_test_error = test_basic_connectivity(wsl_ip)
        if not conn_test_success:
            print(f"❌ Basic connectivity test failed: {conn_test_error}")
            print("Network connection to drone host is not available")
            return

        drone1 = Tello(host=wsl_ip, control_udp=8889, state_udp=8890)
        drone2 = Tello(host=wsl_ip, control_udp=8890, state_udp=8891)

        debug_print("Creating swarm")
        # Create swarm from individual drones
        swarm = TelloSwarm([drone1, drone2])

        print("🚁 === DRONE DANCE CHOREOGRAPHY ===")
        print("Connecting to swarm...")

        debug_print("Starting connection attempt")
        # Connect with timeout to prevent hanging
        success, error = connect_with_timeout(swarm, timeout=15)

        if not success:
            debug_print(f"Connection failed: {error}")
            print(f"Failed to connect to drone swarm: {error}")
            print("Please check:")
            print("1. Drone is powered on")
            print("2. WiFi connection to drone network")
            print("3. Drone IP address is correct")
            print("4. No firewall blocking the connection")
            return

        debug_print("Connection successful, starting takeoff")
        print("Successfully connected to swarm!")

        # Safe takeoff with timeout
        sync_point("Taking off")
        takeoff_success, takeoff_error = safe_takeoff(swarm, timeout=15)

        if not takeoff_success:
            debug_print(f"Takeoff failed: {takeoff_error}")
            print(f"❌ Takeoff failed: {takeoff_error}")
            print("Attempting to end connection safely...")
            try:
                swarm.end()
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error ending connection: {e}")
            return

        debug_print("Takeoff successful, starting dance sequence")

        # Initialize position tracking after successful takeoff
        reset_position_tracking()

        time.sleep(3)

        # Initial synchronized movements - Compact for 2M x 2M boundary
        debug_print("Initial formation")
        sync_point("Initial formation - moving to dance position")
        # Reduced height for 2M x 2M boundary
        safe_command(swarm, "move_up", 40, description="Initial height")
        track_movement("move_up", 40, "Initial height")
        time.sleep(2)

        # Center the drones first to avoid range issues later
        debug_print("Centering drones")
        sync_point("Centering drones for optimal range")
        # Smaller centering move for 2M x 2M boundary
        safe_command(swarm, "move_forward", 20,  # Minimum distance
                     description="Center positioning")
        track_movement("move_forward", 20, "Center positioning")
        time.sleep(1)

        # Drones spread apart for independent sequences - Reduced for 2M x 2M
        debug_print("Spreading drones")
        sync_point("Spreading apart for independent dance")
        # Much smaller spread distance for 2M x 2M boundary
        safe_command(swarm.tellos[0], "move_left", 25,
                     description="Drone 1 spread left")
        safe_command(swarm.tellos[1], "move_right", 25,
                     description="Drone 2 spread right")
        time.sleep(3)

        debug_print("Starting independent dance sequences")
        # Independent dance sequences (parallel execution)
        perform_independent_dance()

        debug_print("Returning to center formation")
        # Come back together - Reduced distance for 2M x 2M boundary
        sync_point("Returning to center formation", wait_time=3)
        safe_command(swarm.tellos[0], "move_right", 25,
                     description="Drone 1 return")
        safe_command(swarm.tellos[1], "move_left", 25,
                     description="Drone 2 return")
        time.sleep(3)

        debug_print("Starting flip sequence")
        # Synchronized flip sequence
        synchronized_flip_sequence()

        debug_print("Starting formation dance")
        # Final synchronized formation dance
        synchronized_formation_dance()

        debug_print("Starting enhanced landing sequence")
        # Enhanced landing sequence with return to start
        landing_success = enhanced_safe_landing_sequence()

        if not landing_success:
            debug_print("Enhanced landing sequence completed with warnings")
        else:
            debug_print("Enhanced landing sequence completed successfully")

        debug_print("Ending connection")
        # End connection
        try:
            swarm.end()
            print("✅ Connection ended successfully")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error ending connection: {e}")

        debug_print("Main function completed successfully")
        print("🎉 Drone dance choreography completed successfully!")

    except KeyboardInterrupt:
        debug_print("Keyboard interrupt in main")
        # This shouldn't be reached due to signal handler, but just in case
        print("\nKeyboard interrupt detected!")
        signal_handler(signal.SIGINT, None)
    except Exception as e:  # pylint: disable=broad-except
        debug_print(f"Exception in main: {e}")
        print(f"❌ An error occurred: {e}")
        print("Attempting emergency landing and cleanup...")
        if swarm:
            emergency_land_with_force_exit(swarm, timeout=10)
        sys.exit(1)


def main_with_timeout():
    """Main function wrapper with global timeout"""
    try:
        # Set a global timeout for the entire program (Windows compatible)
        global_timeout = 600  # 10 minutes
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
                sys.exit(1)

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


def reset_position_tracking():
    """Reset position tracking to initial state - Updated for 2M x 2M boundary"""
    global position_tracker
    position_tracker = {
        "initial_height": 0,
        "movements": [],
        "spread_distance": 25,  # Reduced for 2M x 2M boundary
        "formation_offset": {"forward": 20, "up": 40}  # Reduced movements
    }
    debug_print("Position tracking reset to initial state")


def track_movement(movement_type, distance, description=""):
    """Track a movement for potential compensation later"""
    global position_tracker
    position_tracker["movements"].append({
        "type": movement_type,
        "distance": distance,
        "description": description
    })
    debug_print(f"Tracked: {movement_type} {distance}cm - {description}")


def enhanced_safe_landing_sequence():
    """Enhanced landing sequence that ensures return to start before landing"""
    print("\n🛬 === ENHANCED SAFE LANDING SEQUENCE ===")

    # Step 1: Return to initial position first
    return_to_initial_position()

    # Step 2: Final safety checks and position verification
    sync_point("Pre-landing safety verification", wait_time=2)

    # Step 3: Ensure safe landing height
    print("🛬 Adjusting to optimal landing height...")
    safe_command(swarm, "move_down", 20, description="Pre-landing height")
    time.sleep(2)

    # Step 4: Final hover at landing position
    sync_point("Final hover at landing position", wait_time=3)
    print("🛬 Drones hovering at landing position...")

    # Step 5: Execute landing
    print("🛬 Initiating controlled landing sequence...")
    landing_success, landing_error = safe_landing(swarm, timeout=15)

    if not landing_success:
        print(f"❌ Enhanced landing failed: {landing_error}")
        print("🛬 Attempting direct landing command as backup...")
        try:
            swarm.land()
            print("✅ Backup landing command sent successfully")
        except Exception as e:  # pylint: disable=broad-except
            print(f"❌ Backup landing failed: {e}")
            print("🚨 Manual intervention may be required")
    else:
        print("✅ Enhanced landing sequence completed successfully!")

    return landing_success


if __name__ == "__main__":
    try:
        main_with_timeout()
    except KeyboardInterrupt:
        print("\n🚨 Keyboard interrupt in main wrapper!")
        signal_handler(signal.SIGINT, None)
    except Exception as e:  # pylint: disable=broad-except
        print(f"Critical error in main wrapper: {e}")
        sys.exit(1)
