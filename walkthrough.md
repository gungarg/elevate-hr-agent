# Walkthrough: HR Multi-Agent System Solution Design (MVP 1)

## Overview
We have designed and finalized an enterprise-grade **Solution Design Document (SDD)** and supporting architectural specifications for the **HR Multi-Agent Application**, built on the **Google Agent Development Kit (ADK 2.0)**, **Vertex AI Agent Engine**, **Google Cloud Model Armor**, **Open Knowledge Format (OKF)**, and **FastMCP Streamable HTTP** integrations.

---

## Key Achievements & Design Milestones

### 1. ADK 2.0 Multi-Agent Topology
* **Concierge Agent (Primary Orchestrator):** Routes user intents, performs single-turn policy lookups via OKF tools, and delegates complex operations via typed task tools.
* **WorkWeek Specialist Agent (`mode="task"`):** Covers all 7 FastMCP tools (`get_current_employee_id`, `get_personal_info`, `update_personal_info`, `get_employee_balances`, `request_time_off`, `get_leave_requests`, `cancel_leave_request`), 2 FastMCP resources (`workweek://employees/{id}/profile`, `workweek://employees/{id}/timeoff`), and REST endpoints (leave modifications & feedback).
* **ITSM Specialist Agent (`mode="task"`):** Covers all 4 FastMCP tools (`list_tickets`, `create_ticket`, `add_ticket_comment`, `update_ticket_status`), FastMCP resource (`serviceimmediately://tickets/{id}`), 5-minute duplicate suppression, Priority 1 outage validation, and strict lifecycle state machine rules (`New -> In Progress/Closed`, `In Progress -> Resolved/Closed`, `Resolved -> In Progress/Closed`).

### 2. Open Knowledge Format (OKF) Knowledge Engine
* Replaced probabilistic chunk-based RAG with a deterministic **OKF Knowledge Bundle** (`knowledge/`), enabling two-step progressive disclosure:
  * `list_concepts()`: Discovers relevant policy concepts from YAML frontmatter (~150 tokens).
  * `read_concept()`: Reads complete, intact markdown policy documents with exact footnote citations (`[^source-id]`).
* Eliminates clause fragmentation across chunk boundaries, provides 100% deterministic grounding, and reduces search infrastructure cost to **$0**.

### 3. Google Cloud Model Armor Security (<50ms)
* Pre-execution input sanitization template: Blocks prompt injection, jailbreak attempts, and off-topic queries.
* Post-execution output inspection template: Scans and masks Sensitive PII (SPII: SSNs, phone numbers, home addresses) via Sensitive Data Protection (SDP/DLP).
* 100% audit logging with Security Command Center (SCC) integration.

### 4. Vertex AI Agent Engine Hosting (`agent_runtime`)
* Deployed as a managed container runtime via `agents-cli deploy --deployment-target agent_runtime`.
* Native session persistence via `VertexAiSessionService`, Agent Gateway governance, and Private Service Connect (PSC) network attachments.

---

## Artifact Index

| Artifact | Path / Link | Description |
| :--- | :--- | :--- |
| **Solution Design Document (v3.0)** | [`SOLUTION_DESIGN_DOCUMENT.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/SOLUTION_DESIGN_DOCUMENT.md) | Complete 10-section MVP Solution Design Document following the required enterprise template. |
| **System Architecture Document** | [`ARCHITECTURE.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/ARCHITECTURE.md) | High-level system topology, sequence diagrams, component breakdowns, and FastMCP transport specs. |
| **ADK 2.0 Agent Specification** | [`.agents-cli-spec.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/.agents-cli-spec.md) | Machine-readable ADK 2.0 agent configuration, Pydantic schemas, and token administration specs. |
| **Retrieval Strategy Plan** | [`knowledge_retrieval_strategy_plan.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/knowledge_retrieval_strategy_plan.md) | Detailed comparative evaluation of OKF vs. Vector RAG for bounded policy sets. |
| **BRD Reference Bookmark** | [`HR Agentic Solution BRD.url.json`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/HR%20Agentic%20Solution%20BRD.url.json) | URL artifact referencing the authoritative Business Requirements Document. |

---

## Next Steps: Implementation & Scaffolding
When you are ready to begin implementation, the project can be scaffolded and verified with the following commands:
1. **Scaffold ADK Project:**
   ```bash
   agents-cli scaffold create hr-agent --deployment-target agent_runtime
   ```
2. **Run Local Smoke Test:**
   ```bash
   agents-cli run "What is the bereavement leave policy?"
   ```
3. **Run Automated Evaluation Suite:**
   ```bash
   agents-cli eval run --dataset tests/eval/datasets/policy_benchmark.json
   ```
