#!/usr/bin/env python3
"""
Start the Drone Simulator 3D
Simple script to launch the web-based drone simulator
"""

import sys
import webbrowser
from pathlib import Path

def main():
    """Start the simulator."""
    simulator_path = Path(__file__).parent
    index_file = simulator_path / "index.html"

    if not index_file.exists():
        print("Error: Simulator files not found!")
        print(f"Expected to find: {index_file}")
        return 1

    print("🚁 Starting Drone Simulator 3D...")
    print(f"📂 Simulator location: {simulator_path}")

    # Try to start with Python bridge first
    try:
        from simulator_bridge import start_simulator
        print("🌐 Starting with Python bridge...")
        start_simulator(str(simulator_path))
    except ImportError:
        # Fallback to direct browser opening
        print("📱 Opening simulator in browser...")
        file_url = f"file://{index_file.absolute()}"
        webbrowser.open(file_url)
        print(f"🔗 Opened: {file_url}")
        print("\nNote: For full features, install Python dependencies:")
        print("  pip install websockets")

        # Keep script running
        try:
            input("\nPress Enter to exit...")
        except KeyboardInterrupt:
            pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
