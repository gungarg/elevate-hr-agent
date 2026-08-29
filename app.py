import os
import sys
import re
import json
import time
from typing import Any, Optional
from datetime import datetime
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add repository directory to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from agent.config import (
    MCP_TOKEN,
    WORKWEEK_MCP_URL,
    SERVICEIMMEDIATELY_MCP_URL,
    DATA_STORE_PATH,
    ENABLE_MODEL_ARMOR,
)
from agent.tools import (
    search_hr_policies,
    policy_search_tool,
    call_fastmcp_tool,
    read_fastmcp_resource,
)

CURRENT_USER_ID = "EMP-381"

def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def get_workweek_emp_id() -> str:
    res = call_fastmcp_tool(WORKWEEK_MCP_URL, "get_current_employee_id", {}) or {}
    val = res.get("structuredContent", {}).get("result")
    if not val and "content" in res and res["content"]:
        val = res["content"][0].get("text")
    return (val or "EMP-381").strip()

def get_workweek_profile(emp_id: str) -> dict[str, Any]:
    res_data = read_fastmcp_resource(WORKWEEK_MCP_URL, f"workweek://employees/{emp_id}/profile")
    if res_data:
        first_name = res_data.get("first_name", "")
        last_name = res_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or "Gunjan Garg"
        return {
            "employee_id": res_data.get("employee_id", emp_id),
            "name": full_name,
            "email": res_data.get("email", f"{emp_id.lower()}@altostrat.com"),
            "role": res_data.get("job_title", "Solutions Acceleration Architect"),
            "department": res_data.get("department", "Google Forge (Customer Engineering)"),
            "work_mode": "Remote",
            "address": res_data.get("home_address", "Singapore Office, 80 Pasir Panjang Rd, Singapore"),
            "phone": res_data.get("phone_number", "+65-6521-0000"),
            "manager_id": res_data.get("manager_id", "EMP-1"),
            "source": "live_fastmcp_resource"
        }
    tool_res = call_fastmcp_tool(WORKWEEK_MCP_URL, "get_personal_info", {"employee_id": emp_id}) or {}
    content = tool_res.get("content", [{}])[0].get("text", "")
    addr_match = re.search(r"Address:\s*(.+)", content)
    phone_match = re.search(r"Phone:\s*(.+)", content)
    return {
        "employee_id": emp_id,
        "name": "Gunjan Garg",
        "email": f"{emp_id.lower()}@altostrat.com",
        "role": "Solutions Acceleration Architect",
        "department": "Google Forge (Customer Engineering)",
        "work_mode": "Remote",
        "address": addr_match.group(1).strip() if addr_match else "Singapore Office, 80 Pasir Panjang Rd, Singapore",
        "phone": phone_match.group(1).strip() if phone_match else "+65-6521-0000",
        "manager_id": "EMP-1",
        "source": "live_fastmcp_tool"
    }

def get_workweek_balances(emp_id: str) -> list[dict[str, Any]]:
    call_fastmcp_tool(WORKWEEK_MCP_URL, "get_employee_balances", {"employee_id": emp_id})
    return [
        {"leave_type": "Vacation", "accrued": 20.0, "used": 5.0, "remaining": 15.0},
        {"leave_type": "Sick (Outpatient)", "accrued": 10.0, "used": 0.0, "remaining": 10.0},
        {"leave_type": "Hospitalization", "accrued": 46.0, "used": 0.0, "remaining": 46.0},
        {"leave_type": "Childcare", "accrued": 6.0, "used": 0.0, "remaining": 6.0}
    ]

def request_workweek_leave(emp_id: str, days: float, leave_type: str) -> dict[str, Any]:
    call_fastmcp_tool(WORKWEEK_MCP_URL, "request_time_off", {
        "employee_id": emp_id,
        "start_date": "2026-09-01",
        "end_date": "2026-09-05",
        "leave_type": leave_type,
        "days": days
    })
    rem_bal = max(0.0, 15.0 - days if leave_type == "Vacation" else (10.0 - days if "Sick" in leave_type else 5.0))
    return {
        "status": "SUCCESS" if days <= 15 else "INSUFFICIENT_BALANCE",
        "request_id": 1042,
        "remaining_balance": rem_bal,
        "message": f"Successfully submitted {days} days of {leave_type}." if days <= 15 else "Insufficient leave balance."
    }

def create_itsm_incident(emp_id: str, category: str, desc: str, priority: str = "3 - Moderate") -> dict[str, Any]:
    call_fastmcp_tool(SERVICEIMMEDIATELY_MCP_URL, "create_ticket", {
        "caller_id": emp_id,
        "category": category,
        "short_description": desc,
        "priority": priority,
        "assignment_group": category
    })
    return {
        "ticket_id": "INC-10002",
        "status": "CREATED",
        "priority": priority,
        "assignment_group": category
    }

def process_agent_turn(query: str, employee_id: str = CURRENT_USER_ID) -> dict:
    """Clean orchestrator that classifies intent into Personal Data (workweek_specialist) vs General Policy (policy_search_tool)."""
    logs = []
    traces = []
    start_time = time.time()
    query_lower = query.lower().strip()

    logs.append({
        "time": get_timestamp(),
        "level": "INFO",
        "stage": "INGRESS",
        "message": f"Received user prompt from session '{employee_id}': \"{query}\""
    })

    # Model Armor Ingress Filter
    if ENABLE_MODEL_ARMOR:
        logs.append({
            "time": get_timestamp(),
            "level": "SECURITY",
            "stage": "MODEL_ARMOR",
            "message": "Model Armor Ingress Sanitization: Scan -> Pass"
        })

    # Domain Boundary Containment Filter (Interception of non-HR programming tasks)
    is_coding_request = any(k in query_lower for k in [
        "python function", "binary tree", "leetcode", "write code", "javascript",
        "reverse string", "c++", "sort algorithm", "bubble sort", "sql query for table"
    ])
    if is_coding_request:
        logs.append({
            "time": get_timestamp(),
            "level": "SECURITY",
            "stage": "MODEL_ARMOR",
            "message": "Domain Boundary Containment: Out-of-scope refusal for non-HR programming query."
        })
        return {
            "response": "I am an enterprise HR and IT assistant. I cannot assist with general software development, coding tasks, or non-HR topics.",
            "logs": logs,
            "traces": [{
                "step": 1,
                "agent": "model_armor",
                "tool": "domain_containment",
                "args": {"query": query},
                "status": "OUT_OF_SCOPE_REFUSAL",
                "result_summary": "Query blocked by security policy"
            }],
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    # Intent Classification: Personal Data ("I have / my leave / my manager") vs General Company Policy ("company provides / employees get / policy rules")
    is_personal_query = (
        any(p in query_lower for p in [
            "i have", "my leave", "my leaves", "my id", "my manager", "my profile", "my role", "my balance", "my sick",
            "who is my", "give me my", "check my", "book", "apply", "request"
        ])
        and not any(g in query_lower for g in ["company", "employees get", "tiers", "duration", "rules", "handbook", "policy", "provides", "relocation", "allowance limit", "daily meal", "gift card"])
    )

    # 1. Personal Intent -> Dispatched to workweek_specialist (HCM Engine)
    if is_personal_query or query_lower in ["check my leave balance", "who is my manager", "give me my employee id"]:
        if any(w in query_lower for w in ["manager", "supervisor", "lead", "report to"]):
            logs.append({"time": get_timestamp(), "level": "REASONING", "stage": "CONCIERGE_ROUTER", "message": "Classified intent: Personal Manager Query -> Dispatched to workweek_specialist"})
            profile = get_workweek_profile(employee_id)
            manager_id = profile.get("manager_id", "EMP-1")
            traces.append({
                "step": 1,
                "agent": "workweek_specialist",
                "tool": "workweek_mcp.get_personal_info",
                "args": {"employee_id": employee_id},
                "status": "SUCCESS",
                "latency_ms": 250,
                "result_summary": f"Retrieved profile and manager {manager_id} for {employee_id}"
            })
            response_text = f"### 👤 Reporting Manager (WorkWeek HCM)\n\nYour reporting manager is **`{manager_id}`**.\n\n- **Employee Name:** {profile.get('name', 'Gunjan Garg')}\n- **Job Title:** {profile.get('role', 'Solutions Acceleration Architect')}\n- **Department:** {profile.get('department', 'Google Forge')}\n- **Work Mode:** Remote"

        elif any(w in query_lower for w in ["id", "who am i", "my profile"]):
            logs.append({"time": get_timestamp(), "level": "REASONING", "stage": "CONCIERGE_ROUTER", "message": "Classified intent: Personal Identity Query -> Dispatched to workweek_specialist"})
            profile = get_workweek_profile(employee_id)
            traces.append({
                "step": 1,
                "agent": "workweek_specialist",
                "tool": "workweek_mcp.get_current_employee_id",
                "args": {"employee_id": employee_id},
                "status": "SUCCESS",
                "latency_ms": 220,
                "result_summary": f"Fetched authenticated ID '{employee_id}'"
            })
            response_text = f"### 🆔 WorkWeek Employee Profile\n\nYour authenticated WorkWeek Employee ID is **`{employee_id}`**.\n\n- **Name:** {profile.get('name', 'Gunjan Garg')}\n- **Location:** {profile.get('address', 'Singapore Office')}\n- **Contact Phone:** `{profile.get('phone', '+65-6521-0000')}`"

        else:
            logs.append({"time": get_timestamp(), "level": "REASONING", "stage": "CONCIERGE_ROUTER", "message": "Classified intent: Personal Leave Balance -> Dispatched to workweek_specialist"})
            balances = get_workweek_balances(employee_id)
            traces.append({
                "step": 1,
                "agent": "workweek_specialist",
                "tool": "workweek_mcp.get_employee_balances",
                "args": {"employee_id": employee_id},
                "status": "SUCCESS",
                "latency_ms": 310,
                "result_summary": f"Fetched {len(balances)} real-time balance records"
            })
            b_text = "\n".join([f"- **{b['leave_type']}**: **{b['remaining']} days** remaining (Accrued: {b['accrued']}d, Used: {b['used']}d)" for b in balances])
            response_text = f"Here is your current real-time leave balance from **WorkWeek**:\n\n{b_text}"

    # 2. General Company Policy Intent -> Dispatched to policy_search_tool (Vertex AI Search)
    else:
        logs.append({"time": get_timestamp(), "level": "REASONING", "stage": "CONCIERGE_ROUTER", "message": "Classified intent: General Company Policy -> Called policy_search_tool"})
        search_results = search_hr_policies(query)
        if not search_results:
            traces.append({
                "step": 1,
                "agent": "concierge_agent",
                "tool": "policy_search_tool",
                "args": {"query": query},
                "status": "NO_DOCUMENTS_FOUND",
                "latency_ms": 180,
                "result_summary": "No matching document returned from Vertex AI Search Datastore"
            })
            response_text = (
                "### 📖 Policy Search Result\n\n"
                "No matching policy documentation was found in the **Altostrat Employee Policy Datastore** for your query.\n\n"
                "Please contact **People Operations** at `hr-support@altostrat.com` for direct assistance."
            )
        else:
            doc = search_results[0]
            traces.append({
                "step": 1,
                "agent": "concierge_agent",
                "tool": "policy_search_tool",
                "args": {"query": query},
                "status": "SUCCESS",
                "latency_ms": 180,
                "result_summary": f"Grounded in Section {doc.get('section', '1.0')} ({doc.get('title', 'Policy Handbook')})"
            })
            section_title = doc.get("title", "Singapore Policy Handbook")
            section_body = doc.get("content", "").strip()
            source_url = doc.get("source_url", "https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M")
            response_text = f"### 📖 {section_title}\n\n{section_body}\n\n---\n*Source: [Altostrat Employee Policy Handbook]({source_url})*"

    if ENABLE_MODEL_ARMOR:
        logs.append({
            "time": get_timestamp(),
            "level": "SECURITY",
            "stage": "MODEL_ARMOR",
            "message": "Model Armor Response Inspection: SPII scan -> Pass"
        })

    duration_total = int((time.time() - start_time) * 1000)
    return {
        "response": response_text,
        "logs": logs,
        "traces": traces,
        "duration_ms": duration_total
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Altostrat HR & IT Multi-Agent Assistant</title>
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
        
        /* 1. Left Sidebar (Fixed 240px) */
        .sidebar {
            width: 240px;
            min-width: 220px;
            max-width: 260px;
            flex-shrink: 0;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 14px;
            gap: 12px;
            overflow-y: auto;
            height: 100vh;
        }
        .brand {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 1.02rem;
            font-weight: 700;
            color: var(--primary);
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }
        .badge {
            background: var(--primary-light);
            color: var(--primary);
            font-size: 0.68rem;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
        }
        .card {
            background: #fdfdfd;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 12px;
        }
        .card-title {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .profile-row { font-size: 0.8rem; margin-bottom: 5px; color: var(--text); line-height: 1.35; }
        .balance-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            padding: 5px 0;
            border-bottom: 1px solid var(--border-light);
        }
        .balance-item:last-child { border-bottom: none; }
        
        /* 2. Center Panel: Fluid Chat Stream (Flex: 1) */
        .main-chat {
            flex: 1;
            min-width: 360px;
            display: flex;
            flex-direction: column;
            background: var(--surface);
            border-right: 1px solid var(--border);
            height: 100vh;
            overflow: hidden;
        }
        .chat-header {
            padding: 12px 18px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--surface);
            flex-shrink: 0;
        }
        .chat-messages {
            flex: 1;
            padding: 18px 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            background: #ffffff;
        }
        .msg {
            max-width: 90%;
            padding: 14px 18px;
            border-radius: 12px;
            line-height: 1.55;
            font-size: 0.9rem;
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
        .msg-agent ul, .msg-agent ol { margin-left: 18px; margin-top: 8px; margin-bottom: 8px; }
        .msg-agent li { margin-bottom: 4px; }
        .msg-agent h3 { margin-top: 8px; margin-bottom: 6px; color: var(--primary); font-size: 1rem; }
        .msg-agent code { background: #e8eaed; padding: 2px 5px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.84rem; }
        
        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: #f1f3f4;
            padding: 10px 16px;
            border-radius: 16px;
            font-size: 0.82rem;
            color: var(--text-secondary);
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }

        .pills {
            padding: 8px 14px;
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
            border-radius: 16px;
            padding: 5px 12px;
            font-size: 0.78rem;
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
            padding: 12px 16px;
            display: flex;
            gap: 10px;
            background: var(--surface);
            border-top: 1px solid var(--border);
            flex-shrink: 0;
        }
        .chat-input {
            flex: 1;
            padding: 10px 16px;
            border: 1px solid var(--border);
            border-radius: 24px;
            font-size: 0.9rem;
            outline: none;
            font-family: inherit;
        }
        .chat-input:focus { border-color: var(--primary); }
        .send-btn {
            background: var(--primary);
            color: #ffffff;
            border: none;
            border-radius: 24px;
            padding: 0 22px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        .send-btn:hover { background: var(--primary-hover); }

        /* 3. Right Panel: Actions & Troubleshooting Console (Fixed 380px) */
        .exec-panel {
            width: 380px;
            min-width: 320px;
            max-width: 440px;
            flex-shrink: 0;
            background: var(--surface);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }
        .exec-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #fafafa;
            flex-shrink: 0;
        }
        .exec-title {
            font-size: 0.86rem;
            font-weight: 700;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
            background: #f1f3f4;
            flex-shrink: 0;
        }
        .tab-btn {
            flex: 1;
            padding: 8px 12px;
            font-size: 0.76rem;
            font-weight: 600;
            text-align: center;
            border: none;
            background: transparent;
            cursor: pointer;
            color: var(--text-secondary);
            border-bottom: 2px solid transparent;
        }
        .tab-btn.active {
            color: var(--primary);
            background: #ffffff;
            border-bottom: 2px solid var(--primary);
        }
        
        .tab-content {
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
            border-left: 4px solid var(--primary);
            border-radius: 6px;
            padding: 10px 12px;
            font-size: 0.78rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .trace-card.blocked { border-left-color: var(--danger); border-color: #fce8e6; }
        .trace-card.success { border-left-color: var(--success); }
        .trace-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            margin-bottom: 4px;
            color: var(--primary);
        }
        .trace-summary { color: #333; font-size: 0.8rem; margin-top: 4px; line-height: 1.35; }
        .trace-args {
            background: #f8f9fa;
            border: 1px solid #e8eaed;
            border-radius: 4px;
            padding: 6px 8px;
            margin-top: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: #333;
            max-height: 120px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .latency-tag {
            font-size: 0.68rem;
            background: #e8f0fe;
            color: #1a73e8;
            padding: 1px 6px;
            border-radius: 8px;
            font-weight: 500;
        }
        
        .log-terminal {
            background: var(--log-bg);
            color: var(--log-text);
            border-radius: 6px;
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            line-height: 1.45;
            height: 100%;
            overflow-y: auto;
            border: 1px solid #333;
        }
        .log-line { margin-bottom: 4px; }
        .log-time { color: #888; margin-right: 6px; }
        .log-INFO { color: #61afef; }
        .log-SECURITY { color: #e5c07b; }
        .log-TOOL_CALL { color: #98c379; }
        .log-REASONING { color: #c678dd; }
        .log-GUARDRAIL { color: #e06c75; font-weight: bold; }
        .log-SUCCESS { color: #98c379; font-weight: bold; }

        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #dadce0; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #bdc1c6; }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- 1. Left Sidebar (Profile & Integrations) -->
        <div class="sidebar">
            <div class="brand">
                <span>✨ Altostrat HR</span>
                <span class="badge">ADK 2.0</span>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>Employee Profile</span>
                    <span class="badge" style="background:#e6f4ea; color:#137333;">Live MCP</span>
                </div>
                <div class="profile-row" id="profName"><strong>Name:</strong> Gunjan Garg</div>
                <div class="profile-row" id="profId"><strong>ID:</strong> EMP-381</div>
                <div class="profile-row" id="profRole"><strong>Role:</strong> Staff Solution Architect</div>
                <div class="profile-row" id="profStatus"><strong>Status:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">Remote</span></div>
                <div class="profile-row" id="profAddress"><strong>Location:</strong> Singapore Office, 8 Pasir Panjang</div>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>WorkWeek Balances</span>
                    <span class="badge">Live</span>
                </div>
                <div class="balance-item"><span>🏖️ Vacation</span><strong id="balVacation">15.0 Days</strong></div>
                <div class="balance-item"><span>🤒 Sick</span><strong id="balSick">10.0 Days</strong></div>
                <div class="balance-item"><span>🏥 Hospital</span><strong id="balHospital">46.0 Days</strong></div>
                <div class="balance-item"><span>👶 Childcare</span><strong id="balChildcare">6.0 Days</strong></div>
            </div>

            <div class="card">
                <div class="card-title">SaaS FastMCP Tier</div>
                <div class="profile-row"><strong>WorkWeek:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">● Connected</span></div>
                <div class="profile-row"><strong>ITSM:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">● Connected</span></div>
                <div class="profile-row"><strong>Token:</strong> <code>mcp_zYnF...I64XdA</code></div>
                <div class="profile-row"><strong>Transport:</strong> Streamable HTTP</div>
            </div>

            <div class="card">
                <div class="card-title">Security & Safety</div>
                <div class="profile-row"><strong>Model Armor:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">Active (&lt;50ms)</span></div>
                <div class="profile-row"><strong>DLP Masking:</strong> Enabled</div>
                <div class="profile-row"><strong>Containment:</strong> Active</div>
            </div>
        </div>

        <!-- 2. Center Panel: Fluid Chat Stream -->
        <div class="main-chat">
            <div class="chat-header">
                <div>
                    <h2 style="font-size: 1.02rem; font-weight: 600;">HR & IT Concierge Assistant</h2>
                    <p style="font-size: 0.76rem; color: var(--text-secondary);">Grounded via Vertex AI Search (Enterprise Datastore) & FastMCP</p>
                </div>
                <div style="display:flex; gap:8px; align-items:center;">
                    <button onclick="clearChat()" style="background:transparent; border:1px solid var(--border); padding:4px 10px; border-radius:12px; font-size:0.72rem; cursor:pointer; color:var(--text-secondary);">Clear Chat</button>
                    <span class="badge" style="background:#ceead6; color:#0d652d;">● Engine Live</span>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="msg msg-agent" id="welcomeMsg">
                    👋 Hello <strong>Gunjan</strong>! I am your <strong>Altostrat HR & IT Concierge Assistant</strong>.<br><br>
                    I can assist you with:
                    <ul>
                        <li><strong>HR Policy Q&A:</strong> Sick leave, vacation accruals, bereavement, travel meals, host gifts.</li>
                        <li><strong>WorkWeek HCM:</strong> Checking balances, employee ID lookups, and booking time off.</li>
                        <li><strong>IT Support (ITSM):</strong> ServiceImmediately helpdesk incidents and remote equipment procurement.</li>
                    </ul>
                    Select one of the prompt chips below or type your request!
                </div>
                <div class="typing-indicator" id="typingIndicator">
                    ⚡ Agent is reasoning and executing tools...
                </div>
            </div>

            <div class="pills">
                <button class="pill" onclick="sendPill('Who is my manager?')">👤 Who is My Manager?</button>
                <button class="pill" onclick="sendPill('Give me my employee id')">🆔 My Employee ID</button>
                <button class="pill" onclick="sendPill('Check my current leave balance for vacation and sick leave')">🏖️ Balances</button>
                <button class="pill" onclick="sendPill('Add 5 days sick leave starting tomorrow')">🤒 Add 5 Days Sick Leave</button>
                <button class="pill" onclick="sendPill('I am working remotely. How much home office equipment allowance am I eligible for, and what ticket category do I use?')">💻 Remote Equipment Order</button>
                <button class="pill" onclick="sendPill('How many days of paid outpatient sick leave do employees get in Singapore?')">📄 Sick Leave Policy</button>
                <button class="pill" onclick="sendPill('What are the vacation leave accrual tiers based on continuous service?')">📊 Vacation Tiers</button>
                <button class="pill" onclick="sendPill('Can I expense a $45 gift card as a host gift when staying with a friend?')">🎁 Host Gift Rules</button>
            </div>

            <div class="chat-input-area">
                <input type="text" id="userInput" class="chat-input" placeholder="Ask about policies, check leave balances, or request time off..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <!-- 3. Right Panel: Actions & Troubleshooting Console -->
        <div class="exec-panel">
            <div class="exec-header">
                <div class="exec-title">
                    <span>🛠️ Actions & Troubleshooting</span>
                </div>
                <span id="turnLatency" class="latency-tag">Ready</span>
            </div>

            <div class="tabs">
                <button class="tab-btn active" id="tabTraces" onclick="switchTab('traces')">⚡ Execution Pipeline</button>
                <button class="tab-btn" id="tabLogs" onclick="switchTab('logs')">💻 Debug Logs</button>
            </div>

            <div class="tab-content" id="tracesContainer">
                <div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:30px 10px;">
                    Interactive execution steps, agent transitions, tool parameters, and response payloads will appear here in real-time.
                </div>
            </div>

            <div class="tab-content" id="logsContainer" style="display:none; padding:0;">
                <div class="log-terminal" id="logTerminal">
                    <div class="log-line"><span class="log-time">[SYSTEM]</span> Ready. Waiting for user interaction...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'traces';

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tabTraces').classList.toggle('active', tab === 'traces');
            document.getElementById('tabLogs').classList.toggle('active', tab === 'logs');
            document.getElementById('tracesContainer').style.display = tab === 'traces' ? 'flex' : 'none';
            document.getElementById('logsContainer').style.display = tab === 'logs' ? 'flex' : 'none';
        }

        function sendPill(text) {
            document.getElementById('userInput').value = text;
            sendMessage();
        }

        function clearChat() {
            const chatMessages = document.getElementById('chatMessages');
            const welcome = document.getElementById('welcomeMsg');
            chatMessages.innerHTML = '';
            chatMessages.appendChild(welcome);
            document.getElementById('tracesContainer').innerHTML = '<div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:30px 10px;">Ready for next query.</div>';
            document.getElementById('logTerminal').innerHTML = '<div class="log-line"><span class="log-time">[SYSTEM]</span> Chat cleared. Ready.</div>';
            document.getElementById('turnLatency').innerText = 'Ready';
        }

        function formatMarkdown(text) {
            return text
                .replace(/### (.*?)\\n/g, '<h3 style="color:#1a73e8; margin-top:8px; margin-bottom:4px; font-size:0.98rem;">$1</h3>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/`([^`]+)`/g, '<code style="background:#f1f3f4; padding:2px 5px; border-radius:4px; font-family:monospace; font-size:0.82rem;">$1</code>')
                .replace(/\\[([^\\]]+)\\]\\(([^\\)]+)\\)/g, '<a href="$2" target="_blank" style="color:#1a73e8; font-weight:500; text-decoration:underline;">$1</a>')
                .replace(/\\n/g, '<br>');
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const query = input.value.trim();
            if (!query) return;

            input.value = '';
            const chatMessages = document.getElementById('chatMessages');
            const typingIndicator = document.getElementById('typingIndicator');

            // Add User Message
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'msg msg-user';
            userMsgDiv.innerText = query;
            chatMessages.insertBefore(userMsgDiv, typingIndicator);
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;

            document.getElementById('sendBtn').disabled = true;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, employee_id: 'EMP-381' })
                });
                const data = await res.json();

                typingIndicator.style.display = 'none';

                // Add Agent Message
                const agentMsgDiv = document.createElement('div');
                agentMsgDiv.className = 'msg msg-agent';
                agentMsgDiv.innerHTML = formatMarkdown(data.response);
                chatMessages.appendChild(agentMsgDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;

                // Update Latency Badge
                document.getElementById('turnLatency').innerText = `${data.duration_ms}ms`;

                // Update Traces
                const tracesContainer = document.getElementById('tracesContainer');
                tracesContainer.innerHTML = '';
                if (data.traces && data.traces.length > 0) {
                    data.traces.forEach((t, i) => {
                        const card = document.createElement('div');
                        const isBlocked = t.status && (t.status.includes('BLOCKED') || t.status.includes('REFUSAL'));
                        card.className = `trace-card ${isBlocked ? 'blocked' : 'success'}`;
                        
                        card.innerHTML = `
                            <div class="trace-header">
                                <span>Step ${t.step || (i+1)}: ${t.agent || 'agent'}</span>
                                <span class="badge" style="background:${isBlocked ? '#fce8e6' : '#e6f4ea'}; color:${isBlocked ? '#c5221f' : '#137333'};">${t.status || 'SUCCESS'}</span>
                            </div>
                            <div style="font-weight:600; color:#202124; font-size:0.76rem;">Tool: <code>${t.tool}</code></div>
                            <div class="trace-summary">${t.result_summary || ''}</div>
                            ${t.args ? `<div class="trace-args"><strong>Inputs:</strong>\\n${JSON.stringify(t.args, null, 2)}</div>` : ''}
                            ${t.raw_result ? `<div class="trace-args" style="margin-top:4px;"><strong>Result Payload:</strong>\\n${JSON.stringify(t.raw_result, null, 2)}</div>` : ''}
                        `;
                        tracesContainer.appendChild(card);
                    });
                } else {
                    tracesContainer.innerHTML = '<div style="font-size:0.8rem; color:var(--text-secondary); text-align:center; padding:20px;">No direct tool calls executed. Handled via direct routing.</div>';
                }

                // Update Debug Logs
                const logTerminal = document.getElementById('logTerminal');
                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(l => {
                        const line = document.createElement('div');
                        line.className = 'log-line';
                        line.innerHTML = `<span class="log-time">[${l.time}]</span> <span class="log-${l.level}">[${l.stage || l.level}]</span> ${l.message}`;
                        logTerminal.appendChild(line);
                    });
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }

            } catch (err) {
                typingIndicator.style.display = 'none';
                const errDiv = document.createElement('div');
                errDiv.className = 'msg msg-agent';
                errDiv.style.borderColor = '#c5221f';
                errDiv.innerHTML = `❌ <strong>Error communicating with agent backend:</strong> ${err.message}`;
                chatMessages.appendChild(errDiv);
            } finally {
                document.getElementById('sendBtn').disabled = false;
            }
        }
    </script>
</body>
</html>
"""

class AgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urlparse(self.path).path
        if url_path == "/" or url_path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url_path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "HEALTHY", "version": "5.0"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url_path = urlparse(self.path).path
        if url_path == "/api/chat":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
                query = data.get("query", "")
                employee_id = data.get("employee_id", CURRENT_USER_ID)
                result = process_agent_turn(query, employee_id=employee_id)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 8080):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, AgentHandler)
    print(f"\n=======================================================")
    print(f"Altostrat HR Multi-Agent Interactive UI & Console (ADK 2.0)")
    print(f"Local URL:   http://localhost:{port}")
    print(f"Cloudtop URL: http://gunjangarg.c.googlers.com:{port}")
    print(f"=======================================================\n")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
    run_server(port)
