#!/usr/bin/env python3
"""
Quick test to verify the mock drone works with djitellopy
"""

import time

def test_mock_drone():
    """Test basic commands with the mock drone"""
    try:
        from djitellopy import Tello

        print("🔗 Connecting to mock drone...")
        tello = Tello("127.0.0.1")
        tello.connect()

        print(f"🔋 Battery: {tello.get_battery()}%")
        print(f"📏 Height: {tello.get_height()}cm")

        print("🚁 Taking off...")
        tello.takeoff()
        time.sleep(1)

        print(f"📏 Height after takeoff: {tello.get_height()}cm")

        print("⬆️ Moving up 30cm...")
        tello.move_up(30)
        time.sleep(1)

        print(f"📏 Height after move up: {tello.get_height()}cm")

        print("🔄 Rotating 45 degrees...")
        tello.rotate_clockwise(45)
        time.sleep(1)

        print("⬇️ Landing...")
        tello.land()

        print("✅ Test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mock_drone()
    exit(0 if success else 1)
