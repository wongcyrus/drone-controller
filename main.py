from djitellopy import TelloSwarm
import signal
import sys

# Global variable to hold the swarm instance
swarm = None


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
            "192.168.221.1"
        ])

        print("Connecting to swarm...")
        swarm.connect()

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
