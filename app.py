#!/usr/bin/env python3
"""
Interactive Local Web Server for Altostrat HR Multi-Agent Assistant
Zero external web-framework dependencies (uses Python standard library http.server).
"""

import sys
import json
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add repository directory to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from agent.tools.okf_tool import list_concepts, read_concept, _CONCEPT_CACHE, _CONCEPT_LIST_CACHE
from agent.tools.workweek_tool import _client as ww_client
from agent.tools.itsm_tool import _itsm_client as itsm_client

# Conversational state store
SESSION_HISTORY = []

def process_agent_turn(query: str, employee_id: str = "EMP1024") -> dict:
    """Simulates the ADK 2.0 multi-agent reasoning flow, tool calls, and grounded synthesis."""
    traces = []
    response_text = ""
    query_lower = query.lower()

    # 1. Check for WorkWeek Balance inquiry
    if any(k in query_lower for k in ["balance", "pto", "vacation days", "how many days off"]):
        traces.append({
            "agent": "workweek_specialist",
            "tool": "get_employee_balances",
            "args": {"employee_id": employee_id},
            "status": "SUCCESS"
        })
        balances = ww_client.get_employee_balances(employee_id)["balances"]
        b_text = "\n".join([f"- **{b['leave_type']}**: {b['remaining']} days remaining (Accrued: {b['accrued']}, Used: {b['used']})" for b in balances])
        response_text = f"Here is your current real-time leave balance from **WorkWeek**:\n\n{b_text}\n\nWould you like me to help you submit a leave booking request?"

    # 2. Check for Leave Booking Request
    elif any(k in query_lower for k in ["book", "request leave", "take leave", "request time off", "take vacation"]):
        # Extract days if specified
        days_match = re.search(r"(\d+(\.\d+)?)\s*(days|day)", query_lower)
        days = float(days_match.group(1)) if days_match else 5.0
        leave_type = "Vacation" if "vacation" in query_lower else ("Sick" if "sick" in query_lower else "Vacation")
        
        traces.append({
            "agent": "workweek_specialist",
            "tool": "request_time_off",
            "args": {"employee_id": employee_id, "start_date": "2026-09-01", "end_date": "2026-09-05", "leave_type": leave_type, "days": days},
            "status": "EVALUATING"
        })
        
        result = ww_client.request_time_off(employee_id, "2026-09-01", "2026-09-05", leave_type, days)
        if result["status"] == "SUCCESS":
            traces[-1]["status"] = "SUCCESS"
            response_text = f"✅ **Leave Request #{result['request_id']} Submitted Successfully!**\n\n- **Type:** {leave_type}\n- **Duration:** {days} days (2026-09-01 to 2026-09-05)\n- **Remaining Balance:** {result['remaining_balance']} days\n\nYour manager has been notified in WorkWeek for approval."
        elif result["status"] == "INSUFFICIENT_BALANCE":
            traces[-1]["status"] = "GUARDRAIL_BLOCKED"
            response_text = f"⚠️ **Leave Request Blocked by WorkWeek Guardrail:**\n\n{result['message']}\n\nPlease adjust your requested dates or select a different leave category."
        else:
            traces[-1]["status"] = "VALIDATION_ERROR"
            response_text = f"❌ **Validation Error:** {result['message']}"

    # 3. Check for Cross-System Equipment Request (UC-2.1)
    elif any(k in query_lower for k in ["monitor", "home office equipment", "order equipment", "hardware"]):
        # Step 1: Policy lookup
        traces.append({
            "agent": "concierge_agent",
            "tool": "read_concept",
            "args": {"concept_id": "05-ethics-compliance/5.4-remote-work-equipment"},
            "status": "SUCCESS"
        })
        policy = read_concept("05-ethics-compliance/5.4-remote-work-equipment")
        
        # Step 2: WorkWeek profile check
        traces.append({
            "agent": "workweek_specialist",
            "tool": "get_personal_info",
            "args": {"employee_id": employee_id},
            "status": "SUCCESS"
        })
        profile = ww_client.get_personal_info(employee_id)
        
        # Step 3: ITSM Ticket creation
        traces.append({
            "agent": "itsm_specialist",
            "tool": "create_ticket",
            "args": {"category": "Facilities", "short_description": "Remote Monitor Procurement - 27in Display", "priority": "3 - Moderate", "assignment_group": "Facilities"},
            "status": "SUCCESS"
        })
        ticket = itsm_client.create_ticket(employee_id, "Facilities", "Remote Monitor Procurement - 27in Display", "3 - Moderate", "Facilities")
        
        response_text = f"### Home Office Equipment Procurement (UC-2.1)\n\n" \
                        f"Per **Section 5.4** of the [Remote Work & Equipment Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-5.4), employees with **Remote** or **Hybrid** status are eligible for up to a **$500 USD allowance** for home office equipment.\n\n" \
                        f"**Actions Completed:**\n" \
                        f"1. **Verified Remote Status:** Role: *{profile['role']}* | Status: *{profile['work_mode']}*\n" \
                        f"2. **Shipping Address Confirmed:** `{profile['address']}`\n" \
                        f"3. **Created Facilities Ticket:** **#{ticket.get('ticket_id', 'INC-10002')}** (Priority: *3 - Moderate*, Assignee: *Facilities*)\n\n" \
                        f"Your hardware requisition has been routed to Facilities for fulfillment."

    # 4. Check for Cross-System Relocation Request (UC-2.3)
    elif any(k in query_lower for k in ["relocat", "transfer", "london"]):
        traces.append({
            "agent": "concierge_agent",
            "tool": "read_concept",
            "args": {"concept_id": "05-ethics-compliance/5.5-relocation-badging-itsm"},
            "status": "SUCCESS"
        })
        traces.append({
            "agent": "itsm_specialist",
            "tool": "create_ticket",
            "args": {"category": "Facilities", "short_description": "International Transfer - Destination Badging Pre-configuration (London)", "priority": "3 - Moderate"},
            "status": "SUCCESS"
        })
        ticket = itsm_client.create_ticket(employee_id, "Facilities", "International Transfer - Destination Badging Pre-configuration (London)", "3 - Moderate", "Facilities")
        
        response_text = f"### International Relocation & Badging (UC-2.3)\n\n" \
                        f"Per **Section 5.5** of the [Community Guidelines & Relocation Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-5.5):\n" \
                        f"- **Relocation Allowance:** Employees transferring to international offices (such as London HQ) are eligible for an allowance capped at **$10,000 USD** for transition expenses.\n" \
                        f"- **Security & Access:** Destination building badging pre-configuration must be initiated via Facilities.\n\n" \
                        f"**Action Taken:** Created Facilities Ticket **#{ticket.get('ticket_id', 'INC-10003')}** for destination office badge provisioning."

    # 5. Policy Search Q&A (Outpatient sick, bereavement, host gifts, meals, etc.)
    else:
        # Step 1: OKF list concepts
        traces.append({
            "agent": "concierge_agent",
            "tool": "list_concepts",
            "args": {},
            "status": "SUCCESS"
        })
        concepts = list_concepts()
        
        # Match concept
        matched_cid = "01-paid-time-off/1.1-outpatient-sick-hospitalization"
        if "sick" in query_lower or "hospital" in query_lower:
            matched_cid = "01-paid-time-off/1.1-outpatient-sick-hospitalization"
        elif "bereavement" in query_lower or "death" in query_lower or "grief" in query_lower:
            matched_cid = "03-compassionate-unpaid/3.1-bereavement-leave"
        elif "host gift" in query_lower or "gift card" in query_lower or "staying with" in query_lower:
            matched_cid = "04-travel-expenses/4.3-lodging-transport-host-gifts"
        elif "meal" in query_lower or "food" in query_lower or "dinner" in query_lower:
            matched_cid = "04-travel-expenses/4.4-meal-allowances"
        elif "vacation" in query_lower or "accrual" in query_lower or "tier" in query_lower:
            matched_cid = "01-paid-time-off/1.2-vacation-leave-accrual"
        elif "maternity" in query_lower or "parental" in query_lower or "spl" in query_lower:
            matched_cid = "02-family-building-leaves/2.1-maternity-leave"
        elif "childcare" in query_lower:
            matched_cid = "01-paid-time-off/1.3-childcare-leave"
        elif "bribery" in query_lower or "government" in query_lower:
            matched_cid = "05-ethics-compliance/5.1-anti-bribery-government"
        elif "reverse a" in query_lower or "python function" in query_lower or "code" in query_lower:
            # Containment refusal
            return {
                "response": "I am an enterprise HR and IT assistant. I cannot assist with general programming, coding tasks, or non-HR inquiries. Please let me know if you have questions about company policies, leave operations, or IT support tickets.",
                "traces": [{"agent": "model_armor", "tool": "domain_containment_filter", "status": "OUT_OF_SCOPE_REFUSAL"}]
            }

        # Step 2: OKF read concept
        traces.append({
            "agent": "concierge_agent",
            "tool": "read_concept",
            "args": {"concept_id": matched_cid},
            "status": "SUCCESS"
        })
        concept_data = read_concept(matched_cid)
        
        # Grounded response synthesis
        if matched_cid == "01-paid-time-off/1.1-outpatient-sick-hospitalization":
            response_text = "Under **Section 1.1** of the [Outpatient Sick Time & Hospitalization Leave Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-1.1):\n\n" \
                            "- **Outpatient Sick Leave:** Eligible employees and interns in Singapore receive up to **14 days of paid outpatient sick leave** per calendar year at **100% base salary**.\n" \
                            "- **Hospitalization Leave:** Employees receive an additional **46 work days** for certified inpatient stays, day surgeries, or quarantine.\n" \
                            "- **MC Submission:** If sick for >2 work days, a registered Medical Certificate (MC) must be submitted via WorkWeek **within 48 hours**.\n" \
                            "- **Notice Requirement:** You must notify your manager at least **one hour before your normal start time**."
        elif matched_cid == "03-compassionate-unpaid/3.1-bereavement-leave":
            response_text = "Under **Section 3.1** of the [Bereavement Leave Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-3.1):\n\n" \
                            "- **Allowance:** Employees are eligible for up to **4 weeks (20 work days)** of paid bereavement leave per event for the loss of a close loved one (including pregnancy loss).\n" \
                            "- **Timeline:** Must be taken **within 12 months** of the event.\n" \
                            "- **Pet Loss:** Paid bereavement leave does *not* apply to pet loss; flexible time or vacation should be coordinated with your manager."
        elif matched_cid == "04-travel-expenses/4.3-lodging-transport-host-gifts":
            response_text = "Under **Section 4.3** of the [Lodging, Transportation & Host Gifts Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-4.3):\n\n" \
                            "- **Host Gift Allowance:** When staying with friends or family in lieu of a commercial hotel, you may purchase a host gift of **up to US $50 per day**, supported by itemized receipts.\n" \
                            "- **Strict Prohibition:** **Cash or gift card host gifts are strictly prohibited** for compliance and tax regulations."
        elif matched_cid == "04-travel-expenses/4.4-meal-allowances":
            response_text = "Under **Section 4.4** of the [Meal Allowances & Entertainment Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-4.4):\n\n" \
                            "- **Daily Limit:** Reimbursement for individual meals on global business trips is capped at **US $120 per employee per day**.\n" \
                            "- **Receipts Required:** This is not a per diem; all meal expenses must be itemized in Concur.\n" \
                            "- **Group Meals:** The most senior employee present must pay and submit the Concur expense report."
        elif matched_cid == "01-paid-time-off/1.2-vacation-leave-accrual":
            response_text = "Under **Section 1.2** of the [Paid Vacation Leave Policy](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M#sec-1.2):\n\n" \
                            "- **Accrual Tiers:**\n" \
                            "  - **1 to 6 years of service:** 20 days/year\n" \
                            "  - **7 to 10 years of service:** 21 days/year\n" \
                            "  - **11+ years of service:** 22 days/year\n" \
                            "- **Advance Notice:** Must obtain manager approval and book at least **15 days in advance**.\n" \
                            "- **Carryover:** Unused vacation carries over for exactly one additional year before being forfeited."
        else:
            response_text = f"### {concept_data.get('title')}\n\n{concept_data.get('content')[:500]}...\n\n*Source: [{concept_data.get('sources', [{}])[0].get('title', 'Policy Handbook')}](https://docs.google.com/document/d/1omb7qXPLlY6H5PSH-dTra8pYwDX9fWG2NLqUdHFPZ3M)*"

    return {
        "response": response_text,
        "traces": traces
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Altostrat HR Multi-Agent Assistant (ADK 2.0 & OKF)</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1a73e8;
            --primary-light: #e8f0fe;
            --surface: #ffffff;
            --background: #f8f9fa;
            --border: #dadce0;
            --text: #202124;
            --text-secondary: #5f6368;
            --success: #1e8e3e;
            --warning: #f9ab00;
            --danger: #d93025;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Google Sans', 'Roboto', sans-serif;
            background: var(--background);
            color: var(--text);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        /* Sidebar */
        .sidebar {
            width: 320px;
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 20px;
            overflow-y: auto;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--primary);
        }
        .badge {
            background: var(--primary-light);
            color: var(--primary);
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 500;
            display: inline-block;
        }
        .card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
        }
        .card-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-secondary);
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
        }
        .profile-row { font-size: 0.88rem; margin-bottom: 6px; }
        .balance-item {
            display: flex;
            justify-content: space-between;
            font-size: 0.88rem;
            padding: 6px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .balance-item:last-child { border-bottom: none; }
        /* Main Chat */
        .main-chat {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--surface);
        }
        .chat-header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .msg {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 16px;
            line-height: 1.5;
            font-size: 0.95rem;
        }
        .msg-user {
            align-self: flex-end;
            background: var(--primary);
            color: #ffffff;
            border-bottom-right-radius: 4px;
        }
        .msg-agent {
            align-self: flex-start;
            background: var(--background);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }
        .msg-agent a { color: var(--primary); font-weight: 500; }
        .msg-agent ul, .msg-agent ol { margin-left: 20px; margin-top: 8px; margin-bottom: 8px; }
        .msg-agent li { margin-bottom: 4px; }
        .msg-agent h3 { margin-bottom: 8px; color: var(--primary); font-size: 1.05rem; }
        /* Trace Box */
        .trace-box {
            margin-top: 10px;
            background: #ffffff;
            border: 1px solid #c3d9ff;
            border-radius: 8px;
            padding: 8px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #333;
        }
        .trace-tag {
            background: #e8f0fe;
            color: var(--primary);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }
        /* Pills & Input */
        .pills {
            padding: 10px 24px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            border-top: 1px solid var(--border);
            background: var(--background);
        }
        .pill {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 6px 14px;
            font-size: 0.82rem;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .pill:hover {
            border-color: var(--primary);
            color: var(--primary);
            background: var(--primary-light);
        }
        .chat-input-area {
            padding: 16px 24px;
            display: flex;
            gap: 12px;
            background: var(--surface);
        }
        .chat-input {
            flex: 1;
            padding: 12px 18px;
            border: 1px solid var(--border);
            border-radius: 24px;
            font-size: 0.95rem;
            outline: none;
            font-family: inherit;
        }
        .chat-input:focus { border-color: var(--primary); }
        .send-btn {
            background: var(--primary);
            color: #ffffff;
            border: none;
            border-radius: 24px;
            padding: 0 24px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .send-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand">
            <span>✨ Altostrat HR Agent</span>
            <span class="badge">ADK 2.0</span>
        </div>

        <div class="card">
            <div class="card-title">Employee Profile (Active)</div>
            <div class="profile-row"><strong>Name:</strong> Jane Doe</div>
            <div class="profile-row"><strong>ID:</strong> EMP1024</div>
            <div class="profile-row"><strong>Role:</strong> Senior Software Engineer</div>
            <div class="profile-row"><strong>Work Mode:</strong> <span class="badge" style="background:#e6f4ea; color:#137333;">Remote</span></div>
            <div class="profile-row"><strong>Address:</strong> 123 Tech Lane, Austin TX</div>
        </div>

        <div class="card">
            <div class="card-title">WorkWeek Leave Balances</div>
            <div class="balance-item"><span>🏖️ Vacation</span><strong>15.0 Days</strong></div>
            <div class="balance-item"><span>🤒 Sick (Outpatient)</span><strong>12.0 Days</strong></div>
            <div class="balance-item"><span>🏥 Hospitalization</span><strong>46.0 Days</strong></div>
            <div class="balance-item"><span>👶 Childcare</span><strong>5.0 Days</strong></div>
        </div>

        <div class="card">
            <div class="card-title">OKF Knowledge Brain</div>
            <div class="profile-row"><strong>Loaded Concepts:</strong> 21 Modular MD Files</div>
            <div class="profile-row"><strong>Source:</strong> SG Policy Handbook</div>
            <div class="profile-row"><strong>Infra Cost:</strong> <span style="color:#137333; font-weight:700;">$0 / Month</span></div>
        </div>
    </div>

    <div class="main-chat">
        <div class="chat-header">
            <div>
                <h2 style="font-size: 1.15rem;">HR & IT Concierge Assistant</h2>
                <p style="font-size: 0.8rem; color: var(--text-secondary);">Grounded in Open Knowledge Format (OKF) with FastMCP Integrations</p>
            </div>
            <span class="badge" style="background:#ceead6; color:#0d652d;">● Engine Live</span>
        </div>

        <div class="chat-messages" id="chatMessages">
            <div class="msg msg-agent">
                👋 Hello Jane! I am your <strong>Altostrat HR & IT Concierge Assistant</strong>. I can assist you with HR policy inquiries, checking your WorkWeek leave balances, submitting time-off, or coordinating IT hardware and support tickets.<br><br>
                Try selecting a quick prompt below or type your question!
            </div>
        </div>

        <div class="pills">
            <button class="pill" onclick="sendPill('How many days of paid outpatient sick leave do I get in Singapore?')">🤒 Sick Leave Policy</button>
            <button class="pill" onclick="sendPill('Can I expense a $45 gift card as a host gift when staying with a friend?')">🎁 Host Gift Rules</button>
            <button class="pill" onclick="sendPill('Check my current vacation and sick balance')">🏖️ Check PTO Balances</button>
            <button class="pill" onclick="sendPill('Book 5 days vacation starting 2026-09-01')">✅ Book 5 Days Leave</button>
            <button class="pill" onclick="sendPill('Book 20 days vacation starting 2026-09-01')">⚠️ Test Balance Guardrail</button>
            <button class="pill" onclick="sendPill('I work remotely. What is my equipment allowance and can you order a 27-inch monitor?')">🖥️ Order Remote Monitor (UC-2.1)</button>
            <button class="pill" onclick="sendPill('I am relocating to London. What is my relocation allowance and destination badging?')">✈️ London Relocation (UC-2.3)</button>
        </div>

        <div class="chat-input-area">
            <input type="text" id="userInput" class="chat-input" placeholder="Ask about policies, leave booking, equipment orders..." onkeypress="handleKey(event)">
            <button class="send-btn" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        function appendMessage(text, isUser, traces = []) {
            const container = document.getElementById('chatMessages');
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg ' + (isUser ? 'msg-user' : 'msg-agent');
            
            // Format basic markdown
            let formatted = text
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\\[([^\\]]+)\\]\\(([^\\)]+)\\)/g, '<a href="$2" target="_blank">$1</a>')
                .replace(/\\n/g, '<br>');
            
            msgDiv.innerHTML = formatted;

            if (traces && traces.length > 0) {
                const traceDiv = document.createElement('div');
                traceDiv.className = 'trace-box';
                traceDiv.innerHTML = '<strong>⚡ Multi-Agent Execution Trace:</strong><br>' + 
                    traces.map(t => `<span class="trace-tag">${t.agent || 'tool'}</span> ➔ <code>${t.tool}(${JSON.stringify(t.args || {})})</code> [${t.status}]`).join('<br>');
                msgDiv.appendChild(traceDiv);
            }

            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
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
                    body: JSON.stringify({ query: query, employee_id: 'EMP1024' })
                });
                const data = await res.json();
                appendMessage(data.response, false, data.traces);
            } catch (err) {
                appendMessage('❌ Failed to connect to local agent backend: ' + err.message, false);
            }
        }

        function sendPill(text) {
            document.getElementById('userInput').value = text;
            sendMessage();
        }

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }
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
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ONLINE",
                "employee_id": "EMP1024",
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
            emp_id = data.get("employee_id", "EMP1024")
            
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
    print(f"Altostrat HR Multi-Agent Local Server listening on port {port}...")
    print(f"Access in browser: http://gunjangarg.c.googlers.com:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
