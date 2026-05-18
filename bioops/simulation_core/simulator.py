"""Analytic physics simulator for a laboratory centrifuge.

Implements deterministic vibration calculations based on centripetal
force and structural resonance proximity.  The simulator is the
"Receiver" in the Command Pattern and is governed by a Finite State
Machine that prevents unsafe transitions.

Architecture reference:
    Technical Architecture § "Control Loop Architecture and State Management"
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from bioops.simulation_core.commands import (
    CommandInvoker,
    command_from_json,
)
from bioops.simulation_core.state_machine import (
    MachineState,
    attempt_transition,
)
from bioops.simulation_core.telemetry import (
    TelemetrySnapshot,
    build_sensor_alert,
)
from bioops.security.audit_logger import log_event
from bioops.industrial_edge.mqtt_client import mqtt_edge

logger = logging.getLogger("bioops_twin.simulator")

# ---------------------------------------------------------------------------
# Physics Constants
# ---------------------------------------------------------------------------
MAX_TELEMETRY_POINTS: int = 120
VIBRATION_COEFFICIENT: float = 1e-8
CRITICAL_VIBRATION_G: float = 0.5
MAX_SAFE_RPM: int = 15_000
NATURAL_FREQ_RPM: int = 7_500
RESONANCE_BANDWIDTH_RPM: int = 500
RPM_RAMP_STEP: int = 200


# ---------------------------------------------------------------------------
# Centrifuge Simulator
# ---------------------------------------------------------------------------
@dataclass
class CentrifugeSimulator:
    """Analytic physics model for a laboratory centrifuge.

    Combines a Finite State Machine with deterministic vibration
    modelling (centripetal force + Lorentzian resonance amplification).

    Attributes:
        device_id: Unique hardware identifier.
        state: Current FSM state.
        target_rpm: Operator-requested RPM.
        current_rpm: Actual RPM (ramps toward target).
        vibration_rms_g: Root-mean-square vibration in *g*.
        telemetry_log: Rolling buffer of snapshots.
        invoker: Command Pattern invoker with history.
        last_alert: Most recent sensor alert dict, or ``None``.
    """

    device_id: str = "CENT-01"
    state: MachineState = MachineState.STANDBY
    target_rpm: int = 0
    current_rpm: int = 0
    vibration_rms_g: float = 0.0
    telemetry_log: list[TelemetrySnapshot] = field(default_factory=list)
    invoker: CommandInvoker = field(default_factory=CommandInvoker)
    last_alert: dict[str, Any] | None = field(default=None, repr=False)
    vibration_history: list[float] = field(default_factory=list, repr=False)

    # -- FSM helpers --------------------------------------------------------

    def _transition(self, new_state: MachineState) -> bool:
        """Attempt a state transition; returns True on success."""
        success, resulting = attempt_transition(self.state, new_state)
        if success and self.state != resulting:
            log_event(
                event_type="STATE_TRANSITION",
                source="SIMULATOR",
                details={"old_state": self.state.value, "new_state": resulting.value}
            )
        self.state = resulting
        return success

    # -- Low-level handlers (used by Command objects) -----------------------

    def _handle_set_rpm(self, rpm: int) -> str:
        if rpm < 0 or rpm > MAX_SAFE_RPM:
            return f"❌ RPM {rpm} out of range [0, {MAX_SAFE_RPM}]."

        if self.state in (MachineState.ERROR, MachineState.EMERGENCY_STOP):
            return f"❌ Cannot set RPM while in {self.state.value}. Reset first."

        if self.state == MachineState.STANDBY and rpm > 0:
            self._transition(MachineState.SPINNING)

        self.target_rpm = rpm
        logger.info("Target RPM set to %d", rpm)
        return f"✅ Target RPM set to {rpm}."

    def _handle_stop(self) -> str:
        self.target_rpm = 0
        if self.state == MachineState.SPINNING:
            self._transition(MachineState.STANDBY)
        return "✅ Stop command received. Decelerating."

    def _handle_reset(self) -> str:
        if self.state in (MachineState.ERROR, MachineState.EMERGENCY_STOP):
            self._transition(MachineState.STANDBY)
            self.target_rpm = 0
            self.current_rpm = 0
            self.vibration_rms_g = 0.0
            return "✅ System reset to STANDBY."
        return "ℹ️ System is not in an error state."

    # -- Public command API -------------------------------------------------

    def execute_command(self, command_json: dict[str, Any]) -> str:
        """Parse and execute a JSON command via the Command Pattern.

        Expected schema::

            {"action": "set_rpm" | "stop" | "reset", "value": <int>}

        Args:
            command_json: Parsed JSON dict with ``action`` and optional ``value``.

        Returns:
            Human-readable status string.
        """
        cmd = command_from_json(command_json)
        if cmd is None:
            action = command_json.get("action", "")
            return f"⚠️ Unknown action: '{action}'"
            
        result = self.invoker.execute(cmd, self)
        log_event(
            event_type="COMMAND_EXECUTED",
            source="LLM_AGENT",
            details={"command": command_json, "result": result, "machine_state": self.state.value}
        )
        return result

    # -- Physics tick -------------------------------------------------------

    def tick(self) -> TelemetrySnapshot:
        """Advance the simulation by one time-step.

        1. Ramp ``current_rpm`` toward ``target_rpm``.
        2. Calculate vibration using the analytic unbalance model.
        3. Check safety thresholds — generate sensor alert if breached.
        4. Record and return telemetry.

        Returns:
            A fresh :class:`TelemetrySnapshot`.
        """
        # 1. RPM ramp
        if self.current_rpm < self.target_rpm:
            self.current_rpm = min(
                self.current_rpm + RPM_RAMP_STEP, self.target_rpm,
            )
        elif self.current_rpm > self.target_rpm:
            self.current_rpm = max(
                self.current_rpm - RPM_RAMP_STEP, self.target_rpm,
            )

        # Auto-transition to STANDBY when fully stopped
        if self.current_rpm == 0 and self.state == MachineState.SPINNING:
            self._transition(MachineState.STANDBY)

        # 2. Vibration model: V = k * RPM²
        base_vibration: float = VIBRATION_COEFFICIENT * (self.current_rpm ** 2)

        # Resonance amplification near natural frequency (Lorentzian)
        resonance_factor: float = 1.0
        delta_rpm = abs(self.current_rpm - NATURAL_FREQ_RPM)
        if delta_rpm < RESONANCE_BANDWIDTH_RPM and self.current_rpm > 0:
            resonance_factor = 1.0 + 2.0 * (
                1.0 - delta_rpm / RESONANCE_BANDWIDTH_RPM
            )

        # Stochastic noise (bearing micro-vibrations)
        noise: float = (
            np.random.normal(0, 0.005) if self.current_rpm > 0 else 0.0
        )
        self.vibration_rms_g = max(
            0.0, base_vibration * resonance_factor + noise,
        )

        # 3. Z-Score Anomaly Detection
        self.vibration_history.append(self.vibration_rms_g)
        if len(self.vibration_history) > 20:
            self.vibration_history.pop(0)
            
        z_score = 0.0
        is_anomaly = False
        if len(self.vibration_history) >= 10:
            hist = np.array(self.vibration_history[:-1])  # Exclude current point
            mean_vib = np.mean(hist)
            std_vib = np.std(hist)
            if std_vib > 0.001:
                z_score = (self.vibration_rms_g - mean_vib) / std_vib
                if z_score > 3.0 and self.current_rpm > 1000:
                    is_anomaly = True

        # 4. Safety check — generate sensor alert on breach or anomaly
        self.last_alert = None
        if (self.vibration_rms_g > CRITICAL_VIBRATION_G or is_anomaly) and self.state == MachineState.SPINNING:
            alert_reason = "CRITICAL_VIBRATION" if self.vibration_rms_g > CRITICAL_VIBRATION_G else "STATISTICAL_ANOMALY"
            logger.error(
                "ALARM (%s): %.3f g at %d RPM (Z: %.2f)",
                alert_reason,
                self.vibration_rms_g,
                self.current_rpm,
                z_score
            )
            self.last_alert = build_sensor_alert(
                device_id=self.device_id,
                requested_rpm=self.target_rpm,
                actual_rpm=self.current_rpm,
                vibration_rms_g=self.vibration_rms_g,
                threshold_g=CRITICAL_VIBRATION_G,
            )
            self.last_alert["error_analysis"]["code"] = "E_VIB_ANOMALY" if is_anomaly else "E_VIB_LIMIT"
            
            # Log & Publish alert
            log_event("SENSOR_ALARM", "SIMULATOR", self.last_alert, level="ERROR")
            mqtt_edge.publish_alert(self.last_alert)
            
            if self.vibration_rms_g > CRITICAL_VIBRATION_G:
                self._transition(MachineState.EMERGENCY_STOP)
                self.target_rpm = 0

        # 5. Record snapshot & Publish Telemetry
        snapshot = TelemetrySnapshot(
            timestamp=time.time(),
            rpm=self.current_rpm,
            vibration_rms_g=round(self.vibration_rms_g, 4),
            state=self.state,
            z_score=round(z_score, 2),
            anomaly=is_anomaly
        )
        self.telemetry_log.append(snapshot)
        if len(self.telemetry_log) > MAX_TELEMETRY_POINTS:
            self.telemetry_log = self.telemetry_log[-MAX_TELEMETRY_POINTS:]
            
        mqtt_edge.publish_telemetry({
            "device_id": self.device_id,
            "timestamp": snapshot.timestamp,
            "rpm": snapshot.rpm,
            "vibration_g": snapshot.vibration_rms_g,
            "state": snapshot.state.value,
            "z_score": snapshot.z_score,
            "anomaly": snapshot.anomaly
        })

        return snapshot
