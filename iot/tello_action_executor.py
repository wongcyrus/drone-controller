"""
Tello Drone Action Executor for controlling multiple drones via AWS IoT
"""

import logging
import queue
import threading
import time
import platform
from typing import Any, Dict, Optional, List
from uuid import uuid4

from djitellopy import TelloSwarm, Tello

logger = logging.getLogger(__name__)

# Windows-specific configuration
WINDOWS_SLEEP_INTERVAL = 0.2 if platform.system() == "Windows" else 0.1

# Tello drone action configuration dictionary
tello_actions: Dict[str, Dict[str, Any]] = {
    # Basic movement actions
    "takeoff": {"duration": 5.0, "description": "Take off", "method": "takeoff", "args": []},
    "land": {"duration": 5.0, "description": "Land", "method": "land", "args": []},
    "emergency": {"duration": 0.5, "description": "Emergency stop", "method": "emergency", "args": []},

    # Movement commands
    "move_up": {"duration": 3.0, "description": "Move up 50cm", "method": "move_up", "args": [50]},
    "move_down": {"duration": 3.0, "description": "Move down 50cm", "method": "move_down", "args": [50]},
    "move_left": {"duration": 3.0, "description": "Move left 50cm", "method": "move_left", "args": [50]},
    "move_right": {"duration": 3.0, "description": "Move right 50cm", "method": "move_right", "args": [50]},
    "move_forward": {"duration": 3.0, "description": "Move forward 50cm", "method": "move_forward", "args": [50]},
    "move_back": {"duration": 3.0, "description": "Move back 50cm", "method": "move_back", "args": [50]},

    # Rotation commands
    "rotate_clockwise": {"duration": 3.0, "description": "Rotate 90° clockwise", "method": "rotate_clockwise", "args": [90]},
    "rotate_counter_clockwise": {"duration": 3.0, "description": "Rotate 90° counter-clockwise", "method": "rotate_counter_clockwise", "args": [90]},

    # Flip commands
    "flip_left": {"duration": 4.0, "description": "Flip left", "method": "flip_left", "args": []},
    "flip_right": {"duration": 4.0, "description": "Flip right", "method": "flip_right", "args": []},
    "flip_forward": {"duration": 4.0, "description": "Flip forward", "method": "flip_forward", "args": []},
    "flip_back": {"duration": 4.0, "description": "Flip back", "method": "flip_back", "args": []},

    # Speed control
    "set_speed_slow": {"duration": 1.0, "description": "Set speed to 10", "method": "set_speed", "args": [10]},
    "set_speed_medium": {"duration": 1.0, "description": "Set speed to 50", "method": "set_speed", "args": [50]},
    "set_speed_fast": {"duration": 1.0, "description": "Set speed to 100", "method": "set_speed", "args": [100]},

    # Hover/idle
    "hover": {"duration": 3.0, "description": "Hover in place", "method": None, "args": []},

    # Formation actions (for swarm)
    "formation_line": {"duration": 10.0, "description": "Form line formation", "method": "formation_line", "args": []},
    "formation_circle": {"duration": 10.0, "description": "Form circle formation", "method": "formation_circle", "args": []},
    "formation_diamond": {"duration": 10.0, "description": "Form diamond formation", "method": "formation_diamond", "args": []},

    # Choreographed movements
    "dance_sequence_1": {"duration": 30.0, "description": "Dance sequence 1", "method": "dance_sequence_1", "args": []},
    "dance_sequence_2": {"duration": 45.0, "description": "Dance sequence 2", "method": "dance_sequence_2", "args": []},
    "synchronized_flip": {"duration": 8.0, "description": "Synchronized flip all drones", "method": "synchronized_flip", "args": []},

    # Video streaming
    "stream_on": {"duration": 2.0, "description": "Start video stream", "method": "streamon", "args": []},
    "stream_off": {"duration": 2.0, "description": "Stop video stream", "method": "streamoff", "args": []},
}

# Idle action for drones
idle_action: Dict[str, Any] = {"name": None, "duration": 0}


class TelloSwarmActionExecutor:
    """Action executor for controlling TelloSwarm via AWS IoT commands"""

    def __init__(self, drone_ips: List[str], swarm_id: str = "default_swarm"):
        """
        Initialize the TelloSwarmActionExecutor

        Args:
            drone_ips: List of IP addresses for Tello drones
            swarm_id: Identifier for this drone swarm
        """
        self.swarm_id = swarm_id
        self.drone_ips = drone_ips
        self.logger = logging.getLogger(__name__)

        # Initialize swarm
        try:
            self.swarm = TelloSwarm.fromIps(drone_ips)
            self.logger.info(f"Initialized swarm with {len(drone_ips)} drones")
        except Exception as e:
            self.logger.error(f"Failed to initialize swarm: {e}")
            self.swarm = None

        # Action queue and control
        self.action_queue: queue.Queue = queue.Queue()
        self.current_action: Dict[str, Any] = idle_action.copy()
        self.is_running: bool = False
        self._immediate_stop_event = threading.Event()
        self.queue_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()

        # Swarm state
        self.is_connected = False
        self.is_flying = False

    def connect(self) -> bool:
        """Connect to all drones in the swarm"""
        if not self.swarm:
            return False

        try:
            self.swarm.connect()
            self.is_connected = True
            self.logger.info("Successfully connected to all drones")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to swarm: {e}")
            return False

    def _execute_action(self, action_item: Dict[str, Any]) -> None:
        """Execute a single action on the swarm"""
        action_name = action_item["name"]
        drone_ids = action_item.get("drone_ids", "all")  # Default to all drones

        if action_name not in tello_actions:
            self.logger.error(f"Unknown action: {action_name}")
            return

        action = tello_actions[action_name]
        self.current_action = {
            "name": action_name,
            "duration": action["duration"],
            "drone_ids": drone_ids
        }

        try:
            self._run_tello_action(action_name, action, drone_ids)

            # Wait for action completion with interrupt capability
            elapsed = 0.0
            while elapsed < action["duration"]:
                if self._immediate_stop_event.is_set():
                    self.logger.info(f"Stopping action execution for {action_name}")
                    self._immediate_stop_event.clear()
                    self._emergency_stop()
                    break
                time.sleep(WINDOWS_SLEEP_INTERVAL)
                elapsed += WINDOWS_SLEEP_INTERVAL

        except Exception as e:
            self.logger.error(f"Error executing action {action_name}: {e}")
        finally:
            self._remove_action_by_id(action_item["id"])
            self.current_action = idle_action.copy()

    def _run_tello_action(self, action_name: str, action: Dict[str, Any], drone_ids: Any) -> None:
        """Execute a specific Tello action on specified drones"""
        if not self.swarm or not self.is_connected:
            self.logger.error("Swarm not connected")
            return

        method_name = action["method"]
        args = action["args"]

        # Handle special formation and choreography actions
        if method_name in ["formation_line", "formation_circle", "formation_diamond"]:
            self._execute_formation(method_name)
        elif method_name in ["dance_sequence_1", "dance_sequence_2"]:
            self._execute_dance_sequence(method_name)
        elif method_name == "synchronized_flip":
            self._execute_synchronized_flip()
        elif method_name is None:  # Hover action
            self.logger.info("Hovering in place")
        else:
            # Standard Tello command
            if drone_ids == "all":
                # Execute on all drones in parallel
                self.swarm.parallel(lambda i, tello: getattr(tello, method_name)(*args))
            else:
                # Execute on specific drones
                for drone_id in drone_ids:
                    if 0 <= drone_id < len(self.swarm.tellos):
                        tello = self.swarm.tellos[drone_id]
                        getattr(tello, method_name)(*args)

    def _execute_formation(self, formation_type: str) -> None:
        """Execute formation flying patterns"""
        if formation_type == "formation_line":
            # Line formation - drones in a straight line
            self.swarm.parallel(lambda i, tello: tello.go_xyz_speed(i * 100, 0, 0, 50))
        elif formation_type == "formation_circle":
            # Circle formation
            import math
            num_drones = len(self.swarm.tellos)
            radius = 100
            for i in range(num_drones):
                angle = (2 * math.pi * i) / num_drones
                x = int(radius * math.cos(angle))
                y = int(radius * math.sin(angle))
                self.swarm.tellos[i].go_xyz_speed(x, y, 0, 50)
        elif formation_type == "formation_diamond":
            # Diamond formation for 4 drones
            positions = [(0, 100, 0), (100, 0, 0), (0, -100, 0), (-100, 0, 0)]
            for i, (x, y, z) in enumerate(positions[:len(self.swarm.tellos)]):
                self.swarm.tellos[i].go_xyz_speed(x, y, z, 50)

    def _execute_dance_sequence(self, sequence_name: str) -> None:
        """Execute choreographed dance sequences"""
        if sequence_name == "dance_sequence_1":
            # Simple alternating up/down movement
            self.swarm.parallel(lambda i, tello:
                tello.move_up(50) if i % 2 == 0 else tello.move_down(50))
            time.sleep(2)
            self.swarm.parallel(lambda i, tello:
                tello.move_down(50) if i % 2 == 0 else tello.move_up(50))
        elif sequence_name == "dance_sequence_2":
            # Circular movement pattern
            self.swarm.parallel(lambda i, tello: tello.rotate_clockwise(90))
            time.sleep(2)
            self.swarm.parallel(lambda i, tello: tello.move_forward(50))
            time.sleep(2)
            self.swarm.parallel(lambda i, tello: tello.rotate_clockwise(90))

    def _execute_synchronized_flip(self) -> None:
        """Execute synchronized flips"""
        flip_types = ["flip_left", "flip_right", "flip_forward", "flip_back"]
        self.swarm.parallel(lambda i, tello:
            getattr(tello, flip_types[i % len(flip_types)])())

    def _emergency_stop(self) -> None:
        """Emergency stop all drones"""
        try:
            self.swarm.emergency()
            self.is_flying = False
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")

    def _remove_action_by_id(self, action_id: str) -> None:
        """Remove an action from the queue by its ID"""
        with self.queue_lock:
            temp_list = list(self.action_queue.queue)
            filtered = [item for item in temp_list if item["id"] != action_id]
            self._replace_queue(filtered)

    def _replace_queue(self, items: list) -> None:
        """Replace the current queue with a new list of items"""
        self.action_queue.queue.clear()
        for item in items:
            self.action_queue.put(item)

    def _consumer(self) -> None:
        """Continuously consume actions from the queue and execute them"""
        while not self._stop_event.is_set():
            try:
                if self._immediate_stop_event.is_set():
                    self.logger.info("Immediate stop triggered, clearing queue")
                    self.clear_action_queue()
                    self.current_action = idle_action.copy()
                    self.is_running = False
                    self._immediate_stop_event.clear()
                    time.sleep(0.5)
                    continue

                action_item = self.action_queue.get(timeout=1)
                self.is_running = True
                self._execute_action(action_item)

            except queue.Empty:
                self.is_running = False
                time.sleep(0.5)

    def add_action_to_queue(self, action_name: str, drone_ids: Any = "all") -> str:
        """
        Add a new action to the queue

        Args:
            action_name: Name of the action to execute
            drone_ids: "all" for all drones, or list of drone indices

        Returns:
            Action ID for tracking
        """
        action_id = str(uuid4())

        if action_name == "emergency":
            self.emergency_stop()
            return action_id

        if action_name not in tello_actions:
            self.logger.error(f"Action '{action_name}' not found in tello_actions")
            return action_id

        with self.queue_lock:
            self.action_queue.put({
                "id": action_id,
                "name": action_name,
                "drone_ids": drone_ids
            })

        return action_id

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue"""
        with self.queue_lock:
            self.action_queue.queue.clear()

    def emergency_stop(self) -> None:
        """Emergency stop all actions and drones"""
        self.logger.info("Emergency stop requested")
        self._immediate_stop_event.set()
        self.clear_action_queue()
        self._emergency_stop()

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm status"""
        with self.queue_lock:
            queue_items = list(self.action_queue.queue)

        drone_status = []
        if self.swarm and self.is_connected:
            for i, tello in enumerate(self.swarm.tellos):
                try:
                    battery = tello.get_battery()
                    height = tello.get_height()
                    temperature = tello.get_temperature()
                    drone_status.append({
                        "drone_id": i,
                        "ip": self.drone_ips[i],
                        "battery": battery,
                        "height": height,
                        "temperature": temperature,
                        "is_flying": tello.is_flying
                    })
                except Exception as e:
                    drone_status.append({
                        "drone_id": i,
                        "ip": self.drone_ips[i],
                        "error": str(e)
                    })

        return {
            "swarm_id": self.swarm_id,
            "connected": self.is_connected,
            "drone_count": len(self.drone_ips),
            "queue": queue_items,
            "current_action": self.current_action,
            "is_running": self.is_running,
            "drone_status": drone_status
        }

    def shutdown(self) -> None:
        """Gracefully shutdown the swarm controller"""
        self.logger.info("Shutting down swarm controller")
        self._stop_event.set()
        self.consumer_thread.join()

        if self.swarm and self.is_connected:
            try:
                self.swarm.land()
                self.swarm.end()
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")
