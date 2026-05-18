"""Immutable Audit Logger for BioOps Twin.

Provides JSONL-based audit logging for compliance tracking, recording
every significant state change, LLM decision, and operator action.

Architecture reference:
    Implementation Plan § "Audit Logging Inmutable (Trazabilidad)"
"""

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger("bioops_twin.audit")

AUDIT_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "audit.jsonl"
)


def log_event(
    event_type: str,
    source: str,
    details: dict[str, Any],
    level: str = "INFO"
) -> None:
    """Record an immutable audit event to the JSONL log file.
    
    Args:
        event_type: e.g., 'COMMAND_EXECUTED', 'SHADOW_MODE_SUGGESTION', 'EMERGENCY_STOP'
        source: 'LLM_AGENT', 'OPERATOR', 'SIMULATOR', 'SYSTEM'
        details: Arbitrary dictionary containing the state and context.
        level: Severity level.
    """
    record = {
        "timestamp": time.time(),
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "event_type": event_type,
        "source": source,
        "details": details
    }
    
    try:
        with open(AUDIT_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:
        logger.error(f"Failed to write to audit log: {exc}")

def read_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Read the most recent audit logs.
    
    Args:
        limit: Max number of logs to return (reading from the end).
        
    Returns:
        List of parsed JSON records, newest first.
    """
    if not os.path.exists(AUDIT_FILE_PATH):
        return []
        
    try:
        with open(AUDIT_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        records = []
        for line in reversed(lines[-limit:]):
            if line.strip():
                records.append(json.loads(line))
        return records
    except Exception as exc:
        logger.error(f"Failed to read audit logs: {exc}")
        return []
