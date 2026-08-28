# Implementation Plan: Semantic Knowledge Retrieval Strategy via Vertex AI Search

## 1. Goal Description
Evaluate and formalize the semantic knowledge retrieval architecture for the Enterprise HR Multi-Agent System across corporate HR policy documents (Leave Policies, Remote Work & Equipment, Travel & Expense Reimbursements, Code of Conduct). Document the selection of **Google Cloud Vertex AI Search (Enterprise Datastore on GCS)** as the authoritative semantic search engine and define its integration into the multi-agent system.

---

## 2. Architectural Selection: Google Cloud Vertex AI Search

To deliver high-accuracy, natural-language semantic retrieval without manual chunk management or brittle keyword matching, the enterprise architecture standardizes on **Google Cloud Vertex AI Search (Enterprise Datastore)**.

```
+---------------------------------------------------------------------------------------------------------------+
|                                      VERTEX AI SEARCH POLICY RETRIEVAL TIER                                   |
+---------------------------------------------------------------------------------------------------------------+
|                                                                                                               |
|  [Authoritative Corporate Documents] (Singapore Policy Handbook, PDFs, Docs, Markdown)                      |
|         │                                                                                                     |
|         ▼ Automated Ingestion & Cloud Storage Sync                                                            |
|  [Google Cloud Storage Bucket]: `gs://<project>-hr-policies/raw_docs/`                                        |
|         │                                                                                                     |
|         ▼ Auto-Indexing & Layout-Aware Semantic Parsing                                                       |
|  [Vertex AI Search Datastore] (`hr-policy-datastore`)                                                          |
|    ├── Dense Vector Embeddings (`text-embedding-005` / Multilingual Gecko)                                    |
|    ├── Hybrid Semantic + Lexical Matcher with Google Neural Re-Ranking                                        |
|    └── Metadata Faceting: `region: "Singapore"`, `category: "Time Off"`, `effective_date: "2026"`             |
|         ▲                                                                                                     |
|         │ Semantic Tool Call: `policy_search_tool(query="wfh equipment allowance", region="SG")`              |
|         │ Returns: Extractive answer segments, snippet grounding, and exact document title/URL citations      |
|  [Agents]: Main Concierge Agent & WorkWeek Specialist Agent                                                   |
|                                                                                                               |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 3. Comparative Evaluation Matrix

| Architectural Dimension | Vertex AI Search (Enterprise Datastore) | Legacy Keyword Matching / Manual Frontmatter | Verdict |
| :--- | :--- | :--- | :--- |
| **Semantic Comprehension** | **High:** Understands natural synonyms, intent, and complex paraphrasing (e.g. *"grief leave for parent"* $\rightarrow$ *Section 3.1 Bereavement Leave*). | **Low:** Requires exact keyword or synonym dictionary matches. | 🏆 **Vertex AI Search** |
| **Document Ingestion** | **Zero Manual Formatting:** Ingests raw PDFs, Google Docs, Markdown, and HTML with layout-aware table and header parsing. | **High Manual Effort:** Requires manual markdown conversion and YAML frontmatter tagging. | 🏆 **Vertex AI Search** |
| **Retrieval Accuracy** | **Hybrid + Neural Re-ranking:** Combines BM25 lexical precision with dense vector embeddings and Google's production neural re-ranker. | Static string overlap or basic TF-IDF without re-ranking. | 🏆 **Vertex AI Search** |
| **Attribution & Footnotes** | **Exact Snippet Grounding:** Returns extractive segments, verbatim paragraph context, document titles, and source URLs. | Relies on manually embedded frontmatter URLs. | 🏆 **Vertex AI Search** |
| **Operational Maintenance** | **Fully Managed Serverless:** $0 vector database VM maintenance, auto-indexes on GCS file changes. | Requires maintaining local file parsers and cache invalidation. | 🏆 **Vertex AI Search** |

---

## 4. Multi-Agent Integration Pattern (Option 2: Autonomous Specialist Access)

Both the **Root Concierge Agent** and the **WorkWeek Specialist Agent** are directly equipped with `policy_search_tool`:

```python
from google.adk.tools import VertexAiSearchTool

# Connect to the managed Vertex AI Search Datastore
policy_search_tool = VertexAiSearchTool(
    data_store_id="projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/hr-policy-datastore"
)
```

### Execution Responsibilities:
1. **Concierge Agent (General Q&A):** Resolves standalone policy questions (e.g., *"What is the policy on host gifts when traveling?"*) in a single turn with grounded citations.
2. **WorkWeek Specialist (Autonomous Policy Validation):** When processing transactional leave bookings (e.g., *"Add 5 days sick leave"*), the specialist directly queries `policy_search_tool` to verify rules (e.g., Singapore Section 1.1: Sick leave $>2$ days requires a Medical Certificate within 48h) before calling FastMCP `request_time_off`.

---

## 5. FinOps & Sizing

* **Query Volume:** 25,000 policy searches/month for 5,000 active employees.
* **Pricing Rate:** \$2.00 per 1,000 queries.
* **Estimated Cost:** **\$50.00 / month** (\$0.01 / employee / month).
