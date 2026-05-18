---
title: BioOps Twin
emoji: ⚙️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "5.33.0"
app_file: app.py
pinned: true
license: mit
short_description: AI Digital Twin for Lab Centrifuge Calibration
---

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Gemini_3.1_Pro-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/Gradio-FF9800?style=for-the-badge&logo=gradio&logoColor=white" alt="Gradio"/>
  <img src="https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=eclipsemosquitto&logoColor=white" alt="MQTT"/>
  <img src="https://img.shields.io/badge/ChromaDB-00897B?style=for-the-badge" alt="ChromaDB"/>
</p>

# ⚙️ BioOps Twin — AI-Powered Digital Twin for Laboratory Centrifuge Calibration

> **Enterprise-grade** digital twin that uses **Gemini 3.1 Pro** to autonomously calibrate laboratory centrifuge hardware through natural language, real-time telemetry, and physics-based simulation — with full audit traceability and human-in-the-loop governance.

---

## 🎯 Problem Statement

Biochemical laboratories rely on centrifuges calibrated manually, a process that is:
- **Error-prone** — human operators misconfigure RPM/RCF parameters for sample weights
- **Undocumented** — calibration decisions lack audit trails for regulatory compliance (FDA 21 CFR Part 11, EU GMP Annex 11)
- **Reactive** — failures are detected *after* sample damage, not prevented proactively

**BioOps Twin** solves this by creating an AI copilot that reads calibration manuals, simulates centrifuge physics, and recommends safe parameters — all through a conversational interface.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Operator (Gradio Dashboard)             │
│  Chat Console │ Telemetry Plots │ 3D Model │ Audit Log  │
└──────┬────────────────┬─────────────────┬───────────────┘
       │                │                 │
       ▼                ▼                 ▼
┌─────────────┐ ┌──────────────┐ ┌────────────────┐
│ LLM Engine  │ │  Simulation  │ │ Industrial Edge│
│ Gemini 3.1  │ │   Core       │ │ MQTT Telemetry │
│ Pro + Tools │ │ Physics+FSM  │ │ Z-Score Anomaly│
└──────┬──────┘ └──────┬───────┘ └────────┬───────┘
       │                │                  │
       ▼                ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌────────────────┐
│ RAG Memory  │ │  Security    │ │  Audit Logger  │
│ ChromaDB    │ │  Sanitizer   │ │  JSONL Immut.  │
│ Hybrid BM25 │ │  Zero-PHI    │ │  FDA-ready     │
└─────────────┘ └──────────────┘ └────────────────┘
```

### Modules

| Module | Purpose |
|--------|---------|
| `simulation_core/` | Centrifuge physics engine (RPM → vibration → RCF), finite state machine, command pattern |
| `llm_engine/` | Gemini 3.1 Pro agent with structured function calling, Shadow Mode (HITL) |
| `rag_memory/` | Hybrid search (dense + BM25) with parent-child chunking on calibration manuals |
| `industrial_edge/` | MQTT telemetry publisher + statistical anomaly detection (Z-Score) |
| `security/` | Input sanitization (Zero-PHI), immutable JSONL audit logging |
| `simulation_ui/` | Gradio Blocks industrial dashboard with real-time plots and 3D viewer |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- (Optional) `GEMINI_API_KEY` for live AI mode — runs in MOCK mode without it

### Installation

```bash
git clone https://github.com/maximolopezchenlo-lab/bioops-twin.git
cd bioops-twin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

Open **http://localhost:7860** in your browser.

### Try These Commands
- `"Set the centrifuge to 3000 RPM"`
- `"What is the maximum RPM for a 50g load?"`
- `"Stop"` / `"Reset"`

---

## 🛡️ Enterprise Features

### Shadow Mode (Human-in-the-Loop)
When enabled, all AI-generated commands are intercepted and require explicit operator approval before execution — critical for regulatory compliance.

### Immutable Audit Trail
Every agent decision, operator command, and state transition is logged to an append-only JSONL file with ISO 8601 timestamps, source attribution, and severity levels.

### MQTT Edge Connectivity
Real-time telemetry is published to a configurable MQTT broker (`broker.hivemq.com` for demo), enabling integration with industrial SCADA/HMI systems and external monitoring tools like MQTT Explorer.

### Statistical Anomaly Detection
A rolling Z-Score algorithm (window = 20 ticks) continuously monitors vibration data. When Z > 3σ, the system triggers visual alerts and injects a `SYSTEM_ALERT` into the LLM context to force recalibration.

---

## 📁 Project Structure

```
bioops-twin/
├── main.py                    # Application entry point
├── app.py                     # Hugging Face Spaces entry point
├── requirements.txt
├── assets/
│   └── centrifuge_v3.glb      # 3D centrifuge model
├── data/
│   └── manuals/               # Calibration manual sources for RAG
├── bioops/
│   ├── simulation_core/       # Physics engine + FSM + commands
│   ├── llm_engine/            # Gemini agent + tools + prompts
│   ├── rag_memory/            # ChromaDB hybrid retrieval
│   ├── industrial_edge/       # MQTT + anomaly detection
│   ├── security/              # Audit logger + sanitizer
│   └── simulation_ui/         # Gradio dashboard + callbacks
└── docs/                      # Technical architecture papers
```

---

## 📖 Technical Documentation

| Document | Description |
|----------|-------------|
| [Technical Architecture](docs/technical_architecture.md) | System design, patterns, and component interactions |
| [Gemini 3.1 Integration](docs/gemini_integration.md) | LLM configuration, function calling, and prompt engineering |
| [RAG Architecture](docs/rag_architecture.md) | Hybrid search, parent-child chunking, and retrieval pipeline |
| [Governance & Security](docs/governance_security.md) | Veea Lobster Trap proxy, Zero-PHI, audit compliance |

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Google Gemini API key. Without it, the agent runs in MOCK mode |
| `MQTT_BROKER` | No | MQTT broker host (default: `broker.hivemq.com`) |
| `MQTT_PORT` | No | MQTT broker port (default: `1883`) |

---

## 📜 License

This project was built for the [lablab.ai Transforming Enterprise Through AI Hackathon](https://lablab.ai) (May 2026).

---

<p align="center">
  Built with ❤️ using <strong>Google Gemini 3.1 Pro</strong> · <strong>Veea Lobster Trap</strong> · <strong>Gradio</strong>
</p>
