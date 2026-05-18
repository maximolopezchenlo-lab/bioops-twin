"""BioOps Agent — Gemini 3.1 Pro integration with mock fallback.

Provides ``BioOpsAgent``, the central cognitive engine that wraps the
``google-genai`` SDK.  When ``GEMINI_API_KEY`` is not set the agent
operates in **mock mode**, parsing JSON commands locally so the
dashboard remains fully functional without API costs.

Architecture reference:
    Technical Integration § "Function Calling with Unique Session Identifiers"
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from bioops.llm_engine.prompts import SYSTEM_PROMPT, build_context_prompt
from bioops.llm_engine.tools import ALL_TOOLS, bind_simulator
from bioops.rag_memory.retriever import retrieve_context
from bioops.simulation_core.simulator import CentrifugeSimulator
from bioops.security.sanitizer import get_lobster_trap_http_options
from bioops.security.audit_logger import log_event

logger = logging.getLogger("bioops_twin.agent")

# Conditional import — gracefully degrade if google-genai is missing
try:
    from google import genai
    from google.genai import types

    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    logger.warning(
        "google-genai SDK not installed. LLM features disabled (mock mode)."
    )


@dataclass
class BioOpsAgent:
    """Central cognitive engine for the BioOps Twin.

    Wraps Gemini 3.1 Pro with automatic function calling.  Falls back
    to a local mock that parses JSON commands when the API key is
    absent or the SDK is not installed.

    Attributes:
        simulator: The centrifuge simulator instance.
        model_id: Gemini model identifier.
        is_live: Whether the agent is connected to the real API.
        chat_session: Persistent Gemini chat session (keeps thought
            signatures across turns — Rule from architecture doc).
    """

    simulator: CentrifugeSimulator
    model_id: str = "gemini-3.1-pro-preview"
    shadow_mode: bool = False
    pending_command: dict[str, Any] | None = field(init=False, default=None, repr=False)
    is_live: bool = field(init=False, default=False)
    _client: Any = field(init=False, default=None, repr=False)
    _chat: Any = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialise the Gemini client or activate mock mode."""
        bind_simulator(self.simulator)

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if _GENAI_AVAILABLE and api_key:
            self._client = genai.Client(
                api_key=api_key,
                http_options=get_lobster_trap_http_options()
            )
            self._init_chat_session()
            self.is_live = True
            logger.info(
                "BioOpsAgent LIVE mode: model=%s", self.model_id,
            )
        else:
            reason = (
                "API key missing" if _GENAI_AVAILABLE
                else "google-genai not installed"
            )
            logger.info("BioOpsAgent MOCK mode (%s)", reason)

    def _init_chat_session(self) -> None:
        """Create a persistent chat session with tool config."""
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            temperature=0.1,
        )
        self._chat = self._client.chats.create(
            model=self.model_id,
            config=config,
        )

    # -- Public API ---------------------------------------------------------

    def process_message(self, user_message: str) -> str:
        """Process an operator message and return the agent's response.

        In live mode the message is sent to Gemini which may invoke
        tool functions automatically.  In mock mode JSON commands
        are parsed locally.

        Args:
            user_message: Raw text from the operator.

        Returns:
            The agent's response string.
        """
        log_event("USER_INPUT", "OPERATOR", {"message": user_message})

        # Check for Shadow Mode confirmation
        if self.shadow_mode and self.pending_command:
            lower_msg = user_message.lower().strip()
            if lower_msg in ["confirm", "approve", "yes", "sí", "confirmar"]:
                cmd = self.pending_command
                self.pending_command = None
                log_event("SHADOW_MODE_APPROVED", "OPERATOR", {"command": cmd})
                result = self.simulator.execute_command(cmd)
                return f"✅ **Command Approved & Executed**\n\nResult: {result}"
            elif lower_msg in ["cancel", "reject", "no", "cancelar"]:
                self.pending_command = None
                log_event("SHADOW_MODE_REJECTED", "OPERATOR", {"command": self.pending_command})
                return "❌ **Command Canceled**"

        if self.is_live:
            response = self._process_live(user_message)
        else:
            response = self._process_mock(user_message)
            
        log_event("AGENT_RESPONSE", "LLM_AGENT", {"response": response, "mode": "LIVE" if self.is_live else "MOCK"})
        return response

    # -- Live Gemini processing ---------------------------------------------

    def _process_live(self, user_message: str) -> str:
        """Send the message to Gemini with dynamic telemetry context.

        The SDK's automatic function calling handles tool execution
        and response cycles transparently.

        Args:
            user_message: Operator message.

        Returns:
            Gemini's final text response.
        """
        # Inject live telemetry as context
        context = build_context_prompt(
            state=self.simulator.state,
            current_rpm=self.simulator.current_rpm,
            target_rpm=self.simulator.target_rpm,
            vibration_g=self.simulator.vibration_rms_g,
        )
        enriched = f"{context}\n\nOperator: {user_message}"

        try:
            response = self._chat.send_message(enriched)
            return response.text or "⚙️ Command executed (no text response)."
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            
            # Handle Lobster Trap proxy blocks (Rule 11)
            exc_str = str(exc)
            if "403" in exc_str or "Lobster Trap" in exc_str or "401" in exc_str:
                return (
                    "🛑 **[VEEA LOBSTER TRAP - SECURITY BLOCK]**\n\n"
                    "The prompt or command has been intercepted and blocked by the "
                    "reverse proxy due to security policy violations (e.g., PII/PHI leak, "
                    "prompt injection, or credential exfiltration attempt)."
                )

            # Graceful fallback to mock on transient errors
            return self._process_mock(user_message)

    # -- Mock processing ----------------------------------------------------

    def _process_mock(self, user_message: str) -> str:
        """Local mock agent that parses JSON or provides help.

        Args:
            user_message: Operator message.

        Returns:
            A formatted response string.
        """
        # Helper to execute or shadow a command
        def _execute_or_shadow(command: dict[str, Any]) -> str:
            if self.shadow_mode:
                self.pending_command = command
                log_event("SHADOW_MODE_SUGGESTION", "LLM_AGENT", {"command": command})
                return (
                    f"⚠️ **[SHADOW MODE] Pending Execution** ⚠️\n\n"
                    f"The system suggests executing: `{command}`\n\n"
                    f"Please reply with **'Confirm'** to execute or **'Cancel'** to abort."
                )
            return self.simulator.execute_command(command)

        # Try to parse as JSON command
        try:
            command = json.loads(user_message)
            if isinstance(command, dict) and "action" in command:
                return _execute_or_shadow(command)
        except (json.JSONDecodeError, ValueError):
            pass

        # Natural language parsing (simple keyword matching)
        lower = user_message.lower()

        if any(w in lower for w in ("stop", "halt", "pare", "detener")):
            return _execute_or_shadow({"action": "stop"})

        if any(w in lower for w in ("reset", "reiniciar", "restart")):
            return _execute_or_shadow({"action": "reset"})

        # Try to extract RPM from natural text
        rpm = self._extract_rpm(lower)
        if rpm is not None:
            return _execute_or_shadow({"action": "set_rpm", "value": rpm})

        # RAG-powered response for general questions
        return self._answer_with_rag(user_message)

    def _answer_with_rag(self, user_message: str) -> str:
        """Answer operator questions using the RAG knowledge base.

        Retrieves relevant calibration protocol chunks from ChromaDB
        and formats a structured response.  Falls back to a concise
        help message when no relevant context is found.

        Args:
            user_message: Operator question.

        Returns:
            A formatted response with retrieved knowledge.
        """
        try:
            chunks = retrieve_context(
                query=user_message, equipment_id="CENT-01", top_k=3,
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            chunks = []

        mode = "🟢 LIVE" if self.is_live else "🟡 MOCK"

        if chunks:
            context_block = "\n\n---\n\n".join(
                f"📄 **Source {i+1}:** {chunk[:500]}" for i, chunk in enumerate(chunks)
            )
            return (
                f"🤖 **[BioOps Agent — {mode}]**\n\n"
                f"Based on calibration protocols for CENT-01:\n\n"
                f"{context_block}\n\n"
                f"---\n"
                f"💡 *You can also control the centrifuge with commands like "
                f"\"Set RPM to 3000\" or \"Stop\".*"
            )

        # Fallback: built-in knowledge for common questions
        snap = (
            f"RPM={self.simulator.current_rpm}, "
            f"Vibration={self.simulator.vibration_rms_g:.4f}g, "
            f"State={self.simulator.state.value}"
        )
        return (
            f"🤖 **[BioOps Agent — {mode}]**\n\n"
            f"**Current Telemetry:** {snap}\n\n"
            f"I can help you with centrifuge calibration. "
            f"Here are some things you can ask me:\n\n"
            f"- *\"What is the maximum RPM for a 50g load?\"*\n"
            f"- *\"Set RPM to 3000\"*\n"
            f"- *\"What are the vibration thresholds?\"*\n"
            f"- *\"Stop\"* / *\"Reset\"*\n\n"
            f"📋 **Safety Limits:** Max RPM = 15,000 · "
            f"Critical vibration = 0.5g RMS · "
            f"Resonance zone = 7,000–8,000 RPM"
        )

    @staticmethod
    def _extract_rpm(text: str) -> int | None:
        """Extract an RPM value from natural language text.

        Looks for patterns like "set rpm to 3000", "3000 rpm",
        "a 5000 rpm", "to 8000".

        Args:
            text: Lowercased user message.

        Returns:
            Extracted RPM as int, or ``None`` if not found.
        """
        import re

        # Match patterns like "3000 rpm", "rpm 3000", "to 3000", "a 5000"
        patterns = [
            r"(\d{3,5})\s*rpm",
            r"rpm\s*(?:to|a|=)?\s*(\d{3,5})",
            r"(?:set|pon|to|a)\s+(\d{3,5})",
            r"speed\s*(?:to|=)?\s*(\d{3,5})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None

    # -- Sensor alert injection ---------------------------------------------

    def format_sensor_alert(self, alert: dict[str, Any]) -> str:
        """Format a sensor alert for chat display.

        Args:
            alert: The structured sensor alert dict.

        Returns:
            A Markdown-formatted alert string.
        """
        snap = alert.get("telemetry_snapshot", {})
        err = alert.get("error_analysis", {})
        return (
            f"🚨 **SENSOR ALARM — {alert.get('severity', 'UNKNOWN')}**\n\n"
            f"**Device:** {alert.get('device_id', '?')}\n"
            f"**RPM:** {snap.get('actual_rpm', '?')} "
            f"(requested: {snap.get('requested_rpm', '?')})\n"
            f"**Vibration:** {snap.get('vibration_rms_g', '?')} g "
            f"(peak: {snap.get('vibration_peak_g', '?')} g)\n"
            f"**Resonance:** {snap.get('resonance_probability', '?')}\n\n"
            f"**Error:** `{err.get('code', '?')}` — {err.get('message', '')}\n"
            f"**Suggestion:** {err.get('suggestion', '')}"
        )
