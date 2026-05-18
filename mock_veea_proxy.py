"""Veea Lobster Trap — Mock Reverse Proxy Server.

Simulates the Veea Lobster Trap security proxy for development and demo
purposes.  All traffic destined for the Google Gemini API is intercepted,
logged with security-inspection messages, and forwarded transparently.

In production, this would be replaced by the real Veea DevKit appliance
performing deep prompt inspection (DPI) for PII/PHI sanitisation and
adversarial prompt detection.

Usage::

    python mock_veea_proxy.py

Environment variables:
    GEMINI_API_KEY  — Forwarded to Google's API as ``x-goog-api-key``.
"""

from __future__ import annotations

import logging
import os

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = FastAPI(title="Veea Lobster Trap Mock Proxy")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [VEEA LOBSTER TRAP] | %(message)s",
)
logger = logging.getLogger("veea_proxy")

TARGET_API: str = "https://generativelanguage.googleapis.com"
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# Middleware — Transparent proxy with security logging
# ---------------------------------------------------------------------------

@app.middleware("http")
async def proxy_requests(request: Request, call_next) -> Response:  # noqa: ARG001
    """Intercept, inspect, and forward all LLM traffic.

    Performs three simulated security checks before forwarding:
    1. PII/PHI leak detection (Zero-Trust sanitisation)
    2. Anti-prompt-injection heuristic scan
    3. Credential exfiltration prevention

    Args:
        request: The incoming HTTP request from the Gemini SDK.
        call_next: FastAPI's next middleware (unused — we forward ourselves).

    Returns:
        The proxied response from Google's Gemini API.
    """
    logger.info("Intercepting LLM traffic: %s %s", request.method, request.url.path)
    logger.info("PII/PHI Sanitisation (Zero-Trust) ... PASS")
    logger.info("Anti-Prompt-Injection Scan .......... PASS")
    logger.info("Credential Exfiltration Check ....... PASS")

    # Build target URL
    target_url = f"{TARGET_API}{request.url.path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Read original request body
    body: bytes = await request.body()

    # Prepare headers — inject API key if not already present
    headers = dict(request.headers)
    headers.pop("host", None)
    if GEMINI_API_KEY and "x-goog-api-key" not in headers:
        headers["x-goog-api-key"] = GEMINI_API_KEY

    # Forward request to Google
    async with httpx.AsyncClient() as client:
        try:
            proxy_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=60.0,
            )
            logger.info(
                "Traffic forwarded to Google Gemini and returned securely (status=%d).",
                proxy_response.status_code,
            )
            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=dict(proxy_response.headers),
            )
        except httpx.RequestError as exc:
            logger.error("Connection error to Gemini API: %s", exc)
            return Response(
                content="Internal proxy error — upstream unreachable.",
                status_code=502,
            )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not found in environment. Proxy will forward without authentication.")
    logger.info("Veea Lobster Trap Mock Proxy starting on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
