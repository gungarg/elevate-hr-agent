# Altostrat HR & IT Multi-Agent Assistant

[![ADK 2.0](https://img.shields.io/badge/Google%20ADK-2.0-blue.svg)](https://adk.dev/)
[![Knowledge Retrieval](https://img.shields.io/badge/Retrieval-OKF%20(Open%20Knowledge%20Format)-green.svg)](docs/knowledge_retrieval_strategy_plan.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

An enterprise-grade, deterministic multi-agent HR and IT Service Concierge built on **Google Agent Development Kit (ADK 2.0)**, grounded in the **Open Knowledge Format (OKF)**, and integrated with **WorkWeek HCM** and **ServiceImmediately ITSM** via **FastMCP Streamable HTTP**.

---

## 🏛️ Architecture Overview

```
+---------------------------------------------------------------------------------------------------------------+
|                                            AGENT ARCHITECTURE                                                 |
+---------------------------------------------------------------------------------------------------------------+
|                                                                                                               |
|                                         [Employee / Client]                                                   |
|                                                  │                                                            |
|                                                  ▼                                                            |
|                                        [Concierge Agent] (Root)                                               |
|                                   (OKF Knowledge Engine: 21 Concepts)                                         |
|                                         │                │                                                    |
|                   ┌─────────────────────┘                └────────────────────┐                               |
|                   ▼                                                           ▼                               |
|       [WorkWeek Specialist] (mode="task")                         [ITSM Specialist] (mode="task")             |
|       (Output: `WorkWeekTaskOutput`)                              (Output: `ITSMTaskOutput`)                  |
|                   │                                                           │                               |
|                   ▼                                                           ▼                               |
|       [WorkWeek FastMCP Server]                                   [ServiceImmediately FastMCP Server]         |
|      (/work-week/mcp/ - X-MCP-Token)                             (/service-immediately/mcp/ - X-MCP-Token)    |
|                                                                                                               |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```
elevate-hr-agent/
├── .agents-cli-spec.md          # Primary source of truth for Google Agents CLI
├── .env.example                 # Environment configuration template
├── .gitignore                   # Excludes __pycache__, *.pyc, *.metadata.json, .env
├── README.md                    # Project overview and quickstart guide
├── pyproject.toml               # Package dependencies (google-adk, fastmcp, pydantic)
│
├── agent/                       # Core ADK 2.0 Agent Package
│   ├── __init__.py              # Exports `root_agent` for ADK discovery
│   ├── agent.py                 # Multi-agent definitions (concierge_agent & specialists)
│   ├── config.py                # Environment & MCP URL configuration
│   ├── prompt.py                # Grounding prompts & citation rules
│   ├── schemas.py               # Pydantic task schemas (WorkWeekTaskOutput, ITSMTaskOutput)
│   ├── state.py                 # Immutable identity anchor & turn cache
│   └── tools/                   # Isolated tool modules
│       ├── __init__.py
│       ├── okf_tool.py          # Open Knowledge Format retrieval tool
│       ├── workweek_tool.py     # WorkWeek FastMCP client & guardrails
│       └── itsm_tool.py         # ServiceImmediately FastMCP client & state machine
│
├── knowledge/                   # OKF Modular Policy Knowledge Bundle (21 concepts)
│   ├── index.md                 # Concept catalog index (Progressive Disclosure)
│   ├── log.md                   # Verification and change log
│   ├── check_okf.py             # Schema validator script
│   ├── 01-paid-time-off/
│   ├── 02-family-building-leaves/
│   ├── 03-compassionate-unpaid/
│   ├── 04-travel-expenses/
│   ├── 05-ethics-compliance/
│   ├── 06-confidentiality-assets/
│   └── 07-conduct-harassment/
│
├── evals/                       # ADK Evaluation Framework
│   ├── datasets/
│   │   └── benchmark_golden_cases.json
│   └── run_eval.py              # Automated accuracy and grounding evaluation runner
│
├── docs/                        # Dedicated Documentation Directory
│   ├── ARCHITECTURE.md          # Comprehensive technical architecture
│   ├── SOLUTION_DESIGN_DOCUMENT.md # Solution Design Document (SDD v3.1)
│   ├── knowledge_retrieval_strategy_plan.md # OKF vs RAG evaluation & strategy
│   └── walkthrough.md           # Implementation milestones & walkthrough
│
└── app.py                       # Interactive Web Testing Server (Port 8080)
```

---

## 🚀 Quickstart

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/gungarg/elevate-hr-agent.git
cd elevate-hr-agent

# Install dependencies with uv (or pip)
uv sync
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure your FastMCP token:
```env
MCP_TOKEN=mcp_zYnFTkwwEfKkx6qaHgW2XTiTRzREoiHjwDZR3I64XdA
WORKWEEK_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/
SERVICEIMMEDIATELY_MCP_URL=https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/
```

### 3. Run the Interactive Web Testing UI
```bash
python app.py 8080
```
Open **`http://localhost:8080`** (or your Cloudtop URL `http://gunjangarg.c.googlers.com:8080`) to interact with the 3-panel chat interface and live telemetry inspector.

### 4. Run the Evaluation Benchmark
```bash
python evals/run_eval.py
```

---

## 📚 Documentation Links
* [Solution Design Document (SDD v3.1)](docs/SOLUTION_DESIGN_DOCUMENT.md)
* [System Architecture](docs/ARCHITECTURE.md)
* [Knowledge Retrieval Strategy (OKF vs RAG)](docs/knowledge_retrieval_strategy_plan.md)
* [Implementation Walkthrough](docs/walkthrough.md)
