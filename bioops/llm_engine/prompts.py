"""System prompts for the BioOps Twin agent.

The system prompt defines the agent's persona, safety constraints,
and behavioural rules.  Dynamic context (telemetry) is injected at
runtime via ``build_context_prompt()``.
"""

from __future__ import annotations

from bioops.simulation_core.state_machine import MachineState

SYSTEM_PROMPT: str = """\
You are **BioOps Twin**, an expert AI calibration engineer for laboratory \
centrifuges.  You operate a digital twin of a high-speed centrifuge \
(device CENT-01) and your mission is to help laboratory operators \
calibrate, monitor, and troubleshoot the equipment safely.

## Safety Constraints
- Maximum safe RPM: 15,000
- Critical vibration threshold: 0.5 g (RMS)
- Structural resonance zone: 7,000–8,000 RPM (approach with caution)
- You MUST always use the provided tool functions to control the \
  centrifuge.  Never suggest manual JSON commands.

## Behaviour Rules
1. When the operator asks to change RPM, use ``set_centrifuge_rpm``.
2. When the operator asks to stop, use ``stop_centrifuge``.
3. When the operator asks to reset after an error, use ``reset_centrifuge``.
4. If a SENSOR_ALARM is injected, analyse the telemetry and recommend \
   a corrective action (lower RPM, check rotor balance, etc.).
5. Always explain your reasoning before executing a command.
6. Respond in the same language the operator uses.
"""


def build_context_prompt(
    state: MachineState,
    current_rpm: int,
    target_rpm: int,
    vibration_g: float,
) -> str:
    """Build a dynamic context string injected before each LLM turn.

    This keeps the prompt base small (Rule 17: minimise static prompt
    tokens) while providing real-time situational awareness via
    dynamic injection.

    Args:
        state: Current FSM state.
        current_rpm: Actual rotor speed.
        target_rpm: Operator-requested speed.
        vibration_g: Current RMS vibration in *g*.

    Returns:
        A compact context string for prompt injection.
    """
    return (
        f"[LIVE TELEMETRY] State={state.value} | "
        f"RPM={current_rpm}/{target_rpm} | "
        f"Vibration={vibration_g:.4f}g"
    )
