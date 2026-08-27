# Walkthrough: HR Multi-Agent System Solution Design (MVP 1 - v3.1)

## Overview
We have finalized and published the enterprise-grade **Solution Design Document (SDD v3.1)** and supporting architectural specifications for the **HR Multi-Agent Application**, built on the **Google Agent Development Kit (ADK 2.0)**, **Vertex AI Agent Engine**, **Google Cloud Model Armor**, **GCS-Backed Open Knowledge Format (OKF)**, and **FastMCP Streamable HTTP** integrations.

---

## Key Achievements & Design Milestones

### 1. ADK 2.0 Multi-Agent Topology & State Security
* **Concierge Agent (Primary Orchestrator):** Built on `gemini-3.5-flash`, routes user intents, performs single-turn policy lookups via OKF tools, and delegates complex operations via typed task tools.
* **Immutable Identity Anchoring (`ctx.state["auth_context"]`):** Eliminates parameter spoofing and Confused Deputy vulnerabilities by binding the caller's identity at the ingress gateway.
* **Turn-Scoped Request Memoization (`ctx.state["turn_cache"]`):** Eliminates 3–4 redundant REST round-trips in multi-step workflows (UC-2.1 Equipment Procurement, UC-2.3 Relocation) while satisfying FR-3.4 compliance (zero cross-session PII caching).
* **WorkWeek Specialist Agent (`mode="task"`):** Covers all 7 FastMCP tools, 2 FastMCP resources (`workweek://`), and extended REST endpoints for full HCM self-service.
* **ITSM Specialist Agent (`mode="task"`):** Covers all 4 FastMCP tools, FastMCP resource (`serviceimmediately://tickets/{id}`), 5-minute duplicate suppression, Priority 1 outage validation, and strict lifecycle state machine rules (`Closed -> *` terminal lock).

### 2. GCS-Backed Open Knowledge Format (OKF) Knowledge Engine
* Authoritative policy storage hosted in **Google Cloud Storage** (`gs://<project>-hr-policies/knowledge/`) decoupled from application code.
* Pre-fetched into **fast in-memory RAM cache** on container startup with ETag-based synchronization.
* Two-step progressive disclosure (`list_concepts()` $\rightarrow$ `read_concept()`) delivers **100% deterministic grounding**, exact footnote citations (`[^source-id]`), zero vector chunk fragmentation, and **$0 search infrastructure cost**.

### 3. Google Cloud Model Armor Security (<50ms)
* Pre-execution input sanitization template: Blocks prompt injection, jailbreak attempts, and off-topic queries.
* Post-execution output inspection template: Scans and masks Sensitive PII (SPII: SSNs, phone numbers, home addresses) via Sensitive Data Protection (SDP/DLP).
* 100% audit logging with Security Command Center (SCC) integration.

### 4. Vertex AI Agent Engine Hosting (`agent_runtime`)
* Deployed as a managed container runtime via `agents-cli deploy --deployment-target agent_runtime`.
* Native session persistence via `VertexAiSessionService`, Agent Gateway governance, and Private Service Connect (PSC) network attachments.

---

## Artifact Index & Repository Links

All artifacts are synchronized with the GitHub repository at **[https://github.com/gungarg/elevate-hr-agent](https://github.com/gungarg/elevate-hr-agent)**:

| Artifact | Local Path / Link | GitHub Repository Link | Description |
| :--- | :--- | :--- | :--- |
| **Solution Design Document (v3.1)** | [`SOLUTION_DESIGN_DOCUMENT.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/SOLUTION_DESIGN_DOCUMENT.md) | [SDD on GitHub](https://github.com/gungarg/elevate-hr-agent/blob/main/SOLUTION_DESIGN_DOCUMENT.md) | Master MVP Solution Design Document (SDD v3.1) covering all 10 standard enterprise sections. |
| **System Architecture Document** | [`ARCHITECTURE.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/ARCHITECTURE.md) | [Architecture on GitHub](https://github.com/gungarg/elevate-hr-agent/blob/main/ARCHITECTURE.md) | High-level system topology, sequence flows, component breakdowns, and FastMCP transport specs. |
| **ADK 2.0 Agent Specification** | [`.agents-cli-spec.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/.agents-cli-spec.md) | [Spec on GitHub](https://github.com/gungarg/elevate-hr-agent/blob/main/.agents-cli-spec.md) | Machine-readable ADK 2.0 agent configuration manifest, Pydantic schemas, and token administration specs. |
| **Retrieval Strategy Plan** | [`knowledge_retrieval_strategy_plan.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/knowledge_retrieval_strategy_plan.md) | [Plan on GitHub](https://github.com/gungarg/elevate-hr-agent/blob/main/knowledge_retrieval_strategy_plan.md) | Comparative evaluation of Open Knowledge Format (OKF) vs. Traditional Vector RAG. |
| **Walkthrough & Summary** | [`walkthrough.md`](file:///usr/local/google/home/gunjangarg/.gemini/jetski/brain/7a5d1510-d1db-48ab-8a95-675178dec725/walkthrough.md) | [Walkthrough on GitHub](https://github.com/gungarg/elevate-hr-agent/blob/main/walkthrough.md) | Design walkthrough and milestone summary. |
