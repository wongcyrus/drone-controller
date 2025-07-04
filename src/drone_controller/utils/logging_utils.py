"""
Logging utilities for drone control operations.

Provides standardized logging configuration and drone-specific loggers.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_drone_logging(console_level: str = "INFO", log_to_file: bool = True, log_dir: str = "logs", file_level: str = "DEBUG") -> logging.Logger:
    """
    Set up comprehensive logging for drone operations.

    Args:
        console_level: Console logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file in addition to console
        log_dir: Directory to store log files
        file_level: File logging level (defaults to DEBUG for detailed file logs)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_to_file:
        Path(log_dir).mkdir(exist_ok=True)

    # Set up root logger - use the most permissive level between console and file
    console_level_num = getattr(logging, console_level.upper())
    file_level_num = getattr(logging, file_level.upper()) if log_to_file else console_level_num
    min_level = min(console_level_num, file_level_num)

    logger = logging.getLogger("drone_controller")
    logger.setLevel(min_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler with specified level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level_num)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if enabled) with detailed logging
    if log_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = Path(log_dir) / f"drone_controller_{timestamp}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level_num)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Only show file logging message if console level is INFO or lower
        if console_level_num <= logging.INFO:
            logger.info(f"Logging to file: {log_file}")

    return logger


def get_drone_logger(drone_id: str) -> logging.Logger:
    """
    Get a logger specific to a drone.

    Args:
        drone_id: Unique identifier for the drone

    Returns:
        logging.Logger: Drone-specific logger
    """
    return logging.getLogger(f"drone_controller.drone_{drone_id}")


def get_swarm_logger(swarm_id: str) -> logging.Logger:
    """
    Get a logger specific to a swarm.

    Args:
        swarm_id: Unique identifier for the swarm

    Returns:
        logging.Logger: Swarm-specific logger
    """
    return logging.getLogger(f"drone_controller.swarm_{swarm_id}")
