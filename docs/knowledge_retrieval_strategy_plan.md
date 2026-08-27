# Implementation Plan: Knowledge Retrieval Strategy (OKF vs. RAG)

## Goal Description
Evaluate and determine the optimal knowledge retrieval architecture for the Enterprise HR Multi-Agent System given a **limited, bounded set of corporate HR policy documents** (e.g., Leave Policies, Remote Work Guidelines, Expense Policies, Code of Conduct). Compare **Open Knowledge Format (OKF)** against **Traditional Retrieval-Augmented Generation (RAG via Vertex AI Search)** and propose an implementation plan for the SDD.

---

## User Review Required

> [!IMPORTANT]
> **Key Architectural Trade-Off:**
> - **Open Knowledge Format (OKF):** Converts the limited policy corpus into structured, version-controlled Markdown concept files with YAML frontmatter metadata (`knowledge/` bundle). The agent uses deterministic `list_concepts()` and `read_concept()` tool calls. Eliminates vector search noise, eliminates chunk truncation, provides 100% deterministic grounding, and incurs $0 search infrastructure fees.
> - **Traditional RAG (Vertex AI Search):** Ingests raw PDFs into Vertex AI Search with vector chunking and dense embeddings. Requires less upfront document reformatting, but introduces chunk boundary fragmentation and ongoing search API query costs.

---

## Comparative Evaluation Matrix

| Architectural Dimension | Open Knowledge Format (OKF) | Traditional RAG (Vertex AI Search) | Recommendation for Limited Docs |
| :--- | :--- | :--- | :--- |
| **Corpus Scale & Fit** | Tailored for **bounded, curated enterprise knowledge** (5–50 documents / ~100–150 modular concept files). | Designed for **massive, unbounded document lakes** (thousands of unstructured files). | 🏆 **OKF** |
| **Retrieval Fidelity** | **100% Deterministic:** Agent inspects frontmatter metadata (title, description, tags) and reads complete, intact concept markdown without chunk boundaries. | **Probabilistic:** Vector cosine similarity on 500-token chunks; risks splitting conditions across chunk boundaries. | 🏆 **OKF** |
| **Citation Precision** | **Exact & Verifiable:** Explicit frontmatter provenance (`sources`, `resource`, `section`) and markdown footnotes (`[^fn1]`). | Extractive text segments with probabilistic page metadata. | 🏆 **OKF** |
| **FinOps & Infra Cost** | **$0 Search Infra Cost:** Knowledge bundle lives in local container directory or Cloud Storage; zero embedding or vector indexing fees. | Incurs Vertex AI Search indexing fees ($/GiB/mo) + query fees ($/1K search ops). | 🏆 **OKF** |
| **Governance & GitOps** | **Knowledge-as-Code:** HR policies live in Git; changes are tracked via Pull Requests, line-by-line diffs, and `stale_after` freshness metadata. | Unstructured PDFs managed in Cloud Storage buckets; opaque indexing. | 🏆 **OKF** |
| **Authoring Effort** | Requires initial conversion of HR PDFs into structured Markdown concept files with YAML frontmatter. | Low upfront effort: Upload raw PDF files directly. | ⚖️ **RAG** (if zero document curation is desired) |

---

## Architectural Recommendation: **Adopt OKF as Primary Strategy**

For a limited policy corpus (where the total number of policies is bounded and known), **Open Knowledge Format (OKF)** is overwhelmingly superior to vector RAG:

```mermaid
flowchart TD
    subgraph OKF_Pipeline ["Open Knowledge Format (OKF) Execution"]
        UserQuery["Employee: 'How many days of bereavement leave do I get?'"]
        Concierge["Concierge Agent (Gemini 3.5 Flash)"]
        
        ListTool["list_concepts() Tool\n(Scans YAML frontmatter in knowledge/ bundle)"]
        ReadTool["read_concept('01-paid-time-off/bereavement') Tool\n(Parses complete markdown concept & citations)"]
        
        BundleStore[("OKF Knowledge Bundle (Git / Local)\n* 01-paid-time-off/\n* 02-expenses/\n* 03-remote-work/")]
        
        UserQuery --> Concierge
        Concierge -->|Step 1: Discover Concept| ListTool
        ListTool <--> BundleStore
        ListTool -->>|Returns matched concept_id| Concierge
        Concierge -->|Step 2: Read Full Concept| ReadTool
        ReadTool <--> BundleStore
        ReadTool -->>|Returns intact policy text + citations| Concierge
        Concierge -->>|100% Grounded Answer with Citations| EmployeeResponse["Grounded Response with Clickable Footnotes"]
    end
```

### Why OKF Solves Core RAG Failure Modes in HR Policies:
1. **No Fragmented Policy Clauses:** In HR policies, conditions are tightly coupled (e.g., *"Bereavement leave is 5 days for immediate family, 3 days for extended family, and requires manager sign-off if travel exceeds 500 miles"*). RAG chunking frequently cuts across these sentences; OKF preserves the entire concept as a single atomic unit.
2. **Deterministic Two-Step Progressive Disclosure:**
   - `list_concepts()`: Returns a compact YAML list of available policy concepts (~150 tokens), allowing the LLM to pick the exact concept ID.
   - `read_concept(concept_id)`: Ingests the exact targeted policy markdown file.
3. **Built-in Provenance & Freshness:** OKF concepts carry `verified: {by: "hr-policy-team", at: "2026-08-01"}` and `stale_after: "2027-01-01"`, enabling automated auditing for outdated policies.

---

## Proposed Changes to System Design Document (SDD)

### 1. Update Knowledge Layer in Architecture (Section 1.3 & 3.2)
- Replace generic Vertex AI Search with the **OKF Knowledge Engine**:
  - `knowledge/` directory bundle structured by HR domains (`01-leave-policies/`, `02-remote-work/`, `03-expenses/`, `04-code-of-conduct/`).
  - Tools equipped on Concierge: `list_concepts()` and `read_concept(concept_id)`.

### 2. Update Tool Signatures (Section 5.1)
```python
def list_concepts(domain: Optional[str] = None) -> list[dict]:
    """Lists available HR policy concepts with title, description, and tags from YAML frontmatter."""
    ...

def read_concept(concept_id: str) -> dict:
    """Reads the full markdown body, metadata, and citation sources for a specific concept."""
    ...
```

### 3. Update FinOps (Section 6)
- Remove recurring Vertex AI Search query fees ($8.00 / 1K queries), further lowering monthly operational TCO.

---

## Verification Plan

### Automated Tests
1. Conformance test of OKF bundle:
   ```bash
   uv run python knowledge/check_okf.py knowledge/
   ```
2. Accuracy & Grounding eval across 50 golden policy benchmark questions:
   ```bash
   agents-cli eval run --dataset tests/eval/datasets/policy_benchmark.json
   ```

### Manual Verification
1. Verify that `list_concepts()` returns all available HR topics without loading file bodies.
2. Test complex policy questions (e.g., bereavement leave, host gifts expense rules) and verify zero hallucination with exact footnote citations.
