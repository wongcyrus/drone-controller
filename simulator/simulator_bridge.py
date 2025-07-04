"""
Drone Simulator Bridge - Simple version for demos
"""

import webbrowser
from pathlib import Path


def start_simulator():
    """Start the 3D drone simulator."""
    print("🚁 Starting 3D Drone Simulator...")

    # Try to open the simulator directly
    simulator_path = Path(__file__).parent
    index_file = simulator_path / "index.html"

    if index_file.exists():
        try:
            # Open simulator in browser
            webbrowser.open(f"file://{index_file.absolute()}")
            print(f"✅ Opened simulator: {index_file}")
            print("\n📋 Available Options:")
            print("1. Single Drone Mode:")
            print("   - Click 'Connect Drone' to add a drone")
            print("   - Use the controls to fly")
            print("2. Swarm Mode:")
            print("   - Click 'Swarm Mode' at the top")
            print("   - Add multiple drones")
            print("   - Try formation flying")
            print("\n🎮 Controls:")
            print("  WASD - Move Left/Right/Forward/Back")
            print("  Q/E - Move Up/Down")
            print("  R/T - Rotate Left/Right")
            print("  Space - Takeoff/Land")
            print("\n✨ Have fun flying!")
            print("\nPress Ctrl+C to stop the simulator.")

            # Keep script running
            try:
                input("\nPress Enter to stop the simulator...")
            except KeyboardInterrupt:
                print("\n🛑 Simulator stopped.")

            return True

        except Exception as e:
            print(f"❌ Failed to open simulator: {e}")
            return False
    else:
        print(f"❌ Simulator not found at: {index_file}")
        return False


def run_basic_flight_demo():
    """Run basic flight demonstration."""
    print("🚁 Starting Basic Flight Demo...")
    print("=" * 50)

    # Try to open the simulator directly
    simulator_path = Path(__file__).parent
    index_file = simulator_path / "index.html"

    if index_file.exists():
        try:
            # Open simulator in browser
            webbrowser.open(f"file://{index_file.absolute()}")
            print(f"✅ Opened simulator: {index_file}")
            print("\n📋 Demo Steps:")
            print("1. The simulator should open in your browser")
            print("2. Click 'Connect Drone' to add a drone")
            print("3. Enter drone ID: 'demo_drone'")
            print("4. Click 'Takeoff' to start flying")
            print("5. Use keyboard controls to move:")
            print("   - WASD for movement")
            print("   - Q/E for up/down")
            print("   - R/T for rotation")
            print("6. Click 'Land' when finished")
            print("\n🎮 Manual Controls:")
            print("  WASD - Move Left/Right/Forward/Back")
            print("  Q/E - Move Up/Down")
            print("  R/T - Rotate Left/Right")
            print("  Space - Takeoff/Land")
            print("\n✨ Try flying the drone around!")

            # Keep script running for a bit
            input("\nPress Enter when done with demo...")
            return True

        except Exception as e:
            print(f"❌ Failed to open simulator: {e}")
            return False
    else:
        print(f"❌ Simulator not found at: {index_file}")
        return False


def run_swarm_formation_demo():
    """Run swarm formation demonstration."""
    print("🛸 Starting Swarm Formation Demo...")
    print("=" * 50)

    # Try to open the simulator directly
    simulator_path = Path(__file__).parent
    index_file = simulator_path / "index.html"

    if index_file.exists():
        try:
            # Open simulator in browser
            webbrowser.open(f"file://{index_file.absolute()}")
            print(f"✅ Opened simulator: {index_file}")
            print("\n📋 Demo Steps:")
            print("1. The simulator should open in your browser")
            print("2. Click 'Swarm Mode' at the top")
            print("3. Add drones:")
            print("   - Enter drone ID (e.g., 'alpha')")
            print("   - Click 'Add Drone'")
            print("   - Repeat for 'beta', 'gamma', 'delta'")
            print("4. Click 'Initialize Swarm'")
            print("5. Click 'Swarm Takeoff'")
            print("6. Try different formations:")
            print("   - Select formation type (Line, Circle, Diamond, V)")
            print("   - Click 'Create Formation'")
            print("7. Move the formation with movement controls")
            print("8. Click 'Swarm Land' when finished")
            print("\n🎯 Formation Types Available:")
            print("  • Line - Drones in a straight line")
            print("  • Circle - Drones in a circle")
            print("  • Diamond - Diamond shape formation")
            print("  • V - Classic V-formation")
            print("\n✨ Enjoy the swarm demo!")

            # Keep script running for a bit
            input("\nPress Enter when done with demo...")
            return True

        except Exception as e:
            print(f"❌ Failed to open simulator: {e}")
            return False
    else:
        print(f"❌ Simulator not found at: {index_file}")
        return False
