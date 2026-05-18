"""BioOps Twin — LLM Engine sub-package.

Provides the Gemini 3.1 Pro integration with automatic function calling
for deterministic centrifuge command generation.
"""

from bioops.llm_engine.client import BioOpsAgent

__all__ = ["BioOpsAgent"]
