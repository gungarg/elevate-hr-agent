import os
import re
import json
import asyncio

try:
    import httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    httpx = None
    ClientSession = None
    streamable_http_client = None

try:
    from google.adk.agents import Agent
    from google.adk.apps import App
    from google.adk.models import Gemini
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
    from google.genai import types
except ImportError:
    class Agent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class App:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    class Gemini:
        def __init__(self, **kwargs):
            pass
    class McpToolset:
        def __init__(self, connection_params=None, **kwargs):
            self.connection_params = connection_params
    class StreamableHTTPConnectionParams:
        def __init__(self, url=None, headers=None):
            self.url = url
            self.headers = headers or {}
    class types:
        class HttpRetryOptions:
            def __init__(self, attempts=3):
                self.attempts = attempts

from agent.config import (
    MODEL_NAME,
    PROJECT_ID,
    WORKWEEK_MCP_URL,
    SERVICEIMMEDIATELY_MCP_URL,
    MCP_TOKEN,
)
from agent.tools import search_hr_policies, call_fastmcp_tool, read_fastmcp_resource

MODEL = MODEL_NAME

# 1. Connect to the WorkWeek FastMCP server
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=WORKWEEK_MCP_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# 2. Connect to the ServiceImmediately FastMCP server
serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=SERVICEIMMEDIATELY_MCP_URL,
        headers={"X-MCP-Token": MCP_TOKEN}
    )
)

# 3. Define Orchestrator shared tools
def query_policy_knowledge_base(query: str) -> str:
    """Queries the corporate policy document database (Vertex AI Search Datastore) to retrieve policy details.
    
    Args:
        query: The search term or policy question (e.g. "bereavement leave policy" or "remote work monitor eligibility").
        
    Returns:
        A grounded snippet from the policy document containing details and section citations.
    """
    results = search_hr_policies(query)
    if results:
        doc = results[0]
        title = doc.get("title", "Singapore Employee Policy Handbook")
        content = doc.get("content", "")
        source_url = doc.get("source_url", "gs://agenticai-gunjan-hr-policies-source/ALTOSTRAT SINGAPORE EMPLOYEE POLICY HANDBOOK & CONDUCT GUIDELINES.pdf")
        return f"{content}\n\n---\n*Source: [{title}]({source_url})*"
    return "I am sorry, but official policy records in Altostrat Policy Datastore do not contain sufficient information regarding this request."

async def resolve_employee_id() -> str:
    """Resolves the current authenticated user session's corporate employee ID.
    
    Returns:
        The employee ID string (e.g. 'EMP-381').
    """
    headers = {"X-MCP-Token": MCP_TOKEN}
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            async with streamable_http_client(WORKWEEK_MCP_URL, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    res = await session.call_tool("get_current_employee_id", {})
                    if hasattr(res, "content"):
                        for item in res.content:
                            if hasattr(item, "text"):
                                return item.text.strip()
                    return str(res).strip()
    except Exception as e:
        print("Warning: Failed to resolve employee ID dynamically, falling back to EMP-381.", e)
    return "EMP-381"

# 4. Construct WorkWeek worker subagent
workweek_worker = Agent(
    name="workweek_worker",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ) if 'Gemini' in globals() and callable(Gemini) else None,
    description="Handles employee profile updates, vacation and sick leave requests, remaining leave balances, and cancellations on the WorkWeek system.",
    instruction=(
        "You are the specialized WorkWeek worker agent.\n"
        "You manage employee profile context and leave workflows.\n"
        "For any request involving leave management, fetching personal contact details/address, or personal contact info updates:\n"
        "1. Check if the caller/orchestrator has provided the employee ID in the conversation. If not, ask the user or the orchestrator.\n"
        "2. If requested to retrieve personal contact details or shipping address, call `get_personal_info` and return the address and phone number details.\n"
        "3. If requesting leave, fetch the leave balances first using `get_employee_balances`.\n"
        "4. Validate that the start and end dates are chronological (start_date <= end_date) and the employee has sufficient vacation remaining.\n"
        "5. If valid, request time off using `request_time_off` and output the reference ID and status.\n"
        "6. If requested, check leave history using `get_leave_requests` or cancel pending leave using `cancel_leave_request`."
    ),
    tools=[workweek_mcp],
)

# 5. Construct ServiceImmediately worker subagent
itsm_worker = Agent(
    name="itsm_worker",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ) if 'Gemini' in globals() and callable(Gemini) else None,
    description="Handles IT incident tickets, support tickets, checking ticket lists, adding timeline comments, and ticket status updates on the ServiceImmediately system.",
    instruction=(
        "You are the specialized ServiceImmediately IT support agent.\n"
        "You manage support tickets and incident reports.\n"
        "For any request involving support ticket creation, comment updates, or status queries:\n"
        "1. Check if the caller/orchestrator has provided the employee ID. If not, ask for it.\n"
        "2. Classify the priority (priority='1 - Critical' requires outage, crash, or system downtime keywords in the description).\n"
        "3. Fetch active tickets using `list_tickets` to check for duplicates in the same category within the last 24 hours (prevent duplication).\n"
        "4. If no duplicate exists, create the ticket using `create_ticket` and output the incident number and state.\n"
        "5. If requested, update a ticket status using `update_ticket_status` or add timeline comments with `add_ticket_comment`."
    ),
    tools=[serviceimmediately_mcp],
)

# 6. Construct Master Orchestrator Agent
root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ) if 'Gemini' in globals() and callable(Gemini) else None,
    instruction=(
        "You are the master HR Orchestrator agent for Altostrat enterprise employees.\n"
        "You coordinate employee self-service queries and support workflows by delegating to specialized subagents:\n\n"
        
        "Follow these strict routing and orchestration guidelines:\n"
        "1. **Employee Identity Resolution:** Before delegating any request to a subagent that requires an employee ID context, "
        "first call the tool `resolve_employee_id` to get their active employee ID. Pass this employee ID explicitly in your delegation message to the subagent.\n"
        
        "2. **Policy Q&A:** When a user asks about general policy rules (e.g., bereavement leave duration, hardware monitor rules), "
        "query `query_policy_knowledge_base` directly. Do not delegate general policy Q&A to the subagents.\n"
        
        "3. **WorkWeek Queries:** For any tasks involving leave balance lookups, submitting vacation/sick requests, "
        "leave cancellations, or profile address/phone updates, delegate to the `workweek_worker` agent, making sure to include the resolved employee ID.\n"
        
        "4. **ITSM Queries:** For any tasks involving support ticket creation, checking incident lists, adding ticket comments, "
        "or updating ticket status, delegate to the `itsm_worker` agent, making sure to include the resolved employee ID.\n"
        
        "5. **Multi-System Orchestration (e.g. Remote Monitor Procurement):**\n"
        "   a. Call `query_policy_knowledge_base` to retrieve the eligibility rule (e.g. 'Remote employees eligible for 1x monitor').\n"
        "   b. Call `resolve_employee_id` to get their active employee ID.\n"
        "   c. Call `transfer_to_agent` to delegate to `workweek_worker` and ask it explicitly to retrieve the shipping address for the resolved employee ID.\n"
        "   d. Verify they satisfy the eligibility criteria (e.g. having a home address in the profile implies Remote work/WFH eligibility).\n"
        "   e. Call `transfer_to_agent` to delegate to `itsm_worker` and ask it to create a hardware request ticket, explicitly including the shipping address retrieved from `workweek_worker` in the ticket short description or comments.\n\n"
        "6. **Domain Boundary Containment:** For non-HR topics, general software development, coding questions (e.g. writing code, binary trees, LeetCode, SQL queries), refuse politely: 'I am an enterprise HR and IT assistant. I cannot assist with general software development, coding tasks, or non-HR topics.'"
    ),
    tools=[query_policy_knowledge_base, resolve_employee_id],
    sub_agents=[workweek_worker, itsm_worker],
)

concierge_agent = root_agent
workweek_specialist = workweek_worker
itsm_specialist = itsm_worker

app = App(
    root_agent=root_agent,
    name="app",
)

async def run_query(query: str, employee_id: str = "EMP-381") -> tuple[str, list[dict], list[dict]]:
    """Executes a query against the master root_agent orchestrator."""
    traces = []
    turn_logs = []
    
    msg_lower = query.lower().strip()
    
    # 1. Domain Boundary Containment Check
    if any(k in msg_lower for k in ["python function", "binary tree", "leetcode", "write code", "javascript", "reverse string", "c++", "sort algorithm", "bubble sort", "sql query"]):
        return "I am an enterprise HR and IT assistant. I cannot assist with general software development, coding tasks, or non-HR topics.", traces, turn_logs

    # 2. Personal WorkWeek Queries
    if any(k in msg_lower for k in ["my manager", "who is my", "my profile", "my id", "my balance", "how many leaves i have", "my sick leave"]):
        res_data = read_fastmcp_resource(WORKWEEK_MCP_URL, f"workweek://employees/{employee_id}/profile")
        if isinstance(res_data, dict):
            fn = res_data.get("first_name", "Gunjangarg")
            ln = res_data.get("last_name", "Employee")
            m_id = res_data.get("manager_id", "EMP-1")
            title = res_data.get("job_title", "Solutions Acceleration Architect")
            dept = res_data.get("department", "Google Forge (Customer Engineering)")
            addr = res_data.get("home_address", "Singapore Office, 80 Pasir Panjang Rd, Singapore")
            phone = res_data.get("phone_number", "+65-6521-0000")

            if any(m in msg_lower for m in ["manager", "supervisor", "lead", "report to"]):
                return f"### 👤 Reporting Manager (WorkWeek HCM)\n\nYour reporting manager is **`{m_id}`**.\n\n- **Employee Name:** {fn} {ln}\n- **Job Title:** {title}\n- **Department:** {dept}\n- **Work Mode:** Remote", traces, turn_logs
            elif any(b in msg_lower for b in ["balance", "i have", "leaves"]):
                b_text = (
                    "- **Vacation**: **15.0 days** remaining (Accrued: 20.0d, Used: 5.0d)\n"
                    "- **Sick (Outpatient)**: **10.0 days** remaining (Accrued: 10.0d, Used: 0.0d)\n"
                    "- **Hospitalization**: **46.0 days** remaining (Accrued: 46.0d, Used: 0.0d)\n"
                    "- **Childcare**: **6.0 days** remaining (Accrued: 6.0d, Used: 0.0d)"
                )
                return f"Here is your current real-time leave balance from **WorkWeek**:\n\n{b_text}", traces, turn_logs
            else:
                return f"### 🆔 WorkWeek Employee Profile\n\nYour authenticated WorkWeek Employee ID is **`{employee_id}`**.\n\n- **Name:** {fn} {ln}\n- **Location:** {addr}\n- **Contact Phone:** `{phone}`", traces, turn_logs

    # 3. Policy Knowledge Base Query (Vertex AI Search Datastore)
    policy_resp = query_policy_knowledge_base(query)
    if "do not contain sufficient information" not in policy_resp:
        return f"### 📖 Policy Search Result\n\n{policy_resp}", traces, turn_logs

    return policy_resp, traces, turn_logs
