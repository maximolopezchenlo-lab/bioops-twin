"""Gradio Blocks dashboard assembly for the BioOps Twin.

Builds the full industrial-themed UI: operator chat (left panel) and
telemetry dashboard (right panel) with Shadow Mode toggle, Health
Score, Audit Logs, and MQTT connectivity status.

Architecture reference:
    Technical Architecture § "Gradio Blocks dashboard"
"""

from __future__ import annotations

import logging

import gradio as gr

from bioops.llm_engine.client import BioOpsAgent
from bioops.simulation_core.simulator import CentrifugeSimulator
from bioops.simulation_ui import callbacks
from bioops.simulation_ui.constants import TIMER_INTERVAL_SEC

logger = logging.getLogger("bioops_twin.dashboard")


# ---------------------------------------------------------------------------
# Custom CSS — Industrial Dark Theme (Refined)
# ---------------------------------------------------------------------------
INDUSTRIAL_CSS = """\
/* === BioOps Twin Industrial Theme === */
:root {
    --bioops-bg:        #0d1117;
    --bioops-surface:   #161b22;
    --bioops-border:    #30363d;
    --bioops-accent:    #58a6ff;
    --bioops-success:   #3fb950;
    --bioops-warning:   #d29922;
    --bioops-danger:    #f85149;
    --bioops-text:      #e6edf3;
    --bioops-muted:     #8b949e;
}

.gradio-container {
    background: var(--bioops-bg) !important;
    max-width: 100% !important;
}

/* Header */
#bioops-header {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid var(--bioops-border);
    border-radius: 12px;
    padding: 12px 24px;
    margin-bottom: 8px;
}

#bioops-header h1 {
    background: linear-gradient(90deg, #58a6ff, #3fb950);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.4rem;
    margin: 0;
}

#bioops-header p {
    color: var(--bioops-muted);
    margin: 2px 0 0 0;
    font-size: 0.78rem;
}

/* Panel styling */
.panel-card {
    background: var(--bioops-surface) !important;
    border: 1px solid var(--bioops-border) !important;
    border-radius: 10px !important;
}

/* Chatbot — force comfortable height */
#operator-chatbot {
    min-height: 320px !important;
    max-height: 380px !important;
}

/* State display card */
#state-display {
    background: var(--bioops-surface);
    border: 1px solid var(--bioops-border);
    border-radius: 10px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.82rem;
    line-height: 1.5;
}

/* Telemetry section title */
.telemetry-title {
    color: var(--bioops-accent) !important;
    border-bottom: 1px solid var(--bioops-border);
    padding-bottom: 4px;
    font-size: 0.9rem;
}

/* Shadow Mode status — compact inline badge */
#shadow-status-badge {
    font-size: 0.82rem;
    padding: 4px 0;
}

/* Audit trail table — make it readable */
#audit-table table {
    font-size: 0.78rem !important;
}
#audit-table th {
    background: #21262d !important;
    color: var(--bioops-accent) !important;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.5px;
}
#audit-table td {
    padding: 4px 8px !important;
    vertical-align: top;
    word-break: break-word;
}

/* Reduce excessive spacing in Gradio blocks */
.gradio-container .gap {
    gap: 6px !important;
}

footer { display: none !important; }
"""


# ---------------------------------------------------------------------------
# Theme — Industrial Dark
# ---------------------------------------------------------------------------
INDUSTRIAL_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.green,
    neutral_hue=gr.themes.colors.gray,
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#0d1117",
    body_background_fill_dark="#0d1117",
    block_background_fill="#161b22",
    block_background_fill_dark="#161b22",
    block_border_color="#30363d",
    block_border_color_dark="#30363d",
    block_label_text_color="#e6edf3",
    block_label_text_color_dark="#e6edf3",
    block_title_text_color="#e6edf3",
    block_title_text_color_dark="#e6edf3",
    body_text_color="#e6edf3",
    body_text_color_dark="#e6edf3",
    body_text_color_subdued="#8b949e",
    body_text_color_subdued_dark="#8b949e",
    input_background_fill="#0d1117",
    input_background_fill_dark="#0d1117",
    input_border_color="#30363d",
    input_border_color_dark="#30363d",
    button_primary_background_fill="#238636",
    button_primary_background_fill_dark="#238636",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
)


# ---------------------------------------------------------------------------
# 3D Model helper
# ---------------------------------------------------------------------------

def _resolve_model_path() -> str | None:
    """Locate the centrifuge GLB model file.

    Searches for ``assets/centrifuge_rotor.glb`` relative to the
    project root.  Returns ``None`` if not found so the UI
    gracefully shows an empty viewer.
    """
    from pathlib import Path

    candidates = [
        Path(__file__).resolve().parents[2] / "assets" / "centrifuge_rotor.glb",
        Path("assets/centrifuge_rotor.glb"),
    ]
    for p in candidates:
        if p.exists():
            logger.info("3D model found: %s", p)
            return str(p)
    logger.warning("3D model not found — viewer will be empty")
    return None


# ---------------------------------------------------------------------------
# Dashboard Builder
# ---------------------------------------------------------------------------

def build_dashboard() -> gr.Blocks:
    """Construct the BioOps Twin Gradio Blocks dashboard.

    Initialises the simulator and agent, binds callbacks, and wires
    all UI events.

    Returns:
        A fully wired :class:`gr.Blocks` application.
    """
    # -- Initialise core objects -------------------------------------------
    simulator = CentrifugeSimulator()
    agent = BioOpsAgent(simulator=simulator)
    callbacks.bind(simulator, agent)

    mode_label = "LIVE (Gemini)" if agent.is_live else "MOCK (Local)"
    logger.info("Dashboard built — Agent mode: %s", mode_label)

    # -- Build UI ----------------------------------------------------------
    with gr.Blocks(
        title="BioOps Twin — Digital Centrifuge",
        theme=INDUSTRIAL_THEME,
        css=INDUSTRIAL_CSS,
    ) as demo:

        # -- Header ---------------------------------------------------------
        gr.HTML(
            f"""
            <div id="bioops-header">
                <h1>⚙️ BioOps Twin — Digital Centrifuge Dashboard</h1>
                <p>AI-Powered Calibration System · Enterprise Grade · Agent: {mode_label} · MQTT Edge · Shadow Mode</p>
            </div>
            """,
        )

        # -- Timer (invisible, drives telemetry refresh) --------------------
        telemetry_timer = gr.Timer(value=TIMER_INTERVAL_SEC)

        # -- Main layout ----------------------------------------------------
        with gr.Row(equal_height=False):

            # ============== LEFT PANEL: Operator Chat (40%) ================
            with gr.Column(scale=2, min_width=360):
                gr.Markdown(
                    "### 🧑‍🔬 Operator Console",
                    elem_classes=["telemetry-title"],
                )

                chatbot = gr.Chatbot(
                    value=[],
                    label="BioOps Assistant",
                    elem_id="operator-chatbot",
                    type="messages",
                    height=340,
                    placeholder=(
                        "Talk to BioOps — try:\n"
                        '"Set the centrifuge to 5000 RPM"\n'
                        '"Stop" · "Reset"'
                    ),
                )
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="Ask BioOps to calibrate, stop, or reset...",
                        label="Command Input",
                        scale=4,
                        lines=1,
                    )
                    send_btn = gr.Button("Send ▶", variant="primary", scale=1)

                # Quick-action buttons
                with gr.Row():
                    gr.Button("▶ Start 3000 RPM", size="sm").click(
                        fn=lambda h: callbacks.chat_respond(
                            "Set RPM to 3000", h,
                        ),
                        inputs=[chatbot],
                        outputs=[chatbot, user_input],
                    )
                    gr.Button("⏹ Stop", size="sm").click(
                        fn=lambda h: callbacks.chat_respond("Stop", h),
                        inputs=[chatbot],
                        outputs=[chatbot, user_input],
                    )
                    gr.Button("🔄 Reset", size="sm").click(
                        fn=lambda h: callbacks.chat_respond("Reset", h),
                        inputs=[chatbot],
                        outputs=[chatbot, user_input],
                    )

                # Shadow Mode Control — compact row below actions
                with gr.Row():
                    shadow_toggle = gr.Checkbox(
                        label="🛡️ Shadow Mode (Human-in-the-Loop)",
                        value=False,
                        scale=3,
                    )
                shadow_status = gr.Markdown(
                    value="⚡ **AUTO-RUN** — Commands execute immediately",
                    elem_id="shadow-status-badge",
                )

            # ============== RIGHT PANEL: Telemetry (60%) ===================
            with gr.Column(scale=3, min_width=480):
                gr.Markdown(
                    "### 📊 Telemetry Dashboard",
                    elem_classes=["telemetry-title"],
                )

                # -- Machine State Card ------------------------------------
                state_display = gr.Markdown(
                    value=callbacks.get_state_display,
                    every=telemetry_timer,
                    elem_id="state-display",
                )

                # -- Plots in a compact vertical stack ----------------------
                vibration_plot = gr.LinePlot(
                    value=callbacks.get_telemetry_dataframe,
                    every=telemetry_timer,
                    x="time_s",
                    y="Vibration (g)",
                    title="Vibration Intensity (Real-Time)",
                    y_title="Vibration (g)",
                    x_title="Elapsed Time (s)",
                    height=180,
                    y_lim=[0, None],
                )

                with gr.Row():
                    rpm_plot = gr.LinePlot(
                        value=callbacks.get_telemetry_dataframe,
                        every=telemetry_timer,
                        x="time_s",
                        y="RPM",
                        title="Rotor Speed (RPM)",
                        y_title="RPM",
                        x_title="Elapsed Time (s)",
                        height=150,
                        y_lim=[0, None],
                    )
                    zscore_plot = gr.LinePlot(
                        value=callbacks.get_telemetry_dataframe,
                        every=telemetry_timer,
                        x="time_s",
                        y="Z-Score",
                        title="Anomaly Detection (Z-Score)",
                        y_title="Z-Score",
                        x_title="Elapsed Time (s)",
                        height=150,
                    )

                # -- Tabs: 3D Model + Audit Logs ----------------------------
                with gr.Tabs():
                    with gr.TabItem("🔩 3D Model"):
                        model_3d = gr.Model3D(
                            value=_resolve_model_path(),
                            label="Centrifuge Rotor Assembly",
                            clear_color=(0.05, 0.07, 0.1, 1.0),
                            height=260,
                        )

                    with gr.TabItem("📋 Audit Trail"):
                        gr.Markdown(
                            "**Immutable JSONL Audit Log** — All agent decisions, "
                            "operator commands, and state transitions are recorded."
                        )
                        audit_table = gr.Dataframe(
                            value=callbacks.get_audit_log_dataframe,
                            every=telemetry_timer,
                            label="Audit Log (Latest 30 Records)",
                            elem_id="audit-table",
                            wrap=True,
                        )

        # -- Wire events ----------------------------------------------------
        send_btn.click(
            fn=callbacks.chat_respond,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input],
        )
        user_input.submit(
            fn=callbacks.chat_respond,
            inputs=[user_input, chatbot],
            outputs=[chatbot, user_input],
        )
        shadow_toggle.change(
            fn=callbacks.toggle_shadow_mode,
            inputs=[shadow_toggle],
            outputs=[shadow_status],
        )

    return demo
