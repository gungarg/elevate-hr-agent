# MVP SOLUTION DESIGN DOCUMENT
# Enterprise HR Multi-Agent Assistant

---

## Document Control

### Document Metadata
| Field | Value |
| :--- | :--- |
| **Document Title** | Solution Design Document (SDD) – Enterprise HR Multi-Agent Application |
| **Project Name** | HR Agentic Solution (MVP 1) |
| **Author(s)** | Enterprise AI Solution Architecture & Engineering Team |
| **Creation Date** | August 27, 2026 |
| **Document Status** | Approved / Baseline |
| **Target Audience** | Enterprise HR Leadership, IT Operations, Cloud Solutions Architects, Software Engineers, InfoSec / Compliance Officers |
| **Classification** | Internal / Confidential |

### Revision History
| Version | Date | Author | Description of Change |
| :--- | :--- | :--- | :--- |
| 0.1 | 2026-08-27 | AI Solution Architect | Initial outline setup and architecture draft |
| 1.0 | 2026-08-27 | AI Solution Architect | Full MVP 1 design with ADK multi-agent orchestration, FastMCP integrations, and evaluation framework |
| 1.1 | 2026-08-27 | AI Solution Architect | Integrated Google Cloud Model Armor, Gemini 3.5 Flash, and Vertex AI Agent Engine (Agent Runtime) |
| 2.0 | 2026-08-27 | AI Solution Architect | ADK 2.0 compliance, full FastMCP/REST capabilities, and formalized ITSM state machine matrix |
| 3.0 | 2026-08-27 | AI Solution Architect | **Open Knowledge Format (OKF) Integration:**<br>Adopted **Open Knowledge Format (OKF)** for the policy knowledge layer (`knowledge/` bundle with `list_concepts()` and `read_concept()`), delivering 100% deterministic grounding, exact footnote citations, and zero vector database infrastructure costs. |

---

## 1. Executive Summary & Scope Boundaries

### 1.1. Business Overview & Context
Enterprise employees currently navigate a fragmented, disjointed ecosystem of human resources and IT service portals. Routine inquiries—such as checking PTO balances, understanding bereavement or parental leave policies, updating contact information, or opening IT helpdesk incident tickets—require navigating complex SaaS user interfaces across systems like **WorkWeek** (Human Capital Management) and **ServiceImmediately** (IT Service Management).

**Key Pain Points:**
- **High Tier-1 Support Ticket Volume:** HR and IT helpdesks spend over 40% of their operational bandwidth fielding repetitive status inquiries, basic policy clarifications, and routine profile update tasks.
- **Friction in Cross-System Workflows:** High-frequency employee lifecycles (e.g., remote work equipment requests, medical leave of absence, regional office relocations) require manual, unlinked actions across multiple SaaS portals and policy documents.
- **Context Fragmentation & Compliance Risk:** Lack of centralized policy grounding leads to inconsistent interpretations of company policies, while manual data entry increases error rates and risks unauthorized exposure of Sensitive Personally Identifiable Information (SPII).

**High-Level Business Goals:**
- **Deflect Tier-1 Inquiries:** Automate routine HR and IT inquiries to deflect at least 40% of tier-1 support volume within the first 6 months.
- **Streamline Self-Service Transactions:** Provide a unified, natural-language conversational interface that enables zero-friction execution of transactional tasks (leave booking, ticket tracking, contact updates).
- **Validate Cross-System Agentic Orchestration:** Prove the multi-agent chaining paradigm across unstructured knowledge (HR Policy Documents) and structured transactional APIs (WorkWeek, ServiceImmediately) with 100% transactional correctness.
- **Enforce Zero-Trust Enterprise AI Governance:** Guarantee zero data leaks and zero unauthorized cross-user profile access via managed **Google Cloud Model Armor** inspection, strict identity propagation, and comprehensive auditability.

---

### 1.2. Scope Boundaries

```
+---------------------------------------------------------------------------------------+
|                                    SYSTEM BOUNDARIES                                  |
+---------------------------------------------------+-----------------------------------+
|                  IN SCOPE (MVP 1)                 |            OUT OF SCOPE           |
+---------------------------------------------------+-----------------------------------+
| * Web-based Conversational UI (Chat Interface)    | * Multi-lingual NLP processing    |
| * HR Policy Q&A via Open Knowledge Format (OKF)   | * Voice / Multimodal interactions |
| * WorkWeek HCM: Profile, Balances, Leave Requests | * Payroll, Compensation, & Bonus  |
| * ServiceImmediately ITSM: Incident Lifecycle     | * Performance Reviews & Appraisal |
| * Cross-System Orchestration (UC-2.1, 2.2, 2.3)   | * Integrations outside WorkWeek,  |
| * FastMCP Streamable HTTP Integration Layer       |   ServiceImmediately & Policy KB  |
| * ADK 2.0 Multi-Agent Framework & Graph Workflows | * Multi-Tenant SaaS Partitioning  |
| * Managed Deployment on Vertex AI Agent Engine    | * Enterprise SSO / Okta / Entra   |
| * Model Armor Safety Scanning (<50ms overhead)    |   (Mock PAT authentication used)  |
| * Ephemeral Session Memory (Zero PII retention)   |                                   |
+---------------------------------------------------+-----------------------------------+
```

---

### 1.3. Target Architecture Overview

The system employs a streamlined Multi-Agent Architecture built on the **Google Agent Development Kit (ADK 2.0)** and deployed on **Vertex AI Agent Engine (Agent Runtime)**, protected by **Google Cloud Model Armor**. Policy knowledge retrieval is governed by the **Open Knowledge Format (OKF)** engine.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client & Edge Layer"]
        User["Enterprise Employee (Browser / Web Chat UI)"]
        LB["Google Cloud Armor & HTTPS Load Balancer"]
    end

    subgraph SecurityGuardrails ["Google Cloud Model Armor (<50ms Managed Layer)"]
        MA_Input["Model Armor - User Prompt Sanitizer\n* Jailbreak / Prompt Injection Filter\n* Malicious URI & Toxicity Block\n* Out-of-Scope Containment"]
        MA_Output["Model Armor - Response Inspection\n* Sensitive Data Protection (SDP/DLP)\n* SPII Redaction (Address, Phone, SSN)\n* Hallucination & Leakage Guard"]
    end

    subgraph OrchestrationLayer ["Vertex AI Agent Engine (ADK 2.0 Agent Runtime)"]
        Concierge["Primary Concierge Agent\n(Gemini 3.5 Flash / Orchestrator & Router)"]
        SessionStore["VertexAiSessionService\n(Managed State & Ephemeral Memory)"]
        AgentGateway["Agent Gateway\n(Governed Ingress/Egress & PSC Interface)"]
    end

    subgraph OKFKnowledgeLayer ["Open Knowledge Format (OKF) Engine"]
        OKFTools["OKF Knowledge Tools\n* list_concepts()\n* read_concept(concept_id)"]
        BundleStore[("OKF Knowledge Bundle (Git / Local)\n├── index.md\n├── 01-paid-time-off/\n├── 02-expenses/\n├── 03-remote-work/\n└── 04-code-of-conduct/")]
    end

    subgraph SpecialistAgents ["ADK 2.0 Transactional Sub-Agents (mode='task')"]
        WorkWeekAgent["WorkWeek Specialist Agent\n(Gemini 3.5 Flash / HCM Tools & Resources)"]
        ITSMAgent["ITSM Specialist Agent\n(Gemini 3.5 Flash / ITSM Tools & Resources)"]
    end

    subgraph MCPIntegrationLayer ["Integration & Transport Layer (FastMCP HTTP)"]
        WorkWeekMCP["WorkWeek FastMCP Server\n(/work-week/mcp/)\nHeader: X-MCP-Token"]
        ITSMMCP["ServiceImmediately FastMCP Server\n(/service-immediately/mcp/)\nHeader: X-MCP-Token"]
    end

    subgraph EnterpriseBackends ["Enterprise SaaS Backends"]
        WorkWeekSaaS[("WorkWeek HCM Backend\n(REST API & Database)")]
        ITSMSaaS[("ServiceImmediately ITSM Backend\n(REST API & Database)")]
    end

    subgraph ObservabilityLayer ["Enterprise Governance & Observability"]
        CloudAudit["Cloud Logging & Security Command Center\n(Masked SPII / 100% Traceability)"]
        CloudTrace["Cloud Trace & BigQuery Agent Analytics\n(Distributed Telemetry)"]
    end

    User -->|HTTPS / WSS| LB
    LB --> MA_Input
    MA_Input -->|Sanitized Prompt| Concierge
    Concierge <--> SessionStore
    Concierge <--> AgentGateway

    Concierge -->|Direct Tool Call| OKFTools
    OKFTools <--> BundleStore
    WorkWeekAgent -.->|Optional Policy Self-Check| OKFTools

    Concierge -->|request_task_workweek| WorkWeekAgent
    Concierge -->|request_task_itsm| ITSMAgent

    WorkWeekAgent -->|Streamable HTTP JSON-RPC| WorkWeekMCP
    ITSMAgent -->|Streamable HTTP JSON-RPC| ITSMMCP

    WorkWeekMCP -->|HTTPS REST| WorkWeekSaaS
    ITSMMCP -->|HTTPS REST| ITSMSaaS

    Concierge --> MA_Output
    MA_Output -->|Grounded & Redacted Response| User

    Concierge -.-> CloudAudit
    Concierge -.-> CloudTrace
    WorkWeekAgent -.-> CloudTrace
    ITSMAgent -.-> CloudTrace
```

---

### 1.4. Technical Alternatives & Trade-Offs

#### 1.4.1. Policy Knowledge Strategy: Open Knowledge Format (OKF) vs. Traditional Vector RAG
| Dimension | Open Knowledge Format (OKF) **[CHOSEN]** | Traditional Vector RAG (Vertex AI Search) | Rationale for Selection |
| :--- | :--- | :--- | :--- |
| **Corpus Scale Suitability** | Tailored for **bounded, curated enterprise policy sets** (5–50 documents / ~100–150 concept files). | Designed for massive, unbounded document archives (thousands of unstructured PDFs). | **OKF Selected:** Corporate HR policies are finite, highly structured, and require complete context preservation. |
| **Retrieval Precision** | **100% Deterministic:** Progressive disclosure (`list_concepts` $\rightarrow$ `read_concept`) ingests complete atomic markdown concepts without splitting clauses. | **Probabilistic:** Vector chunking (500 tokens) risks cutting conditions (e.g., manager approval thresholds) across chunk boundaries. | **OKF Selected:** Eliminates chunk fragmentation and hallucinated context gaps. |
| **Citation Fidelity** | **Exact:** Built-in YAML frontmatter provenance (`sources`, `resource`, `section`) and markdown footnotes (`[^fn1]`). | Extractive text snippets with probabilistic page boundaries. | **OKF Selected:** Guarantees 100% auditable citations linking to exact policy sections. |
| **Infrastructure & Search Cost** | **$0 Search Infra Cost:** Knowledge bundle lives in Git / local filesystem; zero embedding or vector indexing fees. | Incurs Vertex AI Search indexing fees ($/GiB/mo) + query fees ($/1K search ops). | **OKF Selected:** Significantly reduces monthly operating TCO. |
| **Governance & GitOps** | **Knowledge-as-Code:** Policies live in Git with PR reviews, line-by-line diffs, and `stale_after` freshness metadata. | Unstructured PDFs in cloud storage buckets with opaque indexing. | **OKF Selected:** Enables collaborative HR policy authoring in Git. |

---

## 2. Production-Ready Future State Design

```
+---------------------------------------------------------------------------------------------------+
|                                  PRODUCTION ROADMAP & EVOLUTION                                   |
+------------------------------------+--------------------------------------------------------------+
| Capability Area                    | Production Target State                                      |
+------------------------------------+--------------------------------------------------------------+
| 1. Enterprise Identity & Auth      | * OIDC / SAML 2.0 federation (Okta, Entra ID, Google Cloud).  |
|                                    | * Per-user OAuth 2.0 token exchange via Cloud IAP & GFE.     |
|                                    | * Fine-grained ABAC / RBAC tied to corporate HR Org units.   |
+------------------------------------+--------------------------------------------------------------+
| 2. Multi-Tenancy & Partitioning    | * Tenant-isolated VPCs and dedicated FastMCP namespaces.     |
|                                    | * Database Row-Level Security (RLS) on Session & Audit Logs. |
|                                    | * Tenant-specific KMS encryption keys (CMEK).                |
+------------------------------------+--------------------------------------------------------------+
| 3. Extended Enterprise SaaS        | * Full HCM connector: Workday, SuccessFactors, BambooHR.     |
|                                    | * Full ITSM connector: ServiceNow HRSD, Jira Service Desk.   |
|                                    | * Corporate ERP & Travel: SAP Concur, Expensify.             |
+------------------------------------+--------------------------------------------------------------+
| 4. Human-In-The-Loop (HITL)        | * Manager approval gates for leave requests > 10 days.       |
|                                    | * Tier-2 HR Generalist escalation channel in Slack/Teams.    |
|                                    | * Real-time agent transfer with full transcript context.     |
+------------------------------------+--------------------------------------------------------------+
| 5. Multi-Channel Integration       | * Direct native Slack bot & Microsoft Teams app integration. |
|                                    | * Google Chat enterprise app with rich adaptive cards.       |
|                                    | * Webhook event triggers (e.g. Workday onboarding probers).  |
+------------------------------------+--------------------------------------------------------------+
| 6. OKF Automated Enrichment        | * Automated AI Enrichment Agent converting incoming policy   |
|                                    |   PDFs/Word docs directly into validated OKF concept bundles.|
+------------------------------------+--------------------------------------------------------------+
```

---

## 3. System Flows, Sequence Diagrams & Agent Design

### 3.1. End-to-End Sequence Flows

#### A. Single Domain: Policy Q&A via OKF Engine (UC-1.1)
```mermaid
sequenceDiagram
    autonumber
    actor User as Employee
    participant Client as Web Chat UI
    participant ModelArmor as Model Armor (Security)
    participant Concierge as Concierge Agent (Gemini 3.5 Flash)
    participant OKF as OKF Knowledge Engine
    participant Bundle as knowledge/ Bundle Store

    User->>Client: "What is the bereavement leave policy for immediate family?"
    Client->>ModelArmor: POST /v1/sanitizeUserPrompt (Input Check)
    ModelArmor->>ModelArmor: Pass (No injection, on-topic) (<25ms)
    ModelArmor->>Concierge: Forward Sanitized Prompt
    Concierge->>Concierge: Direct Policy Query Detected
    
    %% Step 1: Concept Discovery
    Concierge->>OKF: Tool Call: list_concepts(domain="paid-time-off")
    OKF->>Bundle: Read YAML Frontmatter in knowledge/01-paid-time-off/
    Bundle-->>OKF: [{id: "01-paid-time-off/1.4-bereavement-leave", title: "Bereavement Leave Policy", description: "Guidelines on paid bereavement leave for immediate and extended family"}]
    OKF-->>Concierge: Returns Matching Concept Metadata
    
    %% Step 2: Full Concept Reading
    Concierge->>OKF: Tool Call: read_concept(concept_id="01-paid-time-off/1.4-bereavement-leave")
    OKF->>Bundle: Read Markdown Body & Footnotes
    Bundle-->>OKF: Intact Concept: 5 paid days for immediate family, 3 days for extended family. Source: [^leave-policy-doc]
    OKF-->>Concierge: Returns Complete Policy Markdown & Sources
    
    Concierge->>ModelArmor: POST /v1/sanitizeAgentResponse (Output Check)
    ModelArmor-->>Client: "Employees are eligible for **5 consecutive days of paid bereavement leave** for immediate family members (spouse, child, parent, sibling) per Section 3.1 of the [Bereavement Leave Policy](https://policies.corp/leave#sec-3.1)."
    Client-->>User: Render Answer with Exact Footnote Citations
```

---

#### B. Cross-System Orchestration: Equipment Procurement (UC-2.1)
```mermaid
sequenceDiagram
    autonumber
    actor User as Employee
    participant Client as Web Chat UI
    participant ModelArmor as Model Armor
    participant Concierge as Concierge Agent (Gemini 3.5 Flash)
    participant OKF as OKF Knowledge Engine
    participant WW_Agent as WorkWeek Specialist (mode='task')
    participant ITSM_Agent as ITSM Specialist (mode='task')
    participant WW_MCP as WorkWeek FastMCP
    participant ITSM_MCP as ServiceImmediately FastMCP

    User->>Client: "I read the remote work policy. Can I order a home monitor and have it shipped to my address?"
    Client->>ModelArmor: Sanitize Input Prompt
    ModelArmor->>Concierge: Forward Verified Prompt
    Concierge->>Concierge: Orchestration Plan:\n1. Query OKF Remote Work Policy\n2. Retrieve Profile & Address\n3. Create Hardware Procurement Ticket

    %% Step 1: Policy Grounding via OKF
    Concierge->>OKF: Tool Call: read_concept(concept_id="03-remote-work/3.2-home-office-equipment")
    OKF-->>Concierge: Policy Content: "Full-time remote employees are eligible for up to 1 external 27-inch monitor (Section 4.2)." Citation: [^remote-work-spec]

    %% Step 2: WorkWeek Profile Verification
    Concierge->>WW_Agent: request_task_workweek(action="GET_PROFILE", employee_id="EMP1024")
    WW_Agent->>WW_MCP: Read Resource: workweek://employees/EMP1024/profile
    WW_MCP-->>WW_Agent: {role: "Software Engineer", work_mode: "Remote", address: "123 Tech Lane, Austin TX", phone: "+1-512-555-0199"}
    WW_Agent->>WW_Agent: finish_task(status="SUCCESS", is_remote=True, address="123 Tech Lane, Austin TX")
    WW_Agent-->>Concierge: WorkWeekProfileOutput

    %% Step 3: ServiceImmediately Ticket Creation
    Concierge->>ITSM_Agent: request_task_itsm(action="CREATE_TICKET", requested_by="EMP1024", category="Hardware", short_description="Remote Monitor Procurement - 27in Display", priority="3 - Moderate", assignment_group="IT Procurement")
    ITSM_Agent->>ITSM_Agent: Check Duplicate Guardrail (<5 min check) & Priority ('3 - Moderate')
    ITSM_Agent->>ITSM_MCP: Tool: create_ticket(requested_by="EMP1024", category="Hardware", short_description="Remote Monitor Procurement - 27in Display", priority="3 - Moderate", assignment_group="IT Procurement")
    ITSM_MCP-->>ITSM_Agent: {ticket_id: "INC-99042", status: "New", assignee: "IT Procurement"}
    ITSM_Agent->>ITSM_MCP: Tool: add_ticket_comment(ticket_id="INC-99042", author="Automation (HR Agent)", comment="Auto-validated via Remote Work Policy. Shipping Address: 123 Tech Lane, Austin TX.")
    ITSM_Agent->>ITSM_Agent: finish_task(status="CREATED", ticket_id="INC-99042", assignment_group="IT Procurement")
    ITSM_Agent-->>Concierge: ITSMTaskOutput

    Concierge->>ModelArmor: Sanitize Final Response (SDP Masking)
    ModelArmor-->>Client: "Under Section 4.2 of the Remote Work Policy, you are eligible for an external monitor. I have verified your remote status and submitted ticket **#INC-99042** with IT Procurement to ship the display to your registered address (*123 Tech Lane, Austin TX*)."
    Client-->>User: Display Response with Policy Citation Link & Ticket Badge
```

---

### 3.2. ADK 2.0 Agent Architecture & OKF Tool Definitions

```python
import os
import yaml
from pathlib import Path
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from pydantic import BaseModel, Field
from typing import Optional, Literal

# --- OKF Knowledge Engine Implementation ---
KNOWLEDGE_ROOT = Path(__file__).parent / "knowledge"

def list_concepts(domain: Optional[str] = None) -> list[dict]:
    """Scans the OKF knowledge bundle and lists available concepts by parsing YAML frontmatter.
    
    Args:
        domain: Optional domain filter (e.g. '01-paid-time-off', '02-expenses', '03-remote-work').
    """
    concepts = []
    search_dir = KNOWLEDGE_ROOT / domain if domain else KNOWLEDGE_ROOT
    for md_file in search_dir.glob("**/*.md"):
        if md_file.name in ["index.md", "log.md"]:
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                frontmatter = yaml.safe_load(parts[1])
                rel_id = md_file.relative_to(KNOWLEDGE_ROOT).with_suffix("").as_posix()
                concepts.append({
                    "concept_id": rel_id,
                    "title": frontmatter.get("title", md_file.stem),
                    "description": frontmatter.get("description", ""),
                    "tags": frontmatter.get("tags", []),
                })
        except Exception:
            continue
    return concepts

def read_concept(concept_id: str) -> dict:
    """Reads the full content, metadata, and citation sources for a specific OKF concept file.
    
    Args:
        concept_id: The relative concept path (e.g., '01-paid-time-off/1.4-bereavement-leave').
    """
    target_file = (KNOWLEDGE_ROOT / f"{concept_id}.md").resolve()
    # Guard against directory traversal
    if not str(target_file).startswith(str(KNOWLEDGE_ROOT.resolve())):
        return {"error": "Access Denied: Invalid concept path"}
    if not target_file.exists():
        return {"error": f"Concept '{concept_id}' not found"}

    content = target_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
    body = parts[2].strip() if len(parts) >= 3 else content

    return {
        "concept_id": concept_id,
        "title": frontmatter.get("title", ""),
        "sources": frontmatter.get("sources", []),
        "verified": frontmatter.get("verified", {}),
        "content": body,
    }

list_concepts_tool = FunctionTool(func=list_concepts)
read_concept_tool = FunctionTool(func=read_concept)

# --- Typed Output Schemas for ADK 2.0 Task Delegation ---
class WorkWeekTaskOutput(BaseModel):
    status: Literal["SUCCESS", "INSUFFICIENT_BALANCE", "VALIDATION_ERROR", "NOT_FOUND"]
    employee_id: str
    data: Optional[dict] = Field(default_factory=dict, description="Profile or leave result payload")
    message: str = Field(description="Structured explanation of the result")

class ITSMTaskOutput(BaseModel):
    status: Literal["CREATED", "UPDATED", "DUPLICATE_REJECTED", "INVALID_TRANSITION", "ERROR"]
    ticket_id: Optional[str] = None
    state: Optional[str] = None
    message: str

# --- FastMCP Toolset Connections ---
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/",
        headers={"X-MCP-Token": "mcp_your_token_here"}
    )
)

serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/",
        headers={"X-MCP-Token": "mcp_your_token_here"}
    )
)

# --- ADK 2.0 Specialist Sub-Agents (mode='task') ---
workweek_specialist = Agent(
    name="workweek_specialist",
    model="gemini-3.5-flash",
    mode="task",
    output_schema=WorkWeekTaskOutput,
    description="Handles WorkWeek HCM operations: employee profile lookups, contact updates, leave balances, booking/canceling leave.",
    instruction="Execute requested HCM operations using WorkWeek tools/resources. Validate dates and balances. Call finish_task.",
    tools=[workweek_mcp, list_concepts_tool, read_concept_tool],
)

itsm_specialist = Agent(
    name="itsm_specialist",
    model="gemini-3.5-flash",
    mode="task",
    output_schema=ITSMTaskOutput,
    description="Handles ServiceImmediately ITSM operations: ticket queries, incident creation, comments, and lifecycle status updates.",
    instruction="Execute incident operations. Enforce duplicate suppression, priority 1 outage validation, and state machine transition rules. Call finish_task.",
    tools=[serviceimmediately_mcp],
)

# --- ADK 2.0 Primary Concierge Agent ---
concierge_agent = Agent(
    name="concierge_agent",
    model="gemini-3.5-flash",
    description="Enterprise HR Concierge Assistant orchestrating policy queries, HCM actions, and IT support tickets.",
    instruction="""
    You are the Enterprise HR & IT Concierge Virtual Assistant.
    1. For HR policy questions: call `list_concepts()` to find the relevant policy topic, then call `read_concept()` to read the verified text. Always return exact citations and footnote links.
    2. For profile or leave inquiries: delegate to `workweek_specialist` using `request_task_workweek`.
    3. For IT service desk incidents: delegate to `itsm_specialist` using `request_task_itsm`.
    4. For cross-system workflows (e.g. equipment orders, medical leaves): coordinate tools and sub-agents sequentially.
    5. Consolidate results into clear, empathetic, professional markdown responses.
    """,
    tools=[list_concepts_tool, read_concept_tool],
    sub_agents=[workweek_specialist, itsm_specialist],
)
```

---

## 4. Security, Governance & Identity

### 4.1. Google Cloud Model Armor Configuration & Templates
Google Cloud Model Armor acts as the unified, managed security proxy governing both user inputs and agent responses:

```
+-----------------------------------------------------------------------------------+
|                           MODEL ARMOR INSPECTION PIPELINE                         |
+-----------------------------------------------------------------------------------+
|  [Incoming User Turn]                                                             |
|         │                                                                         |
|         ▼                                                                         |
|  [Model Armor: Input Inspection Template]                                         |
|    ├── 1. Prompt Injection Filter (Confidence Threshold >= 0.75)                  |
|    ├── 2. Jailbreak Filter (Detects system override / roleplay prompts)           |
|    ├── 3. Malicious URL / Script Filter                                           |
|    └── 4. Domain Topic Boundary Filter (Rejects coding, math, general advice)     |
|         │                                                                         |
|         ▼ (Sanitized Payload Passed to ADK Concierge Agent)                       |
|  [ADK Multi-Agent Orchestration & FastMCP Tool Execution]                         |
|         │                                                                         |
|         ▼                                                                         |
|  [Model Armor: Output Inspection Template]                                        |
|    ├── 1. Sensitive Data Protection (SDP/DLP) - Automatic Masking:                |
|    │      • US_SSN, PHONE_NUMBER, STREET_ADDRESS, EMAIL_ADDRESS                   |
|    ├── 2. Toxicity & Safety Filter                                                |
|    └── 3. Hallucination & Citation Verification Check                             |
|         │                                                                         |
|         ▼                                                                         |
|  [Sanitized, Redacted Response Delivered to Employee]                             |
+-----------------------------------------------------------------------------------+
```

- **Latency Guarantee:** Model Armor executes inspection within **$20\text{ms} - 45\text{ms}$**, easily within the $300\text{ms}$ budget specified in NFR-2.1.
- **Security Command Center (SCC) Integration:** Every detected threat or policy violation automatically creates an audit event in Cloud Logging and an actionable finding in Security Command Center.

---

### 4.2. Authentication Boundaries & FastMCP Token Handling
Due to Google Frontend (GFE) intercepting standard Authorization headers, FastMCP connections require passing authentication tokens via the custom **`X-MCP-Token`** header:

```http
X-MCP-Token: mcp_your_token_here
```

#### Token Lifecycle Administration & Rotation:
- **Token Generation:** Handled via `POST /api/mcp-tokens` (`TokenGenerationRequest` with `token_name`).
- **Token Storage:** Tokens are stored as versioned secrets in **Google Cloud Secret Manager** (`projects/${PROJECT_ID}/secrets/mcp-token/versions/latest`).
- **Token Revocation:** Handled via `DELETE /api/mcp-tokens/{token_id}` during automated key rotation cycles.

---

## 5. Integration Details & Error Handling

### 5.1. Comprehensive Tool, Resource & API Mapping Matrix

#### A. OKF Knowledge Engine Capabilities
| Tool Name | Parameters | Target Asset | Description & Validation |
| :--- | :--- | :--- | :--- |
| `list_concepts` | `domain: Optional[str] = None` | `knowledge/**/*.md` frontmatter | Scans bundle and returns matched concept IDs, titles, descriptions, and tags. |
| `read_concept` | `concept_id: str` | `knowledge/{concept_id}.md` | Ingests intact concept body, frontmatter sources, and footnotes. Path traversal blocked. |

---

#### B. WorkWeek Server Capabilities (`/work-week/mcp/` & REST APIs)
| Type | Identifier / Method | Parameters / Schema | Target Endpoint | Description & Guardrail Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Tool** | `get_current_employee_id()` | *None* | Session Token | Resolves employee ID of caller session (`EMP1024`). |
| **Tool** | `get_personal_info(employee_id)` | `employee_id: str` | `GET /work-week/api/employees/{id}/profile` | Fetches contact details (address, phone). Ownership checked. |
| **Tool** | `update_personal_info(employee_id, address, phone)` | `employee_id: str`<br>`address: str`<br>`phone: str` | `POST /work-week/api/employees/{id}/profile` (`ProfileUpdateRequest`) | Updates address (min 5 chars) & phone (regex `^\+?[\d\s\-()]{7,20}$`). |
| **Tool** | `get_employee_balances(employee_id)` | `employee_id: str` | `GET /work-week/api/employees/{id}/timeoff` | Real-time fetch of vacation & sick accrued/used/remaining. |
| **Tool** | `request_time_off(employee_id, start_date, end_date, leave_type, days)` | `employee_id: str`<br>`start_date: str`<br>`end_date: str`<br>`leave_type: str`<br>`days: float` | `POST /work-week/api/employees/{id}/timeoff` (`TimeOffRequest`) | Validates `start_date <= end_date`, `start_date >= today`, `days <= remaining_balance`. |
| **Tool** | `get_leave_requests(employee_id)` | `employee_id: str` | `GET /work-week/api/employees/{id}/timeoff/requests` | Fetches full historical leave booking records. |
| **Tool** | `cancel_leave_request(employee_id, request_id)` | `employee_id: str`<br>`request_id: int` | `DELETE /work-week/api/employees/{id}/timeoff/requests/{req_id}` | Cancels leave request and refunds days to available balance. |
| **REST** | `update_leave_request` | `employee_id: str`<br>`request_id: int`<br>`LeaveRequestUpdateRequest` | `PUT /work-week/api/employees/{id}/timeoff/requests/{req_id}` | Modifies existing leave request dates/type and adjusts balance. |
| **REST** | `get_employee_feedback` | `employee_id: str` | `GET /work-week/api/employees/{id}/feedback` | Retrieves manager/peer feedback records for employee. |
| **Resource** | `workweek://employees/{employee_id}/profile` | `employee_id: str` | MCP Resource Protocol | Returns raw employee metadata (role, manager, department). |
| **Resource** | `workweek://employees/{employee_id}/timeoff` | `employee_id: str` | MCP Resource Protocol | Returns raw database leave balances. |

---

#### C. ServiceImmediately Server Capabilities (`/service-immediately/mcp/` & REST APIs)
| Type | Identifier / Method | Parameters / Schema | Target Endpoint | Description & Guardrail Logic |
| :--- | :--- | :--- | :--- | :--- |
| **Tool** | `list_tickets(employee_id)` | `employee_id: str` | `GET /service-immediately/api/tickets?requested_by={id}` | Lists incidents requested by caller. Requires ownership verification. |
| **Tool** | `create_ticket(requested_by, category, short_description, priority, assignment_group)` | `requested_by: str`<br>`category: str`<br>`short_description: str`<br>`priority: str`<br>`assignment_group: str = 'Service Desk'` | `POST /service-immediately/api/tickets` (`TicketCreateRequest`) | Submits incident. Rejects duplicates within 5 min. Priority 1 requires outage/crash keyword. |
| **Tool** | `add_ticket_comment(ticket_id, author, comment)` | `ticket_id: str`<br>`author: str`<br>`comment: str` | `POST /service-immediately/api/tickets/{id}/comments` (`CommentCreateRequest`) | Appends activity log comment with `Automation (HR Agent)` tag. |
| **Tool** | `update_ticket_status(ticket_id, status, resolution_notes, updated_by)` | `ticket_id: str`<br>`status: str`<br>`resolution_notes: str = ''`<br>`updated_by: str = 'System'` | `POST /service-immediately/api/tickets/{id}/status` (`TicketStatusUpdateRequest`) | Drives lifecycle state machine. Enforces allowed state transitions. |
| **Resource** | `serviceimmediately://tickets/{ticket_id}` | `ticket_id: str` | MCP Resource Protocol | Returns structural incident details, status, and timeline. |

---

### 5.2. ServiceImmediately Lifecycle State Machine Matrix

```
+-----------------------------------------------------------------------------------+
|                        INCIDENT LIFECYCLE STATE MACHINE                           |
+-------------------+-----------------------+---------------+-----------------------+
| Current State     | Target State          | Allowed?      | Validation Condition  |
+-------------------+-----------------------+---------------+-----------------------+
| New               | In Progress           | ✅ YES        | Standard assignment   |
| New               | Closed                | ✅ YES        | Direct auto-resolution|
| New               | Resolved              | ❌ BLOCKED    | Must transition via   |
|                   |                       |               | In Progress           |
| In Progress       | Resolved              | ✅ YES        | Resolution notes req. |
| In Progress       | Closed                | ✅ YES        | Immediate close       |
| In Progress       | New                   | ❌ BLOCKED    | Cannot regress to New |
| Resolved          | In Progress           | ✅ YES        | Ticket re-opened      |
| Resolved          | Closed                | ✅ YES        | Verification complete |
| Closed            | * (Any State)         | ❌ LOCKED     | Closed tickets cannot |
|                   |                       |               | transition anymore    |
+-------------------+-----------------------+---------------+-----------------------+
```

---

### 5.3. Resiliency, Fallback & Compensating Actions

| Failure Scenario | Root Cause | System Behavior & Fallback Logic | User-Facing Notification |
| :--- | :--- | :--- | :--- |
| **WorkWeek Backend 503 / Timeout** | HCM Database down or network latency $>5\text{s}$ | Automatic exponential backoff retry (3 attempts: 500ms, 1s, 2s). If failed, log error with correlation ID. | *"I am temporarily unable to access WorkWeek to check your leave balance. Please try again shortly, or contact HR Support directly."* |
| **Insufficient Leave Balance (422)** | User requests 5 days vacation but has 3 remaining | WorkWeek Specialist catches error and extracts balance delta. | *"You requested 5 days of vacation, but your remaining balance is 3 days. Please adjust your request dates."* |
| **Duplicate Ticket Rejection (422)** | Duplicate ticket created within 5 minutes | ITSM Specialist fetches existing ticket ID and shows status. | *"A similar ticket (#INC-99042) was already created in the last 5 minutes. Would you like to view its status or add a comment?"* |
| **Invalid State Transition (422)** | Attempting to update a Closed ticket or invalid transition | ITSM Specialist intercepts rejection and explains valid next states. | *"Ticket #INC-99042 is marked as Closed and cannot be modified. I can open a new ticket for you if this issue persists."* |
| **Partial Chaining Failure (UC-2.2)** | Leave submitted in WorkWeek, but Ticket creation fails in ServiceImmediately | **Compensating Action:** Log failure in audit table; automatically invoke `cancel_leave_request` to rollback days OR present manual ticket link. | *"Your medical leave of absence was recorded in WorkWeek (Request #8812), but our IT ticketing system timed out while setting up email forwarding. I have alerted IT Support to complete this step manually."* |
| **Concept Not Found in OKF Bundle** | User asks about an unindexed policy topic | `list_concepts()` returns empty or low match; LLM triggers containment refusal. | *"I could not find information regarding that policy in our approved HR documentation. Please reach out to your HR Business Partner."* |

---

## 6. Cost Estimation & FinOps

### 6.1. Primary Cost Drivers
1. **LLM Inference Tokens (Gemini 3.5 Flash):** Prompt tokens (~1,200/turn with compact OKF concept parsing) and completion tokens (~300/turn).
2. **Model Armor Inspection:** Billed per 1,000 text sanitization requests (~$0.10 / 1K requests).
3. **OKF Knowledge Storage:** Zero vector DB / search query cost ($0); lightweight GCS/local container storage.
4. **Vertex AI Agent Engine (Agent Runtime):** vCPU-hours and GiB-memory hours during active agent reasoning turns.

---

### 6.2. Monthly FinOps Projection Models

```
+---------------------------------------------------------------------------------------------------+
|                                  MONTHLY COST PROJECTION MATRIX                                   |
+------------------------------------+--------------------+--------------------+--------------------+
| Dimension                          | 1,000 Employees    | 10,000 Employees   | 50,000 Employees   |
|                                    | (Low Volume - MVP) | (Mid Enterprise)   | (Full Rollout)     |
+------------------------------------+--------------------+--------------------+--------------------+
| Monthly Inquiries (Avg 4/user/mo)  | 4,000 turns        | 40,000 turns       | 200,000 turns      |
| Input Tokens (~1,200 tokens/turn)  | 4.8M tokens        | 48M tokens         | 240M tokens        |
| Output Tokens (~300 tokens/turn)   | 1.2M tokens        | 12M tokens         | 60M tokens         |
+------------------------------------+--------------------+--------------------+--------------------+
| Gemini 3.5 Flash Inference Cost    | $0.72              | $7.20              | $36.00             |
| Model Armor Security Scanning      | $0.80              | $8.00              | $40.00             |
| OKF Knowledge Engine Cost          | **$0.00**          | **$0.00**          | **$0.00**          |
| Vertex AI Agent Engine Runtime     | $16.00             | $34.00             | $110.00            |
| Cloud Logging & Observability      | $2.50              | $12.00             | $45.00             |
| Cloud Armor & Load Balancing       | $18.00             | $25.00             | $42.00             |
+------------------------------------+--------------------+--------------------+--------------------+
| **ESTIMATED TOTAL MONTHLY TCO**    | **$38.02**         | **$86.20**         | **$273.00**        |
| **Cost Per Employee / Month**      | **~$0.038**        | **~$0.009**        | **~$0.005**        |
+------------------------------------+--------------------+--------------------+--------------------+
```

---

## 7. Deployment & Delivery Plan

### 7.1. Environments & Deployment Target
- **Primary Deployment Target:** **Vertex AI Agent Engine (Agent Runtime)** configured via `agents-cli deploy --deployment-target agent_runtime`.
- **Infrastructure as Code (Terraform):**
  - `infra/terraform/modules/agent_runtime`: Provisions Vertex AI Agent Engine deployment metadata, Network Attachments for Private Service Connect, and `VertexAiSessionService`.
  - `infra/terraform/modules/model_armor`: Provisions Model Armor safety inspection templates and DLP inspection rulesets.
  - `infra/terraform/modules/secret_manager`: Provisions versioned secret entries for FastMCP `X-MCP-Token`.

---

### 7.2. Phased Delivery Roadmap (8 Weeks)
- **Week 1–2 (Phase 1):** Foundation, Tooling & OKF Knowledge Ingestion (ADK 2.0 project initialization, OKF bundle curation in `knowledge/`, FastMCP client toolsets).
- **Week 3–4 (Phase 2):** Multi-Agent Implementation with Gemini 3.5 Flash (Concierge Agent with OKF Tools, WorkWeek Agent, ITSM Agent, UC-1.x and UC-2.x workflows).
- **Week 5–6 (Phase 3):** Guardrails, Cross-System Workflows & Error Handling (Compensating rollback logic, Model Armor SDP sanitization, PSC network configuration).
- **Week 7–8 (Phase 4):** Quality Evaluation, UAT & Production Readiness (150-case benchmark evaluation via `agents-cli eval run`, UAT sign-off, runbook publication).

---

## 8. Assumptions, Constraints, Risk & Mitigations

### 8.1. Risk & Mitigation Matrix

| Risk ID | Risk Description | Likelihood | Impact | Concrete Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | **Prompt Injection / Jailbreak Attack:** User tricks agent into modifying unauthorized profiles. | Medium | Critical | **Google Cloud Model Armor** template interceptor with strict confidence scoring ($<25\text{ms}$); backend identity token verification in FastMCP servers. |
| **RSK-02** | **Partial Workflow Inconsistency:** Network drop occurs after WorkWeek leave is booked but before ServiceImmediately ticket is created. | Low | High | Implement atomic compensating transaction rollback (automatic call to `cancel_leave_request`) and log failure in audit table with direct user notification. |
| **RSK-03** | **Hallucinated Policy Answers:** Agent invents non-existent maternity or expense benefits. | Low | Critical | OKF deterministic progressive disclosure (`read_concept`) passes complete verified markdown; 0% hallucination mandate in prompt. |
| **RSK-04** | **GFE Header Stripping:** Standard Authorization headers stripped by Google Frontend. | High | Medium | Pass Personal Access Token in custom `X-MCP-Token` header as mandated by FastMCP server specification. |
| **RSK-05** | **Stale Policy Drift:** Policy documents updated in HR without updating agent knowledge. | Medium | Medium | OKF `stale_after` frontmatter metadata triggers automated CI/CD alert when a policy concept reaches its review date. |

---

## 9. Quality Evaluation & UAT Framework

### 9.1. Acceptance Thresholds & Metrics
- **Policy Q&A Accuracy:** $\ge 95\%$ Accuracy, **0% Hallucinations** (LLM-as-a-Judge against 50 golden Q&A pairs).
- **Transaction Integrity:** **100% Correctness** (verified state updates in WorkWeek & ServiceImmediately).
- **Cross-System Chaining:** **100% Pass Rate** on UC-2.1, 2.2, 2.3.
- **Safety & Jailbreak Defense:** **100% Detection**; $<1\%$ False Positives on adversarial test suites via Model Armor.
- **Response Latency:** $<10.0\text{ s}$ total turn time; $<50\text{ms}$ Model Armor safety scanning overhead.
- **Auditability & Traceability:** **100% Log Coverage** with zero SPII leaks.

### 9.2. Evaluation Dataset Curation (150 Cases)
1. **Policy Q&A (40 cases):** Single-turn policy retrieval, deep citations, out-of-scope refusals.
2. **WorkWeek Operations (30 cases):** Balance checks, temporal date validations, contact updates.
3. **ServiceImmediately ITSM (30 cases):** Duplicate mitigation, P1 outage check, status transitions.
4. **Cross-System Workflows (25 cases):** Sequential multi-agent orchestration (UC-2.1, 2.2, 2.3) and rollbacks.
5. **Adversarial & Safety (25 cases):** Jailbreaks, prompt injections, SPII leak probes, toxic overrides evaluated against Model Armor.

---

## 10. Assumptions & Open Questions Tracker

### 10.1. Outstanding Design Decisions
| Item # | Open Question / Decision | Impact Area | Proposed Resolution / Options | Owner | Target Deadline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OQ-01** | Should OKF bundle updates be validated via pre-commit git hooks or automated Cloud Build CI pipelines? | Knowledge Base CI/CD | Recommend pre-commit `check_okf.py` validator paired with Cloud Build PR test. | Cloud AI Engineer | End of Week 2 |
| **OQ-02** | For medical leave (UC-2.2), should email delegation in ServiceImmediately require mandatory Manager approval before ticket execution? | HR Compliance & Privacy | Recommend adding a pre-execution confirmation prompt in Chat UI for MVP 1; integrate full manager approval in Phase 2. | HR Policy Lead | End of Week 3 |
| **OQ-03** | What is the final retention period for Cloud Logging audit trails containing masked user actions? | Compliance & FinOps | Set Cloud Logging bucket retention to 90 days with cold storage archiving to GCS. | Security Officer | End of Week 4 |

---

*End of Solution Design Document (Revision 3.0).*
