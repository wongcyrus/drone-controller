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

        print("Moving up...")
        # run in parallel on all tellos
        swarm.move_up(100)

        print("Moving forward sequentially...")
        # run by one tello after the other
        swarm.sequential(lambda i, tello: tello.move_forward(i * 20 + 20))

        print("Moving left in parallel...")
        # making each tello do something unique in parallel
        swarm.parallel(lambda i, tello: tello.move_left(i * 100 + 20))

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
