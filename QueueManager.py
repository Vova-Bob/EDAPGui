"""
Queue Manager Module for Thread-Safe Communication

This module provides thread-safe queue management for communication
between GUI and Autopilot threads in EDAPGui.

Author: EDAPGui Project
Date: 2025-12-29
"""

import queue
import threading
from enum import Enum
from typing import Any, Optional
from EDlogger import logger


class Command(Enum):
    """Commands that can be sent from GUI to Autopilot."""
    START_FSD = "start_fsd"
    STOP_FSD = "stop_fsd"
    START_SC = "start_sc"
    STOP_SC = "stop_sc"
    START_WAYPOINT = "start_waypoint"
    STOP_WAYPOINT = "stop_waypoint"
    START_ROBIGO = "start_robigo"
    STOP_ROBIGO = "stop_robigo"
    START_DSS = "start_dss"
    STOP_DSS = "stop_dss"
    STOP_ALL = "stop_all"


class StatusMessage:
    """Immutable status message for thread-safe communication."""

    def __init__(self, msg_type: str, data: Any):
        """
        Initialize status message.

        Args:
            msg_type: Type of message ("status", "log", "error")
            data: Message data (dict with mode, state, message, etc.)
        """
        self._type = msg_type
        self._data = data

    @property
    def type(self) -> str:
        """Get message type."""
        return self._type

    @property
    def data(self) -> Any:
        """Get message data (returns copy to prevent mutation)."""
        return self._data.copy() if isinstance(self._data, dict) else self._data


class QueueManager:
    """Manages thread-safe queues for GUI-Autopilot communication."""

    def __init__(self, max_queue_size: int = 100):
        """
        Initialize queue manager.

        Args:
            max_queue_size: Maximum number of items in queue before blocking
        """
        self.max_queue_size = max_queue_size
        self.command_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.status_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)

        # Metrics for monitoring
        self.command_queue_max_size = 0
        self.status_queue_max_size = 0
        self.command_queue_overflow_count = 0
        self.status_queue_overflow_count = 0

    def put_command(self, command: Command, timeout: float = 0.1) -> bool:
        """
        Put command into command queue with size limit.

        Args:
            command: Command to send
            timeout: Timeout in seconds

        Returns:
            True if command was queued, False if queue is full
        """
        try:
            self.command_queue.put(command, timeout=timeout)
            self._update_command_metrics()
            return True
        except queue.Full:
            self.command_queue_overflow_count += 1
            logger.warning(f"Command queue full, dropping command: {command.value}")
            return False

    def put_status(self, status_msg: StatusMessage, timeout: float = 0.1) -> bool:
        """
        Put status message into status queue with size limit.

        Args:
            status_msg: StatusMessage to send
            timeout: Timeout in seconds

        Returns:
            True if message was queued, False if queue is full
        """
        try:
            self.status_queue.put(status_msg, timeout=timeout)
            self._update_status_metrics()
            return True
        except queue.Full:
            self.status_queue_overflow_count += 1
            logger.warning(f"Status queue full, dropping message: {status_msg.type}")
            return False

    def get_command(self, timeout: float = 0.1) -> Optional[Command]:
        """
        Get command from command queue with timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            Command or None if queue is empty
        """
        try:
            return self.command_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_status(self, timeout: float = 0.1) -> Optional[StatusMessage]:
        """
        Get status message from status queue with timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            StatusMessage or None if queue is empty
        """
        try:
            return self.status_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _update_command_metrics(self):
        """Update command queue metrics."""
        current_size = self.command_queue.qsize()
        if current_size > self.command_queue_max_size:
            self.command_queue_max_size = current_size

    def _update_status_metrics(self):
        """Update status queue metrics."""
        current_size = self.status_queue.qsize()
        if current_size > self.status_queue_max_size:
            self.status_queue_max_size = current_size

    def get_metrics(self) -> dict:
        """
        Get queue metrics for monitoring.

        Returns:
            Dictionary with queue sizes and overflow counts
        """
        return {
            "command_queue_size": self.command_queue.qsize(),
            "command_queue_max_size": self.command_queue_max_size,
            "command_queue_overflow_count": self.command_queue_overflow_count,
            "status_queue_size": self.status_queue.qsize(),
            "status_queue_max_size": self.status_queue_max_size,
            "status_queue_overflow_count": self.status_queue_overflow_count,
        }

    def clear_queues(self):
        """Clear all queues (for graceful shutdown)."""
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except queue.Empty:
                break

        while not self.status_queue.empty():
            try:
                self.status_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Queues cleared for shutdown")
