from djitellopy import TelloSwarm
import signal
import sys
import threading
import time

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
    print("\nReceived interrupt signal. Landing drones safely...")
    if swarm:
        try:
            swarm.land()
            swarm.end()
            print("Drones landed safely. Exiting...")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error during emergency landing: {e}")
    sys.exit(0)


# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)


def main():
    global swarm  # pylint: disable=global-statement

    try:
        swarm = TelloSwarm.fromIps([
            "172.28.3.205"
        ])

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
        swarm.takeoff()
        time.sleep(3)

        print("=== DRONE MOVEMENT DEMO ===")

        print("Moving up...")
        swarm.move_up(50)
        time.sleep(2)

        print("Moving down...")
        swarm.move_down(30)
        time.sleep(2)

        print("Moving forward...")
        swarm.move_forward(50)
        time.sleep(2)

        print("Moving back...")
        swarm.move_back(50)
        time.sleep(2)

        print("Moving left...")
        swarm.move_left(50)
        time.sleep(2)

        print("Moving right...")
        swarm.move_right(50)
        time.sleep(2)

        print("Rotating clockwise...")
        swarm.rotate_clockwise(90)
        time.sleep(2)

        print("Rotating counter-clockwise...")
        swarm.rotate_counter_clockwise(90)
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
            swarm.move_up(30)  # Add some extra height
            time.sleep(2)

            # Perform the flip with a longer wait time
            print("Executing flip...")
            swarm.flip_forward()
            time.sleep(5)  # Increased wait time for flip completion
            print("Flip completed successfully!")

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
            swarm.move_forward(60)
            time.sleep(1.5)
            swarm.rotate_clockwise(90)
            time.sleep(1.5)

        print("Final hover...")
        time.sleep(2)

        print("Landing...")
        swarm.land()
        swarm.end()
        print("Mission completed successfully!")

    except KeyboardInterrupt:
        # This shouldn't be reached due to signal handler, but just in case
        print("\nKeyboard interrupt detected!")
        signal_handler(signal.SIGINT, None)
    except Exception as e:  # pylint: disable=broad-except
        print(f"An error occurred: {e}")
        if swarm:
            try:
                swarm.land()
                swarm.end()
            except Exception:  # pylint: disable=broad-except
                pass
        sys.exit(1)


if __name__ == "__main__":
    main()
