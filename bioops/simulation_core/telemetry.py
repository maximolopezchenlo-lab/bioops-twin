"""Telemetry data structures and sensor alert generation.

Provides the ``TelemetrySnapshot`` record for time-series storage and
``build_sensor_alert`` for generating structured JSON alerts that are
injected into the LLM chat when safety thresholds are breached.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bioops.simulation_core.state_machine import MachineState


@dataclass(frozen=True)
class TelemetrySnapshot:
    """Immutable point-in-time telemetry reading.

    Attributes:
        timestamp: Unix epoch seconds.
        rpm: Current rotor speed.
        vibration_rms_g: Root-mean-square vibration in *g*.
        state: Current FSM state.
    """

    timestamp: float
    rpm: int
    vibration_rms_g: float
    state: MachineState
    z_score: float = 0.0
    anomaly: bool = False


def build_sensor_alert(
    device_id: str,
    requested_rpm: int,
    actual_rpm: int,
    vibration_rms_g: float,
    threshold_g: float,
) -> dict[str, Any]:
    """Build a structured Sensor Alert JSON for the LLM feedback loop.

    This alert is injected as a SYSTEM message into the chat history
    when the simulator detects a safety violation (Rule 27).

    The schema follows the specification in the Technical Architecture
    document, section *The Sensor Alert JSON Schema*.

    Args:
        device_id: Hardware identifier (e.g. ``"CENT-01"``).
        requested_rpm: The RPM the operator/LLM originally requested.
        actual_rpm: The RPM at the time of the alert.
        vibration_rms_g: Current RMS vibration in *g*.
        threshold_g: The safety threshold that was exceeded.

    Returns:
        A dict matching the Sensor Alert JSON schema.
    """
    severity = "CRITICAL" if vibration_rms_g > threshold_g * 1.5 else "WARNING"

    # Resonance probability heuristic
    resonance_prob = "HIGH" if 7_000 <= actual_rpm <= 8_000 else "LOW"

    return {
        "device_id": device_id,
        "event": "SENSOR_ALARM",
        "severity": severity,
        "telemetry_snapshot": {
            "requested_rpm": requested_rpm,
            "actual_rpm": actual_rpm,
            "vibration_rms_g": round(vibration_rms_g, 4),
            "vibration_peak_g": round(vibration_rms_g * 1.4, 4),
            "resonance_probability": resonance_prob,
        },
        "error_analysis": {
            "code": "E_VIB_LIMIT",
            "message": (
                f"Vibration exceeded the safe operating threshold of "
                f"{threshold_g}g at {actual_rpm} RPM."
            ),
            "suggestion": (
                "The mass imbalance is excessive for the requested speed. "
                "Check rotor loading or reduce RPM."
            ),
        },
    }
