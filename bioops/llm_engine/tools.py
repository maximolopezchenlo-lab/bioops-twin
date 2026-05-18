"""Tool function declarations for Gemini Function Calling.

These Python functions are passed directly to the ``google-genai`` SDK
as ``tools=[]``.  The SDK uses type hints and docstrings to generate
the JSON schema automatically (Automatic Function Calling).

Each function wraps the global simulator instance and returns a
human-readable string that the model can relay to the operator.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bioops.simulation_core.simulator import CentrifugeSimulator

logger = logging.getLogger("bioops_twin.tools")

# The simulator instance is injected at module level by the
# client.py module during initialisation.  This avoids circular
# imports while keeping the functions as plain callables.
_simulator: CentrifugeSimulator | None = None


def bind_simulator(simulator: CentrifugeSimulator) -> None:
    """Bind the global simulator instance for tool functions.

    Must be called once during application startup before any
    tool function is invoked.

    Args:
        simulator: The centrifuge simulator instance.
    """
    global _simulator  # noqa: PLW0603
    _simulator = simulator
    logger.info("Tool functions bound to simulator %s", simulator.device_id)


def _get_simulator() -> CentrifugeSimulator:
    """Return the bound simulator or raise if not initialised."""
    if _simulator is None:
        raise RuntimeError(
            "Simulator not bound. Call bind_simulator() at startup."
        )
    return _simulator


# ---------------------------------------------------------------------------
# Tool Functions (passed to Gemini as tools=[...])
# ---------------------------------------------------------------------------

def set_centrifuge_rpm(rpm: int) -> str:
    """Set the centrifuge rotor speed to the specified RPM value.

    Use this tool when the operator requests a speed change for
    calibration or testing.  The simulator will ramp the rotor
    gradually toward the target speed.

    Args:
        rpm: Target rotations per minute.  Must be between 0 and 15000.

    Returns:
        A status message indicating success or failure.
    """
    sim = _get_simulator()
    result = sim.execute_command({"action": "set_rpm", "value": rpm})
    logger.info("Tool set_centrifuge_rpm(%d) -> %s", rpm, result)
    return result


def stop_centrifuge() -> str:
    """Immediately stop the centrifuge rotor and return to STANDBY.

    Use this tool when the operator requests an immediate stop or
    when a safety concern requires halting rotation.

    Returns:
        A status message confirming the stop command.
    """
    sim = _get_simulator()
    result = sim.execute_command({"action": "stop"})
    logger.info("Tool stop_centrifuge() -> %s", result)
    return result


def reset_centrifuge() -> str:
    """Reset the centrifuge from ERROR or EMERGENCY_STOP to STANDBY.

    Use this tool after a safety violation has been acknowledged
    and the operator wants to resume operations.

    Returns:
        A status message confirming the reset.
    """
    sim = _get_simulator()
    result = sim.execute_command({"action": "reset"})
    logger.info("Tool reset_centrifuge() -> %s", result)
    return result


def query_calibration_manual(query: str, equipment_id: str = "CENT-01") -> str:
    """Query the laboratory calibration manual for safety limits and protocols.

    Use this tool BEFORE setting RPM if you are unsure about the payload mass
    limits or resonance frequencies for the given equipment.

    Args:
        query: The specific question about limits, payloads, or RPM.
        equipment_id: The equipment identifier (default: CENT-01).

    Returns:
        A string containing the retrieved text chunks from the manual.
    """
    from bioops.rag_memory.retriever import retrieve_context
    logger.info("Function called: query_calibration_manual(query='%s', equipment_id='%s')", query, equipment_id)
    chunks = retrieve_context(query=query, equipment_id=equipment_id, top_k=2)
    if not chunks:
        return "No information found in the calibration manual for that query."
    return "\n\n---\n\n".join(chunks)


# Convenience list for passing to the SDK
ALL_TOOLS = [set_centrifuge_rpm, stop_centrifuge, reset_centrifuge, query_calibration_manual]
