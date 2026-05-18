"""Command Pattern implementation for centrifuge actions.

Each command is a self-contained action object that can be executed,
undone, and logged. The ``CommandInvoker`` maintains a history stack
for traceability (Rule 6: Command Pattern).

Architecture reference:
    Technical Architecture § "The Command Pattern for Laboratory Automation"
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bioops.simulation_core.simulator import CentrifugeSimulator

logger = logging.getLogger("bioops_twin.commands")

# Physics constants (duplicated here to avoid circular imports)
MAX_SAFE_RPM: int = 15_000


# ---------------------------------------------------------------------------
# Abstract Command
# ---------------------------------------------------------------------------
class CentrifugeCommand(ABC):
    """Abstract base class for all centrifuge commands.

    Subclasses must implement ``execute()`` and ``undo()`` to support
    full command history and rollback.
    """

    @abstractmethod
    def execute(self, simulator: CentrifugeSimulator) -> str:
        """Execute the command on the simulator.

        Args:
            simulator: The centrifuge simulator instance.

        Returns:
            A human-readable status message.
        """

    @abstractmethod
    def undo(self, simulator: CentrifugeSimulator) -> str:
        """Reverse the command's effect on the simulator.

        Args:
            simulator: The centrifuge simulator instance.

        Returns:
            A human-readable status message.
        """


# ---------------------------------------------------------------------------
# Concrete Commands
# ---------------------------------------------------------------------------
class SetRPMCommand(CentrifugeCommand):
    """Set the centrifuge rotor to a target RPM.

    Stores the previous target for undo support.

    Args:
        rpm: Desired rotations per minute (0–15 000).
    """

    def __init__(self, rpm: int) -> None:
        self.rpm = rpm
        self._previous_rpm: int = 0

    def execute(self, simulator: CentrifugeSimulator) -> str:
        self._previous_rpm = simulator.target_rpm
        return simulator._handle_set_rpm(self.rpm)

    def undo(self, simulator: CentrifugeSimulator) -> str:
        logger.info("Undo SetRPM: reverting to %d RPM", self._previous_rpm)
        return simulator._handle_set_rpm(self._previous_rpm)


class StopCommand(CentrifugeCommand):
    """Immediately stop the centrifuge rotor."""

    def __init__(self) -> None:
        self._previous_rpm: int = 0

    def execute(self, simulator: CentrifugeSimulator) -> str:
        self._previous_rpm = simulator.target_rpm
        return simulator._handle_stop()

    def undo(self, simulator: CentrifugeSimulator) -> str:
        logger.info("Undo Stop: resuming at %d RPM", self._previous_rpm)
        return simulator._handle_set_rpm(self._previous_rpm)


class ResetCommand(CentrifugeCommand):
    """Reset the centrifuge from an error state to STANDBY."""

    def __init__(self) -> None:
        self._previous_state: str = ""

    def execute(self, simulator: CentrifugeSimulator) -> str:
        self._previous_state = simulator.state.value
        return simulator._handle_reset()

    def undo(self, simulator: CentrifugeSimulator) -> str:
        logger.info("Undo Reset: (no-op, cannot revert to error state)")
        return "ℹ️ Reset cannot be undone for safety reasons."


# ---------------------------------------------------------------------------
# Command Invoker (history manager)
# ---------------------------------------------------------------------------
@dataclass
class CommandInvoker:
    """Manages execution and history of centrifuge commands.

    Maintains a LIFO stack of executed commands for undo support
    and a full log for traceability.

    Attributes:
        history: Stack of executed commands (most recent last).
        log: Chronological list of (command_class_name, result) tuples.
    """

    history: list[CentrifugeCommand] = field(default_factory=list)
    log: list[tuple[str, str]] = field(default_factory=list)

    def execute(
        self,
        command: CentrifugeCommand,
        simulator: CentrifugeSimulator,
    ) -> str:
        """Execute a command and push it onto the history stack.

        Args:
            command: The command object to execute.
            simulator: The centrifuge simulator instance.

        Returns:
            The command's result message.
        """
        result = command.execute(simulator)
        self.history.append(command)
        self.log.append((type(command).__name__, result))
        logger.info("Executed %s -> %s", type(command).__name__, result)
        return result

    def undo_last(self, simulator: CentrifugeSimulator) -> str:
        """Undo the most recent command.

        Args:
            simulator: The centrifuge simulator instance.

        Returns:
            The undo result message, or an info message if history is empty.
        """
        if not self.history:
            return "ℹ️ No commands to undo."
        command = self.history.pop()
        result = command.undo(simulator)
        self.log.append((f"Undo({type(command).__name__})", result))
        return result


# ---------------------------------------------------------------------------
# Factory: JSON -> Command
# ---------------------------------------------------------------------------
def command_from_json(data: dict[str, Any]) -> CentrifugeCommand | None:
    """Create a command object from a parsed JSON dict.

    Expected schema::

        {"action": "set_rpm" | "stop" | "reset", "value": <int>}

    Args:
        data: Parsed JSON with ``action`` and optional ``value``.

    Returns:
        A command instance or ``None`` if the action is unknown.
    """
    action = data.get("action", "")
    if action == "set_rpm":
        return SetRPMCommand(rpm=int(data.get("value", 0)))
    if action == "stop":
        return StopCommand()
    if action == "reset":
        return ResetCommand()
    return None
