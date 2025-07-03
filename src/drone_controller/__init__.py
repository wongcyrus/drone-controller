"""
Drone Controller Package for Multi-Robot Tello Talent Management

This package provides comprehensive tools for controlling multiple Tello Talent drones
simultaneously, including formation flying, coordinated missions, and swarm behaviors.
"""

__version__ = "0.1.0"
__author__ = "Drone Controller Project"

from .core.tello_drone import TelloDrone
from .multi_robot.swarm_controller import SwarmController
from .multi_robot.formation_manager import FormationManager

__all__ = [
    "TelloDrone",
    "SwarmController", 
    "FormationManager",
]
