import os
import re
import json
import urllib.request
from typing import Optional, Any
from pathlib import Path

try:
    from google.adk.tools import VertexAiSearchTool, FunctionTool
except ImportError:
    class FunctionTool:
        def __init__(self, func, **kwargs):
            self.func = func
    class VertexAiSearchTool:
        def __init__(self, data_store_id: str, **kwargs):
            self.data_store_id = data_store_id

from agent.config import DATA_STORE_PATH, PROJECT_ID, WORKWEEK_MCP_URL, SERVICEIMMEDIATELY_MCP_URL, MCP_TOKEN

# 1. Authoritative Policy Corpus (for local development & offline fallback)
_LOCAL_POLICY_CORPUS = [
    {
        "section": "1.1",
        "title": "Outpatient & Hospitalization Sick Leave (Singapore)",
        "keywords": ["sick", "outpatient", "hospital", "hospitalization", "medical", "doctor", "mc", "illness"],
        "content": "1.1 Outpatient & Hospitalization Sick Leave (Singapore)\n- Outpatient Sick Leave: Employees receive 14 days of paid outpatient sick leave per calendar year, paid at 100% base salary.\n- Documentation Rule: Sick leave exceeding 2 consecutive days requires a certified Medical Certificate (MC) from a registered doctor submitted within 48 hours.\n- Hospitalization Leave: 46 work days of paid hospitalization leave per year for inpatient stays and day surgeries.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "1.2",
        "title": "Paid Vacation Leave (Singapore)",
        "keywords": ["vacation", "annual", "pto", "holiday", "accrual", "years", "service", "booking"],
        "content": "1.2 Paid Vacation Leave (Singapore)\n- Accrual Tier Matrix:\n  * 1 to 6 years of service: 20 days per year.\n  * 7 to 10 years of service: 21 days per year.\n  * 11+ years of service: 22 days per year.\n- Booking Rule: Must be booked at least 15 days in advance with manager approval.\n- Carryover: Unused days carry over for exactly 1 year.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "1.3",
        "title": "Parental & Childcare Leave",
        "keywords": ["parental", "maternity", "paternity", "childcare", "baby", "children", "infant"],
        "content": "1.3 Parental & Childcare Leave (Singapore)\n- Maternity Leave: 16 weeks of paid maternity leave for eligible female employees.\n- Paternity Leave: 4 weeks of government-paid paternity leave.\n- Childcare Leave: 6 days of paid childcare leave per year for parents with children aged under 7 years.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "3.1",
        "title": "Bereavement & Compassionate Leave",
        "keywords": ["bereavement", "compassionate", "death", "funeral", "grief", "loss", "family"],
        "content": "3.1 Bereavement & Compassionate Leave\n- Duration: Up to 4 weeks (20 work days) of paid bereavement leave for the loss of a close loved one (spouse, child, parent, sibling).\n- Flexibility: Can be taken continuously or in intermittent blocks within 12 months of the loss.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "4.3",
        "title": "Host Gifts & Entertainment Guidelines",
        "keywords": ["gift", "host", "friend", "lodging", "travel", "gift card", "cash", "expense"],
        "content": "4.3 Host Gifts & Entertainment Guidelines\n- Host Gifts: When staying with friends/family during business travel in lieu of a hotel, employees may expense non-cash host gifts up to US $50 per day.\n- Strictly Prohibited: Cash or gift card host gifts are strictly prohibited under company anti-bribery and expense compliance rules.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "4.4",
        "title": "Business Travel Meals & Incidental Expenses",
        "keywords": ["meal", "meals", "food", "dinner", "breakfast", "lunch", "per diem", "receipts", "travel"],
        "content": "4.4 Business Travel Meals & Incidental Expenses\n- Daily Meal Cap: Actual incurred meal expenses are reimbursable up to US $120 per day on global business trips.\n- Policy Condition: Reimbursement requires itemized receipts; this is an expense reimbursement cap, not an automatic per diem.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "5.4",
        "title": "Remote Work Home Office Equipment Allowance",
        "keywords": ["remote", "wfh", "telework", "equipment", "monitor", "display", "chair", "desk", "allowance"],
        "content": "5.4 Remote Work Home Office Equipment Allowance\n- Equipment Allowance: Full-time remote and designated hybrid employees are eligible for a $500 USD allowance for ergonomic home office equipment (monitors, chairs, peripherals).\n- Procurement: Equipment requests must be ordered through ServiceImmediately under Ticket Category: 'Facilities' with a verified remote shipping address.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    },
    {
        "section": "5.5",
        "title": "Relocation Allowance, Badging & ITSM Ticket Lifecycle",
        "keywords": ["relocation", "london", "move", "badging", "badge", "itsm", "lifecycle", "state", "closed", "ticket"],
        "content": "5.5 Relocation Allowance, Badging & ITSM Ticket Lifecycle\n- Relocation Allowance: Employees transferring to international offices (such as London HQ) receive up to $10,000 USD relocation allowance. Transferring employees must open a Facilities ticket (Priority: '3 - Moderate') for destination building badging.\n- ITSM Ticket State Machine: All service tickets must progress sequentially through standard operational states (New → In Progress → Resolved → Closed). Bypassing intermediate states (e.g. New directly to Closed) or modifying Closed tickets is prohibited.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    }
]

def search_hr_policies(query: str, region_filter: str = "Singapore") -> list[dict[str, Any]]:
    """
    Performs semantic search across enterprise HR and IT policy documents in Vertex AI Search.
    """
    # 1. Live Google Cloud Vertex AI Search Datastore Execution
    try:
        from google.cloud import discoveryengine_v1 as discoveryengine
        client = discoveryengine.SearchServiceClient()
        request = discoveryengine.SearchRequest(
            serving_config=f"{DATA_STORE_PATH}/servingConfigs/default_search",
            query=query,
            page_size=3
        )
        response = client.search(request)
        results = []
        for res in response.results:
            doc = res.document
            data = doc.derived_struct_data or {}
            results.append({
                "title": data.get("title", "Singapore Policy Handbook"),
                "snippet": data.get("snippets", [{}])[0].get("snippet", ""),
                "section": data.get("section", "General"),
                "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
            })
        if results:
            return results
    except Exception:
        pass

    # 2. Local semantic policy search fallback
    q_tokens = set(re.findall(r"\w+", query.lower()))
    best_match = None
    best_score = -1

    for doc in _LOCAL_POLICY_CORPUS:
        score = 0
        doc_tokens = set(re.findall(r"\w+", (doc["title"] + " " + doc["content"]).lower()))
        for kw in doc.get("keywords", []):
            if kw in query.lower():
                score += 3
        overlap = q_tokens.intersection(doc_tokens)
        score += len(overlap)

        if score > best_score:
            best_score = score
            best_match = doc

    if best_match:
        return [{
            "section": best_match["section"],
            "title": best_match["title"],
            "content": best_match["content"],
            "source_url": best_match["source_url"]
        }]

    return [{
        "section": "General",
        "title": "Singapore Employee Policy Handbook",
        "content": "Refer to the Altostrat Employee Policy Handbook for specific guidelines.",
        "source_url": "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M"
    }]

policy_search_tool = FunctionTool(
    func=search_hr_policies
)

# 2. FastMCP Client Helpers (for app.py UI server & evaluation scripts)
def call_fastmcp_tool(base_url: str, name: str, arguments: dict, token: str = MCP_TOKEN) -> Optional[dict]:
    """Invokes a tool on a remote FastMCP server over JSON-RPC 2.0."""
    call_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments
        }
    }
    try:
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/",
            data=json.dumps(call_data).encode("utf-8"),
            headers={"X-MCP-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", {})
    except Exception:
        pass
    return None

def read_fastmcp_resource(base_url: str, uri: str, token: str = MCP_TOKEN) -> Optional[dict]:
    """Reads a resource on a remote FastMCP server via resources/read."""
    req_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/read",
        "params": {"uri": uri}
    }
    try:
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/",
            data=json.dumps(req_data).encode("utf-8"),
            headers={"X-MCP-Token": token, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                contents = data.get("result", {}).get("contents", [])
                if contents and "text" in contents[0]:
                    return json.loads(contents[0]["text"])
    except Exception:
        pass
    return None
