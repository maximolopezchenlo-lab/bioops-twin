"""Veea Lobster Trap integration for BioOps Twin.

This module provides the HTTP configuration to route Gemini API traffic
through the Veea Lobster Trap reverse proxy. The proxy performs deep
prompt inspection (DPI) to block PII/PHI leaks and prompt injections.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("bioops_twin.security")


def get_lobster_trap_http_options() -> dict[str, Any]:
    """Get the http_options configuration for the Gemini SDK.

    Routes traffic through the Veea proxy and injects bidirectional
    metadata headers (Rule 9).

    Returns:
        Dictionary of HTTP options for ``google.genai.Client``.
    """
    proxy_url = os.environ.get("VEEA_PROXY_URL", "http://localhost:8080")
    logger.info("Configuring Lobster Trap proxy at: %s", proxy_url)
    
    return {
        "baseUrl": proxy_url,
        "headers": {
            "_lobstertrap-intent": "calibration_agent",
            "_lobstertrap-client": "bioops_twin"
        }
    }


def sanitize_input(text: str) -> str:
    """Sanitise operator input before forwarding to the LLM.

    With Lobster Trap deployed as a transparent reverse proxy,
    this function is no longer required for content filtering.
    It remains as a pass-through for API compatibility.

    Args:
        text: Raw operator input.

    Returns:
        The unmodified text.
    """
    return text


def sanitize_output(text: str) -> str:
    """Sanitise LLM output before displaying to the operator.

    Egress traffic is inspected by Lobster Trap transparently.
    This remains as a pass-through.

    Args:
        text: Raw LLM response.

    Returns:
        The unmodified text.
    """
    return text
