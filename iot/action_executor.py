"""
Action Executor Module for Drone Controller

This module provides a unified interface for controlling drone swarms via IoT
messaging. It includes a base ActionExecutor class and factory functions for
creating specific executor implementations.
"""

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)

# Import Tello-specific components
try:
    from .tello_action_executor import TelloSwarmActionExecutor
    from .tello_swarm_iot_client import TelloSwarmIoTClient
    TELLO_SUPPORT = True
except ImportError:
    try:
        # Try absolute imports if relative imports fail
        from tello_action_executor import TelloSwarmActionExecutor
        from tello_swarm_iot_client import TelloSwarmIoTClient
        TELLO_SUPPORT = True
    except ImportError as e:
        print(f"Tello support not available: {e}")
        TELLO_SUPPORT = False


class BaseActionExecutor(ABC):
    """
    Abstract base class for action executors.

    This defines the interface that all action executors must implement.
    """

    @abstractmethod
    def add_action_to_queue(self, action_name: str,
                           drone_ids: Union[str, List[int]] = "all") -> str:
        """
        Add an action to the execution queue.

        Args:
            action_name: Name of the action to execute
            drone_ids: Target drones ("all" or list of drone IDs)

        Returns:
            Action ID for tracking
        """
        pass

    @abstractmethod
    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        pass

    @abstractmethod
    def emergency_stop(self) -> None:
        """Emergency stop all actions and drones."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get executor status information."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the executor and cleanup resources."""
        pass


class SimulatorActionExecutor(BaseActionExecutor):
    """
    Action executor for simulator/mock environments.

    This executor logs actions instead of executing them on real hardware.
    Useful for testing and development.
    """

    def __init__(self, robot_name: str, simulator_endpoint: str,
                 session_key: str):
        self.robot_name = robot_name
        self.simulator_endpoint = simulator_endpoint
        self.session_key = session_key
        self.logger = logging.getLogger(__name__)
        self.action_queue: queue.Queue = queue.Queue()
        self.is_running = False
        self._stop_event = threading.Event()

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer,
                                               daemon=True)
        self.consumer_thread.start()

    def add_action_to_queue(self, action_name: str,
                           drone_ids: Union[str, List[int]] = "all") -> str:
        """Add an action to the simulation queue."""
        action_id = str(uuid4())
        action_item = {
            "id": action_id,
            "name": action_name,
            "drone_ids": drone_ids,
            "timestamp": time.time()
        }

        self.action_queue.put(action_item)
        self.logger.info("Simulated action queued: %s for drones %s",
                        action_name, drone_ids)
        return action_id

    def _consumer(self) -> None:
        """Process actions from the queue (simulation)."""
        while not self._stop_event.is_set():
            try:
                action_item = self.action_queue.get(timeout=1)
                self.is_running = True
                self._simulate_action(action_item)
                self.is_running = False
            except queue.Empty:
                self.is_running = False
                time.sleep(0.1)

    def _simulate_action(self, action_item: Dict[str, Any]) -> None:
        """Simulate action execution."""
        action_name = action_item["name"]
        drone_ids = action_item["drone_ids"]

        self.logger.info("Simulating action: %s on drones: %s",
                        action_name, drone_ids)

        # Simulate action duration
        if action_name in ["takeoff", "land"]:
            time.sleep(2.0)
        elif action_name.startswith("move_"):
            time.sleep(1.5)
        elif action_name.startswith("flip_"):
            time.sleep(3.0)
        elif action_name.startswith("formation_"):
            time.sleep(5.0)
        elif action_name.startswith("dance_"):
            time.sleep(10.0)
        else:
            time.sleep(1.0)

        self.logger.info("Completed simulation of: %s", action_name)

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        with self.action_queue.mutex:
            self.action_queue.queue.clear()
        self.logger.info("Simulator action queue cleared")

    def emergency_stop(self) -> None:
        """Simulate emergency stop."""
        self.clear_action_queue()
        self.logger.warning("Simulator emergency stop executed")

    def get_status(self) -> Dict[str, Any]:
        """Get simulator status."""
        return {
            "robot_name": self.robot_name,
            "simulator_endpoint": self.simulator_endpoint,
            "is_running": self.is_running,
            "queue_size": self.action_queue.qsize(),
            "type": "simulator"
        }

    def stop(self) -> None:
        """Stop the simulator."""
        self.logger.info("Stopping simulator executor")
        self._stop_event.set()
        if self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=2.0)


class ActionExecutor(BaseActionExecutor):
    """
    Unified ActionExecutor that wraps different executor implementations.

    This class provides backward compatibility with the existing pubsub.py
    interface while supporting multiple drone platforms.
    """

    def __init__(self,
                 robot_name: str,
                 simulator_endpoint: str = "",
                 session_key: str = "",
                 executor_type: str = "tello",
                 drone_ips: Optional[List[str]] = None,
                 swarm_id: str = "default_swarm"):
        """
        Initialize the ActionExecutor.

        Args:
            robot_name: Name/identifier for this robot/swarm
            simulator_endpoint: Endpoint for simulator (if applicable)
            session_key: Session key for authentication (if applicable)
            executor_type: Type of executor ("tello", "simulator", etc.)
            drone_ips: List of drone IP addresses
            swarm_id: Identifier for the drone swarm
        """
        self.robot_name = robot_name
        self.simulator_endpoint = simulator_endpoint
        self.session_key = session_key
        self.executor_type = executor_type
        self.swarm_id = swarm_id
        self.logger = logging.getLogger(__name__)

        # Default drone IPs if not provided
        if drone_ips is None:
            drone_ips = ['192.168.10.1']  # Default Tello IP
        self.drone_ips = drone_ips

        # Initialize the appropriate executor
        self._executor = self._create_executor()

        # Action tracking
        self._action_counter = 0
        self._action_lock = threading.Lock()

    def _create_executor(self) -> Any:
        """Create the appropriate executor based on type."""
        if self.executor_type == "tello":
            if not TELLO_SUPPORT:
                raise ImportError("Tello support not available")
            return TelloSwarmActionExecutor(self.drone_ips, self.swarm_id)

        elif self.executor_type == "simulator":
            return SimulatorActionExecutor(
                self.robot_name,
                self.simulator_endpoint,
                self.session_key
            )

        else:
            raise ValueError(
                f"Unsupported executor type: {self.executor_type}"
            )

    def add_action_to_queue(self, action_name: str,
                           drone_ids: Union[str, List[int]] = "all") -> str:
        """Add an action to the execution queue."""
        with self._action_lock:
            self._action_counter += 1
            action_id = f"{self.robot_name}_action_{self._action_counter}"

        self.logger.info("Adding action %s to queue (ID: %s)",
                        action_name, action_id)

        # Delegate to the underlying executor
        if hasattr(self._executor, 'add_action_to_queue'):
            return self._executor.add_action_to_queue(action_name, drone_ids)
        else:
            # Fallback for executors that don't support drone_ids parameter
            return self._executor.add_action_to_queue(action_name)

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        self.logger.info("Clearing action queue")
        return self._executor.clear_action_queue()

    def emergency_stop(self) -> None:
        """Emergency stop all actions and drones."""
        self.logger.warning("Emergency stop triggered")
        return self._executor.emergency_stop()

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        base_status = {
            "robot_name": self.robot_name,
            "executor_type": self.executor_type,
            "swarm_id": self.swarm_id,
            "drone_ips": self.drone_ips,
            "action_counter": self._action_counter
        }

        # Merge with executor-specific status
        if hasattr(self._executor, 'get_status'):
            executor_status = self._executor.get_status()
            base_status.update(executor_status)
        elif hasattr(self._executor, 'get_swarm_status'):
            executor_status = self._executor.get_swarm_status()
            base_status.update(executor_status)

        return base_status

    def stop(self) -> None:
        """Stop the executor and cleanup resources."""
        self.logger.info("Stopping ActionExecutor")
        if hasattr(self._executor, 'stop'):
            self._executor.stop()
        elif hasattr(self._executor, 'shutdown'):
            self._executor.shutdown()

    def connect(self) -> bool:
        """Connect to drones (if applicable)."""
        if hasattr(self._executor, 'connect'):
            return self._executor.connect()
        return True

    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.stop()
        except Exception:  # noqa: E722
            pass


def create_action_executor(drone_ips: List[str],
                          swarm_id: str = 'default_swarm') -> ActionExecutor:
    """
    Factory function to create Tello drone swarm action executor

    Args:
        drone_ips: List of IP addresses for Tello drones
        swarm_id: Identifier for this drone swarm

    Returns:
        ActionExecutor instance configured for Tello

    Raises:
        ImportError: If Tello support is not available
    """
    return ActionExecutor(
        robot_name=swarm_id,
        executor_type="tello",
        drone_ips=drone_ips,
        swarm_id=swarm_id
    )


def create_simulator_executor(robot_name: str,
                             simulator_endpoint: str = "",
                             session_key: str = "") -> ActionExecutor:
    """
    Factory function to create simulator action executor

    Args:
        robot_name: Name/identifier for this robot
        simulator_endpoint: Endpoint for simulator
        session_key: Session key for authentication

    Returns:
        ActionExecutor instance configured for simulation
    """
    return ActionExecutor(
        robot_name=robot_name,
        simulator_endpoint=simulator_endpoint,
        session_key=session_key,
        executor_type="simulator"
    )


def create_iot_client(
    client_id: str,
    endpoint: str,
    root_ca_path: str,
    private_key_path: str,
    certificate_path: str,
    swarm_id: str,
    drone_ips: List[str],
    schema_path: Optional[str] = None
):
    """
    Factory function to create Tello drone swarm IoT client

    Args:
        client_id: Unique client identifier
        endpoint: AWS IoT endpoint URL
        root_ca_path: Path to root CA certificate
        private_key_path: Path to private key file
        certificate_path: Path to device certificate
        swarm_id: Identifier for this drone swarm
        drone_ips: List of IP addresses for Tello drones
        schema_path: Optional path to JSON schema file

    Returns:
        TelloSwarmIoTClient instance

    Raises:
        ImportError: If Tello support is not available
    """
    if not TELLO_SUPPORT:
        raise ImportError(
            "Tello support not available. "
            "Install djitellopy and related dependencies."
        )

    return TelloSwarmIoTClient(
        client_id=client_id,
        endpoint=endpoint,
        root_ca_path=root_ca_path,
        pri_key_filepath=private_key_path,
        certificate_path=certificate_path,
        swarm_id=swarm_id,
        drone_ips=drone_ips,
        schema_path=schema_path
    )


def create_legacy_action_executor(executor_type: str = "tello",
                                 **kwargs) -> ActionExecutor:
    """
    Legacy factory function for backward compatibility

    Note: This function is deprecated. Use create_action_executor() instead.

    Args:
        executor_type: Type of executor (only "tello" is supported)
        **kwargs: Additional arguments for executor initialization

    Returns:
        ActionExecutor instance

    Raises:
        ValueError: If executor_type is not "tello"
        ImportError: If Tello support is not available
    """
    logger.warning(
        "create_legacy_action_executor is deprecated. "
        "Use create_action_executor() instead."
    )

    if executor_type != "tello":
        raise ValueError(
            f"Only 'tello' executor type is supported, got: {executor_type}"
        )

    drone_ips = kwargs.get('drone_ips', ['192.168.10.1'])
    swarm_id = kwargs.get('swarm_id', 'default_swarm')

    return create_action_executor(drone_ips, swarm_id)


# Module information
__version__ = "2.0.0"
__author__ = "HKIIT Drone Controller Team"
__description__ = "Unified Action Executor and IoT Client Factory"
