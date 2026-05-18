"""Finite State Machine for the laboratory centrifuge.

Defines the allowed machine states and their legal transitions,
enforcing safety invariants at the FSM level.
"""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger("bioops_twin.fsm")


class MachineState(str, Enum):
    """Finite State Machine states for the centrifuge.

    Each state encodes a distinct operational mode with strict
    transition rules that prevent unsafe sequences (e.g. opening
    the lid while spinning).
    """

    STANDBY = "STANDBY"
    SPINNING = "SPINNING"
    ERROR = "ERROR"
    EMERGENCY_STOP = "EMERGENCY_STOP"


# Allowed transitions: current_state -> {valid next states}
TRANSITIONS: dict[MachineState, set[MachineState]] = {
    MachineState.STANDBY: {MachineState.SPINNING},
    MachineState.SPINNING: {
        MachineState.STANDBY,
        MachineState.ERROR,
        MachineState.EMERGENCY_STOP,
    },
    MachineState.ERROR: {MachineState.STANDBY},
    MachineState.EMERGENCY_STOP: {MachineState.STANDBY},
}


def is_valid_transition(current: MachineState, target: MachineState) -> bool:
    """Check whether a state transition is allowed by the FSM rules.

    Args:
        current: The machine's current state.
        target: The desired next state.

    Returns:
        True if the transition is legal, False otherwise.
    """
    return target in TRANSITIONS.get(current, set())


def attempt_transition(
    current: MachineState,
    target: MachineState,
) -> tuple[bool, MachineState]:
    """Attempt a state transition, logging the outcome.

    Args:
        current: The machine's current state.
        target: The desired next state.

    Returns:
        A tuple of (success, resulting_state). On failure the
        resulting_state equals *current*.
    """
    if is_valid_transition(current, target):
        logger.info("FSM transition: %s -> %s", current.value, target.value)
        return True, target
    logger.warning(
        "Illegal FSM transition blocked: %s -> %s",
        current.value,
        target.value,
    )
    return False, current
