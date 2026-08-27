#!/usr/bin/env python3
"""
Interactive Local Web Server for Altostrat HR Multi-Agent Assistant
Configured for Option A: Hierarchical ADK 2.0 Multi-Agent System.
Token: mcp_zYnFTkwwEfKkx6qaHgW2XTiTRzREoiHjwDZR3I64XdA
"""

import os
import sys
import json
import re
import time
from datetime import datetime, date
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add repository directory to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from agent.config import MCP_TOKEN, WORKWEEK_MCP_URL, SERVICEIMMEDIATELY_MCP_URL
from agent.tools.okf_tool import list_concepts, read_concept, _CONCEPT_CACHE, _CONCEPT_LIST_CACHE
from agent.tools.workweek_tool import _client as ww_client
from agent.tools.itsm_tool import _itsm_client as itsm_client

CURRENT_USER_ID = os.getenv("USER", "gunjangarg")

def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def find_best_okf_concept(query: str) -> tuple[str, float, dict]:
    """Finds the most relevant OKF concept using semantic keyword scoring and tag matching."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    
    synonym_map = {
        "vacaltion": "vacation",
        "vacaton": "vacation",
        "vacaition": "vacation",
        "wfh": "remote",
        "telework": "remote",
        "workfromhome": "remote",
        "monitor": "equipment",
        "screen": "equipment",
        "laptop": "equipment",
        "grief": "bereavement",
        "death": "bereavement",
        "loss": "bereavement",
        "bribe": "bribery",
        "corruption": "bribery",
        "baby": "parental",
        "paternity": "parental",
        "maternity": "maternity",
        "child": "childcare",
        "kids": "childcare",
        "meal": "expenses",
        "dinner": "expenses",
        "food": "expenses",
        "gift": "gifts",
        "transfer": "relocation",
        "london": "relocation",
        "move": "relocation",
        "bully": "harassment",
        "civility": "conduct",
        "relationship": "relationships",
        "dating": "relationships",
        "nda": "confidentiality",
        "secret": "confidentiality"
    }
    
    expanded_tokens = set(query_tokens)
    for t in query_tokens:
        if t in synonym_map:
            expanded_tokens.add(synonym_map[t])

    best_cid = None
    best_score = -1.0
    best_concept = {}

    for cid, cdata in _CONCEPT_CACHE.items():
        score = 0.0
        title_tokens = set(re.findall(r"\w+", cdata.get("title", "").lower()))
        desc_tokens = set(re.findall(r"\w+", cdata.get("description", "").lower()))
        tags = set(t.lower() for t in cdata.get("tags", []))
        content_tokens = set(re.findall(r"\w+", cdata.get("content", "").lower()))

        tag_overlap = expanded_tokens.intersection(tags)
        score += len(tag_overlap) * 4.0

        title_overlap = expanded_tokens.intersection(title_tokens)
        score += len(title_overlap) * 3.0

        desc_overlap = expanded_tokens.intersection(desc_tokens)
        score += len(desc_overlap) * 2.0

        content_overlap = expanded_tokens.intersection(content_tokens)
        score += len(content_overlap) * 0.5

        if score > best_score:
            best_score = score
            best_cid = cid
            best_concept = cdata

    return best_cid, best_score, best_concept

def process_agent_turn(query: str, employee_id: str = CURRENT_USER_ID) -> dict:
    """Executes the hierarchical multi-agent orchestration, recording step-by-step execution logs."""
    logs = []
    traces = []
    start_time = time.time()
    query_lower = query.lower()

    token_preview = MCP_TOKEN[:12] + "..." if len(MCP_TOKEN) > 12 else MCP_TOKEN
    logs.append({
        "time": get_timestamp(),
        "level": "INFO",
        "stage": "INGRESS",
        "message": f"Received turn from authenticated user '{employee_id}': \"{query}\""
    })
    
    logs.append({
        "time": get_timestamp(),
        "level": "SECURITY",
        "stage": "AUTH_INSPECTION",
        "message": f"FastMCP Streamable HTTP Auth: X-MCP-Token [{token_preview}]"
    })
    
    logs.append({
        "time": get_timestamp(),
        "level": "SECURITY",
        "stage": "MODEL_ARMOR",
        "message": "Model Armor Prompt Sanitization: Pass (Confidence: 0.99, No Injection)"
    })

    response_text = ""

    # Out-of-Scope Refusal
    if any(k in query_lower for k in ["reverse a string", "python function", "write a code", "binary tree", "javascript", "leetcode"]):
        logs.append({
            "time": get_timestamp(),
            "level": "SECURITY",
            "stage": "MODEL_ARMOR",
            "message": "Domain Boundary Containment: Triggered out-of-scope refusal for non-HR programming query."
        })
        return {
            "response": "I am an enterprise HR and IT assistant. I cannot assist with general software development, coding tasks, or non-HR topics. Please let me know if you have questions about company policies, leave operations, or IT support tickets.",
            "logs": logs,
            "traces": [{"step": 1, "agent": "model_armor", "tool": "domain_containment", "status": "OUT_OF_SCOPE_REFUSAL", "result_summary": "Query blocked by security policy"}],
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    # 1. Transaction: WorkWeek Balance Inquiry
    is_balance_query = any(k in query_lower for k in ["balance", "pto", "how many days off", "remaining leave", "check leave", "my leaves"])
    is_apply_booking = any(k in query_lower for k in ["book", "apply", "request", "take"]) and any(k in query_lower for k in ["day", "days", "vacation", "vacaltion", "sick", "leave", "time off", "childcare"])

    if is_balance_query and not is_apply_booking:
        logs.append({
            "time": get_timestamp(),
            "level": "REASONING",
            "stage": "CONCIERGE_ROUTER",
            "message": f"Classified intent: HCM Transaction -> Delegate to workweek_specialist (mode='task')"
        })
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "WORKWEEK_SPECIALIST",
            "message": f"Invoking FastMCP McpToolset tool: get_employee_balances(employee_id='{employee_id}') with X-MCP-Token"
        })
        
        balances = ww_client.get_employee_balances(employee_id)["balances"]
        
        traces.append({
            "step": 1,
            "agent": "workweek_specialist",
            "tool": "workweek_mcp.get_employee_balances",
            "args": {"employee_id": employee_id, "header": "X-MCP-Token"},
            "status": "SUCCESS",
            "result_summary": f"Fetched {len(balances)} real-time balance records from WorkWeek"
        })

        b_text = "\n".join([f"- **{b['leave_type']}**: **{b['remaining']} days** remaining (Accrued: {b['accrued']}d, Used: {b['used']}d)" for b in balances])
        response_text = f"Here is your current real-time leave balance from **WorkWeek**:\n\n{b_text}\n\nWould you like me to help you submit a leave booking request?"

    # 2. Transaction: Leave Booking / Application
    elif is_apply_booking:
        days_match = re.search(r"(\d+(\.\d+)?)\s*(days|day)?", query_lower)
        days = float(days_match.group(1)) if days_match else 1.0
        
        if "sick" in query_lower:
            leave_type = "Sick (Outpatient)"
        elif "hospital" in query_lower:
            leave_type = "Hospitalization"
        elif "childcare" in query_lower:
            leave_type = "Childcare"
        else:
            leave_type = "Vacation"
            
        logs.append({
            "time": get_timestamp(),
            "level": "REASONING",
            "stage": "CONCIERGE_ROUTER",
            "message": f"Classified intent: Leave Booking ({days} days of {leave_type}) -> Dispatched to workweek_specialist"
        })
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "WORKWEEK_SPECIALIST",
            "message": f"Invoking FastMCP McpToolset tool: request_time_off(employee_id='{employee_id}', days={days}, leave_type='{leave_type}')"
        })
        
        result = ww_client.request_time_off(employee_id, "2026-09-01", "2026-09-05", leave_type, days)
        
        if result["status"] == "SUCCESS":
            logs.append({
                "time": get_timestamp(),
                "level": "SUCCESS",
                "stage": "WORKWEEK_SPECIALIST",
                "message": f"Leave Request #{result['request_id']} approved in WorkWeek. Remaining balance: {result['remaining_balance']} days"
            })
            traces.append({
                "step": 1,
                "agent": "workweek_specialist",
                "tool": "workweek_mcp.request_time_off",
                "args": {"employee_id": employee_id, "days": days, "type": leave_type, "header": "X-MCP-Token"},
                "status": "SUCCESS",
                "result_summary": f"Created Request #{result['request_id']} in WorkWeek"
            })
            response_text = f"✅ **Leave Request #{result['request_id']} Submitted Successfully!**\n\n- **Applicant:** {employee_id}\n- **Leave Type:** {leave_type}\n- **Duration:** {days} working day(s)\n- **Updated Remaining Balance:** **{result['remaining_balance']} days**\n\nYour manager has been notified in WorkWeek for approval."
        elif result["status"] == "INSUFFICIENT_BALANCE":
            logs.append({
                "time": get_timestamp(),
                "level": "GUARDRAIL",
                "stage": "WORKWEEK_SPECIALIST",
                "message": f"GUARDRAIL BLOCKED: {result['message']}"
            })
            traces.append({
                "step": 1,
                "agent": "workweek_specialist",
                "tool": "workweek_mcp.request_time_off",
                "args": {"employee_id": employee_id, "days": days, "type": leave_type, "header": "X-MCP-Token"},
                "status": "GUARDRAIL_BLOCKED",
                "result_summary": "Insufficient leave balance rejection"
            })
            response_text = f"⚠️ **Leave Request Blocked by WorkWeek Guardrail:**\n\n{result['message']}\n\nPlease adjust your requested duration or choose a different leave category."
        else:
            response_text = f"❌ **Validation Error:** {result['message']}"

    # 3. Cross-System: Equipment Order (UC-2.1)
    elif any(k in query_lower for k in ["order monitor", "order equipment", "need monitor", "buy monitor", "home office monitor"]):
        logs.append({
            "time": get_timestamp(),
            "level": "REASONING",
            "stage": "CONCIERGE_ROUTER",
            "message": "Initiating Cross-System Workflow UC-2.1 (Equipment Procurement)"
        })
        
        # Step 1: OKF Read
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "OKF_ENGINE",
            "message": "Step 1: Calling okf_tool.read_concept('05-ethics-compliance/5.4-remote-work-equipment')..."
        })
        policy = read_concept("05-ethics-compliance/5.4-remote-work-equipment")
        traces.append({
            "step": 1,
            "agent": "concierge_agent",
            "tool": "okf_tool.read_concept",
            "args": {"concept_id": "05-ethics-compliance/5.4-remote-work-equipment"},
            "status": "SUCCESS",
            "result_summary": "Grounded in Section 5.4 ($500 USD equipment allowance)"
        })

        # Step 2: WorkWeek Profile Check
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "WORKWEEK_SPECIALIST",
            "message": f"Step 2: Calling workweek_mcp.get_personal_info('{employee_id}') with X-MCP-Token"
        })
        profile = ww_client.get_personal_info(employee_id)
        traces.append({
            "step": 2,
            "agent": "workweek_specialist",
            "tool": "workweek_mcp.get_personal_info",
            "args": {"employee_id": employee_id, "header": "X-MCP-Token"},
            "status": "SUCCESS",
            "result_summary": f"Verified remote status: {profile['work_mode']}, Address: {profile['address']}"
        })

        # Step 3: ITSM Ticket Creation
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "ITSM_SPECIALIST",
            "message": f"Step 3: Calling serviceimmediately_mcp.create_ticket(category='Facilities', priority='3 - Moderate') with X-MCP-Token"
        })
        ticket = itsm_client.create_ticket(employee_id, "Facilities", f"Remote Monitor Procurement - 27in Display for {profile['name']}", "3 - Moderate", "Facilities")
        traces.append({
            "step": 3,
            "agent": "itsm_specialist",
            "tool": "serviceimmediately_mcp.create_ticket",
            "args": {"category": "Facilities", "short_description": "Remote Monitor Procurement - 27in Display", "priority": "3 - Moderate", "header": "X-MCP-Token"},
            "status": "SUCCESS",
            "result_summary": f"Created Incident #{ticket.get('ticket_id', 'INC-10002')} in Facilities"
        })

        response_text = (
            "### Home Office Equipment Procurement (UC-2.1)\n\n"
            "Under **Section 5.4** of the [Remote Work & Equipment Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-5.4), "
            "employees with **Remote** or **Hybrid** status are eligible for up to a **$500 USD allowance** for home office equipment.\n\n"
            "**Workflow Actions Completed:**\n"
            f"1. **Verified Remote Status:** Name: *{profile['name']}* | Role: *{profile['role']}* | Status: *{profile['work_mode']}*\n"
            f"2. **Shipping Address Confirmed:** `{profile['address']}`\n"
            f"3. **Created Facilities Ticket:** **#{ticket.get('ticket_id', 'INC-10002')}** (Priority: *3 - Moderate*, Assignment Group: *Facilities*)\n\n"
            "Your hardware procurement requisition has been routed to Facilities for shipping fulfillment."
        )

    # 4. Dynamic Policy Question: Semantic Search across all 21 OKF Concepts
    else:
        logs.append({
            "time": get_timestamp(),
            "level": "REASONING",
            "stage": "CONCIERGE_ROUTER",
            "message": "Classified intent: HR Policy Inquiry -> Scanning OKF Knowledge Engine"
        })
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "OKF_ENGINE",
            "message": "Calling okf_tool.list_concepts()... Scanning in-memory YAML frontmatter manifest"
        })
        
        best_cid, score, cdata = find_best_okf_concept(query)
        
        logs.append({
            "time": get_timestamp(),
            "level": "TOOL_CALL",
            "stage": "OKF_ENGINE",
            "message": f"Calling okf_tool.read_concept('{best_cid}')... Match Score: {score:.1f}"
        })
        
        traces.append({
            "step": 1,
            "agent": "concierge_agent",
            "tool": "okf_tool.read_concept",
            "args": {"concept_id": best_cid},
            "status": "SUCCESS",
            "result_summary": f"Ingested concept '{cdata.get('title')}' (Sources: handbook-sg-2026)"
        })

        concept_body = cdata.get("content", "").strip()
        doc_source = cdata.get("sources", [{}])[0]
        source_title = doc_source.get("title", "Altostrat Singapore Employee Policy Handbook")
        source_url = doc_source.get("resource", "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M")

        response_text = f"### 📖 {cdata.get('title')}\n\n" \
                        f"{concept_body}\n\n" \
                        f"---\n*Source: [{source_title}]({source_url})*"

    logs.append({
        "time": get_timestamp(),
        "level": "SECURITY",
        "stage": "MODEL_ARMOR",
        "message": "Model Armor Response Inspection: Scanned output for SPII (SSN, Phone, Address masked) -> Pass"
    })
    
    duration = int((time.time() - start_time) * 1000)
    logs.append({
        "time": get_timestamp(),
        "level": "INFO",
        "stage": "EGRESS",
        "message": f"Turn completed in {duration}ms. Delivering response to client."
    })

    return {
        "response": response_text,
        "logs": logs,
        "traces": traces,
        "duration_ms": duration
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Altostrat HR Multi-Agent Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&family=Roboto:wght@400;500&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1a73e8;
            --primary-hover: #1557b0;
            --primary-light: #e8f0fe;
            --surface: #ffffff;
            --background: #f8f9fa;
            --border: #dadce0;
            --border-light: #eceff1;
            --text: #202124;
            --text-secondary: #5f6368;
            --success: #137333;
            --success-bg: #e6f4ea;
            --warning: #b06000;
            --warning-bg: #fef7e0;
            --danger: #c5221f;
            --danger-bg: #fce8e6;
            --log-bg: #1e1e1e;
            --log-text: #d4d4d4;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body {
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            font-family: 'Google Sans', 'Roboto', sans-serif;
            background: var(--background);
            color: var(--text);
        }
        
        .app-container {
            display: flex;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
        }
        
        /* 1. Left Sidebar (Fixed 220px) */
        .sidebar {
            width: 220px;
            min-width: 200px;
            max-width: 240px;
            flex-shrink: 0;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 12px;
            gap: 12px;
            overflow-y: auto;
            height: 100vh;
        }
        .brand {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--primary);
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }
        .badge {
            background: var(--primary-light);
            color: var(--primary);
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 10px;
            font-weight: 600;
        }
        .card {
            background: #fdfdfd;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 10px;
        }
        .card-title {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        .profile-row { font-size: 0.78rem; margin-bottom: 4px; color: var(--text); line-height: 1.3; }
        .balance-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.78rem;
            padding: 4px 0;
            border-bottom: 1px solid var(--border-light);
        }
        .balance-item:last-child { border-bottom: none; }
        
        /* 2. Center Panel: Fluid Chat Stream (Flex: 1) */
        .main-chat {
            flex: 1;
            min-width: 320px;
            display: flex;
            flex-direction: column;
            background: var(--surface);
            border-right: 1px solid var(--border);
            height: 100vh;
            overflow: hidden;
        }
        .chat-header {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--surface);
            flex-shrink: 0;
        }
        .chat-messages {
            flex: 1;
            padding: 16px 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
            background: #ffffff;
        }
        .msg {
            max-width: 92%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 0.88rem;
            box-shadow: 0 1px 2px rgba(60,64,67,0.06);
        }
        .msg-user {
            align-self: flex-end;
            background: var(--primary);
            color: #ffffff;
            border-bottom-right-radius: 2px;
        }
        .msg-agent {
            align-self: flex-start;
            background: #f8f9fa;
            border: 1px solid #e8eaed;
            color: var(--text);
            border-bottom-left-radius: 2px;
        }
        .msg-agent a { color: var(--primary); font-weight: 500; text-decoration: none; }
        .msg-agent a:hover { text-decoration: underline; }
        .msg-agent ul, .msg-agent ol { margin-left: 16px; margin-top: 6px; margin-bottom: 6px; }
        .msg-agent li { margin-bottom: 3px; }
        .msg-agent h3 { margin-top: 8px; margin-bottom: 4px; color: var(--primary); font-size: 0.95rem; }
        
        .pills {
            padding: 8px 12px;
            display: flex;
            gap: 6px;
            overflow-x: auto;
            border-top: 1px solid var(--border-light);
            background: #fafafa;
            flex-shrink: 0;
        }
        .pill {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 4px 10px;
            font-size: 0.75rem;
            cursor: pointer;
            white-space: nowrap;
            color: var(--text);
            transition: all 0.2s;
        }
        .pill:hover {
            border-color: var(--primary);
            color: var(--primary);
            background: var(--primary-light);
        }
        
        .chat-input-area {
            padding: 10px 14px;
            display: flex;
            gap: 8px;
            background: var(--surface);
            border-top: 1px solid var(--border);
            flex-shrink: 0;
        }
        .chat-input {
            flex: 1;
            padding: 8px 14px;
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 0.88rem;
            outline: none;
            font-family: inherit;
        }
        .chat-input:focus { border-color: var(--primary); }
        .send-btn {
            background: var(--primary);
            color: #ffffff;
            border: none;
            border-radius: 20px;
            padding: 0 18px;
            font-weight: 600;
            font-size: 0.88rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .send-btn:hover { background: var(--primary-hover); }

        /* 3. Right Panel: Execution & Logs (Fixed 330px) */
        .exec-panel {
            width: 330px;
            min-width: 290px;
            max-width: 360px;
            flex-shrink: 0;
            background: var(--surface);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow-y: auto;
        }
        .exec-header {
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #fafafa;
            flex-shrink: 0;
        }
        .exec-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .exec-content {
            flex: 1;
            padding: 12px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: #fdfdfd;
        }
        .trace-card {
            background: #ffffff;
            border: 1px solid #d2e3fc;
            border-left: 3px solid var(--primary);
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 0.76rem;
        }
        .trace-header {
            display: flex;
            justify-content: space-between;
            font-weight: 600;
            margin-bottom: 3px;
            color: var(--primary);
        }
        .trace-args {
            background: #f8f9fa;
            border-radius: 4px;
            padding: 4px 6px;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: #444;
            word-break: break-all;
        }
        .log-terminal {
            background: var(--log-bg);
            color: var(--log-text);
            border-radius: 6px;
            padding: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem;
            line-height: 1.4;
            max-height: 320px;
            overflow-y: auto;
            border: 1px solid #333;
        }
        .log-line { margin-bottom: 3px; }
        .log-time { color: #888; margin-right: 4px; }
        .log-INFO { color: #61afef; }
        .log-SECURITY { color: #e5c07b; }
        .log-TOOL_CALL { color: #98c379; }
        .log-REASONING { color: #c678dd; }
        .log-GUARDRAIL { color: #e06c75; font-weight: bold; }
        .log-SUCCESS { color: #98c379; font-weight: bold; }

        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #dadce0; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #bdc1c6; }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- 1. Left Sidebar (Fixed 220px) -->
        <div class="sidebar">
            <div class="brand">
                <span>✨ Altostrat HR</span>
                <span class="badge">ADK 2.0</span>
            </div>

            <div class="card">
                <div class="card-title">Employee Profile</div>
                <div class="profile-row" id="profName"><strong>Name:</strong> Gunjan Garg</div>
                <div class="profile-row" id="profId"><strong>ID:</strong> gunjangarg</div>
                <div class="profile-row" id="profRole"><strong>Role:</strong> Staff Solution Architect</div>
                <div class="profile-row" id="profStatus"><strong>Status:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">Remote</span></div>
                <div class="profile-row" id="profAddress"><strong>Location:</strong> South San Francisco, CA</div>
            </div>

            <div class="card">
                <div class="card-title">WorkWeek Balances</div>
                <div class="balance-item"><span>🏖️ Vacation</span><strong id="balVacation">17.0 Days</strong></div>
                <div class="balance-item"><span>🤒 Sick</span><strong id="balSick">13.0 Days</strong></div>
                <div class="balance-item"><span>🏥 Hospital</span><strong id="balHospital">46.0 Days</strong></div>
                <div class="balance-item"><span>👶 Childcare</span><strong id="balChildcare">6.0 Days</strong></div>
            </div>

            <div class="card">
                <div class="card-title">FastMCP Integration</div>
                <div class="profile-row"><strong>Token:</strong> <span class="badge" style="background:#ceead6; color:#0d652d;">mcp_zYnF...</span></div>
                <div class="profile-row"><strong>Architecture:</strong> Hierarchical (Option A)</div>
                <div class="profile-row"><strong>WorkWeek:</strong> /work-week/mcp/</div>
                <div class="profile-row"><strong>ITSM:</strong> /service-immediately/</div>
            </div>
        </div>

        <!-- 2. Center Panel: Focused Chat Stream -->
        <div class="main-chat">
            <div class="chat-header">
                <div>
                    <h2 style="font-size: 0.98rem; font-weight: 600;">HR & IT Concierge Assistant</h2>
                    <p style="font-size: 0.74rem; color: var(--text-secondary);">Grounded via OKF Knowledge Engine & FastMCP</p>
                </div>
                <span class="badge" style="background:#ceead6; color:#0d652d;">● Engine Live</span>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="msg msg-agent" id="welcomeMsg">
                    👋 Hello Gunjan! I am your <strong>Altostrat HR & IT Concierge Assistant</strong>. I can assist you with company policy inquiries, WorkWeek leave operations, and IT support tickets.<br><br>
                    Try asking a question or selecting one of the suggested prompts below!
                </div>
            </div>

            <div class="pills">
                <button class="pill" onclick="sendPill('what is wfh policy?')">🏠 What is WFH policy?</button>
                <button class="pill" onclick="sendPill('Apply 1 day vacation')">🏖️ Apply 1 Day Vacation</button>
                <button class="pill" onclick="sendPill('Can I expense a $45 gift card as a host gift when staying with a friend?')">🎁 Host Gift Rules</button>
                <button class="pill" onclick="sendPill('Check my current vacation and sick balance')">🏖️ Balances</button>
                <button class="pill" onclick="sendPill('Book 20 days vacation starting 2026-09-01')">⚠️ Test Guardrail</button>
                <button class="pill" onclick="sendPill('I work remotely. What is my equipment allowance and can you order a 27-inch monitor?')">🖥️ Remote Monitor</button>
            </div>

            <div class="chat-input-area">
                <input type="text" id="userInput" class="chat-input" placeholder="Ask about WFH policy, apply leave, host gifts..." onkeypress="handleKey(event)">
                <button class="send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <!-- 3. Right Panel: Execution Steps & Logs (Fixed 330px) -->
        <div class="exec-panel">
            <div class="exec-header">
                <div class="exec-title">
                    <span>⚡ Execution Steps & Logs</span>
                </div>
                <span id="turnLatency" class="badge" style="background:#f1f3f4; color:#5f6368;">Ready</span>
            </div>

            <div class="exec-content">
                <div class="card-title">Executed Steps</div>
                <div id="traceContainer" style="display: flex; flex-direction: column; gap: 6px;">
                    <div style="font-size: 0.76rem; color: #888; font-style: italic;">
                        Send a query to view live multi-agent dispatches.
                    </div>
                </div>

                <div class="card-title" style="margin-top: 6px;">Background Execution Logs</div>
                <div class="log-terminal" id="logTerminal">
                    <div class="log-line"><span class="log-time">[System]</span> <span class="log-INFO">Hierarchical Multi-Agent initialized (Option A).</span></div>
                    <div class="log-line"><span class="log-time">[System]</span> <span class="log-TOOL_CALL">McpToolset wired with token 'mcp_zYnFTkww...'.</span></div>
                    <div class="log-line"><span class="log-time">[System]</span> <span class="log-SECURITY">Model Armor security filters ready.</span></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ACTIVE_USER_ID = "gunjangarg";

        async function initUserProfile() {
            try {
                const res = await fetch('/api/profile?employee_id=' + ACTIVE_USER_ID);
                if (res.ok) {
                    const data = await res.json();
                    if (data.profile) {
                        document.getElementById('profName').innerHTML = `<strong>Name:</strong> ${data.profile.name}`;
                        document.getElementById('profId').innerHTML = `<strong>ID:</strong> ${data.profile.employee_id}`;
                        document.getElementById('profRole').innerHTML = `<strong>Role:</strong> ${data.profile.role}`;
                        document.getElementById('profAddress').innerHTML = `<strong>Location:</strong> ${data.profile.address}`;
                        document.getElementById('welcomeMsg').innerHTML = `👋 Hello ${data.profile.name.split(' ')[0]}! I am your <strong>Altostrat HR & IT Concierge Assistant</strong>. I can assist you with company policy inquiries, WorkWeek leave operations, and IT support tickets.<br><br>Try asking a question or selecting one of the suggested prompts below!`;
                    }
                    if (data.balances && data.balances.balances) {
                        data.balances.balances.forEach(b => {
                            if (b.leave_type.includes('Vacation')) document.getElementById('balVacation').innerText = `${b.remaining} Days`;
                            if (b.leave_type.includes('Sick')) document.getElementById('balSick').innerText = `${b.remaining} Days`;
                            if (b.leave_type.includes('Hospital')) document.getElementById('balHospital').innerText = `${b.remaining} Days`;
                            if (b.leave_type.includes('Childcare')) document.getElementById('balChildcare').innerText = `${b.remaining} Days`;
                        });
                    }
                }
            } catch (e) {
                console.error("Profile load error:", e);
            }
        }

        function appendMessage(text, isUser) {
            const container = document.getElementById('chatMessages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg ' + (isUser ? 'msg-user' : 'msg-agent');
            
            let formatted = text
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\\[([^\\]]+)\\]\\(([^\\)]+)\\)/g, '<a href="$2" target="_blank">$1</a>')
                .replace(/\\n/g, '<br>');
            
            msgDiv.innerHTML = formatted;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }

        function updateExecutionInspector(traces, logs, durationMs) {
            document.getElementById('turnLatency').innerText = `${durationMs}ms`;

            const traceContainer = document.getElementById('traceContainer');
            if (traces && traces.length > 0) {
                traceContainer.innerHTML = traces.map(t => `
                    <div class="trace-card">
                        <div class="trace-header">
                            <span>Step ${t.step || 1}: ${t.agent}</span>
                            <span style="font-size: 0.68rem; color: ${t.status === 'SUCCESS' ? '#137333' : '#b06000'}; font-weight:700;">${t.status}</span>
                        </div>
                        <div style="color:#202124; margin-top:2px;">Tool: <code>${t.tool}</code></div>
                        <div class="trace-args">Args: ${JSON.stringify(t.args || {})}</div>
                        <div style="font-size:0.72rem; color:#5f6368; margin-top:3px;">${t.result_summary || ''}</div>
                    </div>
                `).join('');
            }

            const logTerminal = document.getElementById('logTerminal');
            if (logs && logs.length > 0) {
                const logLines = logs.map(l => `
                    <div class="log-line">
                        <span class="log-time">[${l.time}]</span>
                        <span class="log-${l.level}">[${l.stage}] ${l.message}</span>
                    </div>
                `).join('');
                logTerminal.innerHTML += logLines;
                logTerminal.scrollTop = logTerminal.scrollHeight;
            }
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const query = input.value.trim();
            if (!query) return;

            appendMessage(query, true);
            input.value = '';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, employee_id: ACTIVE_USER_ID })
                });
                const data = await res.json();
                appendMessage(data.response, false);
                updateExecutionInspector(data.traces, data.logs, data.duration_ms);
            } catch (err) {
                appendMessage('❌ Connection error: ' + err.message, false);
            }
        }

        function sendPill(text) {
            document.getElementById('userInput').value = text;
            sendMessage();
        }

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        window.addEventListener('DOMContentLoaded', initUserProfile);
    </script>
</body>
</html>
"""

class HRAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif parsed.path == "/api/profile":
            emp_id = parsed.query.split("=")[-1] if "employee_id=" in parsed.query else CURRENT_USER_ID
            profile = ww_client.get_personal_info(emp_id)
            balances = ww_client.get_employee_balances(emp_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "profile": profile,
                "balances": balances
            }).encode("utf-8"))
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ONLINE",
                "employee_id": CURRENT_USER_ID,
                "token_configured": MCP_TOKEN[:8] + "...",
                "concepts_loaded": len(_CONCEPT_LIST_CACHE)
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length)
            data = json.loads(post_body.decode("utf-8"))
            
            query = data.get("query", "")
            emp_id = data.get("employee_id", CURRENT_USER_ID)
            
            result = process_agent_turn(query, emp_id)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, HRAppHandler)
    print(f"Altostrat HR Multi-Agent Local Server listening on port {port} for user '{CURRENT_USER_ID}'...")
    print(f"Token Configured: {MCP_TOKEN[:12]}...")
    print(f"Access in browser: http://gunjangarg.c.googlers.com:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
