from djitellopy import TelloSwarm, Tello
import signal
import sys
import threading
import time
import functools
import os
from typing import Optional

# Global variable to hold the swarm instance
swarm: Optional[TelloSwarm] = None

# Position tracking variables - Updated for 2M x 2M boundary
position_tracker = {
    "initial_height": 0,
    "movements": [],  # Track all movements for potential compensation
    "spread_distance": 25,  # Reduced spread distance for 2M x 2M boundary
    # Reduced initial formation moves
    "formation_offset": {"forward": 20, "up": 40}
}


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
        # Compact circular pattern (6-sided hexagon)
        execute_geometric_pattern(drone, "hexagon", 6, 20, "Drone 1", True)

        # Tiny square pattern
        execute_geometric_pattern(drone, "square", 4, 20, "Drone 1", False)

        # Single height adjustment and rotation dance
        try:
            drone.move_up(20)
            track_movement("move_up", 20, "Drone 1 square height up", "drone1")
            time.sleep(0.5)

            # Rotate in place for visual effect
            for i in range(4):
                drone.rotate_clockwise(90)
                track_movement("rotate_clockwise", 90,
                               f"Drone 1 final rotate {i+1}", "drone1")
                time.sleep(0.3)

            drone.move_down(20)
            track_movement("move_down", 20, "Drone 1 square height down",
                           "drone1")
            time.sleep(0.5)

        except Exception as e:  # pylint: disable=broad-except
            print(f"🟦 Drone 1 - Final sequence error: {e}")

        print("🟦 Drone 1 - Independent sequence completed!")

    except Exception as e:  # pylint: disable=broad-except
        print(f"🟦 Drone 1 - Error in independent sequence: {e}")


def drone2_independent_sequence(drone):
    """Independent movement sequence for Drone 2 - Compact 2M x 2M design"""
    print("🟨 Drone 2 - Independent sequence starting...")

    try:
        # Compact triangle pattern
        execute_geometric_pattern(drone, "triangle", 3, 20, "Drone 2", False)

        # Additional height adjustment for triangle
        try:
            drone.move_down(20)
            track_movement("move_down", 20, "Drone 2 triangle height down",
                           "drone2")
            time.sleep(0.5)
        except Exception as e:  # pylint: disable=broad-except
            print(f"🟨 Drone 2 - Height return error: {e}")

        # Vertical oscillation pattern
        print("🟨 Drone 2 - Vertical oscillation pattern")
        oscillation_movements = []
        for i in range(3):
            oscillation_movements.extend([
                {"type": "move_up", "distance": 20,
                 "description": f"Drone 2 oscillation up {i+1}"},
                {"type": "rotate_clockwise", "distance": 120,
                 "description": f"Drone 2 oscillation rotate {i+1}",
                 "wait_time": 0.3},
                {"type": "move_down", "distance": 20,
                 "description": f"Drone 2 oscillation down {i+1}"},
                {"type": "rotate_counter_clockwise", "distance": 120,
                 "description": f"Drone 2 oscillation counter-rotate {i+1}",
                 "wait_time": 0.3}
            ])

        execute_drone_movement_sequence(drone, "vertical oscillation",
                                        oscillation_movements, "drone2")

        # Figure-8 pattern (two circles in opposite directions)
        print("🟨 Drone 2 - Compact figure-8 pattern")
        execute_geometric_pattern(drone, "circle1", 4, 20, "Drone 2", False)

        # Second half of figure-8 (counter-clockwise)
        for i in range(4):
            try:
                drone.move_forward(20)
                track_movement("move_forward", 20,
                               f"Drone 2 figure-8 step2 {i+1}", "drone2")
                time.sleep(0.3)
                drone.rotate_counter_clockwise(90)
                track_movement("rotate_counter_clockwise", 90,
                               f"Drone 2 figure-8 rotate2 {i+1}", "drone2")
                time.sleep(0.3)
            except Exception as e:  # pylint: disable=broad-except
                print(f"🟨 Drone 2 - Figure-8 step2 {i+1} error: {e}")
                continue

        print("🟨 Drone 2 - Independent sequence completed!")

    except Exception as e:  # pylint: disable=broad-except
        print(f"🟨 Drone 2 - Error in independent sequence: {e}")


def perform_independent_dance():
    """Execute independent drone sequences using threading"""
    print("\n🎭 === INDEPENDENT DANCE SEQUENCES ===")

    if not swarm or not swarm.tellos:
        print("❌ Swarm not available for independent dance")
        return

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
        # Check battery levels using helper
        check_battery_levels()

        # Ensure adequate height (respecting 20cm minimum)
        sync_point("Moving to flip height")
        safe_command(swarm, "move_up", 50,  # Well above minimum for safety
                     description="Pre-flip height adjustment")
        track_movement("move_up", 50, "Pre-flip height adjustment")
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
    """Synchronized formation dance - Compact 2M x 2M design"""
    print("\n💫 === SYNCHRONIZED FORMATION DANCE ===")

    # Formation 1: Gentle side by side movement (very small distances)
    sync_point("Formation 1: Compact side by side")
    safe_command(swarm, "move_forward", 20, description="Formation 1 forward")
    track_movement("move_forward", 20, "Formation 1 forward")
    time.sleep(1.5)
    safe_command(swarm, "move_back", 20, description="Formation 1 back")
    track_movement("move_back", 20, "Formation 1 back")
    time.sleep(1.5)

    # Formation 2: Small octagon movement (staying very compact)
    sync_point("Formation 2: Micro octagon movement")
    for i in range(8):  # Octagon has 8 sides
        safe_command(swarm, "move_forward", 20,  # Minimum distance only
                     description=f"Micro octagon step {i+1}")
        track_movement("move_forward", 20, f"Micro octagon step {i+1}")
        time.sleep(0.8)
        # 360/8 = 45 degrees per turn
        safe_command(swarm, "rotate_clockwise", 45,
                     description=f"Micro octagon rotate {i+1}")
        track_movement("rotate_clockwise", 45, f"Micro octagon rotate {i+1}")
        time.sleep(0.8)

    # Formation 3: Minimal up and down waves
    sync_point("Formation 3: Minimal wave pattern")
    for i in range(2):  # Just 2 small waves
        safe_command(swarm, "move_up", 20, description=f"Wave {i+1} up")
        track_movement("move_up", 20, f"Wave {i+1} up")
        time.sleep(1)
        safe_command(swarm, "move_forward", 20,  # Very small forward
                     description=f"Wave {i+1} forward")
        track_movement("move_forward", 20, f"Wave {i+1} forward")
        time.sleep(1)
        safe_command(swarm, "move_down", 20, description=f"Wave {i+1} down")
        track_movement("move_down", 20, f"Wave {i+1} down")
        time.sleep(1)
        safe_command(swarm, "move_back", 20,  # Return to position
                     description=f"Wave {i+1} back")
        track_movement("move_back", 20, f"Wave {i+1} back")
        time.sleep(1)

    # Formation 4: In-place rotation dance (no movement, just rotation)
    sync_point("Formation 4: In-place rotation dance")
    for i in range(4):
        print(f"Rotation sequence {i+1}/4...")
        safe_command(swarm, "rotate_clockwise", 90,
                     description=f"Rotation dance {i+1}")
        track_movement("rotate_clockwise", 90, f"Rotation dance {i+1}")
        time.sleep(1.2)
        # Small height variation while rotating
        if i % 2 == 0:
            safe_command(swarm, "move_up", 20,
                         description=f"Rotation height up {i+1}")
            track_movement("move_up", 20, f"Rotation height up {i+1}")
        else:
            safe_command(swarm, "move_down", 20,
                         description=f"Rotation height down {i+1}")
            track_movement("move_down", 20, f"Rotation height down {i+1}")
        time.sleep(1.2)


def return_to_initial_position():
    """Return both drones to their initial takeoff position"""
    print("\n🏠 === RETURNING TO INITIAL POSITION ===")

    # Get current estimated positions
    swarm_pos = position_tracker["swarm_position"]
    drone1_pos = position_tracker["drone_positions"]["drone1"]
    drone2_pos = position_tracker["drone_positions"]["drone2"]

    print("🏠 Current estimated positions:")
    print(f"   Swarm: x={swarm_pos['x']}, y={swarm_pos['y']}, "
          f"z={swarm_pos['z']}, rot={swarm_pos['rotation']}")
    print(f"   Drone1: x={drone1_pos['x']}, y={drone1_pos['y']}, "
          f"z={drone1_pos['z']}, rot={drone1_pos['rotation']}")
    print(f"   Drone2: x={drone2_pos['x']}, y={drone2_pos['y']}, "
          f"z={drone2_pos['z']}, rot={drone2_pos['rotation']}")

    # Step 1: Ensure both drones are at a safe, standardized height
    sync_point("Standardizing height for return")
    safe_command(swarm, "move_up", 50, description="Safe return height")
    track_movement("move_up", 50, "Safe return height")
    time.sleep(2)

    # Step 2: Bring both individual drones back to swarm center positions
    sync_point("Returning individual drones to swarm formation")

    if not swarm or not swarm.tellos:
        print("❌ Swarm not available for return to center")
        return

    # Use helper functions to return drones to center
    return_drone_to_center(swarm.tellos[0], "Drone 1", drone1_pos)
    return_drone_to_center(swarm.tellos[1], "Drone 2", drone2_pos)

    # Reset individual drone position tracking since they're now centered
    position_tracker["drone_positions"]["drone1"] = {
        "x": 0, "y": 0, "z": 0, "rotation": 0
    }
    position_tracker["drone_positions"]["drone2"] = {
        "x": 0, "y": 0, "z": 0, "rotation": 0
    }

    # Step 3: Reset orientation for both drones
    sync_point("Resetting orientation to forward (0 degrees)")

    # Calculate rotation needed to return to 0 degrees
    swarm_rotation_needed = -swarm_pos["rotation"]
    # Only rotate if significant rotation needed
    if abs(swarm_rotation_needed) > 10:
        # Normalize to shortest rotation path
        if swarm_rotation_needed > 180:
            swarm_rotation_needed -= 360
        elif swarm_rotation_needed < -180:
            swarm_rotation_needed += 360

        print(f"🏠 Swarm rotation needed: {swarm_rotation_needed} degrees")

        # Break into smaller rotation chunks
        rotation_chunks = []
        remaining_rotation = abs(swarm_rotation_needed)
        # Calculate rotation direction
        if swarm_rotation_needed > 0:
            direction = "rotate_clockwise"
        else:
            direction = "rotate_counter_clockwise"

        while remaining_rotation > 0:
            chunk = min(remaining_rotation, 90)  # Max 90 degrees per chunk
            rotation_chunks.append(chunk)
            remaining_rotation -= chunk

        for i, chunk in enumerate(rotation_chunks):
            desc = f"Orientation reset {i+1}/{len(rotation_chunks)}: {chunk}°"
            safe_command(swarm, direction, chunk, description=desc)
            track_movement(direction, chunk, f"Orientation reset {i+1}")
            time.sleep(0.8)

    # Step 4: Return swarm to origin position
    sync_point("Returning swarm to origin position")

    # Calculate movements needed to return swarm to origin
    swarm_return_x = -swarm_pos["x"]
    swarm_return_y = -swarm_pos["y"]
    swarm_return_z = -swarm_pos["z"]

    print(f"🏠 Swarm return needed: x={swarm_return_x}, "
          f"y={swarm_return_y}, z={swarm_return_z}")

    # Return X position
    if abs(swarm_return_x) > 10:
        if swarm_return_x > 0:
            move_dist = min(abs(swarm_return_x), 100)
            safe_command(swarm, "move_right", move_dist,
                         description=f"Swarm return X: {swarm_return_x}")
            track_movement("move_right", move_dist, "Swarm return X")
        else:
            move_dist = min(abs(swarm_return_x), 100)
            safe_command(swarm, "move_left", move_dist,
                         description=f"Swarm return X: {swarm_return_x}")
            track_movement("move_left", move_dist, "Swarm return X")
        time.sleep(2)

    # Return Y position
    if abs(swarm_return_y) > 10:
        if swarm_return_y > 0:
            move_dist = min(abs(swarm_return_y), 100)
            safe_command(swarm, "move_forward", move_dist,
                         description=f"Swarm return Y: {swarm_return_y}")
            track_movement("move_forward", move_dist, "Swarm return Y")
        else:
            move_dist = min(abs(swarm_return_y), 100)
            safe_command(swarm, "move_back", move_dist,
                         description=f"Swarm return Y: {swarm_return_y}")
            track_movement("move_back", move_dist, "Swarm return Y")
        time.sleep(2)

    # Return Z position (height) - be more conservative with height
    if abs(swarm_return_z) > 20:  # Only adjust if significantly off
        # Limit height adjustments
        target_adjustment = min(abs(swarm_return_z), 80)
        if swarm_return_z > 0:
            safe_command(swarm, "move_up", target_adjustment,
                         description=f"Swarm return Z: {swarm_return_z}")
            track_movement("move_up", target_adjustment, "Swarm return Z")
        else:
            safe_command(swarm, "move_down", target_adjustment,
                         description=f"Swarm return Z: {swarm_return_z}")
            track_movement("move_down", target_adjustment, "Swarm return Z")
        time.sleep(2)

    # Final position check
    final_swarm_pos = position_tracker["swarm_position"]
    print(f"🏠 Final estimated position: x={final_swarm_pos['x']}, "
          f"y={final_swarm_pos['y']}, z={final_swarm_pos['z']}, "
          f"rot={final_swarm_pos['rotation']}")

    print("🏠 Return to initial position sequence completed!")
    print("🏠 Drones should now be very close to their takeoff location")


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
            result = {"return_value": None, "exception": None,
                      "completed": False}

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
                timeout_msg = (f"Function {func.__name__} timed out "
                               f"after {timeout_seconds} seconds")
                raise TimeoutError(timeout_msg)

            if result["exception"]:
                raise result["exception"]  # pylint: disable=raising-bad-type

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


def execute_drone_movement_sequence(drone, sequence_name, movements, drone_id):
    """Generic helper for executing drone movements with error handling"""
    print(f"🔄 {drone_id} - Performing {sequence_name}")

    for i, movement in enumerate(movements):
        try:
            movement_type = movement["type"]
            distance = movement.get("distance", 0)
            description = movement.get("description",
                                       f"{sequence_name} step {i+1}")
            wait_time = movement.get("wait_time", 0.5)

            # Execute the movement
            if movement_type == "move_forward":
                drone.move_forward(distance)
            elif movement_type == "move_back":
                drone.move_back(distance)
            elif movement_type == "move_left":
                drone.move_left(distance)
            elif movement_type == "move_right":
                drone.move_right(distance)
            elif movement_type == "move_up":
                drone.move_up(distance)
            elif movement_type == "move_down":
                drone.move_down(distance)
            elif movement_type == "rotate_clockwise":
                drone.rotate_clockwise(distance)
            elif movement_type == "rotate_counter_clockwise":
                drone.rotate_counter_clockwise(distance)

            # Track the movement
            track_movement(movement_type, distance, description, drone_id)
            time.sleep(wait_time)

        except Exception as e:  # pylint: disable=broad-except
            print(f"🔄 {drone_id} - {sequence_name} step {i+1} error: {e}")
            continue


def check_battery_levels():
    """Helper to check battery levels for all drones in swarm"""
    if not swarm or not swarm.tellos:
        print("❌ Swarm not available for battery check")
        return []

    battery_info = []
    for i, tello in enumerate(swarm.tellos):
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


def return_drone_to_center(drone_instance, drone_id, position_offset):
    """Helper to return an individual drone to center position"""
    return_x = -position_offset["x"]
    return_y = -position_offset["y"]

    print(f"🏠 {drone_id} needs: x={return_x}, y={return_y}")

    # Return X position
    if abs(return_x) > 10:  # Only move if significant displacement
        move_distance = min(abs(return_x), 100)
        if return_x > 0:
            safe_command(drone_instance, "move_right", move_distance,
                         description=f"{drone_id} return X: {return_x}")
            track_movement("move_right", move_distance,
                           f"{drone_id} return X", drone_id.lower())
        else:
            safe_command(drone_instance, "move_left", move_distance,
                         description=f"{drone_id} return X: {return_x}")
            track_movement("move_left", move_distance,
                           f"{drone_id} return X", drone_id.lower())
        time.sleep(2)

    # Return Y position
    if abs(return_y) > 10:  # Only move if significant displacement
        move_distance = min(abs(return_y), 100)
        if return_y > 0:
            safe_command(drone_instance, "move_forward", move_distance,
                         description=f"{drone_id} return Y: {return_y}")
            track_movement("move_forward", move_distance,
                           f"{drone_id} return Y", drone_id.lower())
        else:
            safe_command(drone_instance, "move_back", move_distance,
                         description=f"{drone_id} return Y: {return_y}")
            track_movement("move_back", move_distance,
                           f"{drone_id} return Y", drone_id.lower())
        time.sleep(2)


def execute_geometric_pattern(drone, pattern_type, sides, distance, drone_id,
                              include_height=False):
    """Helper to execute geometric patterns (circle, square, triangle, etc.)"""
    angle_per_side = 360 / sides

    for i in range(sides):
        try:
            # Move forward
            drone.move_forward(distance)
            track_movement("move_forward", distance,
                           f"{drone_id} {pattern_type} step {i+1}",
                           drone_id.lower())
            time.sleep(0.5)

            # Rotate
            drone.rotate_clockwise(angle_per_side)
            track_movement("rotate_clockwise", angle_per_side,
                           f"{drone_id} {pattern_type} rotate {i+1}",
                           drone_id.lower())
            time.sleep(0.5)

            # Optional height variation
            if include_height and i % 2 == 0:
                drone.move_up(20)
                track_movement("move_up", 20,
                               f"{drone_id} {pattern_type} up {i+1}",
                               drone_id.lower())
                time.sleep(0.5)
            elif include_height and i % 2 == 1:
                drone.move_down(20)
                track_movement("move_down", 20,
                               f"{drone_id} {pattern_type} down {i+1}",
                               drone_id.lower())
                time.sleep(0.5)

        except Exception as e:  # pylint: disable=broad-except
            print(f"🔄 {drone_id} - {pattern_type} step {i+1} error: {e}")
            continue


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
        track_movement("move_left", 25, "Drone 1 spread left", "drone1")
        safe_command(swarm.tellos[1], "move_right", 25,
                     description="Drone 2 spread right")
        track_movement("move_right", 25, "Drone 2 spread right", "drone2")
        time.sleep(3)

        debug_print("Starting independent dance sequences")
        # Independent dance sequences (parallel execution)
        perform_independent_dance()

        debug_print("Returning to center formation")
        # Come back together - Reduced distance for 2M x 2M boundary
        sync_point("Returning to center formation", wait_time=3)
        safe_command(swarm.tellos[0], "move_right", 25,
                     description="Drone 1 return")
        track_movement("move_right", 25, "Drone 1 return to center", "drone1")
        safe_command(swarm.tellos[1], "move_left", 25,
                     description="Drone 2 return")
        track_movement("move_left", 25, "Drone 2 return to center", "drone2")
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
            except Exception as e:  # pylint: disable=broad-except
                print(f"Emergency command failed for drone {i+1}: {e}")
                try:
                    tello.land()
                    print(f"Land command sent for drone {i+1}")
                except Exception as land_e:  # pylint: disable=broad-except
                    print(f"Land failed for drone {i+1}: {land_e}")

        # Brief wait for commands to process
        time.sleep(2)

        # End connection
        try:
            swarm_instance.end()
            print("Connection terminated")
        except Exception as e:  # pylint: disable=broad-except
            print(f"End connection failed: {e}")

        # Cancel force exit timer since we completed successfully
        force_exit_timer.cancel()

    except Exception as e:  # pylint: disable=broad-except
        print(f"Emergency landing error: {e}")
        # Don't cancel timer - let it force exit


def reset_position_tracking():
    """Reset position tracking to initial state for 2M x 2M boundary"""
    global position_tracker  # pylint: disable=global-statement
    position_tracker = {
        "initial_height": 0,
        "movements": [],
        "spread_distance": 25,  # Reduced for 2M x 2M boundary
        "formation_offset": {"forward": 20, "up": 40},  # Reduced movements
        "drone_positions": {
            "drone1": {"x": 0, "y": 0, "z": 0, "rotation": 0},
            "drone2": {"x": 0, "y": 0, "z": 0, "rotation": 0}
        },
        "swarm_position": {"x": 0, "y": 0, "z": 0, "rotation": 0}
    }
    debug_print("Position tracking reset to initial state")


def track_movement(movement_type, distance, description="", drone_id=None):
    """Track a movement for potential compensation later"""
    # Use position_tracker directly instead of global declaration
    # Track movement in history
    position_tracker["movements"].append({
        "type": movement_type,
        "distance": distance,
        "description": description,
        "drone_id": drone_id
    })

    # Update position estimates
    if drone_id is None:  # Swarm movement
        pos = position_tracker["swarm_position"]
        if movement_type == "move_forward":
            pos["y"] += distance
        elif movement_type == "move_back":
            pos["y"] -= distance
        elif movement_type == "move_left":
            pos["x"] -= distance
        elif movement_type == "move_right":
            pos["x"] += distance
        elif movement_type == "move_up":
            pos["z"] += distance
        elif movement_type == "move_down":
            pos["z"] -= distance
        elif movement_type in ["rotate_clockwise", "rotate_counter_clockwise"]:
            if movement_type == "rotate_clockwise":
                pos["rotation"] = (pos["rotation"] + distance) % 360
            else:
                pos["rotation"] = (pos["rotation"] - distance) % 360
    else:  # Individual drone movement
        pos = position_tracker["drone_positions"][drone_id]
        if movement_type == "move_forward":
            pos["y"] += distance
        elif movement_type == "move_back":
            pos["y"] -= distance
        elif movement_type == "move_left":
            pos["x"] -= distance
        elif movement_type == "move_right":
            pos["x"] += distance
        elif movement_type == "move_up":
            pos["z"] += distance
        elif movement_type == "move_down":
            pos["z"] -= distance
        elif movement_type in ["rotate_clockwise", "rotate_counter_clockwise"]:
            if movement_type == "rotate_clockwise":
                pos["rotation"] = (pos["rotation"] + distance) % 360
            else:
                pos["rotation"] = (pos["rotation"] - distance) % 360

    debug_print(f"Tracked: {movement_type} {distance}cm - {description} "
                f"(drone: {drone_id})")


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
            if swarm:
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
