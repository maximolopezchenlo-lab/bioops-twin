"""BioOps Twin — Application Entry Point.

Launches the Gradio industrial dashboard for the laboratory
centrifuge digital twin.

Usage::

    python main.py

Environment variables:
    GEMINI_API_KEY  — Google Gemini API key.  When set the agent
                      operates in **LIVE** mode (Gemini 3.1 Pro with
                      automatic function calling).  When absent,
                      the agent falls back to local **MOCK** mode.
"""

from __future__ import annotations

import logging

# ---------------------------------------------------------------------------
# Logging — must be configured before any bioops import
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("bioops_twin")


def main() -> None:
    """Build and launch the BioOps Twin dashboard."""
    from bioops.simulation_ui.dashboard import build_dashboard

    logger.info("Launching BioOps Twin dashboard...")
    app = build_dashboard()
    app.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        theme=getattr(app, "_bioops_theme", None),
        css=getattr(app, "_bioops_css", None),
    )


if __name__ == "__main__":
    main()
